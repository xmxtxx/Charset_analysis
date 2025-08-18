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
import shutil
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

def convert_file_encoding(file_path: Path,
                          target_encoding: str,
                          source_encoding: str,
                          backup: bool = True) -> Tuple[bool, str]:
    """
    Convert a single file from source to target encoding.
    Returns (success, message).
    """
    try:
        # Skip if already in target encoding
        if source_encoding.lower() == target_encoding.lower():
            return True, "already_target"

        # Can't convert unknown encodings
        if source_encoding in ['unknown', 'binary'] or source_encoding.startswith('error'):
            return False, f"Cannot convert from {source_encoding}"

        # Read with source encoding
        with open(file_path, 'r', encoding=source_encoding, errors='strict') as f:
            content = f.read()

        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)

        # Write with target encoding
        with open(file_path, 'w', encoding=target_encoding, errors='strict') as f:
            f.write(content)

        return True, f"Converted from {source_encoding} to {target_encoding}"

    except UnicodeDecodeError as e:
        return False, f"Decode error: {str(e)[:50]}"
    except UnicodeEncodeError as e:
        return False, f"Encode error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


# 1. Fix the convert_folder_files function to track by_encoding:
def convert_folder_files(folder_result: Dict,
                         target_encoding: str,
                         dry_run: bool = False,
                         backup: bool = True,
                         show_progress: bool = True,
                         verbose: bool = False) -> Dict:
    """
    Convert all files in a folder result to target encoding.
    Returns statistics about the conversion.
    """
    stats = {
        'total': len(folder_result['files']),
        'converted': 0,
        'skipped': 0,
        'failed': 0,
        'already_target': 0,
        'failed_files': [],
        'by_encoding': defaultdict(int)  # ADD THIS!
    }

    folder_name = folder_result['folder_name']

    # Determine if we should show individual files
    show_individual = verbose or stats['total'] <= 10

    for i, file_info in enumerate(folder_result['files'], 1):
        file_path = file_info['path']
        source_encoding = file_info['encoding']

        if dry_run:
            # Simulation mode
            if source_encoding.lower() == target_encoding.lower():
                stats['already_target'] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.DIM}[SKIP]{Colors.NC} {file_path.name} - already {target_encoding}")
            elif source_encoding in ['unknown', 'binary'] or source_encoding.startswith('error'):
                stats['skipped'] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.YELLOW}[SKIP]{Colors.NC} {file_path.name} - {source_encoding}")
            else:
                stats['converted'] += 1
                stats['by_encoding'][source_encoding] += 1  # TRACK THIS!
                if show_individual and show_progress:
                    print(f"  {Colors.GREEN}[WOULD CONVERT]{Colors.NC} {file_path.name}: "
                          f"{source_encoding} → {target_encoding}")
        else:
            # Actual conversion
            success, message = convert_file_encoding(
                file_path, target_encoding, source_encoding, backup
            )

            if success:
                if message == "already_target":
                    stats['already_target'] += 1
                else:
                    stats['converted'] += 1
                    stats['by_encoding'][source_encoding] += 1  # TRACK THIS!
                    if show_individual and show_progress:
                        print(f"  {Colors.GREEN}✓{Colors.NC} {file_path.name}: "
                              f"{source_encoding} → {target_encoding}")
            else:
                stats['failed'] += 1
                stats['failed_files'].append((file_path.name, message))
                if show_individual and show_progress:
                    print(f"  {Colors.RED}✗{Colors.NC} {file_path.name}: {message}")

        # Show progress counter for large batches
        if not show_individual and show_progress and i % 100 == 0:
            print(f"  {Colors.DIM}Processed {i}/{stats['total']} files...{Colors.NC}", end='\r')

    # Clear the progress line
    if not show_individual and show_progress and stats['total'] > 10:
        print(" " * 80, end='\r')

    # Show summary for this folder
    if not show_individual and show_progress and (stats['converted'] > 0 or stats['failed'] > 0):
        print(f"  {Colors.CYAN}Summary:{Colors.NC}")
        if dry_run:
            for enc, count in stats['by_encoding'].items():
                print(f"    • Would convert {Colors.GREEN}{count}{Colors.NC} files from {enc}")
        else:
            for enc, count in stats['by_encoding'].items():
                print(f"    • Converted {Colors.GREEN}{count}{Colors.NC} files from {enc}")

        if stats['already_target'] > 0:
            print(f"    • Already {target_encoding}: {Colors.BLUE}{stats['already_target']}{Colors.NC} files")
        if stats['skipped'] > 0:
            print(f"    • Skipped (unknown/binary): {Colors.YELLOW}{stats['skipped']}{Colors.NC} files")
        if stats['failed'] > 0:
            print(f"    • Failed: {Colors.RED}{stats['failed']}{Colors.NC} files")

    return stats

def display_conversion_summary(all_conversion_stats: List[Tuple[str, Dict]],
                               target_encoding: str,
                               dry_run: bool = False):
    """Display summary of all conversion operations"""
    total_converted = sum(stats['converted'] for _, stats in all_conversion_stats)
    total_failed = sum(stats['failed'] for _, stats in all_conversion_stats)
    total_already = sum(stats['already_target'] for _, stats in all_conversion_stats)
    total_skipped = sum(stats['skipped'] for _, stats in all_conversion_stats)

    # Aggregate by source encoding
    encoding_totals = defaultdict(int)
    for _, stats in all_conversion_stats:
        for enc, count in stats['by_encoding'].items():
            encoding_totals[enc] += count

    mode = "DRY RUN" if dry_run else "CONVERSION"

    print(f"\n{Colors.BLUE}{'═' * 50}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{mode} SUMMARY → {target_encoding.upper()}{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 50}{Colors.NC}")

    # Show what was/would be converted by source encoding
    if encoding_totals:
        action = "Would convert" if dry_run else "Converted"
        print(f"\n{Colors.BOLD}{action} by source encoding:{Colors.NC}")
        for enc, count in sorted(encoding_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"  {Colors.GREEN}{enc}{Colors.NC}: {count} files")

    # Summary stats
    print(f"\n{Colors.BOLD}Totals:{Colors.NC}")
    if dry_run:
        print(f"  Would convert: {Colors.GREEN}{total_converted}{Colors.NC} files")
    else:
        print(f"  Successfully converted: {Colors.GREEN}{total_converted}{Colors.NC} files")

    if total_already > 0:
        print(f"  Already in target encoding: {Colors.BLUE}{total_already}{Colors.NC} files")

    if total_skipped > 0:
        print(f"  Skipped (unknown/binary): {Colors.YELLOW}{total_skipped}{Colors.NC} files")

    if total_failed > 0:
        print(f"  Failed: {Colors.RED}{total_failed}{Colors.NC} files")

        # Show up to 10 failed files as examples
        print(f"\n{Colors.YELLOW}Failed conversion examples:{Colors.NC}")
        shown = 0
        for folder_name, stats in all_conversion_stats:
            if shown >= 10:
                remaining = total_failed - shown
                if remaining > 0:
                    print(f"  {Colors.DIM}... and {remaining} more failures{Colors.NC}")
                break
            if stats['failed_files']:
                print(f"  {Colors.CYAN}{folder_name}:{Colors.NC}")
                for file_name, error in stats['failed_files'][:min(3, 10-shown)]:
                    print(f"    {Colors.RED}•{Colors.NC} {file_name}: {error}")
                    shown += 1
                    if shown >= 10:
                        break

def rollback_backups(folder_path: Path) -> Tuple[int, int]:
    """Restore .bak files to original names"""
    restored = 0
    failed = 0

    for backup_file in folder_path.rglob('*.csv.bak'):
        original = backup_file.with_suffix('')  # Remove .bak
        try:
            shutil.move(str(backup_file), str(original))
            restored += 1
        except Exception:
            failed += 1

    return restored, failed

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
    Now supports both structures:
    1. Classic: parent/subfolders/csv_files
    2. Direct: csv_folder/csv_files

    Returns:
        Tuple of (total_file_count, list_of_folders_with_csv)
    """
    total_files = 0
    folders_with_csv = []

    # Check if this directory contains CSV files directly
    direct_csv_files = list(top_directory.glob('*.csv')) + list(top_directory.glob('*.CSV'))
    
    if direct_csv_files:
        # Direct CSV folder structure - treat the directory itself as the target
        total_files = len(direct_csv_files)
        folders_with_csv = [top_directory]
        return total_files, folders_with_csv

    # Classic subfolder structure - get all immediate subdirectories
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

        # Check if this is a direct CSV folder (contains CSV files directly)
        direct_csv_files = list(subfolder.glob('*.csv')) + list(subfolder.glob('*.CSV'))
        
        if direct_csv_files:
            # Direct CSV folder - use files directly in this folder
            csv_files = direct_csv_files
        elif csv_mode == 'any':
            # Classic subfolder structure - search recursively
            csv_files = list(subfolder.rglob('*.csv')) + list(subfolder.rglob('*.CSV'))
        else:
            # Specific subfolder mode
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


def display_summary(all_results: List[Dict], elapsed_time: float, interactive: bool = False):
    """Display overall summary of all folders analyzed"""
    total_folders = len(all_results)
    total_files = sum(r['total'] for r in all_results)
    total_detected = sum(r['detected'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)

    # Aggregate all encodings and build file mapping
    all_encodings = defaultdict(int)
    encoding_to_files = defaultdict(list)
    
    for results in all_results:
        for file_info in results['files']:
            encoding = file_info['encoding']
            file_path = file_info['path']
            confidence = file_info['confidence']
            
            all_encodings[encoding] += 1
            encoding_to_files[encoding].append({
                'path': str(file_path),  # Convert Path object to string
                'confidence': confidence,
                'folder': results['folder_name']
            })

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
        encoding_numbers = {}  # Map numbers to encodings for easy selection
        
        for i, (encoding, count) in enumerate(sorted_encodings, 1):
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
            
            encoding_numbers[i] = encoding
            print(f"  [{Colors.BOLD}{i}{Colors.NC}] {enc_color}{encoding}{Colors.NC}: {count} files ({percentage:.1f}%)")
        
        # Add interactive file listing functionality
        if interactive:
            return offer_encoding_exploration(encoding_numbers, encoding_to_files)
    
    return True


def offer_encoding_exploration(encoding_numbers: Dict[int, str], encoding_to_files: Dict[str, List[Dict]]):
    """Interactive exploration of files by encoding"""
    try:
        print(f"\n{Colors.CYAN}💡 Interactive File Explorer:{Colors.NC}")
        print(f"Enter a number [1-{len(encoding_numbers)}] to see all files with that encoding")
        print(f"Type '{Colors.BOLD}all{Colors.NC}' to see all files grouped by encoding")
        print(f"Type '{Colors.BOLD}q{Colors.NC}' to quit")
        
        while True:
            try:
                user_input = input(f"\n{Colors.YELLOW}🔍 Enter choice: {Colors.NC}").strip().lower()
                
                if user_input in ['q', 'quit', 'exit']:
                    print(f"{Colors.GREEN}👋 Goodbye!{Colors.NC}")
                    break
                
                if user_input == 'all':
                    display_all_files_by_encoding(encoding_to_files)
                    continue
                
                try:
                    choice = int(user_input)
                    if choice in encoding_numbers:
                        encoding = encoding_numbers[choice]
                        display_files_for_encoding(encoding, encoding_to_files[encoding])
                    else:
                        print(f"{Colors.RED}❌ Invalid choice. Please enter a number between 1 and {len(encoding_numbers)}{Colors.NC}")
                except ValueError:
                    print(f"{Colors.RED}❌ Invalid input. Please enter a number, 'all', or 'q'{Colors.NC}")
                    
            except (EOFError, KeyboardInterrupt):
                print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.NC}")
                break
                
    except Exception as e:
        print(f"{Colors.RED}❌ Error in interactive mode: {e}{Colors.NC}")
    
    return True


def display_files_for_encoding(encoding: str, files: List[Dict]):
    """Display all files that have a specific encoding"""
    if not files:
        print(f"{Colors.YELLOW}No files found for encoding: {encoding}{Colors.NC}")
        return
    
    # Color encoding name
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
    
    print(f"\n{Colors.BLUE}{'─' * 60}{Colors.NC}")
    print(f"{Colors.BOLD}📋 Files with encoding: {enc_color}{encoding}{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}")
    
    # Group by folder for better organization
    files_by_folder = defaultdict(list)
    for file_info in files:
        files_by_folder[file_info['folder']].append(file_info)
    
    for folder_name in sorted(files_by_folder.keys()):
        folder_files = files_by_folder[folder_name]
        if len(files_by_folder) > 1:  # Only show folder name if multiple folders
            print(f"\n{Colors.CYAN}📁 Folder: {folder_name}{Colors.NC}")
        
        for file_info in sorted(folder_files, key=lambda x: x['path']):
            confidence = file_info['confidence']
            confidence_color = Colors.GREEN if confidence > 0.8 else Colors.YELLOW if confidence > 0.5 else Colors.RED
            
            # Extract just the filename for cleaner display
            file_path = Path(file_info['path'])
            filename = file_path.name
            
            print(f"  📄 {Colors.BOLD}{filename}{Colors.NC}")
            print(f"     {Colors.BLUE}Path:{Colors.NC} {file_info['path']}")
            print(f"     {Colors.BLUE}Confidence:{Colors.NC} {confidence_color}{confidence:.2f}{Colors.NC}")


def display_all_files_by_encoding(encoding_to_files: Dict[str, List[Dict]]):
    """Display all files grouped by encoding"""
    print(f"\n{Colors.BLUE}{'═' * 70}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}📋 ALL FILES BY ENCODING{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 70}{Colors.NC}")
    
    # Sort encodings by file count (most common first)
    sorted_encodings = sorted(encoding_to_files.items(), key=lambda x: len(x[1]), reverse=True)
    
    for encoding, files in sorted_encodings:
        display_files_for_encoding(encoding, files)


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
  %(prog)s data --interactive  # Enable file explorer to browse by encoding
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
    parser.add_argument(
        '--convert-to',
        choices=['utf-8', 'utf-8-sig', 'ascii', 'iso-8859-1', 'windows-1252'],
        help='Convert all detected CSV files to target encoding'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview conversion without making changes'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating .bak backup files when converting'
    )

    parser.add_argument(
        '--convert-filter',
        help='Only convert files with specific source encoding (e.g., "iso-8859-1")'
    )

    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Restore all .bak files to original (undo conversions)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed file-by-file conversion progress'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable interactive file explorer to browse files by encoding'
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

    if args.rollback:
        print(f"{Colors.YELLOW}Rolling back .bak files...{Colors.NC}")
        restored, failed = rollback_backups(directory)
        print(f"{Colors.GREEN}Restored: {restored} files{Colors.NC}")
        if failed > 0:
            print(f"{Colors.RED}Failed: {failed} files{Colors.NC}")
        sys.exit(0)

    # Detect structure type
    direct_csv_files = list(directory.glob('*.csv')) + list(directory.glob('*.CSV'))
    structure_type = "direct" if direct_csv_files else "subfolder"
    
    # Perform analysis
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}CSV Character Encoding Detection{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"📁 Top directory: {Colors.GREEN}{directory.absolute()}{Colors.NC}")
    
    if structure_type == "direct":
        print(f"🔎 Structure: {Colors.GREEN}Direct CSV folder ({len(direct_csv_files)} CSV files found){Colors.NC}")
    elif args.csv_mode == 'any':
        print(f"🔎 Structure: {Colors.GREEN}Subfolder mode - **/*.csv (recursive search){Colors.NC}")
    else:
        print(f"📂 Structure: {Colors.GREEN}Specific subfolder mode - */{args.bak}/*.csv{Colors.NC}")
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
    display_summary(all_results, elapsed_time, args.interactive)

    # Perform conversion if requested
    if args.convert_to:
        print(f"\n{Colors.BLUE}{'─' * 60}{Colors.NC}")

        if args.dry_run:
            print(f"{Colors.BOLD}{Colors.YELLOW}DRY RUN MODE - No files will be modified{Colors.NC}")
        else:
            print(f"{Colors.BOLD}{Colors.CYAN}Starting Encoding Conversion to {args.convert_to}{Colors.NC}")
            if not args.no_backup:
                print(f"{Colors.DIM}Creating .bak backups for all converted files{Colors.NC}")

        # Add info about verbose mode
        if not args.verbose and not args.summary_only:
            total_to_process = sum(len(r['files']) for r in all_results)
            if total_to_process > 10:
                print(f"{Colors.DIM}Processing {total_to_process} files (use --verbose for file-by-file details){Colors.NC}")

        print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}\n")

        conversion_stats = []

        for results in all_results:
            # Filter files if requested
            if args.convert_filter:
                filtered_results = results.copy()
                filtered_results['files'] = [
                    f for f in results['files']
                    if f['encoding'].lower() == args.convert_filter.lower()
                ]
                if not filtered_results['files']:
                    continue
                results_to_convert = filtered_results
            else:
                results_to_convert = results

            # Show folder name with file count
            file_count = len(results_to_convert['files'])
            if file_count > 0:
                print(f"{Colors.CYAN}Converting in {results_to_convert['folder_name']} "
                      f"({file_count} files)...{Colors.NC}")

            stats = convert_folder_files(
                results_to_convert,
                args.convert_to,
                dry_run=args.dry_run,
                backup=not args.no_backup,
                show_progress=not args.summary_only,
                verbose=args.verbose
            )

            conversion_stats.append((results_to_convert['folder_name'], stats))

            # Add a separator between folders if not in summary-only mode
            if not args.summary_only and file_count > 0:
                print()  # Empty line between folders

    print(f"\n{Colors.GREEN}✅ Analysis complete!{Colors.NC}")


if __name__ == "__main__":
    main()
