"""ISBN normalization, validation, and equivalent ISBN conversion."""

import re


class ISBNValidationError(ValueError):
    """Raised when an ISBN is missing or invalid."""


def normalize_isbn(value: str) -> str:
    """Normalize and validate ISBN-10 or ISBN-13."""
    if not isinstance(value, str):
        raise ISBNValidationError("ISBN must be text.")

    isbn = re.sub(r"[\s-]+", "", value).upper()

    if not isbn:
        raise ISBNValidationError("Please enter an ISBN.")

    # Validate ISBN-10.
    if len(isbn) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", isbn):
            raise ISBNValidationError(
                "ISBN-10 must contain 9 digits followed by a digit or X."
            )

        total = sum(
            (10 - index) * (10 if char == "X" else int(char))
            for index, char in enumerate(isbn)
        )

        if total % 11 != 0:
            raise ISBNValidationError("Invalid ISBN-10 checksum.")

        return isbn

    # Validate ISBN-13.
    if len(isbn) == 13:
        if not isbn.isdigit():
            raise ISBNValidationError("ISBN-13 must contain 13 digits.")

        if not isbn.startswith(("978", "979")):
            raise ISBNValidationError(
                "ISBN-13 must start with 978 or 979."
            )

        total = sum(
            int(char) * (1 if index % 2 == 0 else 3)
            for index, char in enumerate(isbn[:12])
        )
        expected_digit = (10 - total % 10) % 10

        if expected_digit != int(isbn[-1]):
            raise ISBNValidationError("Invalid ISBN-13 checksum.")

        return isbn

    raise ISBNValidationError(
        "ISBN must contain 10 or 13 characters."
    )


def isbn13_check_digit(first_twelve_digits: str) -> str:
    """Calculate the check digit for the first 12 ISBN-13 digits."""
    if not re.fullmatch(r"\d{12}", first_twelve_digits):
        raise ISBNValidationError(
            "ISBN-13 conversion requires exactly 12 digits."
        )

    total = sum(
        int(char) * (1 if index % 2 == 0 else 3)
        for index, char in enumerate(first_twelve_digits)
    )

    return str((10 - total % 10) % 10)


def isbn10_to_isbn13(isbn10: str) -> str:
    """Convert a valid ISBN-10 into its 978-prefixed ISBN-13 equivalent."""
    normalized = normalize_isbn(isbn10)

    if len(normalized) != 10:
        raise ISBNValidationError("Expected an ISBN-10.")

    first_twelve = "978" + normalized[:9]
    return first_twelve + isbn13_check_digit(first_twelve)


def isbn13_to_isbn10(isbn13: str) -> str:
    """Convert a 978-prefixed ISBN-13 into ISBN-10."""
    normalized = normalize_isbn(isbn13)

    if len(normalized) != 13:
        raise ISBNValidationError("Expected an ISBN-13.")

    if not normalized.startswith("978"):
        raise ISBNValidationError(
            "Only 978-prefixed ISBN-13 values have an ISBN-10 equivalent."
        )

    first_nine = normalized[3:12]

    weighted_sum = sum(
        (10 - index) * int(char)
        for index, char in enumerate(first_nine)
    )

    check_value = (11 - (weighted_sum % 11)) % 11
    check_digit = "X" if check_value == 10 else str(check_value)

    return first_nine + check_digit


def equivalent_isbns(value: str) -> set[str]:
    """Return valid ISBN forms for the same ISBN edition."""
    isbn = normalize_isbn(value)

    if len(isbn) == 10:
        return {isbn, isbn10_to_isbn13(isbn)}

    equivalents = {isbn}

    # 979 ISBNs do not have a corresponding ISBN-10.
    if isbn.startswith("978"):
        equivalents.add(isbn13_to_isbn10(isbn))

    return equivalents


def is_matching_isbn(requested: str, candidate: str) -> bool:
    """Check whether two ISBNs are equivalent."""
    try:
        return bool(
            equivalent_isbns(requested)
            & equivalent_isbns(candidate)
        )
    except ISBNValidationError:
        return False