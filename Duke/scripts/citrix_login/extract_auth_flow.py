#!/usr/bin/env python3
"""Extract authentication flow details from HAR file."""

import json
import base64
from urllib.parse import parse_qs, urlparse

def extract_auth_flow(har_path):
    """Extract detailed authentication flow."""
    with open(har_path, 'r') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']

    print("=" * 80)
    print("CRITICAL AUTHENTICATION FLOW")
    print("=" * 80)

    # Key endpoints for auth
    auth_endpoints = [
        'doSaml',
        'samlauth',
        'authn/external',
        'GetAuthMethods',
        'Login',
        'getAuthenticationRequirements'
    ]

    for idx, entry in enumerate(entries):
        request = entry['request']
        response = entry['response']
        url = request['url']

        # Check if this is an auth-related endpoint
        is_auth = any(endpoint in url for endpoint in auth_endpoints)

        if is_auth:
            print(f"\n{'='*80}")
            print(f"[{idx}] {request['method']} {url}")
            print(f"Status: {response['status']} {response.get('statusText', '')}")

            # Cookies
            if request.get('cookies'):
                print("\nRequest Cookies:")
                for cookie in request['cookies']:
                    print(f"  {cookie['name']}: {cookie['value'][:50]}...")

            if response.get('cookies'):
                print("\nResponse Cookies:")
                for cookie in response['cookies']:
                    value = cookie.get('value', '')
                    print(f"  {cookie['name']}: {value[:50] if len(value) > 50 else value}")

            # Headers
            print("\nRequest Headers:")
            for header in request.get('headers', []):
                if header['name'].lower() in ['content-type', 'authorization', 'x-csrf-token', 'referer']:
                    print(f"  {header['name']}: {header['value']}")

            print("\nResponse Headers:")
            for header in response.get('headers', []):
                if header['name'].lower() in ['content-type', 'location', 'set-cookie']:
                    print(f"  {header['name']}: {header['value'][:100]}")

            # Request body
            if request.get('postData'):
                post_data = request['postData']
                print(f"\nRequest Body ({post_data.get('mimeType', 'unknown')}):")
                if 'text' in post_data:
                    text = post_data['text']
                    if 'SAMLResponse' in text:
                        print("  [Contains SAML Response - too large to display]")
                    elif len(text) < 500:
                        print(f"  {text}")
                    else:
                        print(f"  {text[:500]}...")

            # Response body
            if response.get('content', {}).get('text'):
                content = response['content']
                text = content.get('text', '')
                mime_type = content.get('mimeType', '')

                if 'json' in mime_type:
                    print(f"\nResponse Body ({mime_type}):")
                    if len(text) < 1000:
                        try:
                            parsed = json.loads(text)
                            print(f"  {json.dumps(parsed, indent=2)}")
                        except:
                            print(f"  {text}")
                    else:
                        print(f"  {text[:500]}...")

if __name__ == '__main__':
    extract_auth_flow('/Users/christian/.reverse-api/runs/har/c45d506a785c/recording.har')
