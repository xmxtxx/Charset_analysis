Here’s the adjusted **README.md** reflecting the new parallel processing, job limit, fast mode, and sampling options:

---

# CSV Character Encoding Detection Tool

A Python script for detecting and analyzing character encodings of CSV files across multiple customer folders with **real-time progress tracking** and **parallel processing**.

## 🎯 Purpose

This tool analyzes CSV files stored in a structured folder hierarchy to detect their character encodings. It provides both per-customer and overall encoding distribution statistics, helping identify encoding inconsistencies across large datasets **much faster** thanks to multiprocessing.

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

* Top-level directory contains customer folders
* Customer folders follow the pattern: `CustomerNR_Customer` (e.g., `0000000000000_customer1`)
* CSV files are located in a `bak` subfolder within each customer folder

## 🚀 Quick Start

### Installation

1. Ensure Python 3.6+ is installed:

```bash
python3 --version
```

2. Install the required dependency (fast optional alternative: `cchardet`):

```bash
pip3 install chardet
# Or faster:
pip3 install cchardet
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

* **Real-time Progress Bar**: Shows ETA, elapsed time, and current file
* **Parallel Processing**: Uses multiple CPU cores for faster detection
* **Job Limit Safety**: Caps excessive job counts automatically with an info message
* **Multi-level Analysis**: Per-customer and overall encoding distribution
* **Color-coded Output**: Easy-to-read terminal output with color indicators
* **Error Handling**: Gracefully handles read errors and missing files
* **Confidence Scoring**: Shows detection confidence for each encoding
* **Performance Optimized**: Intelligent sampling for large files + `--fast` mode for even quicker scans

## 🛠️ Command Line Options

| Option                  | Description                                                                      | Example                                                  |
| ----------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `directory`             | Top-level directory to analyze (default: current)                                | `python3 check_csv_charset.py data`                      |
| `-s, --summary-only`    | Show only overall summary                                                        | `python3 check_csv_charset.py data -s`                   |
| `-d, --details`         | Show detailed information per folder                                             | `python3 check_csv_charset.py data -d`                   |
| `--bak <folder>`        | Specify different backup folder name                                             | `python3 check_csv_charset.py data --bak backup`         |
| `--no-progress`         | Disable progress bar                                                             | `python3 check_csv_charset.py data --no-progress`        |
| `--pattern <type>`      | Filter folders (`underscore` or `all`)                                           | `python3 check_csv_charset.py data --pattern all`        |
| `-j, --jobs <n>`        | Number of parallel workers (default: CPU count, capped at 2×CPU and total files) | `python3 check_csv_charset.py data -j 8`                 |
| `--fast`                | Faster single-pass detection (less I/O, slightly lower accuracy)                 | `python3 check_csv_charset.py data --fast`               |
| `--sample-size <bytes>` | Sample size per pass in bytes (default: 65536)                                   | `python3 check_csv_charset.py data --sample-size 131072` |

> **ℹ Note:** If you set `-j` too high (e.g., `-j 100`), the script will automatically cap it to a safe limit and inform you.

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
ℹ Limiting jobs from 100 to 16 (CPU=8, files=245) for stability

Processing CSV files: [████████████████████████████████████████████████] 245/245 (100.0%) ETA: 0s Elapsed: 41s Complete!

Encoding Distribution customer1:
  UTF-8: 45 files (75.0%)
  ISO-8859-1: 15 files (25.0%)

...

══════════════════════════════════════════════════
OVERALL SUMMARY
══════════════════════════════════════════════════
Total folders analyzed: 12
Total CSV files processed: 245
Successfully detected: 245
Detection success rate: 100.0%
Total runtime: 41s

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

* 🟢 **Green**: UTF-8 (recommended encoding)
* 🔵 **Blue**: ASCII
* 🟡 **Yellow**: ISO-8859, Windows encodings
* 🟣 **Magenta**: Other encodings
* 🔴 **Red**: Errors or detection failures

## 🔒 Security & Privacy

* **100% Local Processing** – No data leaves your computer
* **No Network Connections**
* **Read-Only Access** – Only reads files, never modifies them

## 📋 Requirements

* **Python**: 3.6 or higher
* **Dependencies**: `chardet` or `cchardet`
* **OS**: Linux (including WSL), macOS, or Windows
* **Memory**: Scales with file size (typically < 100MB)

## 💡 Tips

1. **Maximum Speed**: Use `-j <cores>` or higher for I/O-heavy datasets, but the script will auto-cap extreme values.
2. **Fast Mode**: Use `--fast` for large datasets when you just need a rough check.
3. **Larger Samples**: Use `--sample-size` if your files have encoding markers beyond the default 64KB.
4. **Automation**: Integrate into data pipelines or scheduled validation tasks.

---

*For questions or issues, please refer to the inline script documentation or run with `-h` for help.*
