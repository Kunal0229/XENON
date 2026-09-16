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


class TargetManager:
    """Manages creation, validation, storage, and retrieval of assessment targets."""

    def __init__(self):
        self._current_target: Optional[Target] = None

    def set_target(self, target_url: str, status: Optional[str] = None) -> Target:
        """
        Validate and set the current assessment target.
        Raises InvalidTargetError if validation fails.
        """
        if status is None:
            status = settings.get("default_target_status", DEFAULT_TARGET_STATUS)

        logger.info(f"Validating target: {target_url}")
        validate_target(target_url)

        # Check for credentials in URL
        parsed = urlparse(target_url)
        if parsed.username or parsed.password:
            raise InvalidTargetError("Target URL contains credentials - rejected for security")

        if status not in ALLOWED_TARGET_STATUSES:
            raise InvalidTargetError(f"Invalid target status '{status}'. Allowed: {ALLOWED_TARGET_STATUSES}")

        self._current_target = Target(target=target_url.strip(), status=status.lower())
        logger.info(f"Target successfully set: {self._current_target.target} (Status: {self._current_target.status})")
        return self._current_target

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
