"""
Unit tests for validation utilities.
"""

import unittest
from phase01.utils.validation import validate_target, validate_scope_entry, validate_scope
from phase01.core.exceptions import InvalidTargetError, InvalidScopeError


class TestValidation(unittest.TestCase):

    def test_valid_target(self):
        self.assertTrue(validate_target("https://example.com"))
        self.assertTrue(validate_target("https://api.example.com"))
        self.assertTrue(validate_target("http://example.com"))
        self.assertTrue(validate_target("https://example.com:8080"))

    def test_invalid_target_empty(self):
        with self.assertRaises(InvalidTargetError):
            validate_target("")

    def test_invalid_target_scheme(self):
        with self.assertRaises(InvalidTargetError):
            validate_target("invalid://example.com")

    def test_invalid_target_format(self):
        with self.assertRaises(InvalidTargetError):
            validate_target("example.com")  # No scheme

    def test_invalid_target_whitespace(self):
        with self.assertRaises(InvalidTargetError):
            validate_target("https://ex ample.com")

    def test_invalid_target_port(self):
        with self.assertRaises(InvalidTargetError):
            validate_target("https://example.com:99999")

    def test_valid_scope_entry(self):
        self.assertTrue(validate_scope_entry("example.com"))
        self.assertTrue(validate_scope_entry("*.example.com"))
        self.assertTrue(validate_scope_entry("https://example.com"))

    def test_invalid_scope_entry(self):
        with self.assertRaises(InvalidScopeError):
            validate_scope_entry("")
        with self.assertRaises(InvalidScopeError):
            validate_scope_entry("invalid domain")
        with self.assertRaises(InvalidScopeError):
            validate_scope_entry("example")  # No TLD
        with self.assertRaises(InvalidScopeError):
            validate_scope_entry("*.com")  # Wildcard without domain

    def test_valid_scope(self):
        valid_scope = {
            "in_scope": ["example.com", "*.example.com"],
            "out_of_scope": ["payments.example.com"]
        }
        self.assertTrue(validate_scope(valid_scope))

    def test_invalid_scope_empty(self):
        with self.assertRaises(InvalidScopeError):
            validate_scope({"in_scope": []})

    def test_invalid_scope_missing_in_scope(self):
        with self.assertRaises(InvalidScopeError):
            validate_scope({"out_of_scope": ["example.com"]})


if __name__ == '__main__':
    unittest.main()
