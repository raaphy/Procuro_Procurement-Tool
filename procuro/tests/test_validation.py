import pytest
import re


def validate_vat_id(vat_id: str) -> bool:
    """VAT ID must be DE followed by 9 digits."""
    if not vat_id:
        return False
    return bool(vat_id.startswith("DE") and len(vat_id) == 11 and vat_id[2:].isdigit())


class TestVatIdValidation:
    def test_valid_vat_id(self):
        assert validate_vat_id("DE123456789") is True

    def test_valid_vat_id_all_zeros(self):
        assert validate_vat_id("DE000000000") is True

    def test_invalid_vat_id_wrong_prefix(self):
        assert validate_vat_id("AT123456789") is False

    def test_invalid_vat_id_too_short(self):
        assert validate_vat_id("DE12345678") is False

    def test_invalid_vat_id_too_long(self):
        assert validate_vat_id("DE1234567890") is False

    def test_invalid_vat_id_with_letters(self):
        assert validate_vat_id("DE12345678A") is False

    def test_invalid_vat_id_empty(self):
        assert validate_vat_id("") is False

    def test_invalid_vat_id_lowercase(self):
        assert validate_vat_id("de123456789") is False
