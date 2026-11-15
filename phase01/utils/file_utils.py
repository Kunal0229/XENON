"""
File and output utilities for XENON Phase 01.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union
from phase01.core.exceptions import FileOperationError


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, creating it if necessary."""
    try:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception as e:
        raise FileOperationError(f"Failed to create directory {path}: {e}") from e


def verify_output_path(file_path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
    """Verify that file path is safely contained within base_dir (preventing path traversal)."""
    try:
        base = Path(base_dir).resolve()
        target = Path(file_path).resolve()
        if not target.is_relative_to(base):
            raise FileOperationError(f"Path traversal detected: {target} is outside base directory {base}")
        return target
    except Exception as e:
        if isinstance(e, FileOperationError):
            raise
        raise FileOperationError(f"Output path verification failed for {file_path}: {e}") from e


def write_json_file(file_path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Write dictionary data as JSON to file safely."""
    path = Path(file_path)
    from phase01.config.settings import settings
    base_dir = settings.output_dir

    # verify_output_path raises FileOperationError directly
    verify_output_path(path, base_dir)

    try:
        ensure_directory(path.parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except FileOperationError:
        raise
    except Exception as e:
        raise FileOperationError(f"Failed to write JSON file {file_path}: {e}") from e


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Read JSON data from file safely."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"File not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileOperationError:
        raise
    except Exception as e:
        raise FileOperationError(f"Failed to read JSON file {file_path}: {e}") from e