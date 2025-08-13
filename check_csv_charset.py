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
    """Display installation instructions for chardet"""
    print(f"{Colors.RED}Error: 'chardet' library is not installed{Colors.NC}")
    print(f"{Colors.YELLOW}Install it using one of these commands:{Colors.NC}")
    print(f"  pip3 install chardet")
    print(f"  python3 -m pip install chardet")
    print(f"  sudo apt-get install python3-chardet  (for system-wide installation)")
    sys.exit(1)

try:
    import chardet
except ImportError:
    install_chardet_message()

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
            time_str = f"ETA: {self.format_time(remaining)}"
        else:
            time_str = "Calculating..."

        # Create progress bar
        bar = '█' * filled + '░' * (self.width - filled)

        # Truncate item name if too long
        max_item_len = 40
        if len(item_name) > max_item_len:
            item_name = item_name[:max_item_len-3] + "..."

        # Print progress bar
        print(f'\r{Colors.CYAN}{self.title}:{Colors.NC} [{Colors.GREEN}{bar}{Colors.NC}] '
              f'{Colors.YELLOW}{self.current}/{self.total}{Colors.NC} '
              f'({progress*100:.1f}%) {Colors.DIM}{time_str}{Colors.NC} '
              f'{Colors.BLUE}{item_name}{Colors.NC}', end='', flush=True)

        if self.current == self.total:
            print()  # New line when complete

    def format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"

    def finish(self):
        """Mark progress as complete"""
        self.update(self.total, "Complete!")

def detect_encoding(file_path: Path, sample_size: int = 65536) -> Tuple[str, float]:
    """
    Detect the character encoding of a file

    Args:
        file_path: Path to the file
        sample_size: Number of bytes to read for detection (default: 64KB)

    Returns:
        Tuple of (encoding_name, confidence_percentage)
    """
    try:
        with open(file_path, 'rb') as file:
            # Read sample of file for detection
            raw_data = file.read(sample_size)

            # Detect encoding
            result = chardet.detect(raw_data)

            # If confidence is low, try reading more of the file
            if result['confidence'] < 0.7 and os.path.getsize(file_path) > sample_size:
                file.seek(0)
                raw_data = file.read(sample_size * 4)  # Read 256KB
                result = chardet.detect(raw_data)

            encoding = result.get('encoding', 'unknown')
            confidence = result.get('confidence', 0.0) * 100

            return encoding, confidence

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

def analyze_subfolder_csv_files(subfolder: Path, bak_folder_name: str = 'bak',
                                progress_bar: Optional[ProgressBar] = None,
                                file_offset: int = 0) -> Dict:
    """
    Analyze CSV files in a specific subfolder's bak directory

    Args:
        subfolder: Path to subfolder
        bak_folder_name: Name of the backup folder (default: 'bak')
        progress_bar: Optional progress bar to update
        file_offset: Current file count offset for progress bar

    Returns:
        Dictionary with analysis results for this subfolder
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

    # Check if bak folder exists
    bak_path = subfolder / bak_folder_name
    if not bak_path.exists() or not bak_path.is_dir():
        return results

    # Find CSV files in bak folder
    csv_files = list(bak_path.glob('*.csv')) + list(bak_path.glob('*.CSV'))
    results['total'] = len(csv_files)

    # Analyze each file
    for idx, csv_file in enumerate(sorted(csv_files)):
        # Update progress bar
        if progress_bar:
            current_file = file_offset + idx + 1
            progress_bar.update(current_file, f"{results['folder_name']}/{csv_file.name}")

        encoding, confidence = detect_encoding(csv_file)

        file_info = {
            'path': csv_file,
            'name': csv_file.name,
            'encoding': encoding,
            'confidence': confidence
        }

        results['files'].append(file_info)

        if encoding and not encoding.startswith('error'):
            results['detected'] += 1
            results['encodings'][encoding] += 1
        else:
            results['errors'] += 1

    return results

def analyze_all_subfolders(top_directory: Path, pattern: str = None, bak_folder: str = 'bak',
                           show_progress: bool = True) -> List[Dict]:
    """
    Analyze all subfolders in the top directory with progress bar

    Args:
        top_directory: Path to top-level directory
        pattern: Optional pattern to filter folders
        bak_folder: Name of the backup folder (default: 'bak')
        show_progress: Whether to show progress bar

    Returns:
        List of analysis results for each subfolder
    """
    all_results = []

    # First, count total files and get folders to process
    print(f"{Colors.CYAN}Scanning folders...{Colors.NC}")
    total_files, folders_with_csv = count_total_csv_files(top_directory, pattern, bak_folder)

    if total_files == 0:
        return all_results

    print(f"{Colors.GREEN}Found {total_files} CSV files in {len(folders_with_csv)} folders{Colors.NC}\n")

    # Create progress bar
    progress_bar = None
    if show_progress:
        progress_bar = ProgressBar(total_files, title="Processing CSV files")

    # Analyze each subfolder
    file_offset = 0
    for subfolder in folders_with_csv:
        results = analyze_subfolder_csv_files(subfolder, bak_folder, progress_bar, file_offset)
        if results['total'] > 0:
            all_results.append(results)
            file_offset += results['total']

    if progress_bar:
        progress_bar.finish()
        print()  # Extra line after progress bar

    return all_results

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
        if encoding.lower() in ['utf-8', 'utf8']:
            enc_color = Colors.GREEN
        elif encoding.lower() in ['ascii']:
            enc_color = Colors.BLUE
        elif 'iso' in encoding.lower() or 'windows' in encoding.lower():
            enc_color = Colors.YELLOW
        else:
            enc_color = Colors.MAGENTA

        print(f"  {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")

    if results['errors'] > 0:
        print(f"  {Colors.RED}Errors{Colors.NC}: {results['errors']} files")

    if show_details:
        print(f"  {Colors.BLUE}Total files{Colors.NC}: {results['total']}")
        print(f"  {Colors.BLUE}Folder path{Colors.NC}: {results['folder_path']}")

def display_summary(all_results: List[Dict]):
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

    # Success rate
    if total_files > 0:
        success_rate = (total_detected / total_files) * 100
        print(f"Detection success rate: {Colors.GREEN}{success_rate:.1f}%{Colors.NC}")

    if all_encodings:
        print(f"\n{Colors.BOLD}{Colors.CYAN}Overall Encoding Distribution:{Colors.NC}")
        sorted_encodings = sorted(all_encodings.items(), key=lambda x: x[1], reverse=True)

        for encoding, count in sorted_encodings:
            percentage = (count / total_detected) * 100 if total_detected > 0 else 0

            # Color based on encoding type
            if encoding.lower() in ['utf-8', 'utf8']:
                enc_color = Colors.GREEN
            elif encoding.lower() in ['ascii']:
                enc_color = Colors.BLUE
            elif 'iso' in encoding.lower() or 'windows' in encoding.lower():
                enc_color = Colors.YELLOW
            else:
                enc_color = Colors.MAGENTA

            print(f"  {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")

def main():
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
  %(prog)s data -d               # Show detailed output
  %(prog)s data -s               # Show only summary
  %(prog)s data --no-progress   # Disable progress bar
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

    # Analyze all subfolders
    pattern = None if args.pattern == 'all' else args.pattern
    all_results = analyze_all_subfolders(directory, pattern, args.bak, not args.no_progress)

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
    display_summary(all_results)

    print(f"\n{Colors.GREEN}✅ Analysis complete!{Colors.NC}")

if __name__ == "__main__":
    main()
