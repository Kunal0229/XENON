"""
Scope data model for XENON Phase 01.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Scope:
    """Represents in-scope and out-of-scope resources and rules."""
    in_scope: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert scope model to dictionary matching the scope data contract."""
        return {
            "in_scope": self.in_scope,
            "out_of_scope": self.out_of_scope,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scope":
        """Create scope model from dictionary data."""
        return cls(
            in_scope=data.get("in_scope", []),
            out_of_scope=data.get("out_of_scope", []),
        )
