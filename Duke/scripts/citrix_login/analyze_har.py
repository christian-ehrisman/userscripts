#!/usr/bin/env python3
"""Analyze HAR file to extract API endpoints and authentication patterns."""

import json
import sys
from collections import defaultdict
from urllib.parse import urlparse

def analyze_har(har_path):
    """Analyze HAR file and extract relevant API information."""
    with open(har_path, 'r') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']

    # Group requests by domain
    domains = defaultdict(list)
    auth_patterns = {
        'cookies': set(),
        'headers': set(),
        'tokens': []
    }

    print(f"Total entries: {len(entries)}\n")
    print("=" * 80)
    print("API ENDPOINTS DISCOVERED")
    print("=" * 80)

    for idx, entry in enumerate(entries):
        request = entry['request']
        response = entry['response']
        url = request['url']
        parsed = urlparse(url)
        method = request['method']

        # Track authentication patterns
        for cookie in request.get('cookies', []):
            auth_patterns['cookies'].add(cookie['name'])

        for header in request.get('headers', []):
            if 'auth' in header['name'].lower() or 'token' in header['name'].lower():
                auth_patterns['headers'].add(header['name'])

        # Print request details
        print(f"\n[{idx}] {method} {url}")
        print(f"    Status: {response['status']} {response.get('statusText', '')}")

        # Show cookies if present
        if request.get('cookies'):
            print(f"    Cookies: {[c['name'] for c in request['cookies']]}")

        # Show important headers
        important_headers = []
        for h in request.get('headers', []):
            if h['name'].lower() in ['authorization', 'x-csrf-token', 'content-type']:
                important_headers.append(f"{h['name']}: {h['value'][:50]}")
        if important_headers:
            print(f"    Headers: {important_headers}")

        # Show request body if present
        if request.get('postData'):
            post_data = request['postData']
            print(f"    Body Type: {post_data.get('mimeType', 'unknown')}")
            if 'text' in post_data:
                text = post_data['text']
                if len(text) < 200:
                    print(f"    Body: {text}")
                else:
                    print(f"    Body: {text[:200]}... (truncated)")

        domains[parsed.netloc].append({
            'method': method,
            'path': parsed.path,
            'query': parsed.query,
            'status': response['status']
        })

    print("\n" + "=" * 80)
    print("AUTHENTICATION PATTERNS")
    print("=" * 80)
    print(f"Cookie names: {sorted(auth_patterns['cookies'])}")
    print(f"Auth headers: {sorted(auth_patterns['headers'])}")

    print("\n" + "=" * 80)
    print("DOMAINS")
    print("=" * 80)
    for domain, requests in sorted(domains.items()):
        print(f"\n{domain}: {len(requests)} requests")
        # Show unique paths
        paths = set((r['method'], r['path']) for r in requests)
        for method, path in sorted(paths):
            print(f"  {method} {path}")

if __name__ == '__main__':
    analyze_har('/Users/christian/.reverse-api/runs/har/c45d506a785c/recording.har')
