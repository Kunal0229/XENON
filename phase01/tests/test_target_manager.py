"""
Unit tests for Target Manager.
"""

import unittest
from phase01.core.target_manager import TargetManager
from phase01.core.exceptions import InvalidTargetError


class TestTargetManager(unittest.TestCase):

    def setUp(self):
        self.manager = TargetManager()

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

    def test_unsupported_scheme(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("ftp://example.com")

    def test_invalid_hostname(self):
        with self.assertRaises(InvalidTargetError):
            self.manager.set_target("https://invalid_hostname")


if __name__ == '__main__':
    unittest.main()