"""
Target data model for XENON Phase 01.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any
from phase01.config.defaults import DEFAULT_TARGET_STATUS


@dataclass
class Target:
    """Represents an authorized target web resource."""
    target: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: str = DEFAULT_TARGET_STATUS

    def to_dict(self) -> Dict[str, Any]:
        """Convert target model to dictionary matching the target data contract."""
        return {
            "target": self.target,
            "created_at": self.created_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Target":
        """Create target model from dictionary data."""
        return cls(
            target=data.get("target", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            status=data.get("status", DEFAULT_TARGET_STATUS),
        )
