"""
Unit tests for Target Manager.
"""

import unittest
from phase01.core.target_manager import TargetManager
from phase01.core.scope_manager import ScopeManager
from phase01.core.exceptions import InvalidTargetError


class TestTargetManager(unittest.TestCase):

    def setUp(self):
        self.scope_mgr = ScopeManager()
        self.scope_mgr.load_scope({"in_scope": ["example.com"], "out_of_scope": []})
        self.manager = TargetManager(scope_manager=self.scope_mgr)

    def test_set_target(self):
        target = self.manager.set_target("https://example.com")
        self.assertEqual(target.target, "https://example.com")
        self.assertEqual(target.status, "active")

    def test_invalid_target(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("example.com")

    def test_update_status(self):
        self.manager.set_target("https://example.com")
        self.manager.update_status("inactive")
        self.assertEqual(self.manager.get_target().status, "inactive")

    def test_invalid_status(self):
        self.manager.set_target("https://example.com")
        with self.assertRaises(InvalidTargetError):
            self.manager.update_status("invalid")

    def test_get_target(self):
        self.manager.set_target("https://example.com")
        target = self.manager.get_target()
        self.assertIsNotNone(target)
        self.assertEqual(target.target, "https://example.com")

    def test_get_target_url(self):
        self.manager.set_target("https://example.com")
        self.assertEqual(self.manager.get_target_url(), "https://example.com")

    def test_clear(self):
        self.manager.set_target("https://example.com")
        self.manager.clear()
        self.assertIsNone(self.manager.get_target())

    def test_target_with_credentials(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://user:pass@example.com")

    def test_valid_http_target(self):
        target = self.manager.set_target("http://example.com")
        self.assertEqual(target.target, "http://example.com")

    def test_valid_https_target(self):
        target = self.manager.set_target("https://example.com")
        self.assertEqual(target.target, "https://example.com")

    def test_valid_port(self):
        target = self.manager.set_target("https://example.com:8080")
        self.assertEqual(target.target, "https://example.com:8080")

    def test_invalid_port(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://example.com:99999")

    def test_empty_target(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("")

    def test_whitespace_target(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("   ")

    def test_malformed_url(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("example.com/path")

    def test_status_normalization_set_target(self):
        """Test that set_target normalizes status consistently."""
        test_cases = [
            ("active", "active"),
            ("ACTIVE", "active"),
            ("Active", "active"),
            ("inactive", "inactive"),
            ("INACTIVE", "inactive"),
            ("InActive", "inactive"),
        ]
        for input_status, expected_status in test_cases:
            # Clear any existing target
            self.manager.clear()
            # Should succeed for all case variations
            target = self.manager.set_target("https://example.com", status=input_status)
            self.assertEqual(target.status, expected_status)

    def test_status_normalization_update_status(self):
        """Test that update_status normalizes status consistently."""
        self.manager.set_target("https://example.com")
        test_cases = [
            ("active", "active"),
            ("ACTIVE", "active"),
            ("Active", "active"),
            ("inactive", "inactive"),
            ("INACTIVE", "inactive"),
            ("InActive", "inactive"),
        ]
        for input_status, expected_status in test_cases:
            target = self.manager.update_status(input_status)
            self.assertEqual(target.status, expected_status)

    def test_unsupported_scheme(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("ftp://example.com")

    def test_invalid_hostname(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://invalid_hostname")

    # NEW REGRESSION TESTS
    def test_no_scope_manager_fails(self):
        # A manager without scope_manager should fail when setting target
        mgr = TargetManager(scope_manager=None)
        with self.assertRaises(InvalidTargetError):
            mgr.set_target("https://example.com")

    def test_out_of_scope_target_fails(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://payments.example.com")
        self.assertIsNone(self.manager.get_target())

    def test_failed_replacement_preserves_old(self):
        self.manager.set_target("https://example.com")
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://payments.example.com")
        self.assertEqual(self.manager.get_target_url(), "https://example.com")

    def test_invalid_target_preserves_none(self):
        # Already set up with manager None/Empty target
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("invalid_target")
        self.assertIsNone(self.manager.get_target())

if __name__ == '__main__':
    unittest.main()