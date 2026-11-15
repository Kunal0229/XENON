"""
Target Manager module for XENON Phase 01.
Responsible for target lifecycle management, validation, and storage.
"""

from typing import Optional
from urllib.parse import urlparse
from phase01.models.target import Target
from phase01.utils.validation import validate_target
from phase01.core.exceptions import InvalidTargetError
from phase01.core.logger import logger
from phase01.config.defaults import ALLOWED_TARGET_STATUSES, DEFAULT_TARGET_STATUS
from phase01.config.settings import settings
from phase01.core.scope_manager import ScopeManager


class TargetManager:
    """Manages creation, validation, storage, and retrieval of assessment targets."""

    def __init__(self, scope_manager: Optional[ScopeManager] = None):
        """Initialize TargetManager with an optional ScopeManager.

        Args:
            scope_manager: ScopeManager instance for scope enforcement.
                          If None, target setting will fail closed for security.
        """
        self._current_target: Optional[Target] = None
        self._scope_manager = scope_manager

    def set_target(self, target_url: str, status: Optional[str] = None) -> Target:
        """
        Validate and set the current assessment target.
        Raises InvalidTargetError if validation or scope checks fail.
        Atomic: state only mutated after ALL validations and scope checks pass.
        Fails closed if scope_manager is not provided or scope is not loaded.
        """
        if self._scope_manager is None:
            raise InvalidTargetError("ScopeManager is required - scope enforcement is mandatory")

        if status is None:
            status = settings.get("default_target_status", DEFAULT_TARGET_STATUS)

        # Sanitize URL for logging (remove credentials)
        safe_url = self._sanitize_url_for_log(target_url)
        logger.info(f"Validating target: {safe_url}")

        # Phase 1: Validate target structure and security
        validate_target(target_url)

        # Check for credentials in URL
        parsed = urlparse(target_url)
        if parsed.username or parsed.password:
            raise InvalidTargetError("Target URL contains credentials - rejected for security")

        # Phase 2: Normalize and validate status
        normalized_status = status.lower()
        if normalized_status not in ALLOWED_TARGET_STATUSES:
            raise InvalidTargetError(f"Invalid target status '{status}'. Allowed: {ALLOWED_TARGET_STATUSES}")

        # Phase 3: Enforce scope (fails closed if scope not loaded)
        if not self._scope_manager.is_in_scope(target_url):
            safe_target = self._sanitize_url_for_log(target_url)
            raise InvalidTargetError(f"Target {safe_target} is out of scope")

        # Phase 4: ALL VALIDATIONS & SECURITY CHECKS PASSED - now mutate state
        self._current_target = Target(target=target_url.strip(), status=normalized_status)

        safe_target = self._sanitize_url_for_log(self._current_target.target)
        logger.info(f"Target successfully set: {safe_target} (Status: {self._current_target.status})")
        return self._current_target

    def _sanitize_url_for_log(self, url: str) -> str:
        """Remove credentials from URL for safe logging, preserving path, query, and fragment."""
        try:
            parsed = urlparse(url)
            if parsed.username or parsed.password:
                netloc = parsed.hostname
                if parsed.port:
                    netloc = f"{netloc}:{parsed.port}"
                path = parsed.path or ""
                query = f"?{parsed.query}" if parsed.query else ""
                fragment = f"#{parsed.fragment}" if parsed.fragment else ""
                return f"{parsed.scheme}://{netloc}{path}{query}{fragment}"
        except Exception:
            pass
        return url

    def get_target(self) -> Optional[Target]:
        """Retrieve the current target object."""
        return self._current_target

    def get_target_url(self) -> Optional[str]:
        """Retrieve the current target URL string."""
        if self._current_target:
            return self._current_target.target
        return None

    def update_status(self, status: str) -> Target:
        """Update the status of the current target."""
        if not self._current_target:
            raise InvalidTargetError("No target currently set to update.")

        status = status.lower()
        if status not in ALLOWED_TARGET_STATUSES:
            raise InvalidTargetError(f"Invalid target status '{status}'. Allowed: {ALLOWED_TARGET_STATUSES}")

        self._current_target.status = status
        logger.info(f"Target status updated to: {self._current_target.status}")
        return self._current_target

    def clear(self) -> None:
        """Clear the current target."""
        self._current_target = None
        logger.info("Target cleared.")