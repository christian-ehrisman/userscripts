# Citrix VDI Connection File Downloader

A Python client for downloading Citrix VDI connection files (.ica) by resource name from the Duke University Citrix infrastructure.

## Overview

This script allows you to programmatically download Citrix VDI connection files without manually navigating through the web interface. It's designed to work with pre-authenticated sessions (SSO handled externally).

## APIs Discovered

The following Citrix Receiver for Web APIs were identified:

### 1. Resources List API
- **Endpoint**: `POST https://secure.citrix.duke.edu/Citrix/SECUREWeb/Resources/List`
- **Purpose**: Retrieves all available Citrix resources (desktops and applications)
- **Response**: JSON containing resource details including names, types, launch URLs, and metadata

### 2. Launch ICA API
- **Endpoint**: `GET https://secure.citrix.duke.edu/Citrix/SECUREWeb/Resources/LaunchIca/{encoded_id}.ica`
- **Purpose**: Downloads the .ica connection file for a specific resource
- **Query Parameters**:
  - `CsrfToken`: CSRF protection token
  - `IsUsingHttps`: Set to "Yes"
  - `displayNameDesktopTitle`: Display name of the resource
  - `launchId`: Timestamp-based launch identifier

## Authentication

**Important**: This script does NOT handle SSO authentication. It requires pre-authenticated cookies from an existing browser session.

### Required Cookies

- `CsrfToken`: CSRF protection token (also sent as HTTP header)
- `CtxsAuthId`: Main authentication identifier
- `CtxsDeviceId`: Device identifier (optional but recommended)
- `ASP.NET_SessionId`: ASP.NET session cookie (optional but recommended)
- `NSC_AAAC`: Load balancer cookie (optional but recommended)

### How to Obtain Cookies

You can extract cookies from your browser after logging in to the Citrix portal:

1. **Using Browser DevTools**:
   - Log in to https://secure.citrix.duke.edu/
   - Open Developer Tools (F12)
   - Go to Application/Storage → Cookies
   - Copy the required cookie values

2. **Using Browser Extensions**:
   - Install a cookie export extension (e.g., "EditThisCookie" or "Cookie-Editor")
   - Export cookies as JSON

3. **Using Python with Selenium/Playwright** (if you want to automate login):
   - Automate the SSO flow
   - Extract cookies after successful authentication
   - Pass them to this script

## Installation

### Requirements

- Python 3.7+
- `requests` library

### Setup

```bash
# Clone or download the script
cd /path/to/script

# Install dependencies
pip install requests

# Make executable (optional)
chmod +x api_client.py
```

## Usage

### Method 1: Environment Variables

Set cookies via environment variable:

```bash
# Export cookies as JSON
export CITRIX_COOKIES='{"CsrfToken": "YOUR_TOKEN", "CtxsAuthId": "YOUR_AUTH_ID", "CtxsDeviceId": "YOUR_DEVICE_ID", "ASP.NET_SessionId": "YOUR_SESSION_ID", "NSC_AAAC": "YOUR_NSC_AAAC"}'

# List all available resources
python api_client.py --list-resources

# Download a specific resource
python api_client.py --resource-name "Admin03 - UBUNTU" --output desktop.ica
```

Or set individual environment variables:

```bash
export CITRIX_CSRF_TOKEN="YOUR_CSRF_TOKEN"
export CITRIX_AUTH_ID="YOUR_AUTH_ID"
export CITRIX_DEVICE_ID="YOUR_DEVICE_ID"
export CITRIX_SESSION_ID="YOUR_SESSION_ID"
export CITRIX_NSC_AAAC="YOUR_NSC_AAAC"

python api_client.py --resource-name "ADMIN03 Win11 Desktop"
```

### Method 2: Cookies File

Save your cookies to a JSON file:

```json
{
  "CsrfToken": "BFA45B341B4ED42CD4E4F7E4C9180025",
  "CtxsAuthId": "396FAB10C6E7BB0A81BC9B02A7B873FB",
  "CtxsDeviceId": "WR_idmsMaesuoR4",
  "ASP.NET_SessionId": "wfxskn4zz5schn3ob21ffl4d",
  "NSC_AAAC": "7f338d6dcbc1eaca43bb52891e79a6c609b18313f45525d5f4f58455e445a4a42"
}
```

Then use it:

```bash
python api_client.py --cookies-file cookies.json --resource-name "Duke Health Desktop"
```

### Command-Line Options

```
usage: api_client.py [-h] [--resource-name RESOURCE_NAME] [--output OUTPUT]
                     [--list-resources] [--partial-match]
                     [--cookies-file COOKIES_FILE] [--verbose]

Download Citrix VDI connection files by resource name

optional arguments:
  -h, --help            show this help message and exit
  --resource-name RESOURCE_NAME, -r RESOURCE_NAME
                        Name of the Citrix resource to download
  --output OUTPUT, -o OUTPUT
                        Output path for the .ica file (default: <resource-name>.ica)
  --list-resources, -l  List all available resources
  --partial-match, -p   Use partial name matching instead of exact match
  --cookies-file COOKIES_FILE, -c COOKIES_FILE
                        Path to JSON file containing cookies
  --verbose, -v         Enable verbose logging
```

## Examples

### List All Available Resources

```bash
python api_client.py --list-resources
```

Output:
```
================================================================================
AVAILABLE CITRIX RESOURCES
================================================================================

1. Admin03 - UBUNTU
   Type: Desktop
   Description: Admin03 - UBUNTU

2. ADMIN03 Win11 Desktop
   Type: Desktop
   Description: DG-ADMIN-CORE-WIN11

3. Duke Health Desktop
   Type: Desktop

4. Command Prompt
   Type: Application
   ...
```

### Download by Exact Name

```bash
# Download with exact resource name
python api_client.py --resource-name "Admin03 - UBUNTU" --output ubuntu.ica
```

### Download by Partial Name

```bash
# Find resource containing "ubuntu" (case-insensitive)
python api_client.py --resource-name "ubuntu" --partial-match
```

### Verbose Mode

```bash
# Enable verbose logging for debugging
python api_client.py --resource-name "Duke Health Desktop" --verbose
```

## Programmatic Usage

You can also use the `CitrixVDIClient` class in your own Python scripts:

```python
from api_client import CitrixVDIClient

# Initialize with cookies
cookies = {
    'CsrfToken': 'YOUR_TOKEN',
    'CtxsAuthId': 'YOUR_AUTH_ID',
    # ... other cookies
}

client = CitrixVDIClient(cookies=cookies)

# List all resources
resources = client.get_resources()
for resource in resources:
    print(f"{resource['name']} - {resource.get('description', 'N/A')}")

# Find a specific resource
resource = client.find_resource_by_name("Admin03 - UBUNTU")
if resource:
    print(f"Found: {resource['name']}")

# Download an ICA file
success = client.download_ica_file(
    resource_name="ADMIN03 Win11 Desktop",
    output_path="windows_desktop.ica"
)

if success:
    print("Download successful!")
```

## Limitations and Caveats

1. **Cookie Expiration**: Cookies have a limited lifetime. If you get authentication errors, refresh your browser session and extract new cookies.

2. **No SSO Handling**: This script does NOT perform the SSO login flow. You must obtain cookies from an authenticated session.

3. **Session Validation**: Some cookies (like `CtxsAuthId`) may expire after a period of inactivity.

4. **Network Access**: You must have network access to `secure.citrix.duke.edu`.

5. **Resource Availability**: The script can only download resources that are available to your account.

6. **ICA File Usage**: The downloaded .ica file still requires Citrix Receiver/Workspace to be installed on your machine to launch the VDI session.

## Troubleshooting

### Authentication Errors

If you receive 401 or 403 errors:

1. Verify your cookies are current (log in to the web portal again)
2. Export fresh cookies from your browser
3. Ensure you've copied all required cookies correctly

### Resource Not Found

If the script can't find your resource:

1. List all resources first: `python api_client.py --list-resources`
2. Copy the exact resource name
3. Use the exact name or try `--partial-match`

### Connection Errors

If you get network/timeout errors:

1. Verify you're on the Duke network or VPN
2. Check that `secure.citrix.duke.edu` is accessible
3. Try with `--verbose` to see detailed logs

## API Response Formats

### Resources List Response

```json
{
  "isSubscriptionEnabled": true,
  "isUnauthenticatedStore": false,
  "resources": [
    {
      "id": "DefaultAggregationGroup.\\Admin03 - UBUNTU",
      "name": "Admin03 - UBUNTU",
      "description": "Admin03 - UBUNTU",
      "isdesktop": true,
      "launchurl": "Resources/LaunchIca/RGVmYXVsdEFnZ3JlZ2F0aW9uR3JvdXAuXEFkbWluMDMgLSBVQlVOVFU-.ica",
      "iconurl": "Resources/Icon/...",
      "path": "\\\\",
      "clienttypes": ["ica30", "rdp"],
      "desktopassignmenttype": "assigned",
      "subscriptionstatus": "subscribed"
    }
  ]
}
```

### ICA File Format

The downloaded .ica file is a text-based configuration file in INI format:

```ini
[Encoding]
InputEncoding=UTF8

[WFClient]
Version=2
...

[ApplicationServers]
Desktop=
...
```

## Security Notes

⚠️ **Important Security Considerations**:

- **Never commit cookies to version control**
- **Cookies are sensitive credentials** - treat them like passwords
- **Use environment variables or secure credential storage**
- **Rotate cookies regularly** by logging out and back in
- **Consider using a secrets manager** for production use

## License

This script is provided as-is for educational and automation purposes.

## Support

For issues related to:
- **Citrix access**: Contact Duke OIT
- **Script functionality**: Check the troubleshooting section above
- **SSO/Authentication**: This is handled externally - consult your SSO documentation
