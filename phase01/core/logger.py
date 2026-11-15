"""
Centralized logging module for XENON Phase 01.
Ensures sensitive data (tokens, passwords, cookies, auth headers, keys) are not logged.
"""

import logging
import re
import sys


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records."""

    # Sensitive patterns to sanitize in log messages (inline only, no %s)
    # Patterns for key:value or key=value and explicit header/auth formats with optional whitespace.
    #
    # The value class is DELIMITER-AWARE. It matches non-space, non-delimiter characters, and
    # allows internal whitespace ONLY when that whitespace is NOT followed by a trailing
    # key:value/key=value pattern. This means:
    #   - "password: my secret value"  -> the whole multi-word secret is captured (F-01)
    #   - "token=SECRET status=active" -> the trailing "status=active" context is preserved (F-05)
    # A naive "stop at first whitespace" rule would regress F-01 by leaking "secret value".
    # A naive "consume everything" rule would regress F-05 by eating trailing context.
    SENSITIVE_PATTERNS = [
        re.compile(r'(password|passwd|pwd|token|api[_-]?key|access[_-]?token|secret|auth[_-]?token)\s*[:=]\s*(?:[^\r\n,;&(){}[\]<>\"\'\`\s]+|\s+(?![a-zA-Z][a-zA-Z0-9_-]*\s*[:=]))+', re.IGNORECASE),
        re.compile(r'(Bearer|Basic)\s+(?:[^\r\n,;&(){}[\]<>\"\'\`\s]+|\s+(?![a-zA-Z][a-zA-Z0-9_-]*\s*[:=]))+', re.IGNORECASE),
        re.compile(r'(Cookie|Authorization)\s*[:=]\s*(?:[^\r\n,;&(){}[\]<>\"\'\`\s]+|\s+(?![a-zA-Z][a-zA-Z0-9_-]*\s*[:=]))+', re.IGNORECASE),
        re.compile(r'(https?://)([^:@/]+:[^@/]+@)', re.IGNORECASE),
    ]

    # Format string patterns to detect when parameterized logging is about to insert a secret
    # These patterns match format strings that will insert secrets via %s
    SECRET_FORMAT_PATTERNS = [
        re.compile(r'(token|password|api[_-]?key|auth[_-]?token|access[_-]?token|secret|authorization|cookie)\s*[:=]\s*%s', re.IGNORECASE),
        re.compile(r'(token|password|api[_-]?key|auth[_-]?token|access[_-]?token|secret|authorization|cookie)\s+is\s+%s', re.IGNORECASE),
        re.compile(r'Bearer\s+%s', re.IGNORECASE),
        re.compile(r'Basic\s+%s', re.IGNORECASE),
        re.compile(r'%\((token|password|api[_-]?key|auth[_-]?token|access[_-]?token|secret|authorization|cookie)\)s', re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log records before processing."""
        if record.msg is not None and not isinstance(record.msg, str):
            record.msg = str(record.msg)

        # Check if this is a parameterized log with %s placeholders that will be filled by args
        has_secret_format = self._has_secret_format(record.msg) if record.msg else False

        # Handle args for parameterized logging FIRST
        # For secret formats, redact ALL args to prevent leakage
        # For non-secret formats, redact args normally
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, (list, tuple)):
                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        if has_secret_format:
                            # Secret format detected - redact the argument to prevent leakage
                            new_args.append('REDACTED')
                        else:
                            # Non-secret format - redact any sensitive patterns in the argument
                            new_args.append(self._redact_pattern(arg, self.SENSITIVE_PATTERNS))
                    else:
                        new_args.append(arg)
                record.args = tuple(new_args)
            elif isinstance(record.args, dict):
                new_args = {}
                for k, v in record.args.items():
                    if isinstance(v, str):
                        # Check if the format string uses dict-style %(key)s for this key
                        key_is_secret = False
                        if record.msg and f'%({k})s' in record.msg:
                            key_is_secret = self._is_secret_key(k)
                        if has_secret_format or key_is_secret:
                            # Secret format or secret key - redact the value
                            new_args[k] = 'REDACTED'
                        else:
                            # Non-secret format - redact any sensitive patterns
                            new_args[k] = self._redact_pattern(v, self.SENSITIVE_PATTERNS)
                    else:
                        new_args[k] = v
                record.args = new_args

        # Now handle the message itself
        # If this is a secret format, the args have been redacted, so we leave msg alone
        # Formatting will happen later with redacted args, producing a safe result
        # If this is NOT a secret format, we can safely redact inline secrets in the message
        if record.msg and not has_secret_format:
            record.msg = self._redact_pattern(record.msg, self.SENSITIVE_PATTERNS)

        # Handle exc_info (exception information) to prevent leakage of secrets in exceptions
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            # Reduce each string argument in the exception
            new_args = []
            redacted = False
            for arg in exc_value.args:
                if isinstance(arg, str):
                    redacted_arg = self._redact_pattern(arg, self.SENSITIVE_PATTERNS)
                    if redacted_arg != arg:
                        redacted = True
                    new_args.append(redacted_arg)
                else:
                    new_args.append(arg)
            if redacted:
                try:
                    # Create a new exception of the same type with the redacted args
                    new_exc = exc_type(*new_args)
                    record.exc_info = (exc_type, new_exc, exc_traceback)
                except Exception:
                    # If we cannot create a new exception, remove exc_info to prevent leakage
                    record.exc_info = None

        # Handle stack_info to prevent leakage of secrets in stack traces (if any)
        if record.stack_info and isinstance(record.stack_info, str):
            redacted_stack = self._redact_pattern(record.stack_info, self.SENSITIVE_PATTERNS)
            if redacted_stack != record.stack_info:
                record.stack_info = redacted_stack

        return True

    def _has_secret_format(self, msg: str) -> bool:
        if not msg:
            return False
        return any(p.search(msg) for p in self.SECRET_FORMAT_PATTERNS)

    def _is_secret_key(self, key: str) -> bool:
        """Check if a dictionary key corresponds to a sensitive field."""
        sensitive_keys = {'token', 'password', 'api_key', 'auth_token', 'access_token', 'secret', 'authorization', 'cookie'}
        return key.lower() in sensitive_keys

    def _redact_pattern(self, msg: str, patterns: list) -> str:
        result = msg
        for pattern in patterns:
            if pattern.pattern.startswith('(https?://)'):
                result = pattern.sub(r'\1REDACTED@', result)
            else:
                result = pattern.sub(r'\1=REDACTED', result) if '=' in pattern.pattern or ':' in pattern.pattern else pattern.sub(r'\1 REDACTED', result)
        return result


def setup_logger(name: str = "XENON", level: str = None) -> logging.Logger:
    """Configure and return a centralized logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Use provided level, or fall back to settings, then default INFO
    # If level is None, use configured level; if explicitly provided, use it
    try:
        from phase01.config.settings import settings
        config_level = settings.get("log_level", "INFO")
    except Exception:
        config_level = "INFO"

    effective_level = level if level is not None else config_level
    numeric_level = getattr(logging, effective_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    sensitive_filter = SensitiveDataFilter()
    handler.addFilter(sensitive_filter)
    logger.addFilter(sensitive_filter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Default logger instance
logger = setup_logger()