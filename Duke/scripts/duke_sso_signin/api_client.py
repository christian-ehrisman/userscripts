#!/usr/bin/env python3
"""
Duke Federated SSO Authentication Client

This module provides a Python client for authenticating with Duke's federated
SSO system using SAML 2.0 and Duo MFA.

The authentication flow:
1. Initiate SSO flow with Duke's MFA portal
2. Handle Shibboleth IdP SAML redirects
3. Submit credentials (NetID and password)
4. Handle Duo MFA (push, passcode, or phone call)
5. Complete SAML assertion exchange
6. Return authenticated session

Author: Reverse-engineered from HAR file
"""

import requests
import time
import re
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode
from html.parser import HTMLParser
import getpass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DukeFormParser(HTMLParser):
    """Parse HTML forms to extract action URLs and hidden fields."""

    def __init__(self):
        super().__init__()
        self.forms = []
        self.current_form = None
        self.in_form = False

    def handle_starttag(self, tag: str, attrs: list):
        attrs_dict = dict(attrs)

        if tag == 'form':
            self.in_form = True
            self.current_form = {
                'action': attrs_dict.get('action', ''),
                'method': attrs_dict.get('method', 'GET').upper(),
                'fields': {}
            }
        elif tag == 'input' and self.in_form:
            name = attrs_dict.get('name')
            value = attrs_dict.get('value', '')
            input_type = attrs_dict.get('type', 'text')

            if name:
                self.current_form['fields'][name] = {
                    'value': value,
                    'type': input_type
                }

    def handle_endtag(self, tag: str):
        if tag == 'form' and self.in_form:
            self.in_form = False
            if self.current_form:
                self.forms.append(self.current_form)
                self.current_form = None


class DukeSSOClient:
    """Client for authenticating with Duke's federated SSO system."""

    BASE_URL = "https://idms-mfa.oit.duke.edu"
    IDP_URL = "https://shib.oit.duke.edu"

    def __init__(self):
        """Initialize the SSO client with a requests session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.conversation_id = None
        self.duo_devices = []

    def initiate_sso_flow(self) -> Tuple[str, str]:
        """
        Initiate the SSO flow and retrieve the conversation ID.

        Returns:
            Tuple of (conversation_id, login_page_url)

        Raises:
            Exception: If SSO initiation fails
        """
        logger.info("Initiating SSO flow...")

        # Step 1: Access MFA portal
        response = self.session.get(f"{self.BASE_URL}/mfa/", allow_redirects=True)
        logger.debug(f"Initial redirect chain: {len(response.history)} redirects")

        if response.status_code != 200:
            raise Exception(f"Failed to initiate SSO: HTTP {response.status_code}")

        # Extract conversation ID from final URL
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)

        if 'conversation' in query_params:
            self.conversation_id = query_params['conversation'][0]
            logger.info(f"Obtained conversation ID: {self.conversation_id}")
        else:
            raise Exception("Could not extract conversation ID from SSO flow")

        return self.conversation_id, response.url

    def _parse_duo_options(self, html_content: str) -> list:
        """
        Parse Duo MFA options from the login page.

        Args:
            html_content: HTML content of the login page

        Returns:
            List of available Duo devices/methods
        """
        devices = []

        # Look for Duo device options in the HTML
        # Format: <option value="push-DEVICE_ID">Device Name</option>
        device_pattern = r'<option[^>]*value="([^"]*)"[^>]*>([^<]+)</option>'
        matches = re.findall(device_pattern, html_content)

        for value, name in matches:
            if value and value not in ['', 'select']:
                devices.append({
                    'value': value,
                    'name': name.strip()
                })

        # Also check for data attributes
        data_pattern = r'data-device[^=]*=[\'"]\s*([^\'"]+)'
        data_matches = re.findall(data_pattern, html_content)

        logger.debug(f"Found {len(devices)} Duo devices")
        return devices

    def authenticate(
        self,
        username: str,
        password: str,
        duo_method: str = "push",
        duo_device: Optional[str] = None,
        duo_passcode: Optional[str] = None
    ) -> bool:
        """
        Authenticate with Duke SSO using credentials and Duo MFA.

        Args:
            username: Duke NetID
            password: NetID password
            duo_method: Duo method ("push", "passcode", "phone")
            duo_device: Duo device ID (optional, will auto-select if not provided)
            duo_passcode: Duo passcode (required if duo_method is "passcode")

        Returns:
            True if authentication successful, False otherwise

        Raises:
            Exception: If authentication fails
        """
        logger.info(f"Authenticating as {username}...")

        # Ensure SSO flow is initiated
        if not self.conversation_id:
            self.initiate_sso_flow()

        # Get the login page
        login_url = f"{self.IDP_URL}/idp/authn/external?conversation={self.conversation_id}"
        response = self.session.get(login_url)

        if response.status_code != 200:
            raise Exception(f"Failed to load login page: HTTP {response.status_code}")

        # Parse Duo options
        self.duo_devices = self._parse_duo_options(response.text)

        if self.duo_devices and not duo_device:
            logger.info("Available Duo devices:")
            for i, device in enumerate(self.duo_devices):
                logger.info(f"  {i+1}. {device['name']} ({device['value']})")

            # Auto-select first device if available
            duo_device = self.duo_devices[0]['value']
            logger.info(f"Auto-selected: {self.duo_devices[0]['name']}")

        # Prepare authentication payload
        login_page_time = int(datetime.now().timestamp() * 1000)

        payload = {
            'j_username': username,
            'j_password': password,
            'visible_webauthn_default': 'on',
            'duoIssued': '1',
            'passcodev2': duo_passcode or '',
            'rememberme': 'on',
            'loginPageTime': str(login_page_time),
            'Submit': ''
        }

        # Add Duo method selection
        if duo_device:
            payload['duoSelection'] = duo_device

        # Submit credentials
        logger.info(f"Submitting credentials with Duo method: {duo_method}")

        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.IDP_URL,
            'Referer': login_url
        })

        # First POST - submit credentials
        auth_url = f"{self.IDP_URL}/idp/authn/external"
        response = self.session.post(auth_url, data=payload, allow_redirects=False)

        logger.debug(f"Auth POST status: {response.status_code}")

        # Handle Duo MFA flow
        if duo_method == "push":
            return self._handle_duo_push(auth_url)
        elif duo_method == "passcode":
            return self._handle_duo_passcode(auth_url, duo_passcode)
        else:
            raise ValueError(f"Unsupported Duo method: {duo_method}")

    def _handle_duo_push(self, auth_url: str, max_attempts: int = 30) -> bool:
        """
        Handle Duo push notification approval.

        Args:
            auth_url: Authentication endpoint URL
            max_attempts: Maximum polling attempts (30 = ~60 seconds)

        Returns:
            True if MFA approved, False otherwise
        """
        logger.info("Duo push sent! Please approve on your device...")
        logger.info("Waiting for approval (timeout: 60 seconds)...")

        for attempt in range(max_attempts):
            # Poll for approval
            time.sleep(2)

            response = self.session.post(
                auth_url,
                data={},
                allow_redirects=False
            )

            # Check if we got a redirect (indicates approval)
            if response.status_code == 302:
                logger.info("✓ Duo push approved!")
                return self._complete_saml_flow(response)

            # Check response for status
            if 'denied' in response.text.lower():
                logger.error("✗ Duo push denied")
                return False

            if attempt % 5 == 0:
                logger.info(f"Still waiting... ({attempt * 2}s elapsed)")

        logger.error("✗ Duo push timed out")
        return False

    def _handle_duo_passcode(self, auth_url: str, passcode: str) -> bool:
        """
        Handle Duo passcode authentication.

        Args:
            auth_url: Authentication endpoint URL
            passcode: Duo passcode

        Returns:
            True if MFA successful, False otherwise
        """
        if not passcode:
            raise ValueError("Passcode is required for passcode authentication")

        logger.info("Submitting Duo passcode...")

        response = self.session.post(
            auth_url,
            data={'passcodev2': passcode},
            allow_redirects=False
        )

        if response.status_code == 302:
            logger.info("✓ Duo passcode accepted!")
            return self._complete_saml_flow(response)
        else:
            logger.error("✗ Duo passcode rejected")
            return False

    def _complete_saml_flow(self, auth_response: requests.Response) -> bool:
        """
        Complete the SAML assertion exchange after MFA approval.

        Args:
            auth_response: Response from successful authentication

        Returns:
            True if SAML flow completed successfully
        """
        logger.info("Completing SAML flow...")

        # Follow the redirect
        if 'Location' not in auth_response.headers:
            logger.error("No redirect location in auth response")
            return False

        redirect_url = auth_response.headers['Location']
        if not redirect_url.startswith('http'):
            redirect_url = f"{self.IDP_URL}{redirect_url}"

        # Get SAML response
        response = self.session.get(redirect_url, allow_redirects=False)

        if response.status_code != 200:
            logger.error(f"Failed to get SAML response: HTTP {response.status_code}")
            return False

        # Parse SAML form
        parser = DukeFormParser()
        parser.feed(response.text)

        if not parser.forms:
            logger.error("No SAML form found in response")
            return False

        # Submit SAML response to SP
        saml_form = parser.forms[0]
        saml_action = saml_form['action']

        # Build SAML POST data
        saml_data = {}
        for field_name, field_info in saml_form['fields'].items():
            if field_info['type'] == 'hidden':
                saml_data[field_name] = field_info['value']

        logger.debug(f"Submitting SAML response to {saml_action}")

        # POST SAML response
        response = self.session.post(
            saml_action,
            data=saml_data,
            allow_redirects=True
        )

        # Check if we're authenticated
        if response.status_code == 200 and '/mfa/home' in response.url:
            logger.info("✓ Authentication successful!")
            logger.info(f"Authenticated session URL: {response.url}")
            return True
        else:
            logger.error(f"SAML flow failed: {response.status_code} - {response.url}")
            return False

    def get_authenticated_session(self) -> requests.Session:
        """
        Return the authenticated requests session.

        Returns:
            Authenticated requests.Session object

        Raises:
            Exception: If not authenticated
        """
        # Check if session has authentication cookies
        session_cookies = list(self.session.cookies)

        if not session_cookies:
            raise Exception("No authenticated session available. Call authenticate() first.")

        logger.info(f"Session has {len(session_cookies)} cookies")
        return self.session

    def test_authentication(self) -> bool:
        """
        Test if the current session is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/mfa/home", allow_redirects=False)

            # If we get a 200 and we're at /mfa/home, we're authenticated
            if response.status_code == 200:
                logger.info("✓ Session is authenticated")
                return True

            # If we get redirected to login, we're not authenticated
            if response.status_code in [302, 303] and 'SAML' in response.headers.get('Location', ''):
                logger.info("✗ Session is not authenticated")
                return False

            return False
        except Exception as e:
            logger.error(f"Error testing authentication: {e}")
            return False


def interactive_login() -> DukeSSOClient:
    """
    Perform interactive login with user prompts.

    Returns:
        Authenticated DukeSSOClient instance
    """
    print("=" * 60)
    print("Duke Federated SSO Authentication")
    print("=" * 60)

    # Get credentials
    username = input("NetID: ").strip()
    password = getpass.getpass("Password: ")

    print("\nDuo MFA Options:")
    print("  1. Push notification (default)")
    print("  2. Passcode")

    choice = input("Select method [1]: ").strip() or "1"

    duo_method = "push"
    duo_passcode = None

    if choice == "2":
        duo_method = "passcode"
        duo_passcode = input("Enter Duo passcode: ").strip()

    # Create client and authenticate
    client = DukeSSOClient()

    try:
        success = client.authenticate(
            username=username,
            password=password,
            duo_method=duo_method,
            duo_passcode=duo_passcode
        )

        if success:
            print("\n✓ Successfully authenticated!")
            return client
        else:
            print("\n✗ Authentication failed")
            return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        print(f"\n✗ Error: {e}")
        return None


def main():
    """Main entry point for the script."""
    # Example 1: Interactive login
    client = interactive_login()

    if client:
        # Test the session
        is_authenticated = client.test_authentication()

        if is_authenticated:
            print("\nYou can now use the authenticated session:")
            print("  session = client.get_authenticated_session()")
            print("  response = session.get('https://idms-mfa.oit.duke.edu/mfa/home')")

            # Example: Access authenticated resource
            session = client.get_authenticated_session()
            response = session.get(f"{client.BASE_URL}/mfa/home")
            print(f"\nExample request to /mfa/home: HTTP {response.status_code}")

    # Example 2: Programmatic login (uncomment to use)
    # client = DukeSSOClient()
    # success = client.authenticate(
    #     username="your_netid",
    #     password="your_password",
    #     duo_method="push"
    # )
    # if success:
    #     session = client.get_authenticated_session()
    #     # Use the authenticated session for API calls


if __name__ == "__main__":
    main()
