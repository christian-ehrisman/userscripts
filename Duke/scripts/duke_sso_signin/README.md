# Duke Federated SSO Authentication Client

A Python client for authenticating with Duke University's federated Single Sign-On (SSO) system using SAML 2.0 and Duo MFA.

## Overview

This client reverse-engineers Duke's SSO authentication flow to provide a programmatic way to authenticate and obtain an authenticated session. It handles:

- SAML 2.0 authentication flow
- Shibboleth Identity Provider (IdP) integration
- Duo Multi-Factor Authentication (Push and Passcode)
- Session cookie management
- Automatic redirect handling

## Authentication Flow

The authentication process follows this sequence:

1. **Initiate SSO Flow**
   - Access Duke's MFA portal at `https://idms-mfa.oit.duke.edu/mfa/`
   - Get redirected to Shibboleth IdP with SAML request
   - Obtain conversation/execution ID

2. **Submit Credentials**
   - POST NetID and password to `/idp/authn/external`
   - Include Duo device selection

3. **Complete Duo MFA**
   - **Push**: Send push notification, poll for approval
   - **Passcode**: Submit one-time passcode from Duo app

4. **SAML Assertion Exchange**
   - Retrieve SAML response from IdP
   - POST SAML assertion to Service Provider
   - Obtain authenticated session cookies

5. **Access Protected Resources**
   - Use authenticated session for subsequent requests

## Installation

### Requirements

- Python 3.7+
- `requests` library

Install dependencies:

```bash
pip install requests
```

## Usage

### Interactive Mode

The simplest way to use the client is through interactive mode:

```bash
python api_client.py
```

You'll be prompted for:
- NetID (Duke username)
- Password
- Duo MFA method (Push or Passcode)
- Duo passcode (if using passcode method)

### Programmatic Usage

#### Example 1: Duo Push Authentication

```python
from api_client import DukeSSOClient

# Create client
client = DukeSSOClient()

# Authenticate with Duo push
success = client.authenticate(
    username="your_netid",
    password="your_password",
    duo_method="push"
)

if success:
    # Get authenticated session
    session = client.get_authenticated_session()

    # Use session for API calls
    response = session.get("https://idms-mfa.oit.duke.edu/mfa/home")
    print(f"Status: {response.status_code}")
```

#### Example 2: Duo Passcode Authentication

```python
from api_client import DukeSSOClient

client = DukeSSOClient()

# Authenticate with Duo passcode
success = client.authenticate(
    username="your_netid",
    password="your_password",
    duo_method="passcode",
    duo_passcode="123456"  # 6-digit code from Duo app
)

if success:
    session = client.get_authenticated_session()
    # Use the authenticated session
```

#### Example 3: Specify Duo Device

```python
from api_client import DukeSSOClient

client = DukeSSOClient()

# First, initiate SSO to see available devices
client.initiate_sso_flow()

# Then authenticate with specific device
success = client.authenticate(
    username="your_netid",
    password="your_password",
    duo_method="push",
    duo_device="push-DPND4BR6RJEDD0R20VT4"  # Specific device ID
)
```

## API Reference

### DukeSSOClient

Main client class for Duke SSO authentication.

#### Methods

##### `__init__()`
Initialize the SSO client with a requests session.

##### `initiate_sso_flow() -> Tuple[str, str]`
Initiate the SSO flow and retrieve the conversation ID.

**Returns:**
- Tuple of (conversation_id, login_page_url)

**Raises:**
- `Exception`: If SSO initiation fails

##### `authenticate(username: str, password: str, duo_method: str = "push", duo_device: Optional[str] = None, duo_passcode: Optional[str] = None) -> bool`

Authenticate with Duke SSO using credentials and Duo MFA.

**Parameters:**
- `username`: Duke NetID
- `password`: NetID password
- `duo_method`: Duo method - "push" or "passcode" (default: "push")
- `duo_device`: Duo device ID (optional, auto-selects if not provided)
- `duo_passcode`: Duo passcode (required if duo_method is "passcode")

**Returns:**
- `True` if authentication successful, `False` otherwise

**Raises:**
- `Exception`: If authentication fails

##### `get_authenticated_session() -> requests.Session`

Return the authenticated requests session.

**Returns:**
- Authenticated `requests.Session` object

**Raises:**
- `Exception`: If not authenticated

##### `test_authentication() -> bool`

Test if the current session is authenticated.

**Returns:**
- `True` if authenticated, `False` otherwise

## Security Considerations

⚠️ **Important Security Notes:**

1. **Credential Storage**: Never hardcode credentials in your scripts. Use environment variables or secure credential storage.

2. **Session Persistence**: Authenticated sessions are stored in memory. Be careful about sharing or logging session objects.

3. **MFA Requirement**: Duke requires Duo MFA for authentication. This is a security feature and cannot be bypassed.

4. **Cookie Security**: The authenticated session cookies are secure and HTTP-only. Don't expose them.

5. **HTTPS Only**: All communication uses HTTPS. Never disable SSL verification.

## Limitations

1. **Duo MFA Required**: You must have access to Duo MFA (push notification or passcode) to authenticate.

2. **Session Timeout**: Sessions will expire after a period of inactivity (typically 8 hours).

3. **Device Registration**: If using Duo push, your device must be registered with Duke's Duo system.

4. **Rate Limiting**: Excessive login attempts may trigger rate limiting or account lockout.

5. **Bot Detection**: Some Duke systems may have additional bot detection mechanisms.

## Troubleshooting

### "Could not extract conversation ID"

The SSO flow may have changed. Check if the initial redirect chain is working correctly.

```python
client = DukeSSOClient()
client.session.get("https://idms-mfa.oit.duke.edu/mfa/", allow_redirects=True)
# Check the response URL and cookies
```

### "Duo push timed out"

The Duo push notification times out after 60 seconds. Make sure you:
- Have access to your registered Duo device
- Approve the push notification promptly
- Check that your device is connected to the internet

### "No SAML form found"

The SAML response parsing may have failed. This could indicate:
- Authentication was not successful
- The SAML response format has changed
- Network issues during the SAML exchange

### "Session is not authenticated"

If `test_authentication()` returns `False`:
- Re-authenticate using `authenticate()`
- Check if the session cookies have expired
- Verify your credentials are correct

## Advanced Usage

### Custom Session Headers

```python
client = DukeSSOClient()

# Add custom headers
client.session.headers.update({
    'X-Custom-Header': 'value'
})

# Authenticate
client.authenticate(username="netid", password="password")
```

### Proxy Configuration

```python
client = DukeSSOClient()

# Configure proxy
client.session.proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'http://proxy.example.com:8080'
}
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = DukeSSOClient()
# Authentication with verbose output
```

## Technical Details

### Endpoints

- **MFA Portal**: `https://idms-mfa.oit.duke.edu/mfa/`
- **Shibboleth IdP**: `https://shib.oit.duke.edu/idp/`
- **Authentication Endpoint**: `https://shib.oit.duke.edu/idp/authn/external`
- **SAML Consumer**: `https://idms-mfa.oit.duke.edu/Shibboleth.sso/SAML2/POST`

### Key Cookies

- `__Host-JSESSIONID`: Shibboleth session ID
- `_shibsession_*`: Shibboleth SP session cookie
- `mfa`: Duke MFA authentication token
- `_opensaml_req_*`: SAML request state

### Request Flow

```
GET /mfa/
  ↓ (302 redirect)
GET /mfa/home
  ↓ (302 redirect with SAMLRequest)
GET /idp/profile/SAML2/Redirect/SSO?SAMLRequest=...
  ↓ (302 redirect with execution ID)
GET /idp/profile/SAML2/Redirect/SSO?execution=e1s1
  ↓ (302 redirect with conversation ID)
GET /idp/authn/external?conversation=e1s1
  ↓ (Load login page)
POST /idp/authn/external
  ↓ (Submit credentials + Duo)
  ↓ (Poll for Duo approval)
POST /idp/authn/external
  ↓ (302 redirect after approval)
GET /idp/profile/SAML2/Redirect/SSO?execution=e1s1&_eventId_proceed=1
  ↓ (Get SAML response)
POST /Shibboleth.sso/SAML2/POST
  ↓ (Submit SAML assertion)
  ↓ (302 redirect)
GET /mfa/home
  ✓ (Authenticated!)
```

## License

This code is provided as-is for educational and research purposes. Use responsibly and in accordance with Duke University's acceptable use policies.

## Contributing

This client was reverse-engineered from network traffic. If Duke updates their SSO flow, the client may need updates. Please report issues or contribute improvements.

## Changelog

### Version 1.0.0 (2026-02-13)
- Initial release
- Support for Duo Push and Passcode authentication
- SAML 2.0 flow handling
- Session management
- Interactive and programmatic modes
