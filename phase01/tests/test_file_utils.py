"""
Unit tests for file utilities security.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from phase01.utils.file_utils import ensure_directory, verify_output_path, write_json_file
from phase01.core.exceptions import FileOperationError
from phase01.config.settings import settings


class TestFileUtilsSecurity(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir()
        # Save original output_dir
        self.original_output_dir = settings.output_dir
        # Override settings for testing
        settings.output_dir = self.output_dir

    def tearDown(self):
        """Clean up temporary directory and restore settings."""
        import shutil
        shutil.rmtree(self.test_dir)
        # Restore original output_dir
        settings.output_dir = self.original_output_dir

    def test_ensure_directory(self):
        """Test directory creation."""
        test_path = self.output_dir / "test_dir"
        result = ensure_directory(test_path)
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())

    def test_verify_output_path_valid(self):
        """Test that valid paths inside output directory are allowed."""
        test_path = self.output_dir / "test.json"
        result = verify_output_path(test_path, self.output_dir)
        self.assertEqual(result, test_path)

    def test_verify_output_path_traversal(self):
        """Test that path traversal attempts are rejected."""
        test_path = self.output_dir / "../outside.json"
        with self.assertRaises(FileOperationError):
            verify_output_path(test_path, self.output_dir)

    def test_verify_output_path_absolute_outside(self):
        """Test that absolute paths outside output directory are rejected."""
        test_path = "/tmp/outside.json"
        with self.assertRaises(FileOperationError):
            verify_output_path(test_path, self.output_dir)

    def test_write_json_file_valid(self):
        """Test that valid JSON writes inside output directory succeed."""
        test_path = self.output_dir / "test.json"
        test_data = {"key": "value"}
        write_json_file(test_path, test_data)
        self.assertTrue(test_path.exists())
        with open(test_path, "r") as f:
            content = json.load(f)
        self.assertEqual(content, test_data)

    def test_write_json_file_traversal(self):
        """Test that path traversal attempts are rejected."""
        test_path = self.output_dir / "../outside.json"
        test_data = {"key": "value"}
        with self.assertRaises(FileOperationError):
            write_json_file(test_path, test_data)

    def test_write_json_file_absolute_outside(self):
        """Test that absolute paths outside output directory are rejected."""
        test_path = "/tmp/outside.json"
        test_data = {"key": "value"}
        with self.assertRaises(FileOperationError):
            write_json_file(test_path, test_data)


if __name__ == '__main__':
    unittest.main()