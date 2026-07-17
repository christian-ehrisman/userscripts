# Duke Citrix Gateway Authentication Client

This project provides a Python client for automating authentication to Duke University's Citrix Gateway (`secure.citrix.duke.edu`) using SAML-based single sign-on through Duke's Shibboleth identity provider.

## Overview

The authentication flow involves multiple steps:

1. **Initial Access**: Navigate to `https://secure.citrix.duke.edu/`
2. **SAML Redirect**: Citrix Gateway redirects to Duke's Shibboleth IdP
3. **Credential Submission**: Submit Duke NetID username and password
4. **Multi-Factor Authentication**: Complete Duo MFA (push notification or passcode)
5. **SAML Response**: Shibboleth posts SAML response back to Citrix
6. **Session Establishment**: Citrix creates authenticated session with cookies

## API Endpoints Discovered

### Authentication Endpoints

#### Citrix Gateway (secure.citrix.duke.edu)
- `GET /` - Initial gateway access (redirects to SAML)
- `POST /nf/auth/getAuthenticationRequirements.do` - Get authentication requirements
- `GET /nf/auth/doSaml` - Initiate SAML authentication flow
- `POST /cgi/samlauth` - Receive SAML response and create session
- `GET /cgi/setclient` - Set client type
- `POST /Citrix/SECUREWeb/Authentication/GetAuthMethods` - Get available auth methods
- `POST /Citrix/SECUREWeb/GatewayAuth/Login` - Finalize gateway authentication

#### Duke Shibboleth IdP (shib.oit.duke.edu)
- `GET /idp/profile/SAML2/Redirect/SSO` - SAML SSO endpoint
- `GET /idp/authn/external` - External authentication page
- `POST /idp/authn/external` - Submit credentials and handle MFA

### Resource Management Endpoints

- `POST /Citrix/SECUREWeb/Resources/List` - List available applications and desktops
- `POST /Citrix/SECUREWeb/Home/Configuration` - Get configuration
- `POST /Citrix/SECUREWeb/Authentication/GetUserName` - Get authenticated username

### Session Management

- `POST /Citrix/SECUREWeb/ClientAssistant/GetDetectionTicket` - Get client detection ticket
- `POST /Citrix/SECUREWeb/ClientAssistant/GetDetectionStatus` - Check client detection status
- `POST /Citrix/SECUREWeb/Sessions/ListAvailable` - List available sessions

## Authentication Mechanism

### Cookies

The authentication relies on several critical cookies:

1. **NSC_AAAC** - Main Citrix Gateway session cookie (set after SAML authentication)
2. **CtxsAuthId** - Citrix Web authentication ID
3. **ASP.NET_SessionId** - ASP.NET session identifier
4. **CsrfToken** - CSRF protection token
5. **__Host-JSESSIONID** - Shibboleth session ID (during authentication)

### SAML Flow

The system uses SAML 2.0 for single sign-on:

1. Citrix acts as the Service Provider (SP)
2. Duke Shibboleth acts as the Identity Provider (IdP)
3. Browser is redirected with SAML request
4. User authenticates at IdP
5. IdP posts SAML response back to SP
6. SP validates response and creates session

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
# Install Playwright
pip install playwright

# Install Playwright browsers
playwright install chromium
```

## Usage

### Basic Usage (Interactive)

Run the script and follow the prompts:

```bash
python3 api_client.py
```

The script will:
1. Prompt for your Duke NetID
2. Prompt for your password (hidden input)
3. Open a browser window
4. Navigate to the Citrix Gateway
5. Submit your credentials
6. Wait for you to complete Duo MFA
7. Establish an authenticated session
8. Display available resources
9. Keep the browser open for inspection

### Programmatic Usage

Use the client in your own Python code:

```python
import asyncio
from api_client import CitrixGatewayClient

async def my_citrix_automation():
    async with CitrixGatewayClient(headless=False) as client:
        # Login (will prompt for credentials)
        success = await client.login()

        if success:
            # Get available resources
            resources = await client.get_available_resources()
            print(f"Found {len(resources)} resources")

            # Get session info
            session_info = await client.get_session_info()
            print(f"Authenticated: {session_info['authenticated']}")

asyncio.run(my_citrix_automation())
```

### Providing Credentials

#### Method 1: Interactive Prompts (Default)

```python
await client.login()  # Will prompt for username and password
```

#### Method 2: Direct Parameters

```python
await client.login(username="abc123", password="your_password")
```

#### Method 3: Environment Variables

```python
import os

username = os.getenv('DUKE_NETID')
password = os.getenv('DUKE_PASSWORD')
await client.login(username=username, password=password)
```

### Session Management

The client automatically saves authenticated sessions to `.citrix_session.json`. On subsequent runs, it will attempt to reuse the session if still valid:

```python
# Will try to load saved session first
await client.login(skip_if_authenticated=True)

# Force fresh login
await client.login(skip_if_authenticated=False)

# Manually save session
await client.save_session()

# Manually load session
await client.load_session()
```

### Headless Mode

For automation without GUI (MFA must be handled differently):

```python
client = CitrixGatewayClient(headless=True)
```

**Note**: Headless mode is challenging with Duo MFA since you need to see the push notification or enter a passcode. Consider using saved sessions for headless automation.

## API Reference

### `CitrixGatewayClient`

Main client class for Citrix Gateway authentication.

#### Constructor Parameters

- `headless` (bool): Run browser in headless mode (default: False)
- `timeout` (int): Page operation timeout in milliseconds (default: 60000)
- `session_file` (str): Path to save/load session cookies (default: ".citrix_session.json")

#### Methods

##### `async login(username, password, skip_if_authenticated) -> bool`

Perform login to Citrix Gateway.

**Parameters:**
- `username` (str, optional): Duke NetID (prompts if not provided)
- `password` (str, optional): Duke password (prompts if not provided)
- `skip_if_authenticated` (bool): Skip login if session valid (default: True)

**Returns:** `True` if login successful, `False` otherwise

##### `async verify_authentication() -> bool`

Verify current authentication status.

**Returns:** `True` if authenticated, `False` otherwise

##### `async get_available_resources() -> List[Dict]`

Get list of available Citrix resources (apps/desktops).

**Returns:** List of resource dictionaries

##### `async get_session_info() -> Dict`

Get current session information including cookies.

**Returns:** Dictionary with session details

##### `async save_session() -> None`

Save current session cookies to file.

##### `async load_session() -> bool`

Load session cookies from file.

**Returns:** `True` if loaded successfully, `False` otherwise

## Limitations and Considerations

### Multi-Factor Authentication

- **Duo MFA Required**: Duke uses Duo for MFA, which requires manual user interaction
- **MFA Timeout**: Default 120 seconds to complete MFA before timeout
- **Headless Challenges**: Headless mode is difficult with interactive MFA

### Session Persistence

- **Session Expiration**: Citrix sessions expire after inactivity
- **Cookie Lifetime**: Saved sessions may become invalid over time
- **Re-authentication**: May need to re-login periodically

### Browser Automation

- **Playwright Required**: This implementation requires Playwright and Chromium
- **Not Pure API**: Due to SAML/MFA, cannot use simple HTTP requests
- **Browser Overhead**: Running a full browser has resource implications

### Security Considerations

- **Credential Handling**: Never hardcode credentials in source code
- **Session File Security**: `.citrix_session.json` contains authentication cookies
- **MFA Security**: MFA approval is the primary security control
- **Network Security**: Ensure secure network when transmitting credentials

### Bot Detection

- **Minimal Risk**: Using real browser with Playwright bypasses most detection
- **User Agent**: Uses realistic Chrome user agent
- **SAML Flow**: Following standard SAML flow appears legitimate

## Troubleshooting

### Login Fails

1. **Verify Credentials**: Ensure Duke NetID and password are correct
2. **MFA Timeout**: Approve Duo push within 120 seconds
3. **Network Issues**: Check internet connectivity and VPN if required
4. **Session Conflicts**: Delete `.citrix_session.json` and try fresh login

### Resources Not Loading

1. **Check Authentication**: Verify `verify_authentication()` returns True
2. **Wait Longer**: Increase timeout values if network is slow
3. **Check Permissions**: Ensure your account has access to Citrix resources

### Browser Issues

1. **Chromium Not Installed**: Run `playwright install chromium`
2. **Display Issues**: Headless mode may require display configuration
3. **Permissions**: Ensure script has permission to launch browser

## Example Output

```
================================================================================
Duke Citrix Gateway Authentication Client
================================================================================

Duke NetID: abc123
Duke Password: ********
[INFO] Starting Citrix Gateway login process...
[INFO] Initializing browser...
[INFO] Browser initialized successfully
[INFO] Navigating to https://secure.citrix.duke.edu...
[INFO] Current URL: https://shib.oit.duke.edu/idp/authn/external?conversation=e1s1
[INFO] Redirected to Duke Shibboleth IdP
[INFO] Submitting credentials...
[INFO] Credentials submitted
================================================================================
MULTI-FACTOR AUTHENTICATION REQUIRED
================================================================================
Please approve the Duo push notification on your device
or enter your Duo passcode in the browser window.
Waiting up to 120 seconds for MFA completion...
================================================================================
[INFO] MFA completed successfully!
[INFO] Waiting for Citrix session establishment...
[INFO] Redirected to Citrix: https://secure.citrix.duke.edu/Citrix/SECUREWeb/
[INFO] Authentication verified
[INFO] Login successful!
[INFO] Session saved to .citrix_session.json

================================================================================
LOGIN SUCCESSFUL
================================================================================

Current URL: https://secure.citrix.duke.edu/Citrix/SECUREWeb/
Authenticated: True

Session cookies:
  NSC_AAAC: 91f6aedfb088b83802d62768585fc88109b181da945525d5f4...
  CtxsAuthId: EF6ABBAD9BE71CAED4D355145655B8DB...
  ASP.NET_SessionId: b50zfk1102tv11n1nrvqriql...

================================================================================
FETCHING AVAILABLE RESOURCES
================================================================================
Retrieved 1 resource(s)

================================================================================
Browser will remain open for inspection.
Press Enter to close the browser and exit...
================================================================================
```

## Advanced Usage

### Custom Timeout Values

```python
# Increase timeout for slow networks
client = CitrixGatewayClient(timeout=120000)  # 2 minutes

# Customize MFA timeout
async with CitrixGatewayClient() as client:
    await client.login()
    # MFA timeout is handled internally in wait_for_mfa()
```

### Error Handling

```python
async with CitrixGatewayClient() as client:
    try:
        success = await client.login(username="abc123", password="pwd")
        if not success:
            print("Login failed!")
            return

        resources = await client.get_available_resources()
        # Process resources...

    except Exception as e:
        print(f"Error occurred: {e}")
```

### Session Reuse Pattern

```python
# Day 1: Login and save session
async with CitrixGatewayClient() as client:
    await client.login()  # Saves session automatically

# Day 2: Reuse session (if still valid)
async with CitrixGatewayClient() as client:
    success = await client.login(skip_if_authenticated=True)
    # Will reuse saved session if valid, otherwise prompts for login
```

## Support

For issues or questions:
- Check Duke OIT documentation for Citrix Gateway access requirements
- Verify your account has appropriate permissions
- Contact Duke OIT support for access issues

## License

This code is provided as-is for educational and automation purposes.
