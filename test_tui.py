#!/usr/bin/env python3
"""Quick test script for the package selector TUI."""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from pysetitup.brew.client import BrewClient
from pysetitup.config.loader import load_config
from pysetitup.npm.client import NpmClient
from pysetitup.ui.confirmation import show_confirmation
from pysetitup.ui.preset_selector import select_preset
from pysetitup.ui.selector import PackageSelector
from pysetitup.ui.terminal_check import check_and_enforce_terminal_size
from pysetitup.vscode.client import VSCodeClient


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


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="PySetItUp Package Installer - Preview Mode (no actual installation)"
    )
    parser.add_argument(
        "-f", "--preset-file",
        type=Path,
        metavar="FILE",
        help="Path to custom preset YAML file (skips preset selection screen)"
    )
    return parser.parse_args()


async def main():
    """Main entry point for the TUI."""
    # Parse arguments
    args = parse_args()

    # Check terminal size (plain text output, no Rich formatting)
    check_and_enforce_terminal_size(use_rich=False)

    # Load config with optional external preset file
    if args.preset_file:
        print(f"📄 Loading custom preset from: {args.preset_file}\n")
        try:
            config = load_config(external_presets_file=args.preset_file)
        except Exception as e:
            print(f"❌ Failed to load preset file: {e}")
            sys.exit(1)
    else:
        config = load_config()

    # Handle different workflows based on whether custom preset file is provided
    if args.preset_file:
        # Custom preset file provided - skip preset selection screen
        custom_presets = [name for name in config.presets.keys()
                         if name not in ["minimal", "developer", "full"]]

        if not custom_presets:
            print("❌ No custom presets found in the provided file.")
            sys.exit(1)

        # Use the first custom preset
        preset_name = custom_presets[0]
        preset = config.get_preset(preset_name)

        if not preset:
            print(f"❌ Error: Preset '{preset_name}' not found.")
            sys.exit(1)

        print(f"📦 Using custom preset: '{preset_name}'")
        print(f"{preset.description}\n")

        # Load preset packages for customization
        initial_selection = set(
            preset.packages +
            preset.casks +
            preset.npm +
            preset.vscode
        )

        print(f"Starting with {len(initial_selection)} packages from custom preset")
        print("Loading package selector...\n")

        # Go directly to package selector with custom preset
        app = PackageSelector(config=config, preset_packages=initial_selection)
        selected = await app.run_async()

        if not selected:
            print("\n❌ No packages selected. Exiting.")
            sys.exit(0)

        print(f"\n✅ Selected {len(selected)} packages")
        installed_packages = app.installed_packages
        action = "customize"
    else:
        # Normal workflow - show preset selection screen
        # Step 1: Preset selection
        print("Loading preset selector...\n")
        preset_result = await select_preset(config)

        if preset_result is None:
            print("\n❌ User quit. Exiting.")
            sys.exit(0)

        action = preset_result.get("action")
        preset_name = preset_result.get("preset")

        # Handle different actions
        installed_packages = {}

        if action == "install":
            # Install preset directly without customization
            print(f"\n📦 Installing '{preset_name}' preset directly...")
            preset = config.get_preset(preset_name)
            if not preset:
                print(f"❌ Error: Preset '{preset_name}' not found.")
                sys.exit(1)

            # Get all packages from preset
            selected = (
                preset.packages +
                preset.casks +
                preset.npm +
                preset.vscode
            )
            print(f"✅ Selected {len(selected)} packages from '{preset_name}' preset")

            # Don't check packages here - let confirmation screen do it
            installed_packages = {}

        elif action == "customize":
            # Load preset and allow customization
            print(f"\n✏ Customizing '{preset_name}' preset...")
            preset = config.get_preset(preset_name)
            if not preset:
                print(f"❌ Error: Preset '{preset_name}' not found.")
                sys.exit(1)

            initial_selection = set(
                preset.packages +
                preset.casks +
                preset.npm +
                preset.vscode
            )

            print(f"Starting with {len(initial_selection)} packages from '{preset_name}' preset")
            print("Loading package selector...\n")

            # Step 1a: Package selection with preset pre-selected
            app = PackageSelector(config=config, preset_packages=initial_selection)
            selected = await app.run_async()

            if not selected:
                print("\n❌ No packages selected. Exiting.")
                sys.exit(0)

            print(f"\n✅ Selected {len(selected)} packages")
            installed_packages = app.installed_packages

        elif action == "skip":
            # Skip preset selection and go to package selector
            print("\n→ Skipping preset selection...")
            print("Loading package selector...\n")

            # Step 1b: Package selection with no preset
            app = PackageSelector(config=config, preset_packages=set())
            selected = await app.run_async()

            if not selected:
                print("\n❌ No packages selected. Exiting.")
                sys.exit(0)

            print(f"\n✅ Selected {len(selected)} packages")
            installed_packages = app.installed_packages

        else:
            print(f"\n❌ Unknown action: {action}")
            sys.exit(1)

    # Step 2: Show confirmation screen
    print("Loading confirmation screen...\n")

    # Always pass the function to check installed packages dynamically
    # This ensures the confirmation screen shows the most up-to-date information
    confirmed = await show_confirmation(
        selected,
        get_installed_packages_func=get_installed_packages
    )

    if not confirmed:
        print("\n❌ Installation cancelled by user.")
        sys.exit(0)

    # Step 3: Installation (simulated for now)
    print("\n🚀 Installation confirmed! Packages to install:")
    for pkg in sorted(selected):
        if pkg in installed_packages:
            version = installed_packages.get(pkg)
            version_str = f" ({version})" if version else ""
            print(f"  ✓ {pkg}{version_str} [already installed]")
        else:
            print(f"  • {pkg} [will be installed]")

    print("\n✅ Installation process would start here!")


if __name__ == "__main__":
    asyncio.run(main())
