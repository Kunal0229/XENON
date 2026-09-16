"""
Application-level configuration management for XENON Phase 01.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
from phase01.config.defaults import (
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_TARGET_STATUS,
)
from phase01.core.exceptions import ConfigurationError


class Settings:
    """Manages runtime configuration settings for XENON Phase 01."""

    def __init__(self, custom_settings: Optional[Dict[str, Any]] = None):
        self._settings: Dict[str, Any] = {
            "app_name": DEFAULT_APP_NAME,
            "app_version": DEFAULT_APP_VERSION,
            "output_dir": DEFAULT_OUTPUT_DIR,
            "log_level": DEFAULT_LOG_LEVEL,
            "default_target_status": DEFAULT_TARGET_STATUS,
        }

        if custom_settings:
            self.update(custom_settings)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        if not key:
            raise ConfigurationError("Configuration key cannot be empty.")
        self._settings[key] = value

    def update(self, new_settings: Dict[str, Any]) -> None:
        """Update multiple configuration settings."""
        if not isinstance(new_settings, dict):
            raise ConfigurationError("Settings update must be a dictionary.")
        for k, v in new_settings.items():
            self.set(k, v)

    @property
    def output_dir(self) -> Path:
        """Get output directory as a Path object."""
        path = self.get("output_dir")
        if isinstance(path, str):
            return Path(path)
        return path

    @output_dir.setter
    def output_dir(self, value: Union[str, Path]) -> None:
        """Set output directory."""
        self.set("output_dir", value)


# Global settings instance
settings = Settings()