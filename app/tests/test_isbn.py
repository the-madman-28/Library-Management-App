
import pytest

from app.services.isbn import (
    ISBNValidationError,
    equivalent_isbns,
    is_matching_isbn,
    normalize_isbn,
)


def test_valid_isbn10():
    assert normalize_isbn("0306406152") == "0306406152"


def test_valid_isbn13():
    assert normalize_isbn("9780306406157") == "9780306406157"


def test_spaces_and_hyphens_are_removed():
    assert normalize_isbn("978-0-306-40615-7") == "9780306406157"
    assert normalize_isbn("0 306 40615 2") == "0306406152"


def test_invalid_isbn13_checksum_is_rejected():
    with pytest.raises(ISBNValidationError):
        normalize_isbn("9780306406158")


def test_invalid_isbn10_checksum_is_rejected():
    with pytest.raises(ISBNValidationError):
        normalize_isbn("0306406153")


def test_empty_isbn_is_rejected():
    with pytest.raises(ISBNValidationError):
        normalize_isbn("  ")


def test_unsupported_length_is_rejected():
    with pytest.raises(ISBNValidationError):
        normalize_isbn("123456789")


def test_isbn10_and_isbn13_equivalence():
    assert is_matching_isbn("0306406152", "9780306406157")
    assert is_matching_isbn("9780306406157", "0306406152")


def test_979_isbn_does_not_get_isbn10_equivalent():
    assert equivalent_isbns("9791090636071") == {"9791090636071"}
