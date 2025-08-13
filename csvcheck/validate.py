from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .progress import ProgressBar
from .colors import Colors


def _norm_delim(d: str) -> str:
    return '\t' if d == '\\t' else d


def sniff_dialect(sample_text: str, fallback_delims=(",", ";", "\t", "|"), quotechar='"') -> Tuple[str, csv.Dialect]:
    s = csv.Sniffer()
    try:
        dialect = s.sniff(sample_text, delimiters=fallback_delims)
        dialect.quotechar = quotechar
        return dialect.delimiter, dialect
    except Exception:
        # Heuristic fallback
        for line in sample_text.splitlines():
            if not line.strip():
                continue
            best = max(fallback_delims, key=line.count)
            class Simple(csv.Dialect):
                delimiter = best
                quotechar = quotechar
                doublequote = True
                escapechar = None
                lineterminator = "\n"
                quoting = csv.QUOTE_MINIMAL
                skipinitialspace = False
            return best, Simple
        class Simple(csv.Dialect):
            delimiter = ","
            quotechar = quotechar
            doublequote = True
            escapechar = None
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL
            skipinitialspace = False
        return ",", Simple


def validate_csv_file(
        file_path: Path,
        encoding: str,
        delimiter_opt: str = "auto",
        quotechar: str = '"',
        sample_rows: int = 0,
        max_field_size: int = 0,
        fail_fast: bool = False,
        sample_bytes: int = 65536,
) -> Dict:
    result = {"ok": True, "errors": [], "warnings": [], "stats": {"rows": 0, "min_cols": 10**9, "max_cols": 0, "delimiter": None, "header_cols": None}}
    if not encoding or encoding in ("unknown", "binary") or str(encoding).startswith("error"):
        result["ok"] = False
        result["errors"].append(f"Unusable encoding: {encoding}")
        return result
    if max_field_size > 0:
        try:
            csv.field_size_limit(max_field_size)
        except Exception:
            result["warnings"].append("Unable to set field_size_limit")
    try:
        with open(file_path, 'rb') as fb:
            head = fb.read(sample_bytes)
        sample_text = head.decode('utf-8', errors='replace')
        if delimiter_opt == 'auto':
            delim, dialect = sniff_dialect(sample_text, quotechar=quotechar)
        else:
            delim = _norm_delim(delimiter_opt)
            class Force(csv.Dialect):
                delimiter = delim
                quotechar = quotechar
                doublequote = True
                escapechar = None
                lineterminator = '\n'
                quoting = csv.QUOTE_MINIMAL
                skipinitialspace = False
            dialect = Force
        result['stats']['delimiter'] = '\\t' if delim == '\t' else delim
        header = None
        header_cols = None
        with open(file_path, 'r', encoding=encoding, errors='strict', newline='') as f:
            rdr = csv.reader(f, dialect=dialect)
            for idx, row in enumerate(rdr, start=1):
                if any('\x00' in cell for cell in row):
                    result['ok'] = False
                    result['errors'].append(f'Row {idx}: NUL byte in data')
                    if fail_fast: break
                cols = len(row)
                if idx == 1:
                    header = row
                    header_cols = cols
                    result['stats']['header_cols'] = cols
                    seen = set()
                    dups = []
                    for h in header:
                        if h in seen:
                            dups.append(h)
                        else:
                            seen.add(h)
                    if dups:
                        result['warnings'].append('Duplicate header names detected')
                else:
                    if header_cols is not None and cols != header_cols:
                        result['ok'] = False
                        result['errors'].append(f'Row {idx}: expected {header_cols} columns, found {cols}')
                        if fail_fast: break
                result['stats']['rows'] = idx
                result['stats']['min_cols'] = min(result['stats']['min_cols'], cols)
                result['stats']['max_cols'] = max(result['stats']['max_cols'], cols)
                if sample_rows and idx >= sample_rows:
                    break
    except UnicodeDecodeError as e:
        result['ok'] = False
        result['errors'].append(f'Unicode decode error: {str(e).splitlines()[0]}')
    except csv.Error as e:
        result['ok'] = False
        result['errors'].append(f'CSV parse error: {e}')
    except Exception as e:
        result['ok'] = False
        result['errors'].append(f'Error: {e}')
    if result['stats']['rows'] == 0:
        result['warnings'].append('No rows found (empty or header-only file?)')
    if result['stats']['min_cols'] == 10**9:
        result['stats']['min_cols'] = 0
    return result


def validate_all_files(
        all_results: List[Dict],
        delimiter_opt: str,
        quotechar: str,
        sample_rows: int,
        max_field_size: int,
        fail_fast: bool,
        show_progress: bool = True,
        jobs: Optional[int] = None,
) -> Dict:
    files = []
    for res in all_results:
        for f in res['files']:
            files.append((res['folder_name'], f['path'], f['encoding']))
    report = {'folders': {}, 'totals': {'ok': 0, 'bad': 0}}
    if not files:
        return report
    progress = ProgressBar(len(files), title="Validating CSV files") if show_progress else None
    def _one(args):
        folder_name, path, enc = args
        out = validate_csv_file(
            file_path=path,
            encoding=enc,
            delimiter_opt=delimiter_opt,
            quotechar=quotechar,
            sample_rows=sample_rows,
            max_field_size=max_field_size,
            fail_fast=fail_fast,
        )
        return folder_name, path.name, out
    import os
    cpu = os.cpu_count() or 1
    requested = jobs if (jobs and jobs > 0) else max(1, (cpu // 2))
    capped = min(requested, cpu * 2, len(files))
    max_workers = max(1, capped)
    processed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_one, f) for f in files]
        for fut in as_completed(futs):
            folder_name, fname, out = fut.result()
            if folder_name not in report['folders']:
                report['folders'][folder_name] = {'ok': 0, 'bad': 0, 'files': []}
            bucket = report['folders'][folder_name]
            bucket['files'].append((fname, out['ok'], out['errors'], out['warnings'], out['stats']))
            if out['ok']:
                bucket['ok'] += 1
                report['totals']['ok'] += 1
            else:
                bucket['bad'] += 1
                report['totals']['bad'] += 1
            processed += 1
            if progress:
                progress.update(processed, f'{folder_name}/{fname}')
    if progress:
        progress.finish()
    return report

def print_validation_report(report: Dict, verbose: bool = False) -> None:
    """
    Compact summary like the scanner. By default:
      - Total OK / Bad / Files
      - Per-folder: OK, Bad
    If verbose=True:
      - Additionally list bad files per folder (limited to a few lines per file).
    """
    # hardcoded compact limits (not user-configurable)
    MAX_ERRORS_PER_FILE = 3

    tot_files = report.get('totals', {}).get('files', 0)
    tot_ok    = report.get('totals', {}).get('ok', 0)
    tot_bad   = report.get('totals', {}).get('bad', 0)
    interrupted = report.get('interrupted', False)

    print(f"\n{Colors.BLUE}{'═' * 50}{Colors.NC}")
    title = "CSV VALIDATION SUMMARY"
    if interrupted:
        title += " (partial)"
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 50}{Colors.NC}")

    print(f"Total files checked: {Colors.BLUE}{tot_files}{Colors.NC}")
    print(f"Files OK: {Colors.GREEN}{tot_ok}{Colors.NC}")
    print(f"Malformed: {Colors.RED}{tot_bad}{Colors.NC}")

    # Per-folder counts
    for folder_name in sorted(report.get('folders', {}).keys()):
        info = report['folders'][folder_name]
        ok = info.get('ok', 0)
        bad = info.get('bad', 0)
        print(f"{Colors.BOLD}{folder_name}{Colors.NC}: "
              f"{Colors.GREEN}{ok} ok{Colors.NC}, {Colors.RED}{bad} bad{Colors.NC}")

        if verbose and bad > 0:
            # List only the bad files
            for fname, ok_flag, errors, warnings, stats in sorted(info['files']):
                if ok_flag:
                    continue
                rows = stats.get('rows')
                hc = stats.get('header_cols')
                delim = stats.get('delimiter')
                print(f"  • {fname}: {Colors.RED}BAD{Colors.NC} "
                      f"{Colors.DIM}(rows={rows}, header_cols={hc}, delim={delim}){Colors.NC}")
                # Show a few key errors
                if errors:
                    for e in errors[:MAX_ERRORS_PER_FILE]:
                        print(f"    {Colors.RED}✗{Colors.NC} {e}")
                    extra = len(errors) - MAX_ERRORS_PER_FILE
                    if extra > 0:
                        print(f"    {Colors.DIM}… {extra} more errors{Colors.NC}")
                # Warnings (one-line summary)
                if warnings:
                    print(f"    {Colors.YELLOW}⚠{Colors.NC} {warnings[0]}")
                    if len(warnings) > 1:
                        print(f"    {Colors.DIM}… {len(warnings)-1} more warnings{Colors.NC}")

