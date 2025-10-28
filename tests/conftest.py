"""Pytest configuration and shared fixtures for tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_openapi_spec() -> dict:
    """Fixture providing a sample valid OpenAPI specification."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "PhoneAppli API",
            "version": "1.0.0",
            "description": "API for PhoneAppli services",
        },
        "servers": [
            {"url": "https://api.phoneappli.net/v1", "description": "Production"},
            {"url": "https://api-sandbox.phoneappli.net/v1", "description": "Sandbox"},
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "Success"}},
                },
                "post": {
                    "summary": "Create user",
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/items": {
                "get": {
                    "summary": "Get items",
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }


@pytest.fixture
def minimal_openapi_spec() -> dict:
    """Fixture providing a minimal valid OpenAPI specification."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Minimal API", "version": "1.0.0"},
        "paths": {},
    }


@pytest.fixture
def invalid_openapi_spec() -> dict:
    """Fixture providing an invalid OpenAPI specification."""
    return {
        "openapi": "3.0.0",
        # Missing required 'info' field
        "paths": {},
    }


@pytest.fixture
def sample_openapi_yaml(tmp_path: Path, sample_openapi_spec: dict) -> Path:
    """Fixture creating a temporary YAML file with sample OpenAPI spec."""
    import yaml

    spec_file = tmp_path / "openapi.yaml"
    spec_file.write_text(yaml.dump(sample_openapi_spec))
    return spec_file


@pytest.fixture
def minimal_openapi_yaml(tmp_path: Path, minimal_openapi_spec: dict) -> Path:
    """Fixture creating a temporary YAML file with minimal OpenAPI spec."""
    import yaml

    spec_file = tmp_path / "minimal.yaml"
    spec_file.write_text(yaml.dump(minimal_openapi_spec))
    return spec_file
