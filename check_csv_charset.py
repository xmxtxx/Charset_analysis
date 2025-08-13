#!/usr/bin/env python3
"""
CSV Character Encoding Detection Script (Multi-Folder, Parallel, Offline)

Usage:
  python3 check_csv_charset.py [top_directory_path]

What it does:
  • Scans the immediate subfolders of the given top directory.
  • Finds CSV files either recursively anywhere (--csv-mode any, default),
    or only inside a specific subfolder (--csv-mode subdir with --bak <name>).
  • Detects encodings with progress, summaries, and colors.
  • Works fully offline, never sends data anywhere.

Folder structure (dynamic):
  top/
  ├── AnyFolder1/
  │   └── ... (CSV files can be anywhere if --csv-mode any)
  ├── AnyFolder2/
  │   └── <csv_dir>/ (if --csv-mode subdir, default "bak")
  │       └── *.csv
  └── ...
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from collections import defaultdict
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# ---------- Config ----------
DEFAULT_JOBS = max(1, (os.cpu_count() or 1) // 2)  # default: half the cores
# ----------------------------

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'
    DIM = '\033[2m'

def install_chardet_message():
    """Display installation instructions for an encoding detector"""
    print(f"{Colors.RED}Error: No encoding detector found{Colors.NC}")
    print(f"{Colors.YELLOW}Install one of these:{Colors.NC}")
    print(f"  pip3 install cchardet   # fastest (optional)")
    print(f"  pip3 install chardet    # default")
    sys.exit(1)

# Try fast detector first, fallback to chardet
try:
    import cchardet as chardet
except ImportError:
    try:
        import chardet
    except ImportError:
        install_chardet_message()


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"


class ProgressBar:
    """Simple progress bar for terminal output"""

    def __init__(self, total: int, width: int = 50, title: str = "Progress"):
        self.total = total
        self.width = width
        self.title = title
        self.current = 0
        self.start_time = time.time()

    def update(self, current: int, item_name: str = ""):
        """Update progress bar"""
        self.current = current

        if self.total == 0:
            return

        # Calculate progress
        progress = self.current / self.total
        filled = int(self.width * progress)

        # Calculate time
        elapsed = time.time() - self.start_time
        if self.current > 0:
            avg_time = elapsed / self.current
            remaining = avg_time * (self.total - self.current)
            time_str = f"ETA: {format_time(remaining)}"
        else:
            time_str = "Calculating..."

        total_time_str = f"Elapsed: {format_time(elapsed)}"

        # Create progress bar
        bar = '█' * filled + '░' * (self.width - filled)

        # Truncate item name if too long
        max_item_len = 40
        if len(item_name) > max_item_len:
            item_name = item_name[:max_item_len-3] + "..."

        # Print progress bar
        print(
            f'\r{Colors.CYAN}{self.title}:{Colors.NC} '
            f'[{Colors.GREEN}{bar}{Colors.NC}] '
            f'{Colors.YELLOW}{self.current}/{self.total}{Colors.NC} '
            f'({progress*100:.1f}%) {Colors.DIM}{time_str}{Colors.NC} '
            f'{Colors.DIM}{total_time_str}{Colors.NC} '
            f'{Colors.BLUE}{item_name}{Colors.NC}',
            end='',
            flush=True
        )

        if self.current == self.total:
            print()  # New line when complete

    def finish(self):
        """Mark progress as complete"""
        self.update(self.total, "Complete!")


# --- Heuristics to reduce "unknown" without brute-forcing encodings ---

def _detect_bom(sample: bytes) -> Optional[str]:
    """Detect BOM-based encodings quickly and deterministically."""
    if sample.startswith(b'\xEF\xBB\xBF'):
        return 'utf-8-sig'
    if sample.startswith(b'\xFF\xFE\x00\x00'):
        return 'utf-32-le'
    if sample.startswith(b'\x00\x00\xFE\xFF'):
        return 'utf-32-be'
    if sample.startswith(b'\xFF\xFE'):
        return 'utf-16-le'
    if sample.startswith(b'\xFE\xFF'):
        return 'utf-16-be'
    return None

def _guess_utf16_no_bom(sample: bytes) -> Optional[str]:
    """Heuristic for UTF-16 without BOM: many NULs on even or odd indices."""
    if len(sample) < 4:
        return None
    even_zeros = sum(1 for i in range(0, len(sample), 2) if sample[i] == 0)
    odd_zeros  = sum(1 for i in range(1, len(sample), 2) if sample[i] == 0)
    half = max(1, len(sample) // 2)
    even_ratio = even_zeros / half
    odd_ratio  = odd_zeros / half
    if odd_ratio > 0.40 and even_ratio < 0.20:
        return 'utf-16-le'
    if even_ratio > 0.40 and odd_ratio < 0.20:
        return 'utf-16-be'
    return None

def _is_mostly_ascii(sample: bytes, thresh: float = 0.98) -> bool:
    if not sample:
        return False
    ascii_bytes = sum(1 for b in sample if b < 0x80)
    return (ascii_bytes / len(sample)) >= thresh

def _is_binary_like(sample: bytes, nul_thresh: float = 0.30) -> bool:
    """Rough check for non-text files: lots of NUL bytes."""
    if not sample:
        return False
    nul_ratio = sample.count(0) / len(sample)
    return nul_ratio >= nul_thresh


def detect_encoding(file_path: Path,
                    sample_size: int = 65536,
                    do_second_pass: bool = True,
                    second_pass_factor: int = 4,
                    min_confidence_first_pass: float = 0.70) -> Tuple[str, float]:
    """
    Detect the character encoding of a file with minimal I/O (fully offline).
    Order:
      1) BOM check
      2) chardet/cchardet on head
      3) chardet on head+tail if low confidence
      4) chardet on larger read if allowed
      5) UTF-16 no-BOM heuristic, ASCII check, binary-like check
    Returns the encoding name as detected and confidence%.
    """
    try:
        fsize = os.path.getsize(file_path)
        if fsize == 0:
            return "unknown", 0.0

        with open(file_path, 'rb') as f:
            head = f.read(min(sample_size, fsize))

            # 1) BOM detection
            bom_enc = _detect_bom(head)
            if bom_enc:
                return bom_enc, 100.0

            # 2) Primary detection on head
            head_res = chardet.detect(head)
            head_enc = head_res.get('encoding') or "unknown"
            head_conf = float(head_res.get('confidence') or 0.0)

            # If small file, we already read all bytes. Apply heuristics if chardet is unsure.
            if fsize <= sample_size:
                if head_enc != "unknown":
                    return head_enc, head_conf * 100.0
                utf16_guess = _guess_utf16_no_bom(head)
                if utf16_guess:
                    return utf16_guess, 95.0
                if _is_mostly_ascii(head):
                    return 'ascii', 99.0
                if _is_binary_like(head):
                    return 'binary', 100.0
                return "unknown", 0.0

            # For bigger files:
            if head_conf >= min_confidence_first_pass:
                return head_enc, head_conf * 100.0

            # 3) Head + tail
            try:
                f.seek(max(0, fsize - sample_size))
                tail = f.read(sample_size)
            except Exception:
                tail = b''
            combined = head + tail if tail else head

            comb_res = chardet.detect(combined)
            comb_enc = comb_res.get('encoding') or "unknown"
            comb_conf = float(comb_res.get('confidence') or 0.0)
            if comb_conf >= min_confidence_first_pass and comb_enc != "unknown":
                return comb_enc, comb_conf * 100.0

            # 4) Larger second pass
            if do_second_pass:
                f.seek(0)
                big = f.read(min(fsize, sample_size * second_pass_factor))
                bom_enc2 = _detect_bom(big)
                if bom_enc2:
                    return bom_enc2, 100.0

                big_res = chardet.detect(big)
                big_enc = big_res.get('encoding') or "unknown"
                big_conf = float(big_res.get('confidence') or 0.0)
                if big_enc != "unknown":
                    return big_enc, big_conf * 100.0

                # 5) Heuristics on big sample
                utf16_guess2 = _guess_utf16_no_bom(big)
                if utf16_guess2:
                    return utf16_guess2, 95.0
                if _is_mostly_ascii(big):
                    return 'ascii', 99.0
                if _is_binary_like(big):
                    return 'binary', 100.0

            # Final fallback
            return "unknown", 0.0

    except Exception as e:
        return f"error: {str(e)}", 0.0


def get_folder_display_name(folder_path: Path, delimiters: str = "_- ") -> str:
    """
    Determine the display name from a folder name using the first delimiter found.
    If none of the delimiters appear, return the folder name unchanged.
    """
    name = folder_path.name
    first_idx = None
    for ch in delimiters:
        idx = name.find(ch)
        if idx != -1 and (first_idx is None or idx < first_idx):
            first_idx = idx
    if first_idx is None:
        return name
    return name[first_idx + 1:]


def count_total_csv_files(top_directory: Path,
                          pattern: Optional[str] = None,
                          bak_folder: str = 'bak',
                          csv_mode: str = 'any') -> Tuple[int, List[Path]]:
    """
    Count total CSV files and get list of folders to process.

    Returns:
        Tuple of (total_file_count, list_of_folders_with_csv)
    """
    total_files = 0
    folders_with_csv = []

    # Get all immediate subdirectories
    subfolders = [d for d in top_directory.iterdir() if d.is_dir()]

    # Optional filter by pattern
    if pattern:
        if pattern == 'underscore':
            subfolders = [d for d in subfolders if '_' in d.name]

    # Count CSV files in each folder
    for subfolder in sorted(subfolders):
        if csv_mode == 'any':
            csv_files = list(subfolder.rglob('*.csv')) + list(subfolder.rglob('*.CSV'))
        else:
            bak_path = subfolder / bak_folder
            if bak_path.exists() and bak_path.is_dir():
                csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV'))
            else:
                csv_files = []
        if csv_files:
            total_files += len(csv_files)
            folders_with_csv.append(subfolder)

    return total_files, folders_with_csv


def _detect_one(args_tuple):
    file_path, folder_path, folder_display_name, sample_size, do_second_pass = args_tuple
    enc, conf = detect_encoding(
        file_path=file_path,
        sample_size=sample_size,
        do_second_pass=do_second_pass,
        second_pass_factor=4,
        min_confidence_first_pass=0.70
    )
    return file_path, enc, conf, folder_path, folder_display_name


def analyze_all_subfolders(top_directory: Path,
                           pattern: Optional[str] = None,
                           bak_folder: str = 'bak',
                           csv_mode: str = 'any',
                           show_progress: bool = True,
                           jobs: Optional[int] = None,
                           fast: bool = False,
                           sample_size: int = 65536,
                           name_delims: str = "_- ") -> List[Dict]:
    """
    Analyze all subfolders in parallel with a progress bar.
    Gracefully handles Ctrl+C (KeyboardInterrupt).
    """
    all_results: List[Dict] = []

    print(f"{Colors.CYAN}Scanning folders...{Colors.NC}")
    total_files, folders_with_csv = count_total_csv_files(top_directory, pattern, bak_folder, csv_mode)

    if total_files == 0:
        return all_results

    print(f"{Colors.GREEN}Found {total_files} CSV files in {len(folders_with_csv)} folders{Colors.NC}\n")

    # Prepare per-folder result skeletons and tasks
    folder_result_map: Dict[Path, Dict] = {}
    tasks = []

    for subfolder in folders_with_csv:
        display_name = get_folder_display_name(subfolder, name_delims)
        res = {
            'folder_path': subfolder,
            'folder_name': display_name,
            'files': [],
            'encodings': defaultdict(int),
            'total': 0,
            'detected': 0,
            'errors': 0
        }
        folder_result_map[subfolder] = res

        if csv_mode == 'any':
            csv_files = list(subfolder.rglob('*.csv')) + list(subfolder.rglob('*.CSV'))
        else:
            bak_path = subfolder / bak_folder
            csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV')) if bak_path.exists() else []

        res['total'] = len(csv_files)
        for f in csv_files:
            tasks.append((f, subfolder, res['folder_name'], sample_size, not fast))

    progress_bar = ProgressBar(total_files, title="Processing CSV files") if show_progress else None

    processed = 0
    # Decide worker count with hard-cap + info
    cpu = os.cpu_count() or 1
    requested = jobs if (jobs and jobs > 0) else DEFAULT_JOBS
    # Cap to 2x CPU and also to number of files (no point in more workers than files)
    capped = min(requested, cpu * 2, total_files)

    if capped < requested:
        print(
            f"{Colors.YELLOW}ℹ Limiting jobs from {requested} to {capped} "
            f"(CPU={cpu}, files={total_files}) for stability{Colors.NC}"
        )

    max_workers = max(1, capped)

    ex: Optional[ProcessPoolExecutor] = None
    futures = []
    try:
        ex = ProcessPoolExecutor(max_workers=max_workers)
        futures = [ex.submit(_detect_one, t) for t in tasks]

        for fut in as_completed(futures):
            file_path, encoding, confidence, folder_path, folder_display_name = fut.result()
            res = folder_result_map[folder_path]

            res['files'].append({
                'path': file_path,
                'name': file_path.name,
                'encoding': encoding,
                'confidence': confidence
            })

            if encoding and not str(encoding).startswith('error') and encoding != "unknown":
                res['detected'] += 1
                res['encodings'][encoding] += 1
            else:
                res['errors'] += 1

            processed += 1
            if progress_bar:
                progress_bar.update(processed, f"{folder_display_name}/{file_path.name}")

    except KeyboardInterrupt:
        # Graceful interrupt: cancel remaining work and return partial results
        if progress_bar:
            print()
        print(f"{Colors.YELLOW}↩ Ctrl+C detected. Shutting down gracefully...{Colors.NC}")
        # Try to stop quickly
        try:
            for fut in futures:
                fut.cancel()
        except Exception:
            pass
        try:
            # Python 3.9+: cancel_futures available
            ex.shutdown(wait=False, cancel_futures=True)  # type: ignore
        except TypeError:
            # Older Python: best-effort
            ex.shutdown(wait=False)
        except Exception:
            pass
        return [folder_result_map[f] for f in folders_with_csv if folder_result_map[f]['total'] > 0]

    finally:
        if ex is not None:
            try:
                ex.shutdown(wait=False)
            except Exception:
                pass

    if progress_bar:
        progress_bar.finish()
    print()  # Extra line after progress bar (or scanning)

    # Preserve original folder order
    return [folder_result_map[f] for f in folders_with_csv if folder_result_map[f]['total'] > 0]


def display_encoding_distribution(results: Dict, show_details: bool = False):
    """Display encoding distribution for a single folder"""
    folder_name = results['folder_name']
    total = results['detected']

    if total == 0:
        print(f"{Colors.YELLOW}No CSV files detected in {folder_name}{Colors.NC}")
        return

    print(f"{Colors.BOLD}{Colors.CYAN}Encoding Distribution {folder_name}:{Colors.NC}")

    # Sort encodings by count
    sorted_encodings = sorted(results['encodings'].items(), key=lambda x: x[1], reverse=True)

    for encoding, count in sorted_encodings:
        percentage = (count / total) * 100

        # Color based on encoding type
        if encoding and encoding.lower() in ['utf-8', 'utf8', 'utf-8-sig']:
            enc_color = Colors.GREEN
        elif encoding and encoding.lower() in ['ascii']:
            enc_color = Colors.BLUE
        elif encoding and ('iso' in encoding.lower() or 'windows' in encoding.lower()):
            enc_color = Colors.YELLOW
        elif encoding and encoding.lower() in ['binary', 'utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be']:
            enc_color = Colors.RED
        else:
            enc_color = Colors.MAGENTA

        print(f"  {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")

    if results['errors'] > 0:
        print(f"  {Colors.RED}Errors{Colors.NC}: {results['errors']} files")

    if show_details:
        print(f"  {Colors.BLUE}Total files{Colors.NC}: {results['total']}")
        print(f"  {Colors.BLUE}Folder path{Colors.NC}: {results['folder_path']}")


def display_summary(all_results: List[Dict], elapsed_time: float):
    """Display overall summary of all folders analyzed"""
    total_folders = len(all_results)
    total_files = sum(r['total'] for r in all_results)
    total_detected = sum(r['detected'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)

    # Aggregate all encodings
    all_encodings = defaultdict(int)
    for results in all_results:
        for encoding, count in results['encodings'].items():
            all_encodings[encoding] += count

    print(f"\n{Colors.BLUE}{'═' * 50}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}OVERALL SUMMARY{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 50}{Colors.NC}")

    print(f"Total folders analyzed: {Colors.BLUE}{total_folders}{Colors.NC}")
    print(f"Total CSV files processed: {Colors.BLUE}{total_files}{Colors.NC}")
    print(f"Successfully detected: {Colors.GREEN}{total_detected}{Colors.NC}")
    if total_errors > 0:
        print(f"Total errors: {Colors.RED}{total_errors}{Colors.NC}")

    if total_files > 0:
        success_rate = (total_detected / total_files) * 100
        print(f"Detection success rate: {Colors.GREEN}{success_rate:.1f}%{Colors.NC}")

    print(f"Total runtime: {Colors.MAGENTA}{format_time(elapsed_time)}{Colors.NC}")

    if all_encodings:
        print(f"\n{Colors.BOLD}{Colors.CYAN}Overall Encoding Distribution:{Colors.NC}")
        sorted_encodings = sorted(all_encodings.items(), key=lambda x: x[1], reverse=True)
        for encoding, count in sorted_encodings:
            percentage = (count / total_detected) * 100 if total_detected > 0 else 0
            if encoding and encoding.lower() in ['utf-8', 'utf8', 'utf-8-sig']:
                enc_color = Colors.GREEN
            elif encoding and encoding.lower() in ['ascii']:
                enc_color = Colors.BLUE
            elif encoding and ('iso' in encoding.lower() or 'windows' in encoding.lower()):
                enc_color = Colors.YELLOW
            elif encoding and encoding.lower() in ['binary', 'utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be']:
                enc_color = Colors.RED
            else:
                enc_color = Colors.MAGENTA
            print(f"  {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")


def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description='Detect character encoding of CSV files in structured folders with progress tracking (offline)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dynamic folder structure (no fixed naming required):
  top/
  ├── <any-subfolder>/
  │   └── (CSV files anywhere if --csv-mode any, default)
  │   └── <csv_dir>/ (if --csv-mode subdir, e.g., "bak")
  │       └── *.csv

Examples:
  %(prog)s data
  %(prog)s /path/to/top --csv-mode subdir --bak archive
  %(prog)s data -j 8 --fast
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Top-level directory containing subfolders (default: current directory)'
    )

    parser.add_argument(
        '--csv-mode',
        choices=['any', 'subdir'],
        default='any',
        help='Where to look for CSV files: "any" (recursive under each subfolder, default) or "subdir" (only inside --bak)'
    )

    parser.add_argument(
        '--bak',
        default='bak',
        help='Name of the subfolder containing CSV files when --csv-mode subdir (default: bak)'
    )

    parser.add_argument(
        '-d', '--details',
        action='store_true',
        help='Show detailed information for each folder'
    )

    parser.add_argument(
        '-s', '--summary-only',
        action='store_true',
        help='Show only the overall summary'
    )

    parser.add_argument(
        '--pattern',
        choices=['underscore', 'all'],
        default='all',
        help='Folder selection: "all" (default) or only names containing an underscore'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )

    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=DEFAULT_JOBS,
        help=f'Number of parallel workers (default: half cores = {DEFAULT_JOBS})'
    )

    parser.add_argument(
        '--fast',
        action='store_true',
        help='Faster single-pass detection (lower I/O, slightly lower confidence)'
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        default=65536,
        help='Bytes to sample per pass (default: 65536)'
    )

    parser.add_argument(
        '--name-delims',
        default='_- ',
        help='Characters to treat as delimiters for display names (default: "_- ")'
    )

    args = parser.parse_args()

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        print(f"{Colors.RED}Error: Directory '{directory}' does not exist{Colors.NC}")
        sys.exit(1)

    if not directory.is_dir():
        print(f"{Colors.RED}Error: '{directory}' is not a directory{Colors.NC}")
        sys.exit(1)

    # Perform analysis
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}CSV Character Encoding Detection{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"📁 Top directory: {Colors.GREEN}{directory.absolute()}{Colors.NC}")
    if args.csv_mode == 'any':
        print(f"🔎 CSV search: {Colors.GREEN}**/*.csv (recursive under each subfolder){Colors.NC}")
    else:
        print(f"📂 CSV location: {Colors.GREEN}*/{args.bak}/*.csv{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}\n")

    # Analyze all subfolders (parallel)
    pattern = None if args.pattern == 'all' else args.pattern
    try:
        all_results = analyze_all_subfolders(
            top_directory=directory,
            pattern=pattern,
            bak_folder=args.bak,
            csv_mode=args.csv_mode,
            show_progress=not args.no_progress,
            jobs=args.jobs,
            fast=args.fast,
            sample_size=args.sample_size,
            name_delims=args.name_delims
        )
    except KeyboardInterrupt:
        # Extra safety (should already be handled inside), but ensure a friendly exit
        print(f"{Colors.YELLOW}↩ Ctrl+C detected. Shutting down gracefully...{Colors.NC}")
        sys.exit(130)

    if not all_results:
        where = "**/*.csv" if args.csv_mode == 'any' else f"*/{args.bak}/*.csv"
        print(f"{Colors.YELLOW}⚠️  No CSV files found at {where}{Colors.NC}")
        sys.exit(0)

    # Display results
    if not args.summary_only:
        print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}Results by Folder:{Colors.NC}\n")
        for results in all_results:
            display_encoding_distribution(results, args.details)
            print()  # Empty line between folders

    # Display summary
    elapsed_time = time.time() - start_time
    display_summary(all_results, elapsed_time)

    print(f"\n{Colors.GREEN}✅ Analysis complete!{Colors.NC}")


if __name__ == "__main__":
    main()
