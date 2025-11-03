"""CLI for managing slurm-factory infrastructure."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="infra",
    help="Manage slurm-factory infrastructure using AWS CDK",
    no_args_is_help=True,
)
console = Console()


def run_cdk_command(command: list[str], cwd: Path | None = None) -> int:
    """
    Run a CDK command.

    Args:
        command: CDK command to run
        cwd: Working directory for the command

    Returns:
        Exit code
    """
    if cwd is None:
        cwd = Path(__file__).parent.parent

    # Ensure CDK is available
    try:
        subprocess.run(
            ["cdk", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]AWS CDK CLI not found. Install it with:[/red]")
        console.print("  npm install -g aws-cdk")
        return 1

    console.print(f"[dim]Running: {' '.join(command)}[/dim]")
    result = subprocess.run(command, cwd=cwd)
    return result.returncode


@app.command()
def bootstrap(
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile to use"),
    ] = None,
    region: Annotated[
        str | None,
        typer.Option("--region", help="AWS region"),
    ] = None,
) -> None:
    """
    Bootstrap AWS CDK in your AWS account.

    This creates the necessary CDK resources (S3 bucket, ECR repo, etc.)
    in your AWS account. Only needs to be run once per account/region.
    """
    console.print("[bold blue]Bootstrapping AWS CDK...[/bold blue]")

    cmd = ["cdk", "bootstrap"]
    
    if profile:
        cmd.extend(["--profile", profile])
    
    if region:
        cmd.extend(["--region", region])

    exit_code = run_cdk_command(cmd)
    
    if exit_code == 0:
        console.print("[bold green]✓ CDK bootstrapped successfully[/bold green]")
    else:
        console.print("[bold red]✗ CDK bootstrap failed[/bold red]")
        sys.exit(exit_code)


@app.command()
def synth(
    github_org: Annotated[
        str,
        typer.Option("--github-org", help="GitHub organization name"),
    ] = "vantagecompute",
    github_repo: Annotated[
        str,
        typer.Option("--github-repo", help="GitHub repository name"),
    ] = "slurm-factory",
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Custom domain name (e.g., cache.slurm-factory.com)"),
    ] = None,
    hosted_zone_id: Annotated[
        str | None,
        typer.Option("--hosted-zone-id", help="Route53 hosted zone ID"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory for CloudFormation templates"),
    ] = None,
) -> None:
    """
    Synthesize CloudFormation templates from CDK code.

    This generates the CloudFormation templates without deploying them.
    """
    console.print("[bold blue]Synthesizing CDK stack...[/bold blue]")

    # Set context variables
    env_vars = os.environ.copy()
    env_vars["CDK_GITHUB_ORG"] = github_org
    env_vars["CDK_GITHUB_REPO"] = github_repo
    
    if domain:
        env_vars["CDK_DOMAIN_NAME"] = domain
    if hosted_zone_id:
        env_vars["CDK_HOSTED_ZONE_ID"] = hosted_zone_id

    cmd = ["cdk", "synth"]
    
    if output:
        cmd.extend(["--output", str(output)])

    cwd = Path(__file__).parent.parent
    result = subprocess.run(cmd, cwd=cwd, env=env_vars)
    
    if result.returncode == 0:
        console.print("[bold green]✓ Templates synthesized successfully[/bold green]")
        if output:
            console.print(f"[dim]Output: {output}[/dim]")
    else:
        console.print("[bold red]✗ Synthesis failed[/bold red]")
        sys.exit(result.returncode)


@app.command()
def deploy(
    github_org: Annotated[
        str,
        typer.Option("--github-org", help="GitHub organization name"),
    ] = "vantagecompute",
    github_repo: Annotated[
        str,
        typer.Option("--github-repo", help="GitHub repository name"),
    ] = "slurm-factory",
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Custom domain name (e.g., cache.slurm-factory.com)"),
    ] = None,
    hosted_zone_id: Annotated[
        str | None,
        typer.Option("--hosted-zone-id", help="Route53 hosted zone ID"),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile to use"),
    ] = None,
    region: Annotated[
        str | None,
        typer.Option("--region", help="AWS region"),
    ] = None,
    require_approval: Annotated[
        bool,
        typer.Option("--require-approval/--no-approval", help="Require approval for changes"),
    ] = True,
) -> None:
    """
    Deploy the infrastructure stack to AWS.

    This creates or updates all resources defined in the CDK stack.
    """
    console.print("[bold blue]Deploying infrastructure...[/bold blue]")

    # Set context variables
    env_vars = os.environ.copy()
    env_vars["CDK_GITHUB_ORG"] = github_org
    env_vars["CDK_GITHUB_REPO"] = github_repo
    
    if domain:
        env_vars["CDK_DOMAIN_NAME"] = domain
    if hosted_zone_id:
        env_vars["CDK_HOSTED_ZONE_ID"] = hosted_zone_id

    cmd = ["cdk", "deploy"]
    
    if not require_approval:
        cmd.append("--require-approval=never")
    
    if profile:
        cmd.extend(["--profile", profile])
    
    if region:
        cmd.extend(["--region", region])

    cwd = Path(__file__).parent.parent
    result = subprocess.run(cmd, cwd=cwd, env=env_vars)
    
    if result.returncode == 0:
        console.print("[bold green]✓ Infrastructure deployed successfully[/bold green]")
    else:
        console.print("[bold red]✗ Deployment failed[/bold red]")
        sys.exit(result.returncode)


@app.command()
def destroy(
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile to use"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """
    Destroy the infrastructure stack.

    WARNING: This will delete all resources, but the S3 bucket will be retained.
    """
    if not force:
        confirm = typer.confirm(
            "Are you sure you want to destroy the infrastructure?",
            abort=True,
        )
        if not confirm:
            return

    console.print("[bold yellow]Destroying infrastructure...[/bold yellow]")

    cmd = ["cdk", "destroy", "--force"]
    
    if profile:
        cmd.extend(["--profile", profile])

    exit_code = run_cdk_command(cmd)
    
    if exit_code == 0:
        console.print("[bold green]✓ Infrastructure destroyed[/bold green]")
        console.print("[yellow]Note: S3 bucket was retained and must be deleted manually[/yellow]")
    else:
        console.print("[bold red]✗ Destruction failed[/bold red]")
        sys.exit(exit_code)


@app.command()
def diff(
    github_org: Annotated[
        str,
        typer.Option("--github-org", help="GitHub organization name"),
    ] = "vantagecompute",
    github_repo: Annotated[
        str,
        typer.Option("--github-repo", help="GitHub repository name"),
    ] = "slurm-factory",
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Custom domain name"),
    ] = None,
    hosted_zone_id: Annotated[
        str | None,
        typer.Option("--hosted-zone-id", help="Route53 hosted zone ID"),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile to use"),
    ] = None,
) -> None:
    """
    Show differences between deployed stack and current code.
    """
    console.print("[bold blue]Calculating diff...[/bold blue]")

    # Set context variables
    env_vars = os.environ.copy()
    env_vars["CDK_GITHUB_ORG"] = github_org
    env_vars["CDK_GITHUB_REPO"] = github_repo
    
    if domain:
        env_vars["CDK_DOMAIN_NAME"] = domain
    if hosted_zone_id:
        env_vars["CDK_HOSTED_ZONE_ID"] = hosted_zone_id

    cmd = ["cdk", "diff"]
    
    if profile:
        cmd.extend(["--profile", profile])

    cwd = Path(__file__).parent.parent
    subprocess.run(cmd, cwd=cwd, env=env_vars)


@app.command()
def outputs(
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile to use"),
    ] = None,
) -> None:
    """
    Display stack outputs (bucket name, distribution URL, etc.).
    """
    console.print("[bold blue]Fetching stack outputs...[/bold blue]")

    cmd = [
        "aws", "cloudformation", "describe-stacks",
        "--stack-name", "SlurmFactoryInfraStack",
        "--query", "Stacks[0].Outputs",
    ]
    
    if profile:
        cmd.extend(["--profile", profile])

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        console.print("[red]Failed to fetch outputs. Is the stack deployed?[/red]")
        sys.exit(1)

    # Parse and display outputs
    import json
    outputs = json.loads(result.stdout)
    
    table = Table(title="Stack Outputs")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")
    
    for output in outputs:
        table.add_row(
            output.get("OutputKey", ""),
            output.get("OutputValue", ""),
            output.get("Description", ""),
        )
    
    console.print(table)


if __name__ == "__main__":
    app()
