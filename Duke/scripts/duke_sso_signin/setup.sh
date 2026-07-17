#!/bin/bash
#
# Setup script for Duke SSO Authentication Client
#
# This script sets up the Python virtual environment and installs dependencies.
#

set -e  # Exit on error

echo "========================================"
echo "Duke SSO Client - Setup"
echo "========================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if venv exists
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists"
    read -p "Remove and recreate? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "  Removing old virtual environment..."
        rm -rf venv
    else
        echo "  Using existing virtual environment"
    fi
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "✓ Dependencies installed"

# Test import
echo "Testing installation..."
python3 -c "from api_client import DukeSSOClient; print('✓ Import successful')"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the interactive client:"
echo "     python api_client.py"
echo ""
echo "  3. Or run the test suite:"
echo "     python test_flow.py"
echo ""
echo "  4. See example_usage.py for more examples"
echo ""
