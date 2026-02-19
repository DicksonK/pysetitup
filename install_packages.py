#!/usr/bin/env python3
"""Complete installation script with actual package installation."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Awaitable, Callable, Optional, TypeVar

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pysetitup.brew.client import BrewClient
from pysetitup.brew.installer import BrewInstaller
from pysetitup.config.loader import load_config
from pysetitup.installer.models import BrewInstallResult, NpmInstallResult, VSCodeInstallResult
from pysetitup.npm.client import NpmClient
from pysetitup.npm.installer import NpmInstaller
from pysetitup.ui.checks import run_system_checks
from pysetitup.ui.confirmation import show_confirmation
from pysetitup.ui.preset_selector import select_preset
from pysetitup.ui.selector import PackageSelector
from pysetitup.ui.terminal_check import check_and_enforce_terminal_size
from pysetitup.utils.sorting import format_package_summary, sort_packages
from pysetitup.vscode.client import VSCodeClient
from pysetitup.vscode.installer import VSCodeInstaller

# Type variable for install results
InstallResultT = TypeVar(
    "InstallResultT", BrewInstallResult, NpmInstallResult, VSCodeInstallResult
)


async def get_installed_packages() -> dict[str, Optional[str]]:
    """
    Check which packages are already installed.

    Returns
    -------
    dict[str, Optional[str]]
        Dictionary mapping package names to their installed versions
    """
    installed_packages: dict[str, Optional[str]] = {}

    try:
        brew_client = BrewClient()
        npm_client = NpmClient()
        vscode_client = VSCodeClient()

        # Run all checks in parallel for better performance
        tasks = []

        async def check_brew_formulae():
            try:
                return await brew_client.list_formulae_versions()
            except Exception:
                return {}

        async def check_brew_casks():
            try:
                return await brew_client.list_casks_versions()
            except Exception:
                return {}

        async def check_npm():
            try:
                return await npm_client.list_global_versions()
            except Exception:
                return {}

        async def check_vscode():
            try:
                return await vscode_client.list_extensions_with_versions()
            except Exception:
                return {}

        # Gather all results in parallel
        results = await asyncio.gather(
            check_brew_formulae(),
            check_brew_casks(),
            check_npm(),
            check_vscode(),
            return_exceptions=True
        )

        # Combine all results
        for result in results:
            if isinstance(result, dict):
                installed_packages.update(result)

    except Exception:
        pass  # Return empty dict if we can't check

    return installed_packages


async def install_with_progress(
    install_func: Callable[..., Awaitable[list[InstallResultT]]],
    package_type: str,
    console: Console,
    *args,
    **kwargs,
) -> list[InstallResultT]:
    """
    Install packages with progress display and result summary.

    Parameters
    ----------
    install_func : Callable
        Async function that performs the installation
    package_type : str
        Type of package being installed (e.g., "packages", "extensions")
    console : Console
        Rich console for output
    *args : Any
        Positional arguments to pass to install_func
    **kwargs : Any
        Keyword arguments to pass to install_func (on_progress will be injected)

    Returns
    -------
    list[InstallResultT]
        List of installation results
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing...", total=None)

        # Create progress callback
        def on_progress(message: str, status: str = ""):
            if status:
                progress.update(task, description=f"{message}: {status}")
            else:
                progress.update(task, description=message)

        # Execute installation with progress callback
        kwargs["on_progress"] = on_progress
        results = await install_func(*args, **kwargs)

        # Sort results alphabetically by package name
        sorted_results = sorted(results, key=lambda r: r.package.lower())

        # Show results summary
        success_count = sum(1 for r in sorted_results if r.success)
        fail_count = len(sorted_results) - success_count

        console.print(
            f"\n  [green]✓ {success_count} {package_type} installed successfully[/green]"
        )
        if fail_count > 0:
            console.print(f"  [red]✗ {fail_count} {package_type} failed[/red]")

            # Show failed packages (sorted)
            for result in sorted_results:
                if not result.success:
                    error_msg = getattr(result, "message", getattr(result, "error", "Unknown error"))
                    console.print(f"    [red]• {result.package}: {error_msg}[/red]")

        return sorted_results


def debug_pause(console: Console, message: str = "Press ENTER to continue..."):
    """Pause execution in debug mode and wait for user input."""
    console.print(f"\n[dim]{message}[/dim]")
    input()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="PySetItUp Package Installer - Set up your macOS dev environment"
    )
    parser.add_argument(
        "-f", "--preset-file",
        type=Path,
        metavar="FILE",
        help="Path to custom preset YAML file (skips preset selection screen)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with pauses between screens"
    )
    return parser.parse_args()


async def main():
    """Main installation workflow."""
    console = Console()

    # Parse arguments
    args = parse_args()

    # Check terminal size (uses Rich formatting)
    check_and_enforce_terminal_size(console=console, use_rich=True)

    # Load config
    console.print("\n[bold cyan]PySetItUp Package Installer[/bold cyan]\n")
    if args.debug:
        console.print("[yellow]🐛 Debug mode enabled - will pause between screens[/yellow]\n")

    # Load config with optional external preset file
    if args.preset_file:
        console.print(f"[cyan]📄 Loading custom preset from: {args.preset_file}[/cyan]\n")
        try:
            config = load_config(external_presets_file=args.preset_file)
        except Exception as e:
            console.print(f"[red]❌ Failed to load preset file: {e}[/red]")
            sys.exit(1)
    else:
        config = load_config()

    if args.debug:
        debug_pause(console, "🐛 Config loaded. Press ENTER to continue...")

    # Handle different workflows based on whether custom preset file is provided
    if args.preset_file:
        # Custom preset file provided - skip preset selection screen
        # Get the first preset from the loaded config (assumes custom file has one preset)
        custom_presets = [name for name in config.presets.keys()
                         if name not in ["minimal", "developer", "full"]]

        if not custom_presets:
            console.print("[red]❌ No custom presets found in the provided file.[/red]")
            sys.exit(1)

        # Use the first custom preset
        preset_name = custom_presets[0]
        preset = config.get_preset(preset_name)

        if not preset:
            console.print(f"[red]❌ Error: Preset '{preset_name}' not found.[/red]")
            sys.exit(1)

        console.print(f"[bold]📦 Using custom preset: '{preset_name}'[/bold]")
        console.print(f"[dim]{preset.description}[/dim]\n")

        # Load preset packages for customization
        initial_selection = set(
            preset.packages +
            preset.casks +
            preset.npm +
            preset.vscode
        )

        console.print(f"Starting with {len(initial_selection)} packages from custom preset")
        console.print("[dim]Loading package selector...[/dim]\n")

        # Go directly to package selector with custom preset
        app = PackageSelector(config=config, preset_packages=initial_selection)
        selected = await app.run_async()

        if not selected:
            console.print("\n[red]❌ No packages selected. Exiting.[/red]")
            sys.exit(0)

        console.print(f"\n[green]✅ Selected {len(selected)} packages[/green]")
        installed_packages = app.installed_packages
        action = "customize"  # Mark as customize workflow
    else:
        # Normal workflow - show preset selection screen
        # Step 1: Preset selection
        console.print("[dim]Loading preset selector...[/dim]\n")
        preset_result = await select_preset(config)

        if preset_result is None:
            console.print("\n[red]❌ User quit. Exiting.[/red]")
            sys.exit(0)

        action = preset_result.get("action")
        preset_name = preset_result.get("preset")

        if args.debug:
            console.print(f"[dim]Selected action: {action}, preset: {preset_name}[/dim]")
            debug_pause(console, "🐛 Preset selected. Press ENTER to continue...")

        # Handle different actions
        installed_packages = {}

        if action == "install":
            # Install preset directly without customization
            console.print(f"\n[bold]📦 Installing '{preset_name}' preset directly...[/bold]")
            preset = config.get_preset(preset_name)
            if not preset:
                console.print(f"[red]❌ Error: Preset '{preset_name}' not found.[/red]")
                sys.exit(1)

            # Get all packages from preset
            selected = (
                preset.packages +
                preset.casks +
                preset.npm +
                preset.vscode
            )
            console.print(f"[green]✅ Selected {len(selected)} packages from '{preset_name}' preset[/green]")

            # Don't check packages here - let confirmation screen do it
            installed_packages = {}

        elif action == "customize":
            # Load preset and allow customization
            console.print(f"\n[bold]✏ Customizing '{preset_name}' preset...[/bold]")
            preset = config.get_preset(preset_name)
            if not preset:
                console.print(f"[red]❌ Error: Preset '{preset_name}' not found.[/red]")
                sys.exit(1)

            initial_selection = set(
                preset.packages +
                preset.casks +
                preset.npm +
                preset.vscode
            )

            console.print(f"Starting with {len(initial_selection)} packages from '{preset_name}' preset")
            console.print("[dim]Loading package selector...[/dim]\n")

            # Step 1a: Package selection with preset pre-selected
            app = PackageSelector(config=config, preset_packages=initial_selection)
            selected = await app.run_async()

            if not selected:
                console.print("\n[red]❌ No packages selected. Exiting.[/red]")
                sys.exit(0)

            console.print(f"\n[green]✅ Selected {len(selected)} packages[/green]")
            installed_packages = app.installed_packages

        elif action == "skip":
            # Skip preset selection and go to package selector
            console.print("\n[bold]→ Skipping preset selection...[/bold]")
            console.print("[dim]Loading package selector...[/dim]\n")

            # Step 1b: Package selection with no preset
            app = PackageSelector(config=config, preset_packages=set())
            selected = await app.run_async()

            if not selected:
                console.print("\n[red]❌ No packages selected. Exiting.[/red]")
                sys.exit(0)

            console.print(f"\n[green]✅ Selected {len(selected)} packages[/green]")
            installed_packages = app.installed_packages

        else:
            console.print(f"\n[red]❌ Unknown action: {action}[/red]")
            sys.exit(1)

    # Separate selected packages by type
    selected_packages = []
    selected_casks = []
    selected_npm = []
    selected_vscode = []

    for pkg_name in selected:
        pkg = config.get_package(pkg_name)
        if pkg:
            if pkg.type == "formula":
                selected_packages.append(pkg_name)
            elif pkg.type == "cask":
                selected_casks.append(pkg_name)
            elif pkg.type == "npm":
                selected_npm.append(pkg_name)
            elif pkg.type == "vscode":
                selected_vscode.append(pkg_name)
        else:
            # Check if it's in preset vscode list (fallback)
            if action in ("install", "customize") and preset_name:
                preset = config.get_preset(preset_name)
                if preset and pkg_name in preset.vscode:
                    selected_vscode.append(pkg_name)

    # Sort packages
    sorted_pkgs = sort_packages(
        packages=selected_packages,
        taps=[],  # No taps in selection for now
        casks=selected_casks,
        npm=selected_npm,
        vscode=selected_vscode,
    )

    # Step 2: Run system checks
    console.print("\n[bold yellow]Running system checks...[/bold yellow]\n")
    checks_passed = run_system_checks(
        vscode_extensions=sorted_pkgs.vscode,
        npm_packages=sorted_pkgs.npm,
        console=console,
    )

    if not checks_passed:
        console.print("\n[red]❌ Required system checks failed. Please fix the issues above.[/red]")
        sys.exit(1)

    if args.debug:
        debug_pause(console, "🐛 System checks complete. Press ENTER to continue to summary...")

    # Step 3: Show summary
    console.print("\n[bold cyan]Installation Summary:[/bold cyan]\n")
    console.print(format_package_summary(sorted_pkgs))

    if args.debug:
        debug_pause(console, "🐛 Summary shown. Press ENTER to continue to confirmation screen...")

    # Step 4: Show confirmation screen
    console.print("\n[dim]Loading confirmation screen...[/dim]\n")

    if args.debug:
        console.print(f"[dim]Selected packages ({len(selected)}): {sorted(selected)[:5]}...[/dim]")

    # Always pass the function to check installed packages dynamically
    # This ensures the confirmation screen shows the most up-to-date information
    confirmed = await show_confirmation(
        selected,
        get_installed_packages_func=get_installed_packages
    )

    if not confirmed:
        console.print("\n[red]❌ Installation cancelled by user.[/red]")
        sys.exit(0)

    # Step 5: Actual installation
    console.print("\n[bold green]🚀 Starting installation...[/bold green]\n")

    # Install Homebrew packages
    if sorted_pkgs.packages or sorted_pkgs.casks:
        console.print("[bold]Installing Homebrew packages...[/bold]")
        brew_installer = BrewInstaller()
        await install_with_progress(
            brew_installer.install_packages,
            "packages",
            console,
            formulae=sorted_pkgs.packages,
            casks=sorted_pkgs.casks,
        )

    # Install npm packages
    if sorted_pkgs.npm:
        console.print("\n[bold]Installing npm packages...[/bold]")
        npm_installer = NpmInstaller()
        await install_with_progress(
            npm_installer.install_packages,
            "packages",
            console,
            packages=sorted_pkgs.npm,
        )

    # Install VS Code extensions
    if sorted_pkgs.vscode:
        console.print("\n[bold]Installing VS Code extensions...[/bold]")
        vscode_installer = VSCodeInstaller()
        await install_with_progress(
            vscode_installer.install_extensions,
            "extensions",
            console,
            extension_ids=sorted_pkgs.vscode,
        )

    # Done!
    console.print("\n[bold green]✅ Installation complete![/bold green]\n")


if __name__ == "__main__":
    asyncio.run(main())
