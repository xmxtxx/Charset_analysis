# CSV Character Encoding Detection Tool

A Python script for detecting and analyzing character encodings of CSV files across multiple customer folders with real-time progress tracking.

## 🎯 Purpose

This tool analyzes CSV files stored in a structured folder hierarchy to detect their character encodings. It provides both per-customer and overall encoding distribution statistics, helping identify encoding inconsistencies across large datasets.

## 📁 Expected Folder Structure

```
data/
├── CustomerNR_Customer/
│   └── bak/
│       ├── file1.csv
│       ├── file2.csv
│       └── ...
├── CustomerNR_Customer/
│   └── bak/
│       └── *.csv files
└── ...
```

- Top-level directory contains customer folders
- Customer folders follow the pattern: `CustomerNR_Customer` (e.g., `0000000000000_customer1`)
- CSV files are located in a `bak` subfolder within each customer folder

## 🚀 Quick Start

### Installation

1. Ensure Python 3.6+ is installed:
```bash
python3 --version
```

2. Install the required dependency:
```bash
pip3 install chardet
```

### Basic Usage

```bash
# Analyze current directory
python3 check_csv_charset.py

# Analyze specific directory
python3 check_csv_charset.py /path/to/data

# Common usage with data folder
python3 check_csv_charset.py data
```

## 📊 Features

- **Real-time Progress Bar**: Visual feedback showing processing status, ETA, and current file
- **Multi-level Analysis**: Per-customer and overall encoding distribution
- **Color-coded Output**: Easy-to-read terminal output with color indicators
- **Error Handling**: Gracefully handles read errors and missing files
- **Confidence Scoring**: Shows detection confidence for each encoding
- **Performance Optimized**: Intelligent sampling for large files

## 🛠️ Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `directory` | Top-level directory to analyze (default: current) | `python3 check_csv_charset.py data` |
| `-s, --summary-only` | Show only overall summary | `python3 check_csv_charset.py data -s` |
| `-d, --details` | Show detailed information per folder | `python3 check_csv_charset.py data -d` |
| `--bak <folder>` | Specify different backup folder name | `python3 check_csv_charset.py data --bak backup` |
| `--no-progress` | Disable progress bar | `python3 check_csv_charset.py data --no-progress` |
| `--pattern <type>` | Filter folders (`underscore` or `all`) | `python3 check_csv_charset.py data --pattern all` |

## 📈 Output Examples

### Standard Output
```
==============================================================
CSV Character Encoding Detection
==============================================================
📁 Top directory: /home/user/data
📂 CSV location: */bak/*.csv
──────────────────────────────────────────────────────────────

Scanning folders...
Found 245 CSV files in 12 folders

Processing CSV files: [████████████████████████████████████████████████] 245/245 (100.0%) Complete!

Encoding Distribution customer1:
  UTF-8: 45 files (75.0%)
  ISO-8859-1: 15 files (25.0%)

Encoding Distribution customer2:
  ascii: 23 files (41.8%)
  ISO-8859-1: 31 files (56.4%)
  ISO-8859-9: 1 files (1.8%)

══════════════════════════════════════════════════
OVERALL SUMMARY
══════════════════════════════════════════════════
Total folders analyzed: 12
Total CSV files processed: 245
Successfully detected: 245
Detection success rate: 100.0%

Overall Encoding Distribution:
  UTF-8: 120 files (49.0%)
  ISO-8859-1: 80 files (32.7%)
  ascii: 45 files (18.4%)
```

### Summary Only Mode (`-s`)
Shows only the overall summary without per-customer details.

### Detailed Mode (`-d`)
Includes additional information like folder paths and total file counts per customer.

## 🎨 Color Coding

The output uses colors to indicate different encoding types:
- 🟢 **Green**: UTF-8 (recommended encoding)
- 🔵 **Blue**: ASCII
- 🟡 **Yellow**: ISO-8859, Windows encodings
- 🟣 **Magenta**: Other encodings
- 🔴 **Red**: Errors or detection failures

## 🔒 Security & Privacy

- **100% Local Processing**: No data leaves your computer
- **No Network Connections**: Works completely offline
- **No External Services**: All processing happens on your machine
- **Read-Only Access**: Only reads files, never modifies them

## 📋 Requirements

- **Python**: 3.6 or higher
- **Dependencies**: `chardet` library
- **Operating System**: Linux (WSL), macOS, or Windows
- **Disk Space**: Minimal (script size < 20KB)
- **Memory**: Scales with file size (typically < 100MB)

## 🐛 Troubleshooting

### chardet not installed
```bash
# Install via pip
pip3 install chardet

# Or system-wide (Ubuntu/Debian)
sudo apt-get install python3-chardet
```

### Permission denied errors
```bash
# Make script executable
chmod +x check_csv_charset.py

# Check file permissions
ls -la data/*/bak/*.csv
```

### No CSV files found
- Verify folder structure matches expected pattern
- Check if CSV files are in `bak` folders
- Use `--pattern all` to include all folders
- Try different backup folder name with `--bak`

## 📊 Encoding Statistics Interpretation

| Encoding | Description | Compatibility |
|----------|-------------|---------------|
| **UTF-8** | Universal encoding, supports all languages | ✅ Recommended |
| **ASCII** | Basic English characters only | ⚠️ Limited |
| **ISO-8859-1** | Western European languages | ⚠️ Regional |
| **Windows-1252** | Windows Western European | ⚠️ Platform-specific |
| **MacRoman** | Legacy Mac encoding | ❌ Deprecated |


## 📄 License

This tool is provided as-is for data analysis purposes.

## 💡 Tips

1. **Large Datasets**: For folders with thousands of files, consider using `--no-progress` and redirecting output to a file:
   ```bash
   python3 check_csv_charset.py data --no-progress > encoding_report.txt
   ```

2. **Quick Overview**: Use `-s` flag for a quick summary when you don't need per-customer details

3. **Verification**: Use `-d` flag to identify specific problematic folders with encoding issues

4. **Automation**: Can be integrated into data validation pipelines or scheduled tasks

---

*For questions or issues, please refer to the inline script documentation or run with `-h` for help.*
