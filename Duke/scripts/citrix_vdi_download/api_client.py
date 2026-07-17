#!/usr/bin/env python3
"""
Citrix VDI Connection File Downloader

This script downloads Citrix VDI connection (.ica) files by resource name.
Authentication (SSO) is handled externally - this script works with pre-authenticated cookies.

Usage:
    python api_client.py --resource-name "Admin03 - UBUNTU" --output desktop.ica
    python api_client.py --list-resources
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CitrixVDIClient:
    """Client for interacting with Citrix VDI API to download connection files."""

    BASE_URL = "https://secure.citrix.duke.edu"
    RESOURCES_LIST_URL = f"{BASE_URL}/Citrix/SECUREWeb/Resources/List"
    LAUNCH_ICA_BASE_URL = f"{BASE_URL}/Citrix/SECUREWeb/Resources/LaunchIca"

    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        """
        Initialize the Citrix VDI client.

        Args:
            cookies: Dictionary of authentication cookies. If None, will attempt to load from environment.

        Raises:
            ValueError: If required cookies are missing.
        """
        self.session = self._create_session()
        self.cookies = cookies or self._load_cookies_from_env()
        self._validate_cookies()

        # Apply cookies to session
        for name, value in self.cookies.items():
            self.session.cookies.set(name, value)

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set default headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'X-Citrix-IsUsingHTTPS': 'Yes',
            'X-Requested-With': 'XMLHttpRequest',
        })

        return session

    def _load_cookies_from_env(self) -> Dict[str, str]:
        """
        Load cookies from environment variables.

        Expected format: CITRIX_COOKIES='{"CsrfToken": "...", "CtxsAuthId": "...", ...}'

        Returns:
            Dictionary of cookies.
        """
        cookies_json = os.getenv('CITRIX_COOKIES')
        if cookies_json:
            try:
                return json.loads(cookies_json)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse CITRIX_COOKIES: {e}")
                raise ValueError("Invalid CITRIX_COOKIES format. Expected JSON.")

        # Try individual environment variables
        return {
            'CsrfToken': os.getenv('CITRIX_CSRF_TOKEN', ''),
            'CtxsAuthId': os.getenv('CITRIX_AUTH_ID', ''),
            'CtxsDeviceId': os.getenv('CITRIX_DEVICE_ID', ''),
            'ASP.NET_SessionId': os.getenv('CITRIX_SESSION_ID', ''),
            'NSC_AAAC': os.getenv('CITRIX_NSC_AAAC', ''),
        }

    def _validate_cookies(self) -> None:
        """
        Validate that required cookies are present.

        Raises:
            ValueError: If required cookies are missing.
        """
        required_cookies = ['CsrfToken', 'CtxsAuthId']
        missing = [c for c in required_cookies if not self.cookies.get(c)]

        if missing:
            raise ValueError(
                f"Missing required cookies: {', '.join(missing)}. "
                "Please provide authentication cookies via CITRIX_COOKIES environment variable "
                "or individual environment variables (CITRIX_CSRF_TOKEN, CITRIX_AUTH_ID, etc.)"
            )

    def get_resources(self) -> List[Dict[str, Any]]:
        """
        Fetch all available Citrix resources (desktops and applications).

        Returns:
            List of resource dictionaries, each containing name, launchurl, etc.

        Raises:
            requests.HTTPError: If the API request fails.
            ValueError: If the response format is invalid.
        """
        logger.info("Fetching resources list...")

        # Add CSRF token to headers
        headers = {
            'Csrf-Token': self.cookies.get('CsrfToken', ''),
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.BASE_URL,
            'Referer': f'{self.BASE_URL}/Citrix/SECUREWeb/',
        }

        # POST request with empty body (as observed in HAR)
        response = self.session.post(
            self.RESOURCES_LIST_URL,
            headers=headers,
            data='format=json&resourceDetails=Default',
            timeout=30
        )

        # Check for authentication errors
        if response.status_code == 401 or response.status_code == 403:
            logger.error("Authentication failed. Cookies may be expired or invalid.")
            raise requests.HTTPError(
                f"Authentication failed (status {response.status_code}). "
                "Please refresh your cookies."
            )

        response.raise_for_status()

        try:
            data = response.json()
            resources = data.get('resources', [])
            logger.info(f"Found {len(resources)} resources")
            return resources
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse resources response: {e}")
            raise ValueError(f"Invalid response format: {e}")

    def find_resource_by_name(
        self,
        name: str,
        exact_match: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find a resource by name.

        Args:
            name: Resource name to search for.
            exact_match: If True, requires exact match. If False, does case-insensitive substring match.

        Returns:
            Resource dictionary if found, None otherwise.
        """
        resources = self.get_resources()

        if exact_match:
            for resource in resources:
                if resource.get('name') == name:
                    logger.info(f"Found exact match for resource: {name}")
                    return resource
        else:
            name_lower = name.lower()
            for resource in resources:
                if name_lower in resource.get('name', '').lower():
                    logger.info(f"Found partial match for resource: {resource.get('name')}")
                    return resource

        logger.warning(f"Resource not found: {name}")
        return None

    def _build_launch_url(
        self,
        launch_path: str,
        display_name: str
    ) -> str:
        """
        Build the complete launch URL with query parameters.

        Args:
            launch_path: The launch path from the resource (e.g., "Resources/LaunchIca/...ica")
            display_name: The display name for the resource.

        Returns:
            Complete URL with query parameters.
        """
        # Generate launch ID (timestamp in milliseconds, as observed in HAR)
        launch_id = int(time.time() * 1000)

        # Build query parameters
        params = {
            'CsrfToken': self.cookies.get('CsrfToken', ''),
            'IsUsingHttps': 'Yes',
            'displayNameDesktopTitle': display_name,
            'launchId': str(launch_id),
        }

        # Construct full URL
        base_url = f"{self.BASE_URL}/Citrix/SECUREWeb/{launch_path}"
        query_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])

        return f"{base_url}?{query_string}"

    def download_ica_file(
        self,
        resource_name: str,
        output_path: str,
        exact_match: bool = True
    ) -> bool:
        """
        Download a Citrix VDI connection file (.ica) by resource name.

        Args:
            resource_name: Name of the Citrix resource (desktop or application).
            output_path: Path where the .ica file should be saved.
            exact_match: If True, requires exact resource name match.

        Returns:
            True if download was successful, False otherwise.

        Raises:
            ValueError: If resource is not found.
            requests.HTTPError: If download fails.
        """
        # Find the resource
        resource = self.find_resource_by_name(resource_name, exact_match=exact_match)

        if not resource:
            available_names = [r.get('name') for r in self.get_resources()]
            raise ValueError(
                f"Resource '{resource_name}' not found. "
                f"Available resources: {', '.join(available_names[:5])}..."
            )

        # Extract launch URL and display name
        launch_path = resource.get('launchurl')
        display_name = resource.get('name', resource_name)

        if not launch_path:
            raise ValueError(f"Resource '{resource_name}' has no launch URL")

        # Build complete URL
        download_url = self._build_launch_url(launch_path, display_name)
        logger.info(f"Downloading ICA file from: {download_url}")

        # Download the .ica file
        response = self.session.get(download_url, timeout=30)

        # Check for errors
        if response.status_code == 401 or response.status_code == 403:
            logger.error("Authentication failed during download.")
            raise requests.HTTPError("Authentication failed. Cookies may be expired.")

        response.raise_for_status()

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Successfully downloaded ICA file to: {output_path}")
        logger.info(f"File size: {len(response.content)} bytes")

        return True

    def list_resources(self) -> None:
        """Print all available resources to console."""
        resources = self.get_resources()

        print("\n" + "=" * 80)
        print("AVAILABLE CITRIX RESOURCES")
        print("=" * 80 + "\n")

        for i, resource in enumerate(resources, 1):
            name = resource.get('name', 'Unknown')
            is_desktop = resource.get('isdesktop', False)
            resource_type = "Desktop" if is_desktop else "Application"
            description = resource.get('description', '')
            path = resource.get('path', '')

            print(f"{i}. {name}")
            print(f"   Type: {resource_type}")
            if description:
                print(f"   Description: {description}")
            if path and path != '\\':
                print(f"   Path: {path}")
            print()


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Download Citrix VDI connection files by resource name'
    )

    parser.add_argument(
        '--resource-name',
        '-r',
        help='Name of the Citrix resource to download'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output path for the .ica file (default: <resource-name>.ica)'
    )

    parser.add_argument(
        '--list-resources',
        '-l',
        action='store_true',
        help='List all available resources'
    )

    parser.add_argument(
        '--partial-match',
        '-p',
        action='store_true',
        help='Use partial name matching instead of exact match'
    )

    parser.add_argument(
        '--cookies-file',
        '-c',
        help='Path to JSON file containing cookies'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('requests').setLevel(logging.DEBUG)

    try:
        # Load cookies from file if provided
        cookies = None
        if args.cookies_file:
            with open(args.cookies_file, 'r') as f:
                cookies = json.load(f)

        # Initialize client
        client = CitrixVDIClient(cookies=cookies)

        # List resources mode
        if args.list_resources:
            client.list_resources()
            return 0

        # Download mode
        if not args.resource_name:
            parser.error("--resource-name is required (or use --list-resources)")

        # Determine output path
        output_path = args.output
        if not output_path:
            # Sanitize resource name for filename
            safe_name = "".join(c for c in args.resource_name if c.isalnum() or c in (' ', '-', '_'))
            safe_name = safe_name.replace(' ', '_')
            output_path = f"{safe_name}.ica"

        # Download the ICA file
        success = client.download_ica_file(
            args.resource_name,
            output_path,
            exact_match=not args.partial_match
        )

        if success:
            print(f"\n✓ Successfully downloaded: {output_path}")
            return 0
        else:
            print(f"\n✗ Failed to download resource: {args.resource_name}")
            return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n✗ Error: {e}")
        return 1

    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        print(f"\n✗ HTTP Error: {e}")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
