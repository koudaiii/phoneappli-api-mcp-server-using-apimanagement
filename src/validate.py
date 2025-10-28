#!/usr/bin/env python3
"""
OpenAPI Specification Validator

This script validates an OpenAPI specification file (YAML format) against the OpenAPI 3.0 schema.
"""

import sys
from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def load_openapi_spec(file_path: Path) -> dict[str, Any]:
    """
    Load OpenAPI specification from a YAML file.

    Args:
        file_path: Path to the OpenAPI spec file

    Returns:
        Parsed OpenAPI specification as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            spec = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML format: {e}") from e

    return spec


def display_spec_info(spec: dict[str, Any]) -> None:
    """
    Display basic information about the OpenAPI specification.

    Args:
        spec: OpenAPI specification dictionary
    """
    info = spec.get("info", {})

    table = Table(title="OpenAPI Specification Information", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("OpenAPI Version", spec.get("openapi", "N/A"))
    table.add_row("Title", info.get("title", "N/A"))
    table.add_row("Version", info.get("version", "N/A"))
    table.add_row(
        "Description",
        (info.get("description", "N/A")[:100] + "...")
        if len(info.get("description", "")) > 100
        else info.get("description", "N/A"),
    )

    # Count paths and operations
    paths = spec.get("paths", {})
    operation_count = sum(
        len([k for k in path_item.keys() if k in ["get", "post", "put", "patch", "delete", "options", "head"]])
        for path_item in paths.values()
        if isinstance(path_item, dict)
    )

    table.add_row("Paths", str(len(paths)))
    table.add_row("Operations", str(operation_count))

    console.print(table)
    console.print()


def validate_openapi_spec(spec: dict[str, Any]) -> bool:
    """
    Validate OpenAPI specification against the OpenAPI 3.0 schema.

    Args:
        spec: OpenAPI specification dictionary

    Returns:
        True if validation succeeds, False otherwise
    """
    try:
        validate(spec)
        console.print(
            Panel(
                "[bold green]✓ Validation successful![/bold green]\n"
                "The OpenAPI specification is valid and complies with OpenAPI 3.0 standards.",
                title="Validation Result",
                border_style="green",
            )
        )
        return True
    except OpenAPISpecValidatorError as e:
        console.print(
            Panel(
                f"[bold red]✗ Validation failed![/bold red]\n\n[red]Error:[/red] {str(e)}",
                title="Validation Result",
                border_style="red",
            )
        )
        return False


def main() -> int:
    """
    Main function to validate OpenAPI specification.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    console.print(Panel("[bold cyan]OpenAPI Specification Validator[/bold cyan]", expand=False))
    console.print()

    # Get file path from command line arguments
    if len(sys.argv) < 2:
        console.print("[red]Error:[/red] Please provide the path to the OpenAPI spec file.")
        console.print("Usage: python validate.py <openapi-spec-file>")
        return 1

    file_path = Path(sys.argv[1])

    try:
        # Load OpenAPI spec
        console.print(f"[cyan]Loading OpenAPI spec from:[/cyan] {file_path}")
        spec = load_openapi_spec(file_path)
        console.print("[green]✓[/green] File loaded successfully\n")

        # Display spec information
        display_spec_info(spec)

        # Validate spec
        console.print("[cyan]Validating OpenAPI specification...[/cyan]\n")
        if validate_openapi_spec(spec):
            return 0
        else:
            return 1

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1
    except yaml.YAMLError as e:
        console.print(f"[red]YAML Error:[/red] {e}")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
