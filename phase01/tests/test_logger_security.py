"""
Unit tests for sensitive data logging security.
"""

import unittest
import io
import logging
from phase01.core.logger import setup_logger


class TestLoggerSecurity(unittest.TestCase):

    def setUp(self):
        """Set up a fresh logger and capture logs."""
        self.log_capture = io.StringIO()
        self.test_logger = setup_logger("test-logger")

        # Add a handler that writes to our StringIO
        handler = logging.StreamHandler(self.log_capture)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        self.test_logger.addHandler(handler)
        self.test_logger.propagate = False

    def tearDown(self):
        """Clean up."""
        # Find and remove the handler we added in setUp
        for handler in self.test_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and handler.stream == self.log_capture:
                self.test_logger.removeHandler(handler)

    def assert_redacted(self, secret):
        """Assert that the secret is not in the log output."""
        output = self.log_capture.getvalue()
        self.assertNotIn(secret, output, f"Secret {secret} found in log output: {output}")

    def test_password_redaction(self):
        self.test_logger.info("password=SuperSecret123")
        self.assert_redacted("SuperSecret123")

    def test_api_key_redaction(self):
        self.test_logger.info("api_key=ABC123SECRET")
        self.assert_redacted("ABC123SECRET")

    def test_token_redaction(self):
        self.test_logger.info("token=ABC123SECRET")
        self.assert_redacted("ABC123SECRET")

    def test_bearer_token_redaction(self):
        self.test_logger.info("Authorization: Bearer ABC123SECRET")
        self.assert_redacted("ABC123SECRET")

    def test_basic_auth_redaction(self):
        self.test_logger.info("Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==")
        self.assert_redacted("QWxhZGRpbjpvcGVuIHNlc2FtZQ==")

    def test_cookie_redaction(self):
        self.test_logger.info("Cookie: sessionid=SECRET123")
        self.assert_redacted("SECRET123")

    def test_authorization_redaction(self):
        self.test_logger.info("Authorization: SECRET123")
        self.assert_redacted("SECRET123")

    def test_parameterized_logging(self):
        """Test that logger.info('token=%s', SECRET) is properly redacted."""
        secret = "VERY_SECRET_TOKEN_12345"
        self.test_logger.info("token=%s", secret)
        self.assert_redacted(secret)

    def test_normal_parameterized_logging(self):
        """Test that normal parameterized logging is preserved."""
        self.test_logger.info("Target: %s", "example.com")
        self.assertIn("example.com", self.log_capture.getvalue())


if __name__ == '__main__':
    unittest.main()