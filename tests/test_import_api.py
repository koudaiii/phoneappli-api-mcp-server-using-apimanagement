"""Unit tests for import_api.py module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from import_api import (
    generate_api_policy,
    get_api_info_from_spec,
    import_api_to_apim,
    load_openapi_spec,
    main,
)


class TestLoadOpenAPISpec:
    """Tests for load_openapi_spec function."""

    def test_load_valid_spec(self, tmp_path: Path) -> None:
        """Test loading a valid OpenAPI spec file as string."""
        # Create a temporary YAML file
        spec_file = tmp_path / "openapi.yaml"
        spec_content = """openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths: {}
"""
        spec_file.write_text(spec_content)

        # Load and verify
        result = load_openapi_spec(spec_file)
        assert result == spec_content

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a non-existent file raises FileNotFoundError."""
        nonexistent_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_openapi_spec(nonexistent_file)


class TestGetAPIInfoFromSpec:
    """Tests for get_api_info_from_spec function."""

    def test_get_api_info_complete(self, tmp_path: Path) -> None:
        """Test extracting API info from complete spec."""
        spec_file = tmp_path / "openapi.yaml"
        spec_content = """openapi: 3.0.0
info:
  title: PhoneAppli API
  version: 2.0.0
  description: API for PhoneAppli services
paths: {}
"""
        spec_file.write_text(spec_content)

        result = get_api_info_from_spec(spec_file)

        assert result["title"] == "PhoneAppli API"
        assert result["version"] == "2.0.0"
        assert result["description"] == "API for PhoneAppli services"

    def test_get_api_info_missing_fields(self, tmp_path: Path) -> None:
        """Test extracting API info with missing fields uses defaults."""
        spec_file = tmp_path / "openapi.yaml"
        spec_content = """openapi: 3.0.0
info: {}
paths: {}
"""
        spec_file.write_text(spec_content)

        result = get_api_info_from_spec(spec_file)

        assert result["title"] == "Imported API"
        assert result["version"] == "1.0"
        assert result["description"] == ""


class TestGenerateAPIPolicy:
    """Tests for generate_api_policy function."""

    def test_generate_sandbox_policy(self) -> None:
        """Test generating policy for sandbox environment."""
        policy = generate_api_policy("sandbox")

        assert "phoneappli-api-key-sandbox" in policy
        assert "<set-header name=\"X-Pa-Api-Key\"" in policy
        assert "<policies>" in policy
        assert "</policies>" in policy

    def test_generate_production_policy(self) -> None:
        """Test generating policy for production environment."""
        policy = generate_api_policy("production")

        assert "phoneappli-api-key-production" in policy
        assert "<set-header name=\"X-Pa-Api-Key\"" in policy
        assert "<policies>" in policy
        assert "</policies>" in policy


class TestImportAPIToAPIM:
    """Tests for import_api_to_apim function."""

    @patch("import_api.ApiManagementClient")
    @patch("import_api.DefaultAzureCredential")
    @patch("import_api.get_api_info_from_spec")
    @patch("import_api.load_openapi_spec")
    @patch("import_api.console")
    def test_import_api_success_sandbox(
        self,
        mock_console: MagicMock,
        mock_load_spec: MagicMock,
        mock_get_info: MagicMock,
        mock_credential: MagicMock,
        mock_apim_client_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful API import to sandbox environment."""
        # Create test spec file
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        # Mock API info
        mock_get_info.return_value = {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test description",
        }
        mock_load_spec.return_value = "openapi: 3.0.0"

        # Mock subscription - this is imported inside the function
        mock_subscription = Mock()
        mock_subscription.subscription_id = "test-subscription-id"
        mock_subscription_client_instance = Mock()
        mock_subscription_client_instance.subscriptions.list.return_value = [
            mock_subscription
        ]

        # Mock APIM client
        mock_api_result = Mock()
        mock_api_result.display_name = "Test API"
        mock_api_result.path = "test-api"
        mock_api_result.name = "test-api-id"

        mock_begin_create = Mock()
        mock_begin_create.result.return_value = mock_api_result

        mock_apim_instance = Mock()
        mock_apim_instance.api.begin_create_or_update.return_value = mock_begin_create
        mock_apim_instance.api_policy.create_or_update.return_value = None

        mock_apim_client_class.return_value = mock_apim_instance

        # Patch the SubscriptionClient that's imported inside the function
        with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
            mock_sub_client.return_value = mock_subscription_client_instance

            # Call function
            result = import_api_to_apim(
                resource_group="test-rg",
                apim_name="test-apim",
                openapi_spec_path=spec_file,
                api_id="test-api",
                api_path="test-api",
                environment="sandbox",
            )

        assert result is True
        mock_apim_instance.api.begin_create_or_update.assert_called_once()
        mock_apim_instance.api_policy.create_or_update.assert_called_once()

    @patch("import_api.console")
    def test_import_api_invalid_environment(
        self, mock_console: MagicMock, tmp_path: Path
    ) -> None:
        """Test import with invalid environment."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        result = import_api_to_apim(
            resource_group="test-rg",
            apim_name="test-apim",
            openapi_spec_path=spec_file,
            api_id="test-api",
            api_path="test-api",
            environment="invalid",
        )

        assert result is False

    @patch("import_api.DefaultAzureCredential")
    @patch("import_api.console")
    def test_import_api_authentication_failure(
        self, mock_console: MagicMock, mock_credential: MagicMock, tmp_path: Path
    ) -> None:
        """Test import with authentication failure."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        mock_credential.side_effect = Exception("Authentication failed")

        result = import_api_to_apim(
            resource_group="test-rg",
            apim_name="test-apim",
            openapi_spec_path=spec_file,
            api_id="test-api",
            api_path="test-api",
            environment="sandbox",
        )

        assert result is False


class TestMain:
    """Tests for main function."""

    @patch("import_api.import_api_to_apim")
    @patch("import_api.console")
    def test_main_success(
        self, mock_console: MagicMock, mock_import: MagicMock, tmp_path: Path
    ) -> None:
        """Test main function with successful import."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        mock_import.return_value = True

        test_args = [
            "import_api.py",
            "--resource-group",
            "test-rg",
            "--apim-name",
            "test-apim",
            "--openapi-spec",
            str(spec_file),
            "--environment",
            "sandbox",
        ]

        with patch("sys.argv", test_args):
            result = main()

        assert result == 0
        mock_import.assert_called_once()

    @patch("import_api.import_api_to_apim")
    @patch("import_api.console")
    def test_main_import_failure(
        self, mock_console: MagicMock, mock_import: MagicMock, tmp_path: Path
    ) -> None:
        """Test main function with import failure."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        mock_import.return_value = False

        test_args = [
            "import_api.py",
            "--resource-group",
            "test-rg",
            "--apim-name",
            "test-apim",
            "--openapi-spec",
            str(spec_file),
        ]

        with patch("sys.argv", test_args):
            result = main()

        assert result == 1

    @patch("import_api.console")
    def test_main_file_not_found(self, mock_console: MagicMock) -> None:
        """Test main function with non-existent spec file."""
        test_args = [
            "import_api.py",
            "--resource-group",
            "test-rg",
            "--apim-name",
            "test-apim",
            "--openapi-spec",
            "/nonexistent/file.yaml",
        ]

        with patch("sys.argv", test_args):
            result = main()

        assert result == 1

    @patch("import_api.import_api_to_apim")
    @patch("import_api.console")
    def test_main_with_custom_parameters(
        self, mock_console: MagicMock, mock_import: MagicMock, tmp_path: Path
    ) -> None:
        """Test main function with custom API ID and path."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        mock_import.return_value = True

        test_args = [
            "import_api.py",
            "--resource-group",
            "test-rg",
            "--apim-name",
            "test-apim",
            "--openapi-spec",
            str(spec_file),
            "--api-id",
            "custom-api",
            "--api-path",
            "custom/path",
            "--environment",
            "production",
        ]

        with patch("sys.argv", test_args):
            result = main()

        assert result == 0
        mock_import.assert_called_once_with(
            resource_group="test-rg",
            apim_name="test-apim",
            openapi_spec_path=spec_file,
            api_id="custom-api",
            api_path="custom/path",
            environment="production",
        )
