#!/usr/bin/env python3
"""Test script to verify Playwright installation and basic functionality."""

import sys
import asyncio

def check_playwright_installed():
    """Check if Playwright is installed."""
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright Python package is installed")
        return True
    except ImportError:
        print("✗ Playwright is not installed")
        print("\nInstall with:")
        print("  pip install playwright")
        return False


async def check_browser_installed():
    """Check if Chromium browser is installed."""
    try:
        from playwright.async_api import async_playwright

        print("\nTesting browser launch...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.example.com")
            title = await page.title()
            await browser.close()

            print(f"✓ Browser launched successfully")
            print(f"✓ Navigated to example.com (title: '{title}')")
            return True

    except Exception as e:
        print(f"✗ Browser test failed: {e}")
        print("\nInstall Chromium with:")
        print("  playwright install chromium")
        return False


async def main():
    """Run all installation tests."""
    print("=" * 80)
    print("Duke Citrix Gateway Client - Installation Test")
    print("=" * 80)
    print()

    # Check Python version
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print("✓ Python version is compatible")

    print()

    # Check Playwright package
    if not check_playwright_installed():
        return False

    # Check browser
    if not await check_browser_installed():
        return False

    print()
    print("=" * 80)
    print("✓ All tests passed! You're ready to use the Citrix Gateway client.")
    print("=" * 80)
    print("\nRun the client with:")
    print("  python3 api_client.py")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
