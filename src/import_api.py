#!/usr/bin/env python3
"""
API Import Script for Azure API Management

This script imports an OpenAPI specification into Azure API Management.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from azure.identity import DefaultAzureCredential
from azure.mgmt.apimanagement import ApiManagementClient
from azure.mgmt.apimanagement.models import (
    ApiCreateOrUpdateParameter,
    ApiType,
    ContentFormat,
    PolicyContract,
    Protocol,
)
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def load_openapi_spec(file_path: Path) -> str:
    """
    Load OpenAPI specification from a YAML file and return as string.

    Args:
        file_path: Path to the OpenAPI spec file

    Returns:
        OpenAPI specification as a YAML string

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content


def get_api_info_from_spec(file_path: Path) -> dict[str, Any]:
    """
    Extract basic API information from the OpenAPI spec.

    Args:
        file_path: Path to the OpenAPI spec file

    Returns:
        Dictionary containing API title and version
    """
    with open(file_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    info = spec.get("info", {})
    return {
        "title": info.get("title", "Imported API"),
        "version": info.get("version", "1.0"),
        "description": info.get("description", ""),
    }


def generate_api_policy() -> str:
    """
    Generate API-level policy XML that validates X-Pa-Api-Key header.

    Returns:
        Policy XML string
    """
    policy_xml = """<policies>
    <inbound>
        <base />
        <!-- Check if X-Pa-Api-Key header exists -->
        <choose>
            <when condition="@(context.Request.Headers.GetValueOrDefault(&quot;X-Pa-Api-Key&quot;,&quot;&quot;) == &quot;&quot;)">
                <return-response>
                    <set-status code="401" reason="Unauthorized" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/json</value>
                    </set-header>
                    <set-body>@{
                        return new JObject(
                            new JProperty("error", "X-Pa-Api-Key header is required")
                        ).ToString();
                    }</set-body>
                </return-response>
            </when>
        </choose>
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>"""

    return policy_xml


def import_api_to_apim(
    resource_group: str,
    apim_name: str,
    openapi_spec_path: Path,
    api_id: str = "phoneappli-api",
    api_path: str = "phoneappli",
    environment: str = "sandbox",
) -> bool:
    """
    Import OpenAPI specification to Azure API Management.

    Args:
        resource_group: Azure resource group name
        apim_name: API Management service name
        openapi_spec_path: Path to OpenAPI spec file
        api_id: API identifier in APIM (default: phoneappli-api)
        api_path: API path in gateway URL (default: phoneappli)
        environment: Target environment - 'sandbox' or 'production' (default: sandbox)

    Returns:
        True if import succeeds, False otherwise
    """
    try:
        # Map environment to backend URL
        environment_urls = {
            "sandbox": "https://api-sandbox.phoneappli.net/v1",
            "production": "https://api.phoneappli.net/v1",
        }

        if environment not in environment_urls:
            console.print(f"[red]Error:[/red] Invalid environment '{environment}'. Must be 'sandbox' or 'production'")
            return False

        service_url = environment_urls[environment]

        # Get Azure subscription ID
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Authenticating to Azure...", total=None)

            credential = DefaultAzureCredential()

            # Get subscription ID from Azure CLI context
            from azure.mgmt.resource import SubscriptionClient

            subscription_client = SubscriptionClient(credential)
            subscriptions = list(subscription_client.subscriptions.list())

            if not subscriptions:
                console.print("[red]Error:[/red] No Azure subscriptions found")
                return False

            subscription_id = subscriptions[0].subscription_id
            console.print(f"[green]✓[/green] Authenticated to subscription: {subscription_id}\n")

        # Load OpenAPI spec
        console.print(f"[cyan]Loading OpenAPI spec from:[/cyan] {openapi_spec_path}")
        openapi_content = load_openapi_spec(openapi_spec_path)
        api_info = get_api_info_from_spec(openapi_spec_path)
        console.print(f"[green]✓[/green] Loaded API: {api_info['title']} (v{api_info['version']})\n")

        # Create API Management client
        apim_client = ApiManagementClient(credential, subscription_id)

        # Prepare API parameters
        api_params = ApiCreateOrUpdateParameter(
            display_name=api_info["title"],
            description=api_info["description"],
            service_url=service_url,
            path=api_path,
            protocols=[Protocol.HTTPS],
            api_type=ApiType.HTTP,
            format=ContentFormat.OPENAPI_LINK if openapi_spec_path.suffix == ".json" else ContentFormat.OPENAPI,
            value=openapi_content,
            subscription_required=True,
        )

        # Import API
        console.print(f"[cyan]Importing API to API Management:[/cyan] {apim_name}")
        console.print(f"  Resource Group: {resource_group}")
        console.print(f"  API ID: {api_id}")
        console.print(f"  API Path: /{api_path}")
        console.print(f"  Environment: {environment}")
        console.print(f"  Backend URL: {service_url}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="Importing API...", total=None)

            result = apim_client.api.begin_create_or_update(
                resource_group_name=resource_group,
                service_name=apim_name,
                api_id=api_id,
                parameters=api_params,
            ).result()

            progress.update(task, completed=True)

        # Set API-level policy to validate X-Pa-Api-Key header
        console.print("\n[cyan]Configuring API policy to validate X-Pa-Api-Key header...[/cyan]")
        policy_xml = generate_api_policy()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="Setting API policy...", total=None)

            policy_contract = PolicyContract(
                value=policy_xml,
                format="xml",
            )

            apim_client.api_policy.create_or_update(
                resource_group_name=resource_group,
                service_name=apim_name,
                api_id=api_id,
                policy_id="policy",
                parameters=policy_contract,
            )

            progress.update(task, completed=True)

        console.print(
            Panel(
                f"[bold green]✓ API imported successfully![/bold green]\n\n"
                f"[cyan]API Details:[/cyan]\n"
                f"  Name: {result.display_name}\n"
                f"  Version: {api_info['version']}\n"
                f"  Path: /{result.path}\n"
                f"  API ID: {result.name}\n"
                f"  Environment: {environment}\n\n"
                f"[cyan]Backend URL:[/cyan]\n"
                f"  {service_url}\n\n"
                f"[cyan]Gateway URL:[/cyan]\n"
                f"  https://{apim_name}.azure-api.net/{result.path}",
                title="Import Result",
                border_style="green",
            )
        )

        return True

    except Exception as e:
        console.print(
            Panel(
                f"[bold red]✗ API import failed![/bold red]\n\n[red]Error:[/red] {str(e)}",
                title="Import Result",
                border_style="red",
            )
        )
        return False


def main() -> int:
    """
    Main function to import API to Azure API Management.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    console.print(Panel("[bold cyan]Azure API Management - API Import[/bold cyan]", expand=False))
    console.print()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Import OpenAPI specification to Azure API Management")
    parser.add_argument("--resource-group", "-g", required=True, help="Azure resource group name")
    parser.add_argument("--apim-name", "-n", required=True, help="API Management service name")
    parser.add_argument("--openapi-spec", "-s", required=True, help="Path to OpenAPI specification file")
    parser.add_argument("--api-id", default="phoneappli-api", help="API identifier (default: phoneappli-api)")
    parser.add_argument("--api-path", default="phoneappli", help="API path (default: phoneappli)")
    parser.add_argument(
        "--environment",
        "-e",
        choices=["sandbox", "production"],
        default="sandbox",
        help="Target environment: 'sandbox' or 'production' (default: sandbox)",
    )

    args = parser.parse_args()

    # Convert to Path object
    openapi_spec_path = Path(args.openapi_spec)

    # Validate file exists
    if not openapi_spec_path.exists():
        console.print(f"[red]Error:[/red] OpenAPI spec file not found: {openapi_spec_path}")
        return 1

    # Import API
    if import_api_to_apim(
        resource_group=args.resource_group,
        apim_name=args.apim_name,
        openapi_spec_path=openapi_spec_path,
        api_id=args.api_id,
        api_path=args.api_path,
        environment=args.environment,
    ):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
