#!/usr/bin/env python3
"""Simplified TUI test script with better error handling."""

import asyncio
import sys

try:
    from pysetitup.config.loader import load_config
    from pysetitup.ui.selector import PackageSelector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you've installed the package:")
    print("  uv pip install -e .")
    sys.exit(1)


async def main():
    """Run the package selector TUI."""
    print("🔄 Loading configuration...")

    try:
        # Load config
        config = load_config()
        print(f"✅ Loaded {len(config.packages)} packages from {len(config.presets)} presets")

        # Get minimal preset as starting point
        preset = config.get_preset("minimal")
        if preset:
            initial_selection = set(preset.packages)
            print(f"✅ Starting with {len(initial_selection)} packages from 'minimal' preset")
        else:
            initial_selection = set()
            print("⚠️  No preset found, starting with empty selection")

        print("\n" + "="*60)
        print("Starting TUI...")
        print("Use: Space=toggle, Tab=category, /=search, Enter=confirm")
        print("="*60 + "\n")

        # Create and run the TUI app
        app = PackageSelector(config=config, preset_packages=initial_selection)
        selected = await app.run_async()

        # Show results
        if selected:
            print(f"\n✅ Selected {len(selected)} packages:")
            for pkg in sorted(selected):
                print(f"  - {pkg}")
        else:
            print("\n⚠️  No packages selected")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
