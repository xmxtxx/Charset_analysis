from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from .colors import Colors
from .folder_scan import analyze_all_subfolders, count_total_csv_files, DEFAULT_JOBS
from .reporting import display_encoding_distribution, display_summary
from .convert import convert_folder_files, display_conversion_summary
from .validate import validate_all_files, print_validation_report


def _print_header(directory: Path, csv_mode: str, bak: str) -> None:
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}CSV Character Encoding Detection{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"📁 Top directory: {Colors.GREEN}{directory.absolute()}{Colors.NC}")
    if csv_mode == 'any':
        print(f"🔎 CSV search: {Colors.GREEN}**/*.csv (recursive under each subfolder){Colors.NC}")
    else:
        print(f"📂 CSV location: {Colors.GREEN}*/{bak}/*.csv{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='Detect character encoding of CSV files in structured folders with progress tracking (offline)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s data\n"
            "  %(prog)s /path/to/top --csv-mode subdir --bak archive\n"
            "  %(prog)s data -j 8 --fast\n"
        ),
    )
    parser.add_argument('directory', nargs='?', default='.', help='Top-level directory containing subfolders (default: current directory)')
    parser.add_argument('--csv-mode', choices=['any', 'subdir'], default='any', help='Where to look for CSV files: "any" or only inside --bak')
    parser.add_argument('--bak', default='bak', help='Subfolder name when --csv-mode subdir (default: bak)')
    parser.add_argument('-d', '--details', action='store_true', help='Show detailed information for each folder')
    parser.add_argument('-s', '--summary-only', action='store_true', help='Show only the overall summary')
    parser.add_argument('--pattern', choices=['underscore', 'all'], default='all', help='Folder selection: "all" or only names containing an underscore')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress bar')
    parser.add_argument('-j', '--jobs', type=int, default=DEFAULT_JOBS, help=f'Number of parallel workers (default: half cores = {DEFAULT_JOBS})')
    parser.add_argument('--fast', action='store_true', help='Faster single-pass detection (lower I/O)')
    parser.add_argument('--sample-size', type=int, default=65536, help='Bytes to sample per pass (default: 65536)')
    parser.add_argument('--name-delims', default='_- ', help='Delimiters for display names (default: "_- ")')

    # Conversion options
    parser.add_argument('--convert-to', choices=['utf-8', 'utf-8-sig', 'ascii', 'iso-8859-1', 'windows-1252'], help='Convert all detected CSV files to target encoding')
    parser.add_argument('--dry-run', action='store_true', help='Preview conversion without making changes')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating .bak backup files when converting')
    parser.add_argument('--convert-filter', help='Only convert files with specific source encoding (e.g., "iso-8859-1")')
    parser.add_argument('--rollback', action='store_true', help='Restore all .bak files to original (undo conversions)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed file-by-file conversion progress')

    # Validation options
    parser.add_argument('--validate', action='store_true', help='Validate CSV structure (delimiter, quoting, consistent columns)')
    parser.add_argument('--validate-sample-rows', type=int, default=0, help='If >0, only validate first N data rows')
    parser.add_argument('--delimiter', default='auto', help='Delimiter to use (",", ";", "\\t", "|", or "auto")')
    parser.add_argument('--quotechar', default='"', help='Quote character (default: ")')
    parser.add_argument('--max-field-size', type=int, default=0, help='If >0, set csv.field_size_limit to this many bytes')
    parser.add_argument('--fail-fast', action='store_true', help='Stop at first structural error per file')

    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.exists():
        print(f"{Colors.RED}Error: Directory '{directory}' does not exist{Colors.NC}")
        return 1
    if not directory.is_dir():
        print(f"{Colors.RED}Error: '{directory}' is not a directory{Colors.NC}")
        return 1

    if args.rollback:
        from .convert import shutil
        print(f"{Colors.YELLOW}Rolling back .bak files...{Colors.NC}")
        restored = 0
        failed = 0
        for backup_file in directory.rglob('*.csv.bak'):
            original = backup_file.with_suffix('')
            try:
                shutil.move(str(backup_file), str(original))
                restored += 1
            except Exception:
                failed += 1
        print(f"{Colors.GREEN}Restored: {restored} files{Colors.NC}")
        if failed > 0:
            print(f"{Colors.RED}Failed: {failed} files{Colors.NC}")
        return 0

    _print_header(directory, args.csv_mode, args.bak)

    pattern = None if args.pattern == 'all' else args.pattern
    start_time = time.time()
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
            name_delims=args.name_delims,
        )
    except KeyboardInterrupt:
        print(f"{Colors.YELLOW}↩ Ctrl+C detected. Shutting down gracefully...{Colors.NC}")
        return 130

    if not all_results:
        where = "**/*.csv" if args.csv_mode == 'any' else f"*/{args.bak}/*.csv"
        print(f"{Colors.YELLOW}⚠️  No CSV files found at {where}{Colors.NC}")
        return 0

    if not args.summary_only:
        print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}Results by Folder:{Colors.NC}\n")
        for results in all_results:
            display_encoding_distribution(results, args.details)
            print()

    elapsed_time = time.time() - start_time
    display_summary(all_results, elapsed_time)

    # Optional validation
    if args.validate:
        print(f"\n{Colors.BLUE}{'─' * 60}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}Starting CSV Validation{Colors.NC}")
        report = validate_all_files(
            all_results=all_results,
            delimiter_opt=args.delimiter,
            quotechar=args.quotechar,
            sample_rows=args.validate_sample_rows,
            max_field_size=args.max_field_size,
            fail_fast=args.fail_fast,
            show_progress=not args.no_progress,
            jobs=args.jobs,
        )
        print_validation_report(report, verbose=args.details)

    # Optional conversion
    if args.convert_to:
        print(f"\n{Colors.BLUE}{'─' * 60}{Colors.NC}")
        if args.dry_run:
            print(f"{Colors.BOLD}{Colors.YELLOW}DRY RUN MODE - No files will be modified{Colors.NC}")
        else:
            print(f"{Colors.BOLD}{Colors.CYAN}Starting Encoding Conversion to {args.convert_to}{Colors.NC}")
            if not args.no_backup:
                print(f"{Colors.DIM}Creating .bak backups for all converted files{Colors.NC}")
        if not args.verbose and not args.summary_only:
            total_to_process = sum(len(r['files']) for r in all_results)
            if total_to_process > 10:
                print(f"{Colors.DIM}Processing {total_to_process} files (use --verbose for file-by-file details){Colors.NC}")
        print(f"{Colors.BLUE}{'─' * 60}{Colors.NC}\n")
        conversion_stats = []
        for results in all_results:
            if args.convert_filter:
                filtered_results = results.copy()
                filtered_results['files'] = [f for f in results['files'] if f['encoding'].lower() == args.convert_filter.lower()]
                if not filtered_results['files']:
                    continue
                results_to_convert = filtered_results
            else:
                results_to_convert = results
            file_count = len(results_to_convert['files'])
            if file_count > 0:
                print(f"{Colors.CYAN}Converting in {results_to_convert['folder_name']} ({file_count} files)...{Colors.NC}")
            stats = convert_folder_files(
                results_to_convert,
                args.convert_to,
                dry_run=args.dry_run,
                backup=not args.no_backup,
                show_progress=not args.summary_only,
                verbose=args.verbose,
            )
            conversion_stats.append((results_to_convert['folder_name'], stats))
            if not args.summary_only and file_count > 0:
                print()
        display_conversion_summary(conversion_stats, args.convert_to, dry_run=args.dry_run)

    print(f"\n{Colors.GREEN}✅ Analysis complete!{Colors.NC}")
    return 0