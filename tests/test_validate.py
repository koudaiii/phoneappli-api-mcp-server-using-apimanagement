"""Unit tests for validate.py module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validate import (
    display_spec_info,
    load_openapi_spec,
    main,
    validate_openapi_spec,
)


class TestLoadOpenAPISpec:
    """Tests for load_openapi_spec function."""

    def test_load_valid_spec(self, tmp_path: Path) -> None:
        """Test loading a valid OpenAPI spec file."""
        # Create a temporary YAML file
        spec_file = tmp_path / "openapi.yaml"
        spec_content = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        spec_file.write_text(yaml.dump(spec_content))

        # Load and verify
        result = load_openapi_spec(spec_file)
        assert result == spec_content

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a non-existent file raises FileNotFoundError."""
        nonexistent_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_openapi_spec(nonexistent_file)

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading invalid YAML raises YAMLError."""
        # Create a file with invalid YAML
        spec_file = tmp_path / "invalid.yaml"
        spec_file.write_text("{ invalid: yaml: content:")

        with pytest.raises(yaml.YAMLError):
            load_openapi_spec(spec_file)


class TestValidateOpenAPISpec:
    """Tests for validate_openapi_spec function."""

    @patch("validate.validate")
    @patch("validate.console")
    def test_validate_valid_spec(
        self, mock_console: MagicMock, mock_validate: MagicMock
    ) -> None:
        """Test validating a valid OpenAPI spec."""
        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}}

        result = validate_openapi_spec(spec)

        assert result is True
        mock_validate.assert_called_once_with(spec)
        mock_console.print.assert_called_once()

    @patch("validate.validate")
    @patch("validate.console")
    def test_validate_invalid_spec(
        self, mock_console: MagicMock, mock_validate: MagicMock
    ) -> None:
        """Test validating an invalid OpenAPI spec."""
        spec = {"invalid": "spec"}
        mock_validate.side_effect = OpenAPISpecValidatorError("Invalid spec")

        result = validate_openapi_spec(spec)

        assert result is False
        mock_validate.assert_called_once_with(spec)
        mock_console.print.assert_called_once()


class TestDisplaySpecInfo:
    """Tests for display_spec_info function."""

    @patch("validate.console")
    def test_display_basic_info(self, mock_console: MagicMock) -> None:
        """Test displaying basic spec information."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "A test API",
            },
            "paths": {
                "/users": {"get": {}, "post": {}},
                "/items": {"get": {}, "put": {}, "delete": {}},
            },
        }

        display_spec_info(spec)

        # Verify console.print was called (table and empty line)
        assert mock_console.print.call_count == 2

    @patch("validate.console")
    def test_display_with_long_description(self, mock_console: MagicMock) -> None:
        """Test displaying spec with long description (truncation)."""
        long_description = "A" * 150
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": long_description,
            },
            "paths": {},
        }

        display_spec_info(spec)

        # Verify console.print was called
        assert mock_console.print.call_count == 2

    @patch("validate.console")
    def test_display_missing_fields(self, mock_console: MagicMock) -> None:
        """Test displaying spec with missing fields."""
        spec = {}

        display_spec_info(spec)

        # Should not raise an error and display N/A values
        assert mock_console.print.call_count == 2


class TestMain:
    """Tests for main function."""

    @patch("validate.validate_openapi_spec")
    @patch("validate.display_spec_info")
    @patch("validate.load_openapi_spec")
    @patch("validate.console")
    def test_main_success(
        self,
        mock_console: MagicMock,
        mock_load: MagicMock,
        mock_display: MagicMock,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test main function with successful validation."""
        # Create a temporary spec file
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        # Mock the spec loading and validation
        mock_spec = {"openapi": "3.0.0"}
        mock_load.return_value = mock_spec
        mock_validate.return_value = True

        # Mock sys.argv
        with patch("sys.argv", ["validate.py", str(spec_file)]):
            result = main()

        assert result == 0
        mock_load.assert_called_once()
        mock_display.assert_called_once_with(mock_spec)
        mock_validate.assert_called_once_with(mock_spec)

    @patch("validate.console")
    def test_main_no_arguments(self, mock_console: MagicMock) -> None:
        """Test main function with no arguments."""
        with patch("sys.argv", ["validate.py"]):
            result = main()

        assert result == 1
        # Should print error message
        assert mock_console.print.call_count >= 2

    @patch("validate.load_openapi_spec")
    @patch("validate.console")
    def test_main_file_not_found(
        self, mock_console: MagicMock, mock_load: MagicMock
    ) -> None:
        """Test main function with non-existent file."""
        mock_load.side_effect = FileNotFoundError("File not found")

        with patch("sys.argv", ["validate.py", "/nonexistent/file.yaml"]):
            result = main()

        assert result == 1

    @patch("validate.load_openapi_spec")
    @patch("validate.console")
    def test_main_yaml_error(
        self, mock_console: MagicMock, mock_load: MagicMock
    ) -> None:
        """Test main function with YAML parsing error."""
        mock_load.side_effect = yaml.YAMLError("Invalid YAML")

        with patch("sys.argv", ["validate.py", "/some/file.yaml"]):
            result = main()

        assert result == 1

    @patch("validate.validate_openapi_spec")
    @patch("validate.display_spec_info")
    @patch("validate.load_openapi_spec")
    @patch("validate.console")
    def test_main_validation_failure(
        self,
        mock_console: MagicMock,
        mock_load: MagicMock,
        mock_display: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test main function with validation failure."""
        mock_spec = {"openapi": "3.0.0"}
        mock_load.return_value = mock_spec
        mock_validate.return_value = False

        with patch("sys.argv", ["validate.py", "/some/file.yaml"]):
            result = main()

        assert result == 1
