#!/usr/bin/env python3
"""
Example usage of Duke SSO Authentication Client.

This file demonstrates various ways to use the DukeSSOClient.
"""

import os
from api_client import DukeSSOClient


def example_1_interactive():
    """Example 1: Interactive authentication with prompts."""
    print("=" * 60)
    print("Example 1: Interactive Authentication")
    print("=" * 60)

    from api_client import interactive_login

    client = interactive_login()

    if client:
        print("\n✓ Successfully authenticated!")

        # Use the authenticated session
        session = client.get_authenticated_session()

        # Example: Access authenticated resource
        response = session.get("https://idms-mfa.oit.duke.edu/mfa/home")
        print(f"Home page status: {response.status_code}")


def example_2_environment_variables():
    """Example 2: Use environment variables for credentials."""
    print("\n" + "=" * 60)
    print("Example 2: Environment Variables")
    print("=" * 60)

    # Get credentials from environment
    netid = os.getenv('DUKE_NETID')
    password = os.getenv('DUKE_PASSWORD')

    if not netid or not password:
        print("⚠ Set DUKE_NETID and DUKE_PASSWORD environment variables")
        print("  export DUKE_NETID=your_netid")
        print("  export DUKE_PASSWORD=your_password")
        return

    client = DukeSSOClient()

    # Authenticate with Duo push
    success = client.authenticate(
        username=netid,
        password=password,
        duo_method="push"
    )

    if success:
        print("✓ Authenticated successfully!")
        session = client.get_authenticated_session()
        # Use the session...
    else:
        print("✗ Authentication failed")


def example_3_duo_passcode():
    """Example 3: Authenticate with Duo passcode."""
    print("\n" + "=" * 60)
    print("Example 3: Duo Passcode Authentication")
    print("=" * 60)

    # This example shows how to use Duo passcode instead of push
    netid = input("NetID: ")
    password = input("Password: ")
    passcode = input("Duo Passcode (6 digits): ")

    client = DukeSSOClient()

    success = client.authenticate(
        username=netid,
        password=password,
        duo_method="passcode",
        duo_passcode=passcode
    )

    if success:
        print("✓ Authenticated with passcode!")
        session = client.get_authenticated_session()
    else:
        print("✗ Authentication failed")


def example_4_session_reuse():
    """Example 4: Reuse authenticated session."""
    print("\n" + "=" * 60)
    print("Example 4: Session Reuse")
    print("=" * 60)

    from api_client import interactive_login

    # Authenticate once
    client = interactive_login()

    if not client:
        print("✗ Authentication failed")
        return

    # Get the session
    session = client.get_authenticated_session()

    # Reuse the session for multiple requests
    print("\nMaking multiple requests with the same session:")

    urls = [
        "https://idms-mfa.oit.duke.edu/mfa/home",
        "https://idms-mfa.oit.duke.edu/mfa/",
    ]

    for url in urls:
        response = session.get(url)
        print(f"  {url}: HTTP {response.status_code}")

    # Test if session is still valid
    if client.test_authentication():
        print("\n✓ Session is still authenticated!")
    else:
        print("\n⚠ Session expired, re-authentication needed")


def example_5_error_handling():
    """Example 5: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    client = DukeSSOClient()

    try:
        # Attempt authentication
        success = client.authenticate(
            username="invalid_user",
            password="invalid_password",
            duo_method="push"
        )

        if success:
            print("✓ Authenticated")
        else:
            print("✗ Authentication failed")
            print("  Possible reasons:")
            print("  - Invalid credentials")
            print("  - Duo push denied or timed out")
            print("  - Network issues")

    except ValueError as e:
        print(f"✗ Invalid parameters: {e}")

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def example_6_custom_duo_device():
    """Example 6: Specify custom Duo device."""
    print("\n" + "=" * 60)
    print("Example 6: Custom Duo Device Selection")
    print("=" * 60)

    client = DukeSSOClient()

    # First, initiate SSO to discover available devices
    try:
        client.initiate_sso_flow()

        # Get login page to parse devices
        login_url = f"{client.IDP_URL}/idp/authn/external?conversation={client.conversation_id}"
        response = client.session.get(login_url)

        # Parse available Duo devices
        devices = client._parse_duo_options(response.text)

        if devices:
            print(f"Found {len(devices)} Duo device(s):")
            for i, device in enumerate(devices, 1):
                print(f"  {i}. {device['name']} ({device['value']})")

            # Select a specific device
            # device_id = devices[0]['value']

            print("\nYou can now authenticate with a specific device:")
            print(f"  client.authenticate(..., duo_device='{devices[0]['value']}')")
        else:
            print("No Duo devices found")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main menu for examples."""
    print("\n" + "=" * 60)
    print("Duke SSO Authentication - Example Usage")
    print("=" * 60)

    examples = {
        "1": ("Interactive Authentication", example_1_interactive),
        "2": ("Environment Variables", example_2_environment_variables),
        "3": ("Duo Passcode", example_3_duo_passcode),
        "4": ("Session Reuse", example_4_session_reuse),
        "5": ("Error Handling", example_5_error_handling),
        "6": ("Custom Duo Device", example_6_custom_duo_device),
    }

    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    choice = input("\nSelect example (1-6, or 'all'): ").strip()

    if choice.lower() == 'all':
        for _, func in examples.values():
            func()
    elif choice in examples:
        _, func = examples[choice]
        func()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
