# CSV Character Encoding Detection Tool

Detect and analyze character encodings of CSV files across many folders — **fast**, **parallel**, and **fully offline**. Dynamic folder discovery, half-core default for stability, and graceful **Ctrl+C**.

---

## 🎯 What it does

* Recursively scans CSV files under each immediate subfolder of a top directory (**no fixed naming required**).
* Detects encoding (UTF-8/UTF-8-SIG, ASCII, ISO-8859-\*, Windows-125x, plus UTF-16/UTF-32 via BOM and heuristics).
* Per-folder breakdowns and an overall summary with success rate.
* **Offline only**: never touches the network; read-only.

---

## 📁 Folder structure (flexible)

```
top/
├── AnyFolder1/
│   └── ... (CSV files can be anywhere if --csv-mode any)
├── AnyFolder2/
│   └── <csv_dir>/ (if --csv-mode subdir, e.g., "bak" or "archive")
│       └── *.csv
└── ...
```

You choose where CSVs live:

* `--csv-mode any` *(default)*: search `**/*.csv` anywhere under each subfolder
* `--csv-mode subdir`: only search inside a specific subfolder (set with `--bak`)

---

## 🚀 Quick start

```bash
# 1) Install an encoding detector (choose one)
pip3 install chardet
# or (optional, often faster)
pip3 install cchardet

# 2) Run on current directory (uses half your CPU cores by default)
python3 check_csv_charset.py

# 3) Run on a specific top directory (e.g., ~/data)
python3 check_csv_charset.py ~/data

# 4) Only look in a named subfolder under each folder (e.g., "archive")
python3 check_csv_charset.py /path/to/top --csv-mode subdir --bak archive
```

---

## 🧩 Features

* **Dynamic CSV discovery**: `--csv-mode any` (recursive) or `--csv-mode subdir` (e.g., only in `bak`)
* **Parallel processing**: default **half** your CPU cores (can override with `-j`)
* **Job safety**: caps extreme `-j` values to avoid thrashing and respects file count
* **Real-time progress**: progress bar with ETA and elapsed time
* **Heuristics**: BOM detection (UTF-8/16/32 LE/BE), small UTF-16 no-BOM detection, ASCII/binary hinting
* **Graceful Ctrl+C**: prints a friendly message and stops cleanly
* **Display naming**: extract readable names from folder prefixes (configurable delimiters)

---

## 🛠️ Options

| Option                       | Description                                                 | Default        |
| ---------------------------- | ----------------------------------------------------------- | -------------- |
| `directory`                  | Top directory containing subfolders                         | `.`            |
| `--csv-mode {any,subdir}`    | Where to look for CSVs                                      | `any`          |
| `--bak <name>`               | Subfolder name when `--csv-mode subdir`                     | `bak`          |
| `-j, --jobs <n>`             | Parallel workers; auto-capped for stability                 | **half cores** |
| `--fast`                     | Single-pass detection (less I/O, slightly lower confidence) | off            |
| `--sample-size <bytes>`      | Bytes sampled per pass                                      | `65536`        |
| `--pattern {all,underscore}` | Filter subfolders by name                                   | `all`          |
| `--name-delims "<chars>"`    | Delimiters for display names; fallback = full name          | `_- `          |
| `-d, --details`              | Show more info per folder                                   | off            |
| `-s, --summary-only`         | Only overall summary                                        | off            |
| `--no-progress`              | Disable progress bar                                        | off            |

> **Job safety:** Even if you pass `-j 100`, the tool caps to `min(requested, 2×CPU, total_files)` and prints an info line.

---

## 🧠 Display naming

Folder names like `000123_CustomerA` or `42-CorpX` are shown as `CustomerA` or `CorpX`.
Customize delimiters with `--name-delims "_- "`. If no delimiter is found, the **full folder name** is used.

---

## ⌨️ Graceful interrupt

Press **Ctrl+C** any time:
You’ll see a message like **“↩ Ctrl+C detected. Shutting down gracefully…”**, remaining tasks are canceled (best-effort), and the tool exits cleanly.

---

## 📊 Example output

```
============================================================
CSV Character Encoding Detection
============================================================
📁 Top directory: /home/user/data
🔎 CSV search: **/*.csv (recursive under each subfolder)
────────────────────────────────────────────────────────────

Scanning folders...
Found 24,236 CSV files in 32 folders
ℹ Limiting jobs from 32 to 32 (CPU=64, files=24236) for stability

Processing CSV files: [████████████████████████████████████████████████] 24236/24236 (100.0%) ETA: 0s Elapsed: 41s Complete!

Encoding Distribution CustomerA:
  UTF-8: 120 files (80.0%)
  ISO-8859-1: 30 files (20.0%)

…

══════════════════════════════════════════════════
OVERALL SUMMARY
══════════════════════════════════════════════════
Total folders analyzed: 32
Total CSV files processed: 24236
Successfully detected: 24190
Detection success rate: 99.8%
Total runtime: 41s

Overall Encoding Distribution:
  UTF-8: 17893 files (73.9%)
  ISO-8859-1: 3912 files (16.2%)
  ascii: 2385 files (9.8%)
  utf-16-le: 46 files (0.2%)
```

---

## 🔒 Privacy

* **100% offline** — no network calls, telemetry, or uploads
* **Read-only** — files are never modified

---

## 🐞 Troubleshooting

* **“No encoding detector found”** → `pip3 install chardet` (or `cchardet`)
* **Slow disks (e.g., `/mnt/…`)** → try `--fast` or reduce `-j`
* **Ambiguous encodings** → increase `--sample-size 131072` for more context

---

## 📝 License

This tool is provided as-is for data analysis purposes.
