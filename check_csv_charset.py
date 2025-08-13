#!/usr/bin/env python3
"""
CSV Character Encoding Detection Script for Multi-Folder Structure
Usage: python3 check_csv_charset.py [top_directory_path]

Expects folder structure:
    data/
    ├── CustomerNR_Customer/
    │   └── bak/
    │       └── *.csv files
    ├── CustomerNR_Customer/
    │   └── bak/
    │       └── *.csv files
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


def detect_encoding(file_path: Path,
                    sample_size: int = 65536,
                    do_second_pass: bool = True,
                    second_pass_factor: int = 4,
                    min_confidence_first_pass: float = 0.70) -> Tuple[str, float]:
    """
    Detect the character encoding of a file with minimal I/O.

    Strategy:
    1) Read head sample (sample_size) → detect
    2) If low confidence, read tail sample (sample_size) and detect on head+tail
    3) If still low and allowed, second pass with larger read (sample_size * factor)
    """
    try:
        fsize = os.path.getsize(file_path)
        if fsize == 0:
            return "unknown", 0.0

        with open(file_path, 'rb') as f:
            # Head sample
            head = f.read(sample_size)
            result = chardet.detect(head)
            encoding = result.get('encoding', 'unknown') or 'unknown'
            confidence = float(result.get('confidence') or 0.0)

            if confidence >= min_confidence_first_pass or fsize <= sample_size:
                return encoding, confidence * 100.0

            # Tail sample (avoid reading the whole file)
            if fsize > sample_size:
                try:
                    f.seek(max(0, fsize - sample_size))
                    tail = f.read(sample_size)
                    combined = head + tail
                    result2 = chardet.detect(combined)
                    enc2 = result2.get('encoding', 'unknown') or 'unknown'
                    conf2 = float(result2.get('confidence') or 0.0)
                    if conf2 >= min_confidence_first_pass:
                        return enc2, conf2 * 100.0
                    encoding, confidence = enc2, conf2
                except Exception:
                    # Fall through to second pass if needed
                    pass

            # Second pass (bigger sample)
            if do_second_pass and fsize > sample_size:
                f.seek(0)
                big = f.read(min(fsize, sample_size * second_pass_factor))
                result3 = chardet.detect(big)
                enc3 = result3.get('encoding', 'unknown') or 'unknown'
                conf3 = float(result3.get('confidence') or 0.0)
                return enc3, conf3 * 100.0

            return encoding, confidence * 100.0

    except Exception as e:
        return f"error: {str(e)}", 0.0

def get_folder_name(folder_path: Path) -> str:
    """Extract the name part after underscore from folder name"""
    folder_name = folder_path.name
    if '_' in folder_name:
        return folder_name.split('_', 1)[1]
    return folder_name

def count_total_csv_files(top_directory: Path, pattern: str = None, bak_folder: str = 'bak') -> Tuple[int, List[Path]]:
    """
    Count total CSV files and get list of folders to process

    Returns:
        Tuple of (total_file_count, list_of_folders_with_csv)
    """
    total_files = 0
    folders_with_csv = []

    # Get all subdirectories
    subfolders = [d for d in top_directory.iterdir() if d.is_dir()]

    # Filter by pattern if specified
    if pattern:
        if pattern == 'underscore':
            subfolders = [d for d in subfolders if '_' in d.name]

    # Count CSV files in each folder
    for subfolder in sorted(subfolders):
        bak_path = subfolder / bak_folder
        if bak_path.exists() and bak_path.is_dir():
            csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV'))
            if csv_files:
                total_files += len(csv_files)
                folders_with_csv.append(subfolder)

    return total_files, folders_with_csv

def _detect_one(args_tuple):
    """
    Helper for multiprocessing (must be top-level to be pickleable).
    """
    file_path, folder_path, folder_display_name, sample_size, do_second_pass = args_tuple
    enc, conf = detect_encoding(
        file_path=file_path,
        sample_size=sample_size,
        do_second_pass=do_second_pass,
        second_pass_factor=4,
        min_confidence_first_pass=0.70
    )
    return file_path, enc, conf, folder_path, folder_display_name

def analyze_subfolder_csv_files(subfolder: Path, bak_folder_name: str = 'bak',
                                progress_bar: Optional[ProgressBar] = None,
                                file_offset: int = 0) -> Dict:
    """
    (Unused in parallel mode, kept for compatibility or potential fallback)
    Analyze CSV files in a specific subfolder's bak directory
    """
    results = {
        'folder_path': subfolder,
        'folder_name': get_folder_name(subfolder),
        'files': [],
        'encodings': defaultdict(int),
        'total': 0,
        'detected': 0,
        'errors': 0
    }

    bak_path = subfolder / bak_folder_name
    if not bak_path.exists() or not bak_path.is_dir():
        return results

    csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV'))
    results['total'] = len(csv_files)

    for idx, csv_file in enumerate(sorted(csv_files)):
        if progress_bar:
            current_file = file_offset + idx + 1
            progress_bar.update(current_file, f"{results['folder_name']}/{csv_file.name}")

        encoding, confidence = detect_encoding(csv_file)
        results['files'].append({'path': csv_file, 'name': csv_file.name, 'encoding': encoding, 'confidence': confidence})

        if encoding and not str(encoding).startswith('error'):
            results['detected'] += 1
            results['encodings'][encoding] += 1
        else:
            results['errors'] += 1

    return results


def analyze_all_subfolders(top_directory: Path, pattern: str = None, bak_folder: str = 'bak',
                           show_progress: bool = True, jobs: Optional[int] = None,
                           fast: bool = False, sample_size: int = 65536) -> List[Dict]:
    """
    Analyze all subfolders in parallel with a progress bar.
    """
    all_results: List[Dict] = []

    print(f"{Colors.CYAN}Scanning folders...{Colors.NC}")
    total_files, folders_with_csv = count_total_csv_files(top_directory, pattern, bak_folder)

    if total_files == 0:
        return all_results

    print(f"{Colors.GREEN}Found {total_files} CSV files in {len(folders_with_csv)} folders{Colors.NC}\n")

    # Prepare per-folder result skeletons and tasks
    folder_result_map: Dict[Path, Dict] = {}
    tasks = []

    for subfolder in folders_with_csv:
        res = {
            'folder_path': subfolder,
            'folder_name': get_folder_name(subfolder),
            'files': [],
            'encodings': defaultdict(int),
            'total': 0,
            'detected': 0,
            'errors': 0
        }
        folder_result_map[subfolder] = res

        bak_path = subfolder / bak_folder
        csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV'))
        res['total'] = len(csv_files)
        for f in csv_files:
            tasks.append((f, subfolder, res['folder_name'], sample_size, not fast))

    progress_bar = ProgressBar(total_files, title="Processing CSV files") if show_progress else None

    processed = 0
    # Decide worker count with hard-cap + info
    cpu = os.cpu_count() or 1
    requested = jobs if (jobs and jobs > 0) else cpu
    # Cap to 2x CPU and also to number of files (no point in more workers than files)
    capped = min(requested, cpu * 2, total_files)

    if capped < requested:
        print(
            f"{Colors.YELLOW}ℹ Limiting jobs from {requested} to {capped} "
            f"(CPU={cpu}, files={total_files}) for stability{Colors.NC}"
        )

    max_workers = max(1, capped)

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
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

            if encoding and not str(encoding).startswith('error'):
                res['detected'] += 1
                res['encodings'][encoding] += 1
            else:
                res['errors'] += 1

            processed += 1
            if progress_bar:
                progress_bar.update(processed, f"{folder_display_name}/{file_path.name}")

    if progress_bar:
        progress_bar.finish()
        print()  # Extra line after progress bar

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
        if encoding and encoding.lower() in ['utf-8', 'utf8']:
            enc_color = Colors.GREEN
        elif encoding and encoding.lower() in ['ascii']:
            enc_color = Colors.BLUE
        elif encoding and ('iso' in encoding.lower() or 'windows' in encoding.lower()):
            enc_color = Colors.YELLOW
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
            if encoding and encoding.lower() in ['utf-8', 'utf8']:
                enc_color = Colors.GREEN
            elif encoding and encoding.lower() in ['ascii']:
                enc_color = Colors.BLUE
            elif encoding and ('iso' in encoding.lower() or 'windows' in encoding.lower()):
                enc_color = Colors.YELLOW
            else:
                enc_color = Colors.MAGENTA
            print(f"  {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description='Detect character encoding of CSV files in structured folders with progress tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Expected folder structure:
  top_folder/
  ├── CustomerNR_Customer/
  │   └── bak/
  │       └── *.csv files
  ├── CustomerNR_Customer/
  │   └── bak/
  │       └── *.csv files
  └── ...

Examples:
  %(prog)s data                 # Analyze all subfolders in 'data'
  %(prog)s /path/to/data        # Analyze specific directory
  %(prog)s data --bak backup    # Use 'backup' instead of 'bak' folder
  %(prog)s data -d              # Show detailed output
  %(prog)s data -s              # Show only summary
  %(prog)s data --no-progress   # Disable progress bar
  %(prog)s data -j 8            # Use 8 parallel workers
  %(prog)s data --fast          # Faster single-pass detection
  %(prog)s data --sample-size 131072  # Larger sample
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Top-level directory containing subfolders (default: current directory)'
    )

    parser.add_argument(
        '--bak',
        default='bak',
        help='Name of the backup folder containing CSV files (default: bak)'
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
        default='underscore',
        help='Pattern for folder selection (default: underscore - folders with underscore in name)'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )

    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=os.cpu_count(),
        help='Number of parallel workers (default: CPU count)'
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
    print(f"📂 CSV location: {Colors.GREEN}*/{args.bak}/*.csv{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}\n")

    # Analyze all subfolders (parallel)
    pattern = None if args.pattern == 'all' else args.pattern
    all_results = analyze_all_subfolders(
        top_directory=directory,
        pattern=pattern,
        bak_folder=args.bak,
        show_progress=not args.no_progress,
        jobs=args.jobs,
        fast=args.fast,
        sample_size=args.sample_size
    )

    if not all_results:
        print(f"{Colors.YELLOW}⚠️  No CSV files found in any subfolder's '{args.bak}' directory{Colors.NC}")
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
