"""
Unit tests for Scope Manager.
"""

import unittest
from phase01.core.scope_manager import ScopeManager
from phase01.core.exceptions import InvalidScopeError, OutOfScopeError


class TestScopeManager(unittest.TestCase):

    def setUp(self):
        self.manager = ScopeManager()
        self.scope_config = {
            "in_scope": ["example.com", "*.example.com"],
            "out_of_scope": ["payments.example.com"]
        }
        self.manager.load_scope(self.scope_config)

    def test_in_scope(self):
        self.assertTrue(self.manager.is_in_scope("example.com"))
        self.assertTrue(self.manager.is_in_scope("api.example.com"))
        self.assertTrue(self.manager.is_in_scope("deep.api.example.com"))
        self.assertTrue(self.manager.is_in_scope("https://example.com"))
        self.assertTrue(self.manager.is_in_scope("https://api.example.com"))
        self.assertTrue(self.manager.is_in_scope("https://api.example.com:443"))
        self.assertTrue(self.manager.is_in_scope("https://api.example.com/path"))
        self.assertTrue(self.manager.is_in_scope("http://example.com"))

    def test_out_of_scope(self):
        self.assertFalse(self.manager.is_in_scope("payments.example.com"))
        self.assertFalse(self.manager.is_in_scope("third-party.example.net"))
        self.assertFalse(self.manager.is_in_scope("https://payments.example.com"))
        self.assertFalse(self.manager.is_in_scope("https://payments.example.com/path"))

    def test_precedence(self):
        # Out-of-scope should take precedence over in-scope
        self.assertFalse(self.manager.is_in_scope("payments.example.com"))

    def test_wildcard_semantics(self):
        # *.example.com must NOT match example.com itself
        self.assertFalse(self.manager.is_in_scope("evil-example.com"))
        self.assertFalse(self.manager.is_in_scope("example.com.evil.com"))
        self.assertFalse(self.manager.is_in_scope("evil.com"))

    def test_enforce_scope_success(self):
        # Should not raise for in-scope resources
        self.manager.enforce_scope("example.com")
        self.manager.enforce_scope("api.example.com")
        self.manager.enforce_scope("deep.api.example.com")
        self.manager.enforce_scope("https://example.com")

    def test_enforce_scope_failure(self):
        # Should raise OutOfScopeError for out-of-scope resources
        with self.assertRaises(OutOfScopeError):
            self.manager.enforce_scope("payments.example.com")
        with self.assertRaises(OutOfScopeError):
            self.manager.enforce_scope("third-party.example.net")
        with self.assertRaises(OutOfScopeError):
            self.manager.enforce_scope("https://payments.example.com")

    def test_invalid_scope_entry(self):
        invalid_config = {
            "in_scope": ["example.com"],
            "out_of_scope": ["invalid domain"]
        }
        with self.assertRaises(InvalidScopeError):
            self.manager.load_scope(invalid_config)

    def test_empty_scope(self):
        empty_config = {
            "in_scope": [],
            "out_of_scope": []
        }
        with self.assertRaises(InvalidScopeError):
            self.manager.load_scope(empty_config)

    def test_unknown_domain(self):
        # unknown.example.com should be IN SCOPE because it matches *.example.com wildcard
        self.assertTrue(self.manager.is_in_scope("unknown.example.com"))

    def test_malformed_resource(self):
        self.assertFalse(self.manager.is_in_scope(""))
        self.assertFalse(self.manager.is_in_scope("   "))
        self.assertFalse(self.manager.is_in_scope("http://"))
        self.assertFalse(self.manager.is_in_scope("https://"))

    def test_unloaded_scope(self):
        new_manager = ScopeManager()
        with self.assertRaises(OutOfScopeError):
            new_manager.enforce_scope("example.com")

    def test_resource_normalization(self):
        # Various resource formats should normalize to the same hostname
        self.assertTrue(self.manager.is_in_scope("http://example.com"))
        self.assertTrue(self.manager.is_in_scope("https://example.com"))
        self.assertTrue(self.manager.is_in_scope("example.com:443"))
        self.assertTrue(self.manager.is_in_scope("example.com/path"))
        self.assertTrue(self.manager.is_in_scope("api.example.com:8080/path"))

    def test_case_insensitivity(self):
        # Scope matching should be case-insensitive
        self.assertTrue(self.manager.is_in_scope("EXAMPLE.COM"))
        self.assertTrue(self.manager.is_in_scope("API.EXAMPLE.COM"))

    def test_suffix_attack(self):
        # Test for suffix attacks like example.com.evil.com
        self.assertFalse(self.manager.is_in_scope("example.com.evil.com"))

    def test_similar_domain(self):
        # Test for similar-looking domains
        self.assertFalse(self.manager.is_in_scope("evil-example.com"))

    def test_host_port_validation(self):
        # Test host:port validation
        self.assertFalse(self.manager.is_in_scope("example.com:invalid"))
        self.assertFalse(self.manager.is_in_scope("example.com:99999"))

    def test_wildcard_does_not_match_base_domain(self):
        # *.example.com should not match example.com when example.com is not explicitly in scope
        scope_config = {
            "in_scope": ["*.example.com"],  # only wildcard, no explicit base domain
            "out_of_scope": []
        }
        self.manager.load_scope(scope_config)
        self.assertFalse(self.manager.is_in_scope("example.com"))
        # But a subdomain should match
        self.assertTrue(self.manager.is_in_scope("api.example.com"))

    def test_no_scope_manager_fails(self):
        # Test that ScopeManager fails closed when no scope is loaded
        new_manager = ScopeManager()
        with self.assertRaises(OutOfScopeError):
            new_manager.enforce_scope("example.com")


if __name__ == '__main__':
    unittest.main()