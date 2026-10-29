
import requests

from unittest.mock import Mock, patch

from app.services import book_metadata


VALID_ISBN = "9780306406157"


def test_first_provider_success_still_checks_fallbacks():
    google = {
        "title": "Example Book",
        "author": "A. Writer",
        "publisher": None,
        "category": None,
        "isbn": VALID_ISBN,
    }

    with patch.object(
        book_metadata,
        "PROVIDERS",
        [
            ("google_books", Mock(return_value=google)),
            ("open_library", Mock(return_value=None)),
            ("crossref", Mock(return_value=None)),
        ],
    ) as providers:
        result = book_metadata.lookup_book_metadata(VALID_ISBN)

    assert result["found"] is True
    assert result["metadata"]["title"] == "Example Book"
    assert result["sources"] == ["google_books"]
    assert all(call[1].called for call in providers)


def test_first_provider_failure_does_not_stop_fallback():
    second = {
        "title": "Fallback Title",
        "author": None,
        "publisher": "Publisher",
        "category": None,
        "isbn": VALID_ISBN,
    }

    with patch.object(
        book_metadata,
        "PROVIDERS",
        [
            ("google_books", Mock(side_effect=requests.Timeout())),
            ("open_library", Mock(return_value=second)),
            ("crossref", Mock(return_value=None)),
        ],
    ):
        result = book_metadata.lookup_book_metadata(VALID_ISBN)

    assert result["found"] is True
    assert result["metadata"]["title"] == "Fallback Title"
    assert "open_library" in result["sources"]


def test_all_providers_fail_without_crashing():
    with patch.object(
        book_metadata,
        "PROVIDERS",
        [
            ("google_books", Mock(side_effect=requests.Timeout())),
            ("open_library", Mock(side_effect=requests.ConnectionError())),
            ("crossref", Mock(side_effect=ValueError("bad response"))),
        ],
    ):
        result = book_metadata.lookup_book_metadata(VALID_ISBN)

    assert result["found"] is False
    assert result["metadata"]["isbn"] == VALID_ISBN
    assert result["sources"] == []


def test_partial_metadata_is_preserved():
    first = {
        "title": "Preferred Title",
        "author": None,
        "publisher": None,
        "category": None,
        "isbn": VALID_ISBN,
    }
    second = {
        "title": "Different Title",
        "author": "A. Writer",
        "publisher": "Example Press",
        "category": "Science",
        "isbn": VALID_ISBN,
    }

    with patch.object(
        book_metadata,
        "PROVIDERS",
        [
            ("google_books", Mock(return_value=first)),
            ("open_library", Mock(return_value=second)),
            ("crossref", Mock(return_value=None)),
        ],
    ):
        result = book_metadata.lookup_book_metadata(VALID_ISBN)

    assert result["metadata"]["title"] == "Preferred Title"
    assert result["metadata"]["author"] == "A. Writer"
    assert result["metadata"]["publisher"] == "Example Press"
    assert result["metadata"]["category"] == "Science"


def test_invalid_isbn_is_rejected_before_provider_calls():
    with patch.object(book_metadata, "PROVIDERS") as providers:
        try:
            book_metadata.lookup_book_metadata("123")
        except ValueError:
            pass
        else:
            raise AssertionError("Expected invalid ISBN to be rejected")

    providers.assert_not_called()


class FakeResponse:
    def __init__(self, status_code=200, data=None, json_error=False):
        self.status_code = status_code
        self.data = data
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("invalid JSON")
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("HTTP error")


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_google_empty_result_does_not_create_metadata():
    session = FakeSession(FakeResponse(data={"totalItems": 0, "items": []}))

    result = book_metadata._google_books(session, VALID_ISBN)

    assert result is None
    assert len(session.calls) == 1


def test_google_rejects_non_matching_isbn():
    session = FakeSession(
        FakeResponse(
            data={
                "items": [
                    {
                        "volumeInfo": {
                            "title": "Wrong Book",
                            "industryIdentifiers": [
                                {"type": "ISBN_13", "identifier": "9780140328721"}
                            ],
                        }
                    }
                ]
            }
        )
    )

    assert book_metadata._google_books(session, VALID_ISBN) is None


def test_http_429_and_503_are_handled():
    for status in (429, 503):
        session = FakeSession(FakeResponse(status_code=status))
        assert book_metadata._get_json(
            session,
            "https://example.test/books",
            params={},
            provider="test",
        ) is None


def test_invalid_json_is_handled():
    session = FakeSession(FakeResponse(json_error=True))

    assert book_metadata._get_json(
        session,
        "https://example.test/books",
        params={},
        provider="test",
    ) is None
