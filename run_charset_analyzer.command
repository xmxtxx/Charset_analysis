#!/bin/bash
# macOS Double-Click Launcher for CSV Charset Analyzer
# This file opens the web-based GUI in your browser
#
# SECURITY NOTICE: Your Mac may show security warnings for this file
# because it's an executable script from the internet. This is normal.
# To run: Right-click → Open (don't double-click first time)
# Then click "Open" when prompted about unidentified developer
#
# DISCLAIMER: No warranty provided - use at your own risk
# Always backup your data before running conversions

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 CSV Charset Analyzer"
echo "======================="
echo ""
echo "⚠️  DISCLAIMER: This software is provided AS IS without warranty."
echo "   No liability accepted for any damage or data loss."
echo "   Always backup your data before conversions!"
echo ""
echo "📁 Script location: $SCRIPT_DIR"

# Check if Python files exist
if [ ! -f "$SCRIPT_DIR/charset_web_gui.py" ]; then
    echo "❌ Error: charset_web_gui.py not found!"
    echo "Please make sure all files are in the same folder:"
    echo "  - charset_web_gui.py"
    echo "  - check_csv_charset.py" 
    echo "  - run_charset_analyzer.command (this file)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/check_csv_charset.py" ]; then
    echo "❌ Error: check_csv_charset.py not found!"
    echo "Please make sure all files are in the same folder."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if chardet is installed
echo "🔧 Checking dependencies..."
python3 -c "import chardet" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing chardet dependency..."
    pip3 install chardet
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install chardet. Please install manually:"
        echo "   pip3 install chardet"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo ""
echo "🚀 Starting CSV Charset Analyzer..."
echo "🌐 Your browser will open automatically"
echo ""
echo "💡 Instructions:"
echo "   1. Browser window will open with the interface"
echo "   2. Enter your CSV folder path in the interface"
echo "   3. Choose analysis options"
echo "   4. Click 'Start Analysis'"
echo ""
echo "⏹️  To stop: Close this window or press Ctrl+C"
echo ""

# Change to script directory and run
cd "$SCRIPT_DIR"
python3 charset_web_gui.py