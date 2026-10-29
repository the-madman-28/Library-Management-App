"""ISBN-based book metadata lookup with provider fallback."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from app.services.isbn import (
    ISBNValidationError,
    is_matching_isbn,
    normalize_isbn,
)

logger = logging.getLogger(__name__)

# app/services/book_metadata.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

# Do not overwrite environment variables already set by the system.
load_dotenv(dotenv_path=ENV_FILE, override=False)

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()

TIMEOUT_SECONDS = (3.0, 5.0)

PROVIDER_URLS = {
    "google_books": "https://www.googleapis.com/books/v1/volumes",
    "open_library": "https://openlibrary.org/api/books",
    "crossref": "https://api.crossref.org/works",
}

FIELDS = ("title", "author", "publisher", "category")


def _get_json(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any],
    provider: str,
) -> dict[str, Any] | list[Any] | None:
    """Request JSON from a provider without exposing request errors."""
    try:
        response = session.get(
            url,
            params=params,
            timeout=TIMEOUT_SECONDS,
            headers={
                "User-Agent": "LibraryManagementApp/1.0"
            },
        )

        if response.status_code == 429 or response.status_code >= 500:
            logger.warning(
                "%s metadata provider is temporarily unavailable.",
                provider,
            )
            return None

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, (dict, list)):
            logger.warning(
                "%s returned an unexpected response.",
                provider,
            )
            return None

        return data

    except (requests.RequestException, ValueError):
        logger.warning(
            "%s metadata request failed.",
            provider,
        )
        return None


def _clean_text(value: Any) -> str | None:
    """Normalize text and limit its length."""
    if not isinstance(value, str):
        return None

    value = " ".join(value.split()).strip()

    if not value:
        return None

    return value[:500]


def _join_names(values: Any) -> str | None:
    """Convert provider lists of names into a single string."""
    if isinstance(values, str):
        return _clean_text(values)

    if not isinstance(values, list):
        return None

    names: list[str] = []

    for item in values:
        if isinstance(item, str):
            name = _clean_text(item)
        elif isinstance(item, dict):
            name = _clean_text(item.get("name"))
        else:
            name = None

        if name and name not in names:
            names.append(name)

    return _clean_text(", ".join(names)) if names else None


def _has_matching_isbn(
    requested_isbn: str,
    candidates: Any,
) -> bool:
    """Return True if a candidate ISBN matches the requested ISBN."""
    if isinstance(candidates, str):
        candidates = [candidates]

    if not isinstance(candidates, list):
        return False

    return any(
        isinstance(candidate, str)
        and is_matching_isbn(requested_isbn, candidate)
        for candidate in candidates
    )


def _google_books(
    session: requests.Session,
    isbn: str,
) -> dict[str, Any] | None:
    """Look up and verify a book using Google Books."""
    params: dict[str, Any] = {
        "q": f"isbn:{isbn}",
        "maxResults": 10,
    }

    # The API key is optional in this code, but recommended for Google Books.
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    data = _get_json(
        session,
        PROVIDER_URLS["google_books"],
        params=params,
        provider="Google Books",
    )

    if not isinstance(data, dict):
        return None

    items = data.get("items", [])

    if not isinstance(items, list):
        return None

    for item in items:
        if not isinstance(item, dict):
            continue

        info = item.get("volumeInfo")

        if not isinstance(info, dict):
            continue

        identifiers = info.get("industryIdentifiers", [])

        if not isinstance(identifiers, list):
            continue

        candidates = [
            entry.get("identifier")
            for entry in identifiers
            if isinstance(entry, dict)
        ]

        # Do not accept a record unless its ISBN can be verified.
        if not _has_matching_isbn(isbn, candidates):
            continue

        return {
            "title": _clean_text(info.get("title")),
            "author": _join_names(info.get("authors")),
            "publisher": _clean_text(info.get("publisher")),
            "category": _join_names(info.get("categories")),
            "isbn": isbn,
        }

    return None


def _open_library(
    session: requests.Session,
    isbn: str,
) -> dict[str, Any] | None:
    """Look up and verify a book using Open Library."""
    data = _get_json(
        session,
        PROVIDER_URLS["open_library"],
        params={
            "bibkeys": f"ISBN:{isbn}",
            "format": "json",
            "jscmd": "data",
        },
        provider="Open Library",
    )

    if not isinstance(data, dict):
        return None

    for record in data.values():
        if not isinstance(record, dict):
            continue

        identifiers = record.get("identifiers")

        if not isinstance(identifiers, dict):
            continue

        candidates: list[str] = []

        for key in ("isbn_10", "isbn_13", "isbn"):
            values = identifiers.get(key, [])

            if isinstance(values, str):
                candidates.append(values)
            elif isinstance(values, list):
                candidates.extend(
                    value for value in values
                    if isinstance(value, str)
                )

        if not _has_matching_isbn(isbn, candidates):
            continue

        return {
            "title": _clean_text(record.get("title")),
            "author": _join_names(record.get("authors")),
            "publisher": _join_names(record.get("publishers")),
            "category": _join_names(record.get("subjects")),
            "isbn": isbn,
        }

    return None


def _crossref(
    session: requests.Session,
    isbn: str,
) -> dict[str, Any] | None:
    """Look up and verify a book using Crossref."""
    data = _get_json(
        session,
        PROVIDER_URLS["crossref"],
        params={
            "query.bibliographic": isbn,
            "rows": 10,
        },
        provider="Crossref",
    )

    if not isinstance(data, dict):
        return None

    message = data.get("message")

    if not isinstance(message, dict):
        return None

    items = message.get("items", [])

    if not isinstance(items, list):
        return None

    for item in items:
        if not isinstance(item, dict):
            continue

        if not _has_matching_isbn(isbn, item.get("ISBN", [])):
            continue

        return {
            "title": _join_names(item.get("title")),
            "author": _join_names(item.get("author")),
            "publisher": _clean_text(item.get("publisher")),
            "category": None,
            "isbn": isbn,
        }

    return None


PROVIDERS = (
    ("google_books", _google_books),
    ("open_library", _open_library),
    ("crossref", _crossref),
)


def lookup_book_metadata(
    raw_isbn: str,
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Fetch metadata using multiple providers.

    This function does not create or update database records.

    Returns a dictionary containing:
        isbn: normalized ISBN
        found: whether any provider returned a verified record
        metadata: available title, author, publisher, and category
        sources: providers that returned verified records
        message: user-friendly status
    """
    isbn = normalize_isbn(raw_isbn)

    own_session = session is None
    http = session if session is not None else requests.Session()

    records: list[tuple[str, dict[str, Any]]] = []

    try:
        for name, provider in PROVIDERS:
            try:
                record = provider(http, isbn)
            except Exception:
                # A single provider must not break the whole lookup.
                logger.warning(
                    "%s provider failed unexpectedly.",
                    name,
                )
                record = None

            if record:
                records.append((name, record))

    finally:
        if own_session:
            http.close()

    merged: dict[str, str] = {}
    sources: list[str] = []

    # First provider with a value wins; later providers fill missing fields.
    for source, record in records:
        sources.append(source)

        for field in FIELDS:
            value = _clean_text(record.get(field))

            if value and field not in merged:
                merged[field] = value

    # Preserve the exact normalized ISBN entered by the user.
    merged["isbn"] = isbn

    found = bool(records)

    if found:
        message = (
            "Book details found. Please review them before saving."
        )
    else:
        message = (
            "No matching metadata was found. "
            "You can enter the book details manually."
        )

    return {
        "isbn": isbn,
        "found": found,
        "metadata": merged,
        "sources": sources,
        "message": message,
    }