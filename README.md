# CSV Character Encoding Detection & Conversion Tool

Detect, analyze, and **convert** character encodings of CSV files across many folders — **fast**, **parallel**, and **fully offline**. Now with encoding conversion and rollback support!

---

## 🎯 What it does

* **Detects** encoding of CSV files (UTF-8, ISO-8859-*, Windows-125x, UTF-16/32, ASCII)
* **Converts** files between encodings with automatic backup
* **Rollback** feature to undo conversions using backup files
* Parallel processing with smart job management
* Per-folder and overall statistics with success rates
* **100% offline** - no network calls, read-only by default

---

## ✨ New Features

### 🔄 **Encoding Conversion**
Convert your CSV files to a standard encoding with safety features:
- Automatic `.bak` backup creation
- Dry-run mode to preview changes
- Filter by source encoding
- Detailed conversion reports

### ↩️ **Rollback Support**
Made a mistake? Instantly restore from backups:
```bash
python3 check_csv_charset.py /path/to/data --rollback
```

---

## 📁 Flexible Folder Structure

```
top/
├── AnyFolder1/
│   └── ... (CSV files anywhere if --csv-mode any)
├── AnyFolder2/
│   └── <csv_dir>/ (if --csv-mode subdir, e.g., "bak")
│       └── *.csv
└── ...
```

---

## 🚀 Quick Start

### Installation
```bash
# Install an encoding detector (choose one)
pip3 install chardet      # standard
pip3 install cchardet     # faster (optional)
```

### Basic Usage
```bash
# Detect encodings in current directory
python3 check_csv_charset.py

# Detect in specific directory
python3 check_csv_charset.py ~/data

# Convert all files to UTF-8 (with preview)
python3 check_csv_charset.py ~/data --convert-to utf-8 --dry-run

# Actually convert files
python3 check_csv_charset.py ~/data --convert-to utf-8

# Rollback if something went wrong
python3 check_csv_charset.py ~/data --rollback
```

---

## 🛠️ Command Options

### Core Options
| Option | Description | Default |
|--------|-------------|---------|
| `directory` | Top directory to scan | `.` |
| `--csv-mode {any,subdir}` | Where to look for CSVs | `any` |
| `--bak <name>` | Subfolder name when using subdir mode | `bak` |
| `-j, --jobs <n>` | Parallel workers | half cores |
| `--fast` | Single-pass detection (less I/O) | off |
| `--sample-size <bytes>` | Bytes to sample per pass | `65536` |

### Display Options
| Option | Description |
|--------|-------------|
| `-d, --details` | Show detailed folder information |
| `-s, --summary-only` | Only show overall summary |
| `--no-progress` | Disable progress bar |
| `--pattern {all,underscore}` | Filter folders by name pattern |
| `--name-delims "<chars>"` | Characters for display name extraction |

### 🔄 Conversion Options
| Option | Description |
|--------|-------------|
| `--convert-to {encoding}` | Target encoding (utf-8, utf-8-sig, ascii, iso-8859-1, windows-1252) |
| `--dry-run` | Preview changes without modifying files |
| `--no-backup` | Skip creating .bak files (dangerous!) |
| `--convert-filter <encoding>` | Only convert files with specific source encoding |
| `--rollback` | Restore all .bak files to original |

---

## 📊 Example Workflows

### 1. Analyze and Fix Mixed Encodings
```bash
# First, see what you're dealing with
python3 check_csv_charset.py /data/customers

# Preview conversion of ISO-8859-1 files only
python3 check_csv_charset.py /data/customers \
    --convert-to utf-8 \
    --convert-filter iso-8859-1 \
    --dry-run

# Do the actual conversion
python3 check_csv_charset.py /data/customers \
    --convert-to utf-8 \
    --convert-filter iso-8859-1

# If something went wrong, rollback
python3 check_csv_charset.py /data/customers --rollback
```

### 2. Fast Scan of Large Dataset
```bash
# Use more cores and fast mode for quick overview
python3 check_csv_charset.py /bigdata \
    --fast \
    -j 16 \
    --summary-only
```

### 3. Convert Everything to UTF-8
```bash
# Safely convert all CSV files
python3 check_csv_charset.py /project \
    --convert-to utf-8 \
    --dry-run  # Always preview first!

# If happy with preview, run conversion
python3 check_csv_charset.py /project --convert-to utf-8
```

---

## 🎨 Output Example

```
============================================================
CSV Character Encoding Detection
============================================================
📁 Top directory: /home/user/data
🔎 CSV search: **/*.csv (recursive under each subfolder)
────────────────────────────────────────────────────────────

Processing CSV files: [████████████] 1250/1250 (100.0%)

Encoding Distribution CustomerA:
  UTF-8: 120 files (80.0%)
  ISO-8859-1: 30 files (20.0%)

────────────────────────────────────────────────────────────
Starting Encoding Conversion to utf-8
Creating .bak backups for all converted files
────────────────────────────────────────────────────────────

Converting in CustomerA...
  ✓ data_001.csv: iso-8859-1 → utf-8
  ✓ data_002.csv: iso-8859-1 → utf-8
  [SKIP] data_003.csv - already utf-8

══════════════════════════════════════════════════
CONVERSION SUMMARY → UTF-8
══════════════════════════════════════════════════
Successfully converted: 30 files
Already in target encoding: 120 files

✅ Analysis complete!
```

---

## 🔒 Safety Features

* **Automatic backups**: Creates `.bak` files before conversion
* **Dry-run mode**: Preview all changes before applying
* **Graceful Ctrl+C**: Safe interrupt at any time
* **Rollback capability**: Instant restoration from backups
* **Strict error handling**: Won't corrupt files on encoding errors

---

## ⚡ Performance

* **Parallel processing**: Uses half CPU cores by default
* **Smart job capping**: Prevents system overload
* **Progress tracking**: Real-time ETA and progress
* **Optimized I/O**: Minimal disk reads with smart sampling

---

## 🐞 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No encoding detector found" | `pip3 install chardet` |
| Slow on network drives | Use `--fast` mode or reduce `-j` |
| Low confidence detections | Increase `--sample-size 131072` |
| Conversion errors | Check source file isn't corrupted |
| Need to undo conversions | Use `--rollback` |

---

## 📝 License

Released under the **MIT License**.  
See **[LICENSE](LICENSE)** for the full text. The software is provided **“as is”**, without warranty of any kind.

**SPDX**: `MIT`  
**Copyright** © 2025 xmxtxx

