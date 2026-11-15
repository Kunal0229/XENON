"""
Unit tests for sensitive data logging security.
"""

import unittest
import io
import logging
from phase01.core.logger import setup_logger, SensitiveDataFilter


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

    def test_parameterized_logging_tuple(self):
        """Test that logger.info('token=%s', SECRET) is properly redacted."""
        secret = "VERY_SECRET_TOKEN_12345"
        self.test_logger.info("token=%s", secret)
        self.assert_redacted(secret)

    def test_parameterized_logging_dict(self):
        """Test that logger.info('%(token)s', {'token': SECRET}) is properly redacted."""
        secret = "DICTARG_SECRET_XYZ"
        self.test_logger.info("token=%(token)s", {"token": secret})
        self.assert_redacted(secret)

    def test_normal_parameterized_logging(self):
        """Test that normal parameterized logging is preserved."""
        self.test_logger.info("Target: %s", "example.com")
        self.assertIn("example.com", self.log_capture.getvalue())

    def test_dict_parameterized_non_secret(self):
        """Test that dict args without secret format specifiers are preserved."""
        self.test_logger.info("User: %(name)s, Host: %(host)s", {"name": "alice", "host": "example.com"})
        output = self.log_capture.getvalue()
        self.assertIn("alice", output)
        self.assertIn("example.com", output)

    def test_credential_url_redaction(self):
        """Test that credential-bearing URLs are redacted."""
        self.test_logger.info("Connecting to https://bob:secret123@example.com")
        self.assert_redacted("bob:secret123")
        self.assertIn("REDACTED", self.log_capture.getvalue())

    def test_credential_url_redaction_in_args(self):
        """Test that credential-bearing URLs in args are redacted."""
        self.test_logger.info("URL: %s", "https://user:pass@example.com")
        self.assert_redacted("user:pass")
        self.assertIn("REDACTED", self.log_capture.getvalue())

    def test_non_string_message(self):
        """Test that non-string messages don't crash the logger."""
        self.test_logger.info(12345)
        self.test_logger.warning(None)
        self.test_logger.error({"status": "failed"})
        # Should not raise any exception
        output = self.log_capture.getvalue()
        self.assertIn("12345", output)
        self.assertIn("None", output)
        self.assertIn("'status': 'failed'", output)

    def test_parameterized_authorization_secret(self):
        """Test parameterized Authorization logging redacts secret and doesn't leak."""
        secret = "STDERR_SECRET_42"
        self.test_logger.info("Authorization: %s", secret)
        output = self.log_capture.getvalue()
        self.assertNotIn(secret, output)
        self.assertIn("REDACTED", output)
        # Ensure no logging exception occurred (would appear in stderr/test output)
        self.assertNotIn("TypeError", output)
        self.assertNotIn("not all arguments converted", output)

    def test_parameterized_cookie_secret(self):
        """Test parameterized Cookie logging redacts secret."""
        secret = "COOKIE_SECRET_123"
        self.test_logger.info("Cookie: %s", secret)
        output = self.log_capture.getvalue()
        self.assertNotIn(secret, output)
        self.assertIn("REDACTED", output)

    def test_parameterized_authorization_bearer_secret(self):
        """Test parameterized Authorization Bearer logging redacts secret."""
        secret = "BEARER_SECRET_789"
        self.test_logger.info("Authorization: Bearer %s", secret)
        output = self.log_capture.getvalue()
        self.assertNotIn(secret, output)
        self.assertIn("REDACTED", output)

    def test_whitespace_separator_token_colon(self):
        """Test token : SECRET redaction with whitespace around colon."""
        self.test_logger.info("token : ABC123")
        output = self.log_capture.getvalue()
        self.assertNotIn("ABC123", output)
        self.assertIn("token=REDACTED", output)

    def test_whitespace_separator_token_equals(self):
        """Test token = SECRET redaction with whitespace around equals."""
        self.test_logger.info("token = ABC123")
        output = self.log_capture.getvalue()
        self.assertNotIn("ABC123", output)
        self.assertIn("token=REDACTED", output)

    def test_whitespace_separators_all_keys(self):
        """Test whitespace separators for all sensitive keys."""
        test_cases = [
            "token : SECRET1",
            "password = SECRET2",
            "api_key : SECRET3",
            "api-key = SECRET4",
            "Authorization : SECRET5",
            "Cookie = SECRET6",
            "secret : SECRET7",
            "auth_token = SECRET8",
            "access_token : SECRET9",
            "X-Api-Key = SECRET10",
        ]
        for case in test_cases:
            # Clear log capture for each test
            self.log_capture.seek(0)
            self.log_capture.truncate(0)
            self.test_logger.info(case)
            output = self.log_capture.getvalue()
            self.assertNotIn("SECRET", output, f"Secret leaked in case: {case}")
            self.assertIn("REDACTED", output, f"No REDACTED in case: {case}")

    def test_explicit_info_level_respected(self):
        """Test that explicit INFO level is respected even when config is different."""
        # This test requires access to the settings and logger creation
        # We'll test it indirectly by creating a new logger
        from phase01.core.logger import setup_logger
        from phase01.config.settings import settings

        # Save original config level
        original_level = settings.get("log_level")
        try:
            # Set config to WARNING
            settings.set("log_level", "WARNING")

            # Create logger with explicit INFO
            logger = setup_logger("test_info", level="INFO")
            self.assertEqual(logger.level, logging.INFO)

            # Create logger with omitted level (should use config)
            logger2 = setup_logger("test_omitted")
            self.assertEqual(logger2.level, logging.WARNING)
        finally:
            # Restore original level
            settings.set("log_level", original_level)


    def _assert_no_partial_secret_fragment(self, output, secret):
        """Reject recognizable secret fragments immediately around REDACTED.

        This catches split leaks such as ``token=abc123=REDACTEDdef`` and
        ``Basic=REDACTEDwYXNz`` without treating separated, legitimate context
        (for example ``REDACTED status=active``) as a leak.
        """
        import re

        marker = output.find("REDACTED")
        self.assertNotEqual(marker, -1, f"No REDACTED marker in {output!r}")
        before = output[:marker]
        after = output[marker + len("REDACTED"):]

        # A leaked suffix directly after REDACTED must not match the end of the
        # original secret. Stop at whitespace/punctuation so normal context is safe.
        right_match = re.match(r"([A-Za-z0-9_+/=.-]+)", after)
        if right_match:
            right_fragment = right_match.group(1)
            for length in range(min(len(right_fragment), len(secret)), 2, -1):
                candidate = right_fragment[:length]
                if secret.endswith(candidate):
                    self.fail(
                        f"Partial secret suffix {candidate!r} leaked after REDACTED: {output!r}"
                    )

        # A leaked prefix may appear immediately before an extra separator and
        # REDACTED, e.g. token=abc123=REDACTEDdef. Do not mistake the sensitive
        # field name in a normal 'token=REDACTED' output for a leaked value.
        left_match = re.search(r"([A-Za-z0-9_+./-]{3,})[=:]\s*$", before)
        if left_match:
            left_fragment = left_match.group(1)
            sensitive_names = {
                "token", "password", "passwd", "pwd", "api_key", "api-key",
                "access_token", "access-token", "auth_token", "auth-token",
                "secret", "authorization", "cookie", "basic", "bearer",
            }
            if left_fragment.lower() not in sensitive_names and secret.startswith(left_fragment):
                self.fail(
                    f"Partial secret prefix {left_fragment!r} leaked before REDACTED: {output!r}"
                )

    def _assert_redacted(self, msg, secret, args=None):
        """Log a message and assert complete redaction without partial leaks."""
        self.log_capture.seek(0)
        self.log_capture.truncate(0)
        if args:
            self.test_logger.info(msg, *args)
        else:
            self.test_logger.info(msg)
        output = self.log_capture.getvalue()

        self.assertNotIn(secret, output, f"Secret leaked: {secret!r} in {output!r}")
        self.assertIn("REDACTED", output, f"No REDACTED in {output!r}")
        self._assert_no_partial_secret_fragment(output, secret)

        # Keep additional F-01 checks for dotted/JWT/multi-word credentials.
        import re
        marker = output.find("REDACTED")
        after = output[marker + len("REDACTED"):]

        if "." in secret:
            remainder = secret[secret.rfind("."):]
            self.assertNotIn(
                remainder, after,
                f"Leaked fragment {remainder!r} after REDACTED in {output!r}",
            )

        if secret.count(".") >= 2 and re.search(r"\.[a-zA-Z0-9_]+", after):
            self.fail(f"JWT segment leaked after REDACTED in {output!r}")

        if " " in secret:
            secret_words = set(secret.split())
            for word in after.split():
                if word in secret_words:
                    self.fail(f"Multi-word secret fragment {word!r} leaked in {output!r}")

    # ------------------------------------------------------------------
    # F-01 regression tests — complete secret redaction (no partial leaks)
    # ------------------------------------------------------------------
    # Negative controls: prove the helper rejects known partial-leak shapes.
    def test_f01_negative_control_basic_alphanumeric_suffix(self):
        with self.assertRaises(AssertionError):
            self._assert_no_partial_secret_fragment(
                "[INFO] Basic=REDACTEDwYXNz", "dXNlcjpwYXNz"
            )

    def test_f01_negative_control_split_alphanumeric_secret(self):
        with self.assertRaises(AssertionError):
            self._assert_no_partial_secret_fragment(
                "[INFO] token=abc123=REDACTEDdef", "abc123def"
            )

    def test_f01_negative_control_preserves_valid_trailing_context(self):
        self._assert_no_partial_secret_fragment(
            "[INFO] token=REDACTED status=active", "SECRET"
        )


    def test_f01_dot_secret_redaction(self):
        self._assert_redacted("secret: secret.with.dots", "secret.with.dots")

    def test_f01_complex_secret_redaction(self):
        self._assert_redacted("api_key: abc+DEF/123==", "abc+DEF/123==")

    def test_f01_jwt_redaction(self):
        self._assert_redacted("token: abc.def.ghi", "abc.def.ghi")

    def test_f01_jwt_realistic_redaction(self):
        self._assert_redacted(
            "token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",
        )

    def test_f01_multiword_secret_redaction(self):
        self._assert_redacted("password: my secret value", "my secret value")

    def test_f01_bearer_secret_redaction(self):
        self._assert_redacted("token: Bearer SUPER_SECRET_VALUE", "SUPER_SECRET_VALUE")

    def test_f01_bearer_complex_redaction(self):
        self._assert_redacted("Bearer abc+DEF/123==", "abc+DEF/123==")

    def test_f01_basic_redaction(self):
        self._assert_redacted("Basic dXNlcjpwYXNz", "dXNlcjpwYXNz")

    def test_f01_url_query_redaction(self):
        self._assert_redacted(
            "https://example.com/?token=abc.def.ghi", "abc.def.ghi"
        )

    def test_f01_url_path_redaction(self):
        self._assert_redacted(
            "https://example.com/path/api_key=abc+DEF/123==", "abc+DEF/123=="
        )

    def test_f01_url_fragment_redaction(self):
        self._assert_redacted(
            "https://example.com/#access_token=SECRET.VALUE", "SECRET.VALUE"
        )

    # ------------------------------------------------------------------
    # F-05 regression tests — secret redaction must NOT consume trailing context
    # ------------------------------------------------------------------

    def test_f05_space_context_preserved(self):
        self._assert_redacted("token=SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f05_comma_context_preserved(self):
        self._assert_redacted("token=SECRET, status=active", "SECRET")
        self.assertIn(", status=active", self.log_capture.getvalue())

    def test_f05_semicolon_context_preserved(self):
        self._assert_redacted("token=SECRET; status=active", "SECRET")
        self.assertIn("; status=active", self.log_capture.getvalue())

    def test_f05_multi_context_preserved(self):
        self._assert_redacted("token=SECRET status=active role=user", "SECRET")
        output = self.log_capture.getvalue()
        self.assertIn("status=active", output)
        self.assertIn("role=user", output)

    def test_f05_url_context_preserved(self):
        self._assert_redacted("?token=abc.def.ghi&status=active", "abc.def.ghi")
        self.assertIn("&status=active", self.log_capture.getvalue())

    # ------------------------------------------------------------------
    # F-06 regression tests — Bearer/Basic/Authorization context preservation
    # ------------------------------------------------------------------

    def test_f06_bearer_space_context_preserved(self):
        self._assert_redacted("Bearer SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f06_bearer_comma_context_preserved(self):
        self._assert_redacted("Bearer SECRET, status=active", "SECRET")
        self.assertIn(", status=active", self.log_capture.getvalue())

    def test_f06_bearer_semicolon_context_preserved(self):
        self._assert_redacted("Bearer SECRET; status=active", "SECRET")
        self.assertIn("; status=active", self.log_capture.getvalue())

    def test_f06_basic_space_context_preserved(self):
        self._assert_redacted("Basic SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f06_basic_comma_context_preserved(self):
        self._assert_redacted("Basic SECRET, status=active", "SECRET")
        self.assertIn(", status=active", self.log_capture.getvalue())

    def test_f06_basic_semicolon_context_preserved(self):
        self._assert_redacted("Basic SECRET; status=active", "SECRET")
        self.assertIn("; status=active", self.log_capture.getvalue())

    def test_f06_authorization_bearer_context_preserved(self):
        self._assert_redacted("Authorization: Bearer SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f06_cookie_context_preserved(self):
        self._assert_redacted("Cookie: SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f06_authorization_context_preserved(self):
        self._assert_redacted("Authorization: SECRET status=active", "SECRET")
        self.assertIn("status=active", self.log_capture.getvalue())

    def test_f06_bearer_multiword_redaction(self):
        self._assert_redacted("Bearer SUPER SECRET VALUE", "SUPER SECRET VALUE")


    def test_exc_info_redaction(self):
        # Test that secrets in exception messages are redacted when using exc_info
        try:
            raise Exception('password=SuperSecret')
        except Exception as e:
            self.test_logger.error('Error occurred', exc_info=True)
        output = self.log_capture.getvalue()
        # Check that the secret does not appear in the exception line (the line starting with 'Exception:')
        exception_line = None
        for line in output.splitlines():
            if line.startswith('Exception:'):
                exception_line = line
                break
        self.assertIsNotNone(exception_line, "Expected to find an exception line in the output")
        self.assertNotIn('SuperSecret', exception_line)
        # The exception type and traceback should still be present
        self.assertIn('Exception', output)
        self.assertIn('Traceback', output)

    def test_exc_info_non_secret_preserved(self):
        # Test that non-secret exception messages are preserved
        try:
            raise Exception('Something happened')
        except Exception as e:
            self.test_logger.error('Error occurred', exc_info=True)
        output = self.log_capture.getvalue()
        # Check that the non-secret string appears in the exception line
        exception_line = None
        for line in output.splitlines():
            if line.startswith('Exception:'):
                exception_line = line
                break
        self.assertIsNotNone(exception_line, "Expected to find an exception line in the output")
        self.assertIn('Something happened', exception_line)

    def test_stack_info_redaction(self):
        # Create a log record with stack_info containing a secret
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        # Set stack_info to a string containing a secret
        record.stack_info = "password=SuperSecret"
        # Apply the filter
        filter_obj = SensitiveDataFilter()
        # The filter method modifies the record in place and returns True/False
        filter_obj.filter(record)
        # Check that the secret is redacted from stack_info
        self.assertNotIn('SuperSecret', record.stack_info)
        # Check that the redaction occurred (the string changed)
        self.assertEqual(record.stack_info, 'password=REDACTED')

    def test_stack_info_non_secret_preserved(self):
        # Create a log record with stack_info containing a non-secret
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        # Set stack_info to a string containing a non-secret
        record.stack_info = "This is a normal stack trace"
        # Apply the filter
        filter_obj = SensitiveDataFilter()
        # The filter method modifies the record in place and returns True/False
        filter_obj.filter(record)
        # Check that the non-secret is preserved in stack_info
        self.assertIn('This is a normal stack trace', record.stack_info)
        # Check that the string did not change
        self.assertEqual(record.stack_info, 'This is a normal stack trace')


    def test_exc_info_custom_incompatible_exception_fails_closed(self):
        '''
        Test that a custom exception with an incompatible constructor signature
        does not leak secrets and the fail-closed behavior is properly handled.

        When SensitiveDataFilter attempts to reconstruct such an exception
        with redacted args, reconstruction fails. The filter should then
        set record.exc_info to None to prevent any potential leakage.

        This test verifies:
        1. Secrets are never exposed in the log output
        2. record.exc_info becomes None after the filter processes it
        3. The fail-closed behavior is confirmed via exc_info being None
        '''
        # Define a custom exception requiring extra arguments not in redacted args
        class CustomIncompatibleException(Exception):
            def __init__(self, code, detail):
                self.code = code
                super().__init__(detail)

        # Create a log record with exc_info
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Custom exception test",
            args=(),
            exc_info=None
        )

        # Raise and capture the exception
        try:
            raise CustomIncompatibleException(500, 'password=SuperSecret')
        except Exception as e:
            record.exc_info = (type(e), e, e.__traceback__)

        # Verify initial state
        self.assertIsNotNone(record.exc_info)
        exc_type_before, exc_value_before, exc_tb_before = record.exc_info
        self.assertEqual(exc_value_before.args, ('password=SuperSecret',))

        # Apply the filter
        filter_obj = SensitiveDataFilter()
        filter_obj.filter(record)

        # Verify fail-closed behavior: exc_info should be None
        self.assertIsNone(record.exc_info,
            "record.exc_info should be None when exception reconstruction fails to prevent leakage")


if __name__ == '__main__':
    unittest.main()