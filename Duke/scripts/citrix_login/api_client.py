#!/usr/bin/env python3
"""
Citrix Gateway (Duke University) Authentication Client

This script automates the login process to secure.citrix.duke.edu using
Duke's Shibboleth SAML-based single sign-on system.

The authentication flow involves:
1. Initial Citrix Gateway access
2. SAML redirect to Duke's Shibboleth IdP (shib.oit.duke.edu)
3. NetID credential submission
4. Multi-factor authentication (Duo MFA)
5. SAML response POST back to Citrix
6. Session establishment with authenticated cookies

Due to the complex SAML flow and MFA requirements, this implementation uses
Playwright with Chrome DevTools Protocol (CDP) to maintain the real browser
context and handle all authentication steps.
"""

import asyncio
import getpass
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: Playwright is not installed.")
    print("Install it with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CitrixGatewayClient:
    """Client for authenticating to Duke's Citrix Gateway."""

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60000,
        session_file: Optional[str] = None
    ):
        """
        Initialize the Citrix Gateway client.

        Args:
            headless: Whether to run browser in headless mode (default: False for MFA)
            timeout: Page operation timeout in milliseconds (default: 60000)
            session_file: Path to save/load session cookies (default: None)
        """
        self.base_url = "https://secure.citrix.duke.edu"
        self.headless = headless
        self.timeout = timeout
        self.session_file = session_file or ".citrix_session.json"
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies: Dict[str, Any] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize_browser(self) -> None:
        """Initialize the Playwright browser instance."""
        logger.info("Initializing browser...")
        self.playwright = await async_playwright().start()

        # Launch browser with realistic user agent
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create context with realistic browser fingerprint
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
        )

        # Create a new page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        logger.info("Browser initialized successfully")

    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        logger.info("Closing browser...")
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")

    async def save_session(self) -> None:
        """Save current session cookies to file."""
        if not self.context:
            logger.warning("No context available to save session")
            return

        cookies = await self.context.cookies()
        session_data = {
            'cookies': cookies,
            'url': self.base_url
        }

        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session saved to {self.session_file}")

    async def load_session(self) -> bool:
        """
        Load session cookies from file.

        Returns:
            True if session loaded successfully, False otherwise
        """
        if not os.path.exists(self.session_file):
            logger.info("No saved session found")
            return False

        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)

            await self.context.add_cookies(session_data['cookies'])
            logger.info(f"Session loaded from {self.session_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    async def wait_for_mfa(self, timeout: int = 120) -> bool:
        """
        Wait for user to complete MFA authentication.

        Args:
            timeout: Maximum time to wait for MFA in seconds (default: 120)

        Returns:
            True if MFA completed successfully, False otherwise
        """
        logger.info("=" * 80)
        logger.info("MULTI-FACTOR AUTHENTICATION REQUIRED")
        logger.info("=" * 80)
        logger.info("Please approve the Duo push notification on your device")
        logger.info("or enter your Duo passcode in the browser window.")
        logger.info(f"Waiting up to {timeout} seconds for MFA completion...")
        logger.info("=" * 80)

        try:
            # Wait for redirect back to Citrix after successful auth
            # The successful MFA will redirect to Citrix with SAML response
            await self.page.wait_for_url(
                lambda url: 'secure.citrix.duke.edu' in url and 'samlauth' in url,
                timeout=timeout * 1000
            )
            logger.info("MFA completed successfully!")
            return True
        except PlaywrightTimeoutError:
            logger.error("MFA timeout - authentication not completed in time")
            return False
        except Exception as e:
            logger.error(f"Error during MFA wait: {e}")
            return False

    async def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        skip_if_authenticated: bool = True
    ) -> bool:
        """
        Perform login to Citrix Gateway via Duke Shibboleth SSO.

        Args:
            username: Duke NetID (will prompt if not provided)
            password: Duke password (will prompt if not provided)
            skip_if_authenticated: Skip login if already authenticated (default: True)

        Returns:
            True if login successful, False otherwise
        """
        logger.info("Starting Citrix Gateway login process...")

        # Try to load existing session
        if skip_if_authenticated:
            session_loaded = await self.load_session()
            if session_loaded:
                # Verify session is still valid
                if await self.verify_authentication():
                    logger.info("Using existing authenticated session")
                    return True
                else:
                    logger.info("Saved session expired, performing fresh login")

        # Get credentials if not provided
        if not username:
            username = input("Duke NetID: ")
        if not password:
            password = getpass.getpass("Duke Password: ")

        try:
            # Step 1: Navigate to Citrix Gateway
            logger.info(f"Navigating to {self.base_url}...")
            await self.page.goto(self.base_url, wait_until='networkidle')

            # Check if we're redirected to Shibboleth IdP
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")

            if 'shib.oit.duke.edu' in current_url:
                logger.info("Redirected to Duke Shibboleth IdP")

                # Step 2: Enter credentials
                logger.info("Submitting credentials...")

                # Wait for login form
                await self.page.wait_for_selector('input[name="j_username"]', timeout=10000)

                # Fill in username
                await self.page.fill('input[name="j_username"]', username)

                # Fill in password
                await self.page.fill('input[name="j_password"]', password)

                # Submit the form
                await self.page.click('button[type="submit"]')

                logger.info("Credentials submitted")

                # Step 3: Handle MFA
                # Wait a moment for the page to process
                await self.page.wait_for_timeout(2000)

                # Check if we're still on Shibboleth (MFA required)
                if 'shib.oit.duke.edu' in self.page.url:
                    mfa_success = await self.wait_for_mfa()
                    if not mfa_success:
                        logger.error("MFA authentication failed or timed out")
                        return False

            # Step 4: Wait for redirect to Citrix and session establishment
            logger.info("Waiting for Citrix session establishment...")

            try:
                # Wait for the Citrix Web interface to load
                await self.page.wait_for_url(
                    lambda url: 'secure.citrix.duke.edu/Citrix' in url,
                    timeout=30000
                )
                logger.info(f"Redirected to Citrix: {self.page.url}")
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for Citrix redirect, checking current state...")

            # Step 5: Verify we're authenticated
            if await self.verify_authentication():
                logger.info("Login successful!")

                # Save session for future use
                await self.save_session()

                return True
            else:
                logger.error("Login verification failed")
                return False

        except Exception as e:
            logger.error(f"Login failed with error: {e}", exc_info=True)
            return False

    async def verify_authentication(self) -> bool:
        """
        Verify that we're currently authenticated to Citrix Gateway.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Check if we can access the Citrix Web interface
            response = await self.page.goto(
                f"{self.base_url}/Citrix/SECUREWeb/",
                wait_until='networkidle',
                timeout=15000
            )

            # If we're authenticated, we should be on the Citrix interface
            current_url = self.page.url

            if 'SECUREWeb' in current_url and response.status == 200:
                logger.info("Authentication verified")
                return True
            else:
                logger.warning(f"Not authenticated - redirected to {current_url}")
                return False

        except Exception as e:
            logger.error(f"Authentication verification failed: {e}")
            return False

    async def get_available_resources(self) -> List[Dict[str, Any]]:
        """
        Get list of available Citrix resources (applications and desktops).

        Returns:
            List of resource dictionaries with name, type, and other metadata
        """
        logger.info("Fetching available resources...")

        try:
            # Make sure we're authenticated
            if not await self.verify_authentication():
                logger.error("Not authenticated - please login first")
                return []

            # Navigate to the Citrix Web interface
            await self.page.goto(
                f"{self.base_url}/Citrix/SECUREWeb/",
                wait_until='networkidle'
            )

            # Wait for resources to load
            await self.page.wait_for_timeout(3000)

            # Get cookies for API calls
            cookies = await self.context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}

            # Make API call to get resources list
            response = await self.page.evaluate('''
                async () => {
                    const response = await fetch('/Citrix/SECUREWeb/Resources/List', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        },
                        body: ''
                    });
                    return await response.text();
                }
            ''')

            logger.info(f"Resources response received: {len(response)} bytes")

            # Parse the response (it's XML)
            # For simplicity, we'll return the raw response
            # In a production implementation, you'd parse the XML
            return [{'raw_response': response}]

        except Exception as e:
            logger.error(f"Failed to get resources: {e}", exc_info=True)
            return []

    async def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information including cookies and user details.

        Returns:
            Dictionary containing session information
        """
        if not self.context:
            return {}

        cookies = await self.context.cookies()

        return {
            'url': self.page.url if self.page else None,
            'cookies': {c['name']: c['value'] for c in cookies},
            'authenticated': await self.verify_authentication()
        }


async def main():
    """Main entry point for the script."""
    print("=" * 80)
    print("Duke Citrix Gateway Authentication Client")
    print("=" * 80)
    print()

    # Create client (non-headless so user can see MFA prompts)
    async with CitrixGatewayClient(headless=False) as client:
        # Perform login
        success = await client.login()

        if success:
            print("\n" + "=" * 80)
            print("LOGIN SUCCESSFUL")
            print("=" * 80)

            # Get session info
            session_info = await client.get_session_info()
            print(f"\nCurrent URL: {session_info['url']}")
            print(f"Authenticated: {session_info['authenticated']}")
            print(f"\nSession cookies:")
            for name, value in session_info['cookies'].items():
                print(f"  {name}: {value[:50]}...")

            # Try to get available resources
            print("\n" + "=" * 80)
            print("FETCHING AVAILABLE RESOURCES")
            print("=" * 80)
            resources = await client.get_available_resources()
            print(f"Retrieved {len(resources)} resource(s)")

            # Keep browser open for inspection
            print("\n" + "=" * 80)
            print("Browser will remain open for inspection.")
            print("Press Enter to close the browser and exit...")
            print("=" * 80)
            input()

        else:
            print("\n" + "=" * 80)
            print("LOGIN FAILED")
            print("=" * 80)
            print("Please check your credentials and try again.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
