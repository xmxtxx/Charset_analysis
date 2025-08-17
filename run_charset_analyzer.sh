#!/bin/bash
# Linux Double-Click Launcher for CSV Charset Analyzer
# This file opens the web-based GUI in your browser
#
# SECURITY NOTICE: You may need to make this file executable first:
# chmod +x run_charset_analyzer.sh
# Some file managers require manual execution permission
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
    echo "  - run_charset_analyzer.sh (this file)"
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
    
    # Try different installation methods
    if command -v pip3 &> /dev/null; then
        pip3 install chardet
    elif command -v pip &> /dev/null; then
        pip install chardet
    else
        echo "❌ pip not found. Please install chardet manually:"
        echo "   sudo apt install python3-chardet  # Ubuntu/Debian"
        echo "   sudo dnf install python3-chardet  # Fedora"
        echo "   pip3 install chardet              # General"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install chardet. Please install manually."
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