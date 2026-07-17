#!/usr/bin/env python3
"""
Example usage of the CitrixVDIClient

This demonstrates how to use the CitrixVDIClient class programmatically.
"""

from api_client import CitrixVDIClient

# Example 1: Initialize with cookies dictionary
def example_with_cookies_dict():
    """Example using a cookies dictionary."""
    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
        'CtxsDeviceId': 'YOUR_DEVICE_ID',
        'ASP.NET_SessionId': 'YOUR_SESSION_ID',
        'NSC_AAAC': 'YOUR_NSC_AAAC',
    }

    try:
        client = CitrixVDIClient(cookies=cookies)

        # List all resources
        print("Fetching all resources...")
        resources = client.get_resources()

        print(f"\nFound {len(resources)} resources:")
        for resource in resources[:5]:  # Show first 5
            name = resource.get('name', 'Unknown')
            is_desktop = resource.get('isdesktop', False)
            resource_type = "Desktop" if is_desktop else "Application"
            print(f"  - {name} ({resource_type})")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Example 2: Download a specific resource by exact name
def example_download_exact_match():
    """Example downloading a resource by exact name."""
    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
    }

    try:
        client = CitrixVDIClient(cookies=cookies)

        # Download by exact name
        resource_name = "Admin03 - UBUNTU"
        output_path = "ubuntu_desktop.ica"

        print(f"Downloading '{resource_name}'...")
        success = client.download_ica_file(
            resource_name=resource_name,
            output_path=output_path,
            exact_match=True
        )

        if success:
            print(f"✓ Downloaded to {output_path}")
        else:
            print("✗ Download failed")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Example 3: Download with partial name matching
def example_download_partial_match():
    """Example downloading a resource by partial name match."""
    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
    }

    try:
        client = CitrixVDIClient(cookies=cookies)

        # Download by partial name (case-insensitive)
        search_term = "ubuntu"
        output_path = "ubuntu.ica"

        print(f"Searching for resource containing '{search_term}'...")
        success = client.download_ica_file(
            resource_name=search_term,
            output_path=output_path,
            exact_match=False  # Enable partial matching
        )

        if success:
            print(f"✓ Downloaded to {output_path}")
        else:
            print("✗ Download failed")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Example 4: Find resource and inspect details
def example_find_resource():
    """Example finding a resource and inspecting its details."""
    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
    }

    try:
        client = CitrixVDIClient(cookies=cookies)

        # Find resource
        resource_name = "ADMIN03 Win11 Desktop"
        resource = client.find_resource_by_name(resource_name, exact_match=True)

        if resource:
            print(f"Found resource: {resource_name}")
            print(f"  ID: {resource.get('id')}")
            print(f"  Type: {'Desktop' if resource.get('isdesktop') else 'Application'}")
            print(f"  Description: {resource.get('description', 'N/A')}")
            print(f"  Launch URL: {resource.get('launchurl')}")
            print(f"  Path: {resource.get('path', 'N/A')}")
        else:
            print(f"Resource '{resource_name}' not found")

    except Exception as e:
        print(f"Error: {e}")


# Example 5: Download multiple resources
def example_download_multiple():
    """Example downloading multiple resources."""
    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
    }

    resource_list = [
        ("Admin03 - UBUNTU", "ubuntu.ica"),
        ("ADMIN03 Win11 Desktop", "windows.ica"),
        ("Duke Health Desktop", "health.ica"),
    ]

    try:
        client = CitrixVDIClient(cookies=cookies)

        for resource_name, output_path in resource_list:
            try:
                print(f"Downloading '{resource_name}'...")
                success = client.download_ica_file(resource_name, output_path)
                if success:
                    print(f"  ✓ Saved to {output_path}")
            except ValueError as e:
                print(f"  ✗ Skipped: {e}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    except Exception as e:
        print(f"Client initialization error: {e}")


# Example 6: Using environment variables
def example_with_env_vars():
    """Example using environment variables for cookies."""
    import os

    # Set environment variables (normally done in shell)
    os.environ['CITRIX_CSRF_TOKEN'] = 'YOUR_CSRF_TOKEN'
    os.environ['CITRIX_AUTH_ID'] = 'YOUR_AUTH_ID'

    try:
        # Client will automatically load from environment
        client = CitrixVDIClient()

        # Use the client
        resources = client.get_resources()
        print(f"Found {len(resources)} resources")

    except ValueError as e:
        print(f"Error: {e}")


# Example 7: Error handling
def example_error_handling():
    """Example with comprehensive error handling."""
    import requests

    cookies = {
        'CsrfToken': 'YOUR_CSRF_TOKEN',
        'CtxsAuthId': 'YOUR_AUTH_ID',
    }

    try:
        client = CitrixVDIClient(cookies=cookies)

        resource_name = "Nonexistent Resource"
        output_path = "output.ica"

        success = client.download_ica_file(resource_name, output_path)

    except ValueError as e:
        # Handle resource not found or validation errors
        print(f"Validation Error: {e}")

    except requests.HTTPError as e:
        # Handle HTTP errors (401, 403, 500, etc.)
        print(f"HTTP Error: {e}")

        if e.response.status_code in [401, 403]:
            print("Your cookies may have expired. Please refresh them.")

    except requests.ConnectionError:
        # Handle network connectivity issues
        print("Network Error: Unable to connect to Citrix server")

    except requests.Timeout:
        # Handle timeout errors
        print("Timeout Error: Request took too long")

    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected Error: {e}")


if __name__ == '__main__':
    print("=== CitrixVDIClient Examples ===\n")

    print("These are example functions demonstrating different usage patterns.")
    print("Uncomment the example you want to run and update the cookies.\n")

    # Uncomment to run examples:
    # example_with_cookies_dict()
    # example_download_exact_match()
    # example_download_partial_match()
    # example_find_resource()
    # example_download_multiple()
    # example_with_env_vars()
    # example_error_handling()

    print("To use these examples:")
    print("1. Update the cookies with your actual authentication cookies")
    print("2. Uncomment the example function you want to run")
    print("3. Run: python example_usage.py")
