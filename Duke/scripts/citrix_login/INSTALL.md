# Installation Guide

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install Playwright directly:

```bash
pip install playwright
```

## Step 2: Install Playwright Browsers

After installing the Python package, you need to install the browser binaries:

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright will use.

## Step 3: Verify Installation

Test that everything is installed correctly:

```bash
python3 -c "from playwright.async_api import async_playwright; print('✓ Playwright installed successfully')"
```

## Step 4: Run the Client

```bash
python3 api_client.py
```

## Troubleshooting

### ModuleNotFoundError: No module named 'playwright'

Run: `pip install playwright`

### Browser not found

Run: `playwright install chromium`

### Permission Denied

On macOS, you may need to grant terminal permissions to access the browser.

### Display Issues (Linux Headless)

If running on a headless Linux server, you may need to install dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

Or run: `playwright install-deps chromium`
