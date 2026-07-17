# Quick Start Guide - Duke SSO Authentication

Get started with Duke SSO authentication in 3 minutes!

## Setup (One-Time)

```bash
# 1. Navigate to the directory
cd /Users/christian/.reverse-api/runs/scripts/fa87b57d9445

# 2. Run setup script
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate
```

## Usage

### Option 1: Interactive Mode (Recommended)

```bash
python api_client.py
```

Then follow the prompts:
1. Enter your NetID
2. Enter your password
3. Select Duo method (Push or Passcode)
4. Approve on your phone (if using Push)

### Option 2: Programmatic Use

```python
from api_client import DukeSSOClient

# Create client
client = DukeSSOClient()

# Authenticate
success = client.authenticate(
    username="your_netid",
    password="your_password",
    duo_method="push"  # or "passcode"
)

# Use authenticated session
if success:
    session = client.get_authenticated_session()
    response = session.get("https://idms-mfa.oit.duke.edu/mfa/home")
    print(f"Status: {response.status_code}")
```

### Option 3: Environment Variables

```bash
# Set credentials
export DUKE_NETID=your_netid
export DUKE_PASSWORD=your_password

# Run
python example_usage.py
# Select option 2
```

## Testing (Without Credentials)

```bash
# Run test suite
python test_flow.py
```

Expected output:
```
✓ PASSED: SSO Initialization
✓ PASSED: Cookie Handling
✓ PASSED: Duo Parsing
✓ PASSED: Session Methods

4/4 tests passed
```

## Common Use Cases

### Just Need to Login Once

```bash
python api_client.py
```

### Need to Automate Regular Logins

1. Store credentials in environment variables
2. Use programmatic API in your script
3. Handle Duo MFA (push or passcode)

### Building an Integration

See `example_usage.py` for:
- Session reuse
- Error handling
- Custom Duo device selection
- Multiple request patterns

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | Run `./setup.sh` or `pip install -r requirements.txt` |
| "Duo push timed out" | Approve faster or use passcode method |
| "Authentication failed" | Check credentials, ensure Duo is registered |
| "Session expired" | Re-authenticate by calling `client.authenticate()` again |

## Files Overview

| File | Purpose | When to Use |
|------|---------|-------------|
| `api_client.py` | Main client | Import this in your code |
| `example_usage.py` | Examples | Learn different usage patterns |
| `test_flow.py` | Tests | Verify setup without credentials |
| `README.md` | Full docs | Complete API reference |
| `ANALYSIS.md` | Technical details | Understand the implementation |

## Quick Examples

### Example 1: Login and Get Session

```python
from api_client import interactive_login

client = interactive_login()
if client:
    session = client.get_authenticated_session()
    # Use session for requests
```

### Example 2: Duo Passcode

```python
from api_client import DukeSSOClient

client = DukeSSOClient()
client.authenticate(
    username="netid",
    password="password",
    duo_method="passcode",
    duo_passcode="123456"  # From Duo app
)
```

### Example 3: Test Session

```python
client = DukeSSOClient()
# ... authenticate ...

if client.test_authentication():
    print("Still logged in!")
else:
    print("Need to re-authenticate")
```

## Next Steps

1. ✅ Run `./setup.sh`
2. ✅ Test with `python test_flow.py`
3. ✅ Try interactive mode: `python api_client.py`
4. ✅ Check examples: `python example_usage.py`
5. ✅ Read full docs: `README.md`

## Need Help?

- **Technical details**: See `ANALYSIS.md`
- **API reference**: See `README.md`
- **Examples**: See `example_usage.py`
- **Issues**: Check "Troubleshooting" section above

---

**Ready to start?** Run: `./setup.sh && python api_client.py`
