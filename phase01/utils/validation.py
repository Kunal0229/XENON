"""
Validation utilities for targets and scope in XENON Phase 01.
"""

from urllib.parse import urlparse
from phase01.config.defaults import SUPPORTED_SCHEMES
from phase01.core.exceptions import InvalidTargetError, InvalidScopeError


def validate_target(target: str) -> bool:
    """
    Validate target URL structure, scheme, and hostname.
    Raises InvalidTargetError if invalid.
    Returns True if valid.
    """
    if not target or not isinstance(target, str):
        raise InvalidTargetError("Target cannot be empty or non-string.")

    target = target.strip()
    if not target:
        raise InvalidTargetError("Target cannot be empty.")

    # Reject target with whitespace inside URL
    if any(c in target for c in " \t\n\r"):
        raise InvalidTargetError(f"Target URL contains whitespace: '{target}'")

    try:
        parsed = urlparse(target)
        # Validate port if specified
        if parsed.port is not None:
            if not (1 <= parsed.port <= 65535):
                raise InvalidTargetError(f"Invalid port in target URL: {parsed.port}")
    except ValueError as e:
        raise InvalidTargetError(f"Malformed target URL or port: {target}") from e
    except Exception as e:
        raise InvalidTargetError(f"Malformed target URL: {target}") from e

    if not parsed.scheme:
        raise InvalidTargetError(f"Target missing URL scheme: {target}")

    if parsed.scheme.lower() not in SUPPORTED_SCHEMES:
        raise InvalidTargetError(
            f"Unsupported target scheme '{parsed.scheme}'. Supported schemes: {SUPPORTED_SCHEMES}"
        )

    if not parsed.netloc:
        raise InvalidTargetError(f"Target missing hostname/netloc: {target}")

    # Reject credential-bearing URLs
    if parsed.username or parsed.password:
        raise InvalidTargetError("Target URL contains credentials - rejected for security")

    try:
        hostname = parsed.hostname
    except ValueError as e:
        raise InvalidTargetError(f"Invalid hostname in target URL: {target}") from e

    if not hostname:
        raise InvalidTargetError(f"Target has invalid or missing hostname: {target}")

    if not _is_valid_hostname(hostname):
        raise InvalidTargetError(f"Invalid hostname format: {hostname}")

    return True


def _is_valid_hostname(hostname: str) -> bool:
    """Check if hostname format is valid (RFC 1123 / standard domain)."""
    if not hostname or len(hostname) > 253:
        return False

    if hostname.startswith("*."):
        hostname = hostname[2:]

    if hostname.endswith("."):
        hostname = hostname[:-1]

    if not hostname:
        return False

    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if not all(c in allowed_chars for c in hostname):
        return False

    labels = hostname.split(".")

    for label in labels:
        if not label:
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
        if len(label) > 63:
            return False

    return True


def validate_scope_entry(entry: str) -> bool:
    """
    Validate a single scope entry (domain, wildcard domain, or URL).
    Raises InvalidScopeError if invalid.
    Returns True if valid.
    """
    if not entry or not isinstance(entry, str):
        raise InvalidScopeError("Scope entry cannot be empty or non-string.")

    entry = entry.strip()
    if not entry:
        raise InvalidScopeError("Scope entry cannot be empty.")

    if any(c in entry for c in " \t\n\r"):
        raise InvalidScopeError(f"Scope entry contains whitespace: '{entry}'")

    if "://" in entry:
        try:
            validate_target(entry)
            return True
        except InvalidTargetError as e:
            raise InvalidScopeError(f"Invalid scope URL entry '{entry}': {e}") from e

    check_hostname = entry
    if check_hostname.startswith("*."):
        check_hostname = check_hostname[2:]
        if "." not in check_hostname:
            raise InvalidScopeError(f"Unsafe or invalid wildcard scope entry '{entry}': must target a specific domain")

    if not _is_valid_hostname(check_hostname):
        raise InvalidScopeError(f"Invalid scope domain entry: {entry}")

    if "." not in check_hostname and check_hostname != "localhost":
        raise InvalidScopeError(f"Scope domain entry must contain a top-level domain: {entry}")

    return True


def validate_scope(scope_dict: dict) -> bool:
    """
    Validate complete scope configuration dictionary.
    Raises InvalidScopeError if invalid.
    Returns True if valid.
    """
    if not isinstance(scope_dict, dict):
        raise InvalidScopeError("Scope configuration must be a dictionary.")

    if "in_scope" not in scope_dict:
        raise InvalidScopeError("Scope configuration missing required 'in_scope' key.")

    in_scope = scope_dict.get("in_scope")
    out_of_scope = scope_dict.get("out_of_scope", [])

    if not isinstance(in_scope, list):
        raise InvalidScopeError("'in_scope' must be a list.")

    if not isinstance(out_of_scope, list):
        raise InvalidScopeError("'out_of_scope' must be a list.")

    if not in_scope:
        raise InvalidScopeError("'in_scope' list cannot be empty. Scope configuration must define at least one in-scope resource.")

    for entry in in_scope:
        validate_scope_entry(entry)

    for entry in out_of_scope:
        validate_scope_entry(entry)

    return True