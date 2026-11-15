"""
Scope Manager module for XENON Phase 01.
Responsible for scope loading, storage, and enforcement (in-scope/out-of-scope).
"""

from typing import List, Optional, Dict
from urllib.parse import urlparse
from phase01.models.scope import Scope
from phase01.utils.validation import validate_scope
from phase01.core.exceptions import InvalidScopeError, OutOfScopeError
from phase01.core.logger import logger


class ScopeManager:
    """Manages scope enforcement and checks if resources are authorized for assessment."""

    def __init__(self):
        self._scope: Optional[Scope] = None

    def load_scope(self, scope_dict: Dict[str, List[str]]) -> None:
        """
        Load and validate scope configuration.
        Raises InvalidScopeError if validation fails.
        """
        logger.info("Loading and validating scope...")
        validate_scope(scope_dict)

        # Normalize rules when loading
        normalized_in_scope = [self._normalize_rule(rule) for rule in scope_dict.get("in_scope", [])]
        normalized_out_of_scope = [self._normalize_rule(rule) for rule in scope_dict.get("out_of_scope", [])]

        self._scope = Scope(
            in_scope=normalized_in_scope,
            out_of_scope=normalized_out_of_scope
        )
        logger.info(f"Scope loaded: {len(self._scope.in_scope)} in-scope, {len(self._scope.out_of_scope)} out-of-scope.")

    def _normalize_rule(self, rule: str) -> str:
        """Normalize a scope rule to canonical form (lowercase hostname)."""
        if not rule:
            return rule
        rule = rule.strip()
        if "://" in rule:
            parsed = urlparse(rule)
            return parsed.hostname.lower() if parsed.hostname else rule
        return rule.lower()

    def enforce_scope(self, resource: str) -> None:
        """
        Enforce scope validation.
        Raises OutOfScopeError if the resource is not allowed.
        Security-critical: This is the mandatory security boundary for all future modules.
        """
        if not self._scope:
            raise OutOfScopeError("Scope is not loaded - failing closed for security.")

        try:
            normalized_resource = self._normalize_resource(resource)
            if not normalized_resource:
                raise OutOfScopeError("Malformed or invalid resource format")
        except Exception:
            raise OutOfScopeError("Resource normalization failed")

        is_in_scope = self.is_in_scope(normalized_resource)

        if not is_in_scope:
            raise OutOfScopeError(f"Resource {normalized_resource} is out of scope.")

        logger.debug(f"Scope enforcement passed for: {normalized_resource}")

    def is_in_scope(self, resource: str) -> bool:
        """
        Determine if a resource is in scope.
        Returns True only if definitively in scope, False otherwise.
        """
        if not self._scope:
            logger.warning("Scope not loaded, assuming out-of-scope for safety.")
            return False

        if not resource:
            logger.warning("Empty or None resource provided for scope check")
            return False

        try:
            normalized_resource = self._normalize_resource(resource)
            if not normalized_resource:
                logger.warning("Resource normalization failed for scope check")
                return False
        except Exception:
            logger.warning("Resource normalization error in scope check")
            return False

        # Precedence: Explicit out-of-scope rules MUST always take precedence over in-scope rules
        if self._is_out_of_scope(normalized_resource):
            logger.info(f"Resource {normalized_resource} is explicitly OUT OF SCOPE.")
            return False

        if self._is_in_scope(normalized_resource):
            logger.info(f"Resource {normalized_resource} is IN SCOPE.")
            return True

        logger.info(f"Resource {normalized_resource} is NOT IN SCOPE (unknown/not matched).")
        return False

    def _normalize_resource(self, resource: str) -> Optional[str]:
        """
        Safely normalize a resource to hostname for scope matching.
        Handles: hostname, http://hostname, https://hostname, URLs with path/port.
        Returns hostname or None if resource is malformed/invalid.
        Uses proper URL parsing for hostname/port extraction.
        """
        if not resource or not isinstance(resource, str):
            return None

        resource = resource.strip()
        if not resource:
            return None

        # Check for whitespace
        if any(c in resource for c in " \t\n\r"):
            return None

        try:
            # Handle URL with scheme using standard URL parsing
            if "://" in resource:
                parsed = urlparse(resource)
                if not parsed.netloc:
                    return None

                # Validate port if present
                if parsed.port is not None:
                    # If port is specified but invalid, reject the resource
                    if not (1 <= parsed.port <= 65535):
                        return None

                return parsed.hostname.lower() if parsed.hostname else None
            else:
                # For bare hostnames, parse as a URL to validate format
                # This handles hostname:port format safely
                parsed = urlparse("http://" + resource)
                hostname = parsed.hostname
                if not hostname:
                    return None

                # If we got a port from parsing, validate it
                if parsed.port is not None:
                    # If port is invalid, reject the resource
                    if not (1 <= parsed.port <= 65535):
                        return None

                return hostname.lower()

        except Exception:
            return None

    def _is_out_of_scope(self, resource_host: str) -> bool:
        """Check if resource host matches any out-of-scope rule."""
        if not self._scope or not resource_host:
            return False

        for rule in self._scope.out_of_scope:
            if not rule:
                continue
            if self._matches_rule(resource_host, rule):
                return True
        return False

    def _is_in_scope(self, resource_host: str) -> bool:
        """Check if resource host matches any in-scope rule."""
        if not self._scope or not resource_host:
            return False

        for rule in self._scope.in_scope:
            if not rule:
                continue
            if self._matches_rule(resource_host, rule):
                return True
        return False

    def _matches_rule(self, resource_host: str, rule: str) -> bool:
        """
        Securely match resource host against a scope rule with strict wildcard semantics.

        Rule types:
        - "example.com" - exact match only
        - "*.example.com" - wildcard for subdomains only

        Semantics:
        - *.example.com matches api.example.com, deep.api.example.com
        - *.example.com does NOT match example.com
        - *.example.com does NOT match evil-example.com
        - *.example.com does NOT match example.com.evil.com
        - *.example.com does NOT match evil.com
        """
        if not resource_host or not rule:
            return False

        # Exact match
        if resource_host == rule:
            return True

        # Handle wildcard rules (*.example.com)
        if rule.startswith("*."):
            domain = rule[2:]
            # Ensure wildcard rule has a valid domain
            if "." not in domain:
                return False

            # Match must be a proper subdomain
            if resource_host == domain:
                return False  # *.example.com must not match example.com

            # Check if resource_host is a subdomain of domain
            if resource_host.endswith("." + domain):
                # Validate prefix structure - ensure no adjacent dots and validate subdomain structure
                prefix = resource_host[:-len("." + domain)]
                if not prefix:
                    return False

                # Check for adjacent dots
                if prefix.startswith(".") or prefix.endswith("."):
                    return False

                # Validate each label in prefix
                labels = prefix.split(".")
                for label in labels:
                    if not label or label.startswith("-") or label.endswith("-") or len(label) > 63:
                        return False

                return True

        return False