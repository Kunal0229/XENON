"""
Default configuration values for XENON Phase 01.
"""

from pathlib import Path

DEFAULT_APP_NAME = "XENON"
DEFAULT_APP_VERSION = "1.0.0"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TARGET_STATUS = "active"
INACTIVE_TARGET_STATUS = "inactive"
ALLOWED_TARGET_STATUSES = {DEFAULT_TARGET_STATUS, INACTIVE_TARGET_STATUS}
SUPPORTED_SCHEMES = {"http", "https"}
DEFAULT_TARGET_URL = "https://example.com"
DEFAULT_SCOPE_CONFIG = {
    "in_scope": ["example.com", "*.example.com"],
    "out_of_scope": ["payments.example.com"]
}