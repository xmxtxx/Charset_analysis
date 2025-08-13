from __future__ import annotations
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from .colors import Colors


def _normalize_enc_for_target(source: str, target: str) -> str:
    """Normalize source encoding name for comparison against a target.

    - Unifies common aliases (utf8 → utf-8, us-ascii → ascii)
    - Treats ASCII as already OK when target is UTF-8 (since ASCII ⊂ UTF-8)
    - (Optional) You can also consider UTF-8-SIG as UTF-8 if you do not care
      about removing BOMs — see commented lines below.
    """
    s = (source or "").lower()
    t = (target or "").lower()

    aliases = {
        "utf8": "utf-8",
        "utf_8": "utf-8",
        "us-ascii": "ascii",
    }
    s = aliases.get(s, s)
    t = aliases.get(t, t)

    # ASCII is valid UTF-8, so skip converting when target is utf-8
    if t == "utf-8" and s == "ascii":
        return t

    # (Optional) If you don't want to strip BOMs, uncomment this:
    # if t == "utf-8" and s == "utf-8-sig":
    #     return t

    return s


def convert_file_encoding(
        file_path: Path,
        target_encoding: str,
        source_encoding: str,
        backup: bool = True,
) -> Tuple[bool, str]:
    """Convert a single file from source to target encoding.

    Returns (success, message). The message is "already_target" when no work
    is necessary.
    """
    try:
        # Early-out: if effectively already the target, do nothing
        if _normalize_enc_for_target(source_encoding, target_encoding) == target_encoding.lower():
            return True, "already_target"

        if source_encoding in ["unknown", "binary"] or str(source_encoding).startswith("error"):
            return False, f"Cannot convert from {source_encoding}"

        # Read with source encoding
        with open(file_path, "r", encoding=source_encoding, errors="strict") as f:
            content = f.read()

        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)

        # Write with target encoding
        with open(file_path, "w", encoding=target_encoding, errors="strict") as f:
            f.write(content)

        return True, f"Converted from {source_encoding} to {target_encoding}"

    except UnicodeDecodeError as e:
        return False, f"Decode error: {str(e)[:50]}"
    except UnicodeEncodeError as e:
        return False, f"Encode error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


def convert_folder_files(
        folder_result: Dict,
        target_encoding: str,
        dry_run: bool = False,
        backup: bool = True,
        show_progress: bool = True,
        verbose: bool = False,
) -> Dict:
    """Convert all files listed in a folder_result to target encoding.

    Tracks counts by original source encoding and records failures.
    """
    stats = {
        "total": len(folder_result["files"]),
        "converted": 0,
        "skipped": 0,
        "failed": 0,
        "already_target": 0,
        "failed_files": [],  # list of (filename, error)
        "by_encoding": defaultdict(int),
    }

    show_individual = verbose or stats["total"] <= 10

    for i, file_info in enumerate(folder_result["files"], 1):
        file_path = file_info["path"]
        source_encoding = file_info["encoding"]
        norm_source = _normalize_enc_for_target(source_encoding, target_encoding)

        if dry_run:
            if norm_source == target_encoding.lower():
                stats["already_target"] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.DIM}[SKIP]{Colors.NC} {file_path.name} - already {target_encoding}")
            elif source_encoding in ["unknown", "binary"] or str(source_encoding).startswith("error"):
                stats["skipped"] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.YELLOW}[SKIP]{Colors.NC} {file_path.name} - {source_encoding}")
            else:
                stats["converted"] += 1
                stats["by_encoding"][source_encoding] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.GREEN}[WOULD CONVERT]{Colors.NC} {file_path.name}: {source_encoding} → {target_encoding}")
        else:
            # Short-circuit to avoid I/O when effectively already target
            if norm_source == target_encoding.lower():
                stats["already_target"] += 1
                if show_individual and show_progress:
                    print(f"  {Colors.DIM}[SKIP]{Colors.NC} {file_path.name} - already {target_encoding}")
            else:
                success, message = convert_file_encoding(file_path, target_encoding, source_encoding, backup)
                if success:
                    stats["converted"] += 1
                    stats["by_encoding"][source_encoding] += 1
                    if show_individual and show_progress:
                        print(f"  {Colors.GREEN}✓{Colors.NC} {file_path.name}: {source_encoding} → {target_encoding}")
                else:
                    stats["failed"] += 1
                    stats["failed_files"].append((file_path.name, message))
                    if show_individual and show_progress:
                        print(f"  {Colors.RED}✗{Colors.NC} {file_path.name}: {message}")

        # Compact progress hint for large batches
        if not show_individual and show_progress and i % 100 == 0:
            print(f"  {Colors.DIM}Processed {i}/{stats['total']} files...{Colors.NC}", end='\r')

    # Clear the progress line
    if not show_individual and show_progress and stats["total"] > 10:
        print(" " * 80, end='\r')

    # Folder-level summary (if we suppressed per-file lines)
    if not show_individual and show_progress and (stats["converted"] > 0 or stats["failed"] > 0):
        print(f"  {Colors.CYAN}Summary:{Colors.NC}")
        action = "Converted" if not dry_run else "Would convert"
        for enc, count in stats["by_encoding"].items():
            print(f"    • {action} {Colors.GREEN}{count}{Colors.NC} files from {enc}")
        if stats["already_target"] > 0:
            print(f"    • Already {target_encoding}: {Colors.BLUE}{stats['already_target']}{Colors.NC} files")
        if stats["skipped"] > 0:
            print(f"    • Skipped (unknown/binary): {Colors.YELLOW}{stats['skipped']}{Colors.NC} files")
        if stats["failed"] > 0:
            print(f"    • Failed: {Colors.RED}{stats['failed']}{Colors.NC} files")

    return stats


def display_conversion_summary(
        all_conversion_stats: List[Tuple[str, Dict]],
        target_encoding: str,
        dry_run: bool = False,
) -> None:
    total_converted = sum(stats["converted"] for _, stats in all_conversion_stats)
    total_failed = sum(stats["failed"] for _, stats in all_conversion_stats)
    total_already = sum(stats["already_target"] for _, stats in all_conversion_stats)
    total_skipped = sum(stats["skipped"] for _, stats in all_conversion_stats)

    encoding_totals = defaultdict(int)
    for _, stats in all_conversion_stats:
        for enc, count in stats["by_encoding"].items():
            encoding_totals[enc] += count

    mode = "DRY RUN" if dry_run else "CONVERSION"
    print(f"\n{Colors.BLUE}{'═' * 50}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{mode} SUMMARY → {target_encoding.upper()}{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 50}{Colors.NC}")

    if encoding_totals:
        action = "Would convert" if dry_run else "Converted"
        print(f"\n{Colors.BOLD}{action} by source encoding:{Colors.NC}")
        for enc, count in sorted(encoding_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"  {Colors.GREEN}{enc}{Colors.NC}: {count} files")

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
