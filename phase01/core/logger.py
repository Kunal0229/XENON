"""
Centralized logging module for XENON Phase 01.
Ensures sensitive data (tokens, passwords, cookies, auth headers, keys) are not logged.
"""

import logging
import re
import sys


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records."""

    # Sensitive patterns to sanitize in log messages
    # Each pattern is designed to match actual secret values, not format specifiers
    SENSITIVE_PATTERNS = [
        # password=VALUE with actual value (word characters, not format specifiers)
        re.compile(r'(password|passwd|pwd)=([a-zA-Z0-9_@\-]+)', re.IGNORECASE),
        # token=VALUE with actual value (standalone token pattern)
        re.compile(r'token=([a-zA-Z0-9_@\-]+)', re.IGNORECASE),
        # api_key=VALUE or similar patterns
        re.compile(r'(api[_-]?key|auth[_-]?token|access[_-]?token|secret)=([a-zA-Z0-9_@\-]+)', re.IGNORECASE),
        # Bearer TOKEN with actual value (not %s format specifier)
        re.compile(r'Bearer\s+([a-zA-Z0-9_@\-.\+]+)', re.IGNORECASE),
        # Basic BASE64_VALUE with actual value (not %s format specifier)
        re.compile(r'Basic\s+([a-zA-Z0-9\+\/]+=*)', re.IGNORECASE),
        # Cookie: VALUE with actual value
        re.compile(r'Cookie:\s*([a-zA-Z0-9_@\-.]+(?:=[a-zA-Z0-9_@\-.]*)?)', re.IGNORECASE),
        # Authorization: VALUE with actual value
        re.compile(r'Authorization:\s+(.+)', re.IGNORECASE),
    ]

    # Format string patterns that indicate the next argument is a secret
    SECRET_FORMAT_PATTERNS = [
        re.compile(r'token\s*=\s*%s', re.IGNORECASE),
        re.compile(r'password\s*=\s*%s', re.IGNORECASE),
        re.compile(r'api[_-]?key\s*=\s*%s', re.IGNORECASE),
        re.compile(r'auth[_-]?token\s*=\s*%s', re.IGNORECASE),
        re.compile(r'access[_-]?token\s*=\s*%s', re.IGNORECASE),
        re.compile(r'secret\s*=\s*%s', re.IGNORECASE),
        re.compile(r'Bearer\s+%s', re.IGNORECASE),
        re.compile(r'Basic\s+%s', re.IGNORECASE),
        re.compile(r'Cookie:\s*%s', re.IGNORECASE),
        re.compile(r'Authorization:\s+%s', re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log messages before processing."""
        # Redact the message itself - handles inline key=value patterns
        if record.msg:
            record.msg = self._redact_pattern(record.msg, self.SENSITIVE_PATTERNS)

        # Handle args for parameterized logging (logger.info("token=%s", SECRET))
        # When args are present, we need to redact them to prevent secret exposure
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                # Check if the format string suggests secrets are coming
                has_secret_format = self._has_secret_format(record.msg)

                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        if has_secret_format:
                            # Format string indicates secret - redact the argument entirely
                            new_args.append('REDACTED')
                        else:
                            # Redact any sensitive strings in args using patterns
                            redacted_arg = self._redact_pattern(arg, self.SENSITIVE_PATTERNS)
                            new_args.append(redacted_arg)
                    else:
                        new_args.append(arg)
                record.args = tuple(new_args)

        return True

    def _has_secret_format(self, msg: str) -> bool:
        """Check if the format string indicates sensitive data is expected."""
        if not msg:
            return False
        for pattern in self.SECRET_FORMAT_PATTERNS:
            if pattern.search(msg):
                return True
        return False

    def _redact_pattern(self, msg: str, patterns: list) -> str:
        """Apply regex patterns to redact sensitive information."""
        result = msg
        for pattern in patterns:
            result = pattern.sub('REDACTED', result)
        return result


def setup_logger(name: str = "XENON", level: str = "INFO") -> logging.Logger:
    """Configure and return a centralized logger instance."""
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    handler.addFilter(sensitive_filter)
    logger.addFilter(sensitive_filter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Default logger instance
logger = setup_logger()