#!/usr/bin/env python3
"""Quick test script for the preset selector TUI."""

import asyncio

from pysetitup.ui.preset_selector import select_preset


async def main():
    """Test the preset selector."""
    print("Testing preset selector...\n")

    result = await select_preset()

    if result is None:
        print("\n❌ User quit")
    else:
        action = result.get("action")
        preset = result.get("preset")

        if action == "install":
            print(f"\n✅ User selected: Install '{preset}' preset directly")
        elif action == "customize":
            print(f"\n✅ User selected: Customize '{preset}' preset")
        elif action == "skip":
            print("\n✅ User selected: Skip preset selection")
        else:
            print(f"\n⚠️  Unknown action: {action}")


if __name__ == "__main__":
    asyncio.run(main())
