#!/usr/bin/env bash
set -e

echo ""
echo "  Checking Python installation..."
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] python3 not found. Please install Python 3.8+."
    exit 1
fi

echo "  Installing required packages..."
python3 -m pip install flask mysql-connector-python python-dateutil --quiet

echo ""
echo "  Starting Bank Application..."
echo ""
python3 "$(dirname "$0")/app.py"
