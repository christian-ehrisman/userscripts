#!/usr/bin/env python3
"""
Test script to verify Duke SSO authentication flow.

This script tests the authentication flow without requiring actual credentials.
It validates that the client can:
1. Initiate SSO flow
2. Obtain conversation ID
3. Parse login page
4. Handle redirects properly

For full authentication testing, use api_client.py in interactive mode.
"""

import logging
from api_client import DukeSSOClient

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sso_initialization():
    """Test SSO flow initialization."""
    print("=" * 70)
    print("TEST 1: SSO Flow Initialization")
    print("=" * 70)

    client = DukeSSOClient()

    try:
        conversation_id, login_url = client.initiate_sso_flow()

        print(f"\n✓ SSO flow initialized successfully")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Login URL: {login_url}")

        # Validate conversation ID format
        assert conversation_id, "Conversation ID should not be empty"
        assert login_url.startswith("https://"), "Login URL should use HTTPS"

        print(f"\n✓ Validation passed")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cookie_handling():
    """Test cookie management."""
    print("\n" + "=" * 70)
    print("TEST 2: Cookie Handling")
    print("=" * 70)

    client = DukeSSOClient()
    client.initiate_sso_flow()

    cookies = list(client.session.cookies)
    print(f"\n✓ Session has {len(cookies)} cookies")

    required_cookies = ['__Host-JSESSIONID']

    for cookie_name in required_cookies:
        found = any(c.name == cookie_name for c in cookies)
        if found:
            print(f"  ✓ Found required cookie: {cookie_name}")
        else:
            print(f"  ✗ Missing required cookie: {cookie_name}")
            return False

    print(f"\n✓ All required cookies present")
    return True


def test_duo_parsing():
    """Test Duo options parsing."""
    print("\n" + "=" * 70)
    print("TEST 3: Duo Options Parsing")
    print("=" * 70)

    client = DukeSSOClient()
    client.initiate_sso_flow()

    # Get login page
    login_url = f"{client.IDP_URL}/idp/authn/external?conversation={client.conversation_id}"
    response = client.session.get(login_url)

    if response.status_code != 200:
        print(f"✗ Failed to load login page: HTTP {response.status_code}")
        return False

    print(f"✓ Login page loaded successfully")

    # Parse Duo options
    duo_devices = client._parse_duo_options(response.text)

    if duo_devices:
        print(f"✓ Found {len(duo_devices)} Duo device(s):")
        for device in duo_devices:
            print(f"  - {device['name']}: {device['value']}")
    else:
        print("⚠ No Duo devices found (may need actual authentication)")

    return True


def test_session_methods():
    """Test session utility methods."""
    print("\n" + "=" * 70)
    print("TEST 4: Session Methods")
    print("=" * 70)

    client = DukeSSOClient()

    # Test unauthenticated session
    is_auth = client.test_authentication()
    print(f"✓ Unauthenticated session test: {is_auth}")
    assert not is_auth, "New session should not be authenticated"

    print(f"\n✓ Session methods working correctly")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Duke SSO Authentication Flow Test Suite")
    print("=" * 70 + "\n")

    tests = [
        ("SSO Initialization", test_sso_initialization),
        ("Cookie Handling", test_cookie_handling),
        ("Duo Parsing", test_duo_parsing),
        ("Session Methods", test_session_methods),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\n  {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All tests passed!")
        print("\n  To test full authentication, run:")
        print("    python api_client.py")
        return 0
    else:
        print("\n  ⚠ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
