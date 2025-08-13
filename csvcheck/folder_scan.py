from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from .detectors import detect_encoding
from .progress import ProgressBar
from .colors import Colors

DEFAULT_JOBS = max(1, (os.cpu_count() or 1) // 2)


def get_folder_display_name(folder_path: Path, delimiters: str = "_- ") -> str:
    name = folder_path.name
    first_idx = None
    for ch in delimiters:
        idx = name.find(ch)
        if idx != -1 and (first_idx is None or idx < first_idx):
            first_idx = idx
    if first_idx is None:
        return name
    return name[first_idx + 1 :]


def count_total_csv_files(
        top_directory: Path,
        pattern: Optional[str] = None,
        bak_folder: str = "bak",
        csv_mode: str = "any",
) -> Tuple[int, List[Path]]:
    total_files = 0
    folders_with_csv: List[Path] = []
    subfolders = [d for d in top_directory.iterdir() if d.is_dir()]
    if pattern:
        if pattern == "underscore":
            subfolders = [d for d in subfolders if "_" in d.name]
    for subfolder in sorted(subfolders):
        if csv_mode == "any":
            csv_files = list(subfolder.rglob("*.csv")) + list(subfolder.rglob("*.CSV"))
        else:
            bak_path = subfolder / bak_folder
            if bak_path.exists() and bak_path.is_dir():
                csv_files = list(bak_path.glob("*.csv")) + list(bak_path.glob("*.CSV"))
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
        min_confidence_first_pass=0.70,
    )
    return file_path, enc, conf, folder_path, folder_display_name


def analyze_all_subfolders(
        top_directory: Path,
        pattern: Optional[str] = None,
        bak_folder: str = "bak",
        csv_mode: str = "any",
        show_progress: bool = True,
        jobs: Optional[int] = None,
        fast: bool = False,
        sample_size: int = 65536,
        name_delims: str = "_- ",
) -> List[Dict]:
    """Analyze all subfolders in parallel with a progress bar."""
    all_results: List[Dict] = []
    print(f"{Colors.CYAN}Scanning folders...{Colors.NC}")
    total_files, folders_with_csv = count_total_csv_files(top_directory, pattern, bak_folder, csv_mode)
    if total_files == 0:
        return all_results
    print(f"{Colors.GREEN}Found {total_files} CSV files in {len(folders_with_csv)} folders{Colors.NC}\n")
    folder_result_map: Dict[Path, Dict] = {}
    tasks = []
    for subfolder in folders_with_csv:
        display_name = get_folder_display_name(subfolder, name_delims)
        res = {
            "folder_path": subfolder,
            "folder_name": display_name,
            "files": [],
            "encodings": defaultdict(int),
            "total": 0,
            "detected": 0,
            "errors": 0,
        }
        folder_result_map[subfolder] = res
        if csv_mode == "any":
            csv_files = list(subfolder.rglob("*.csv")) + list(subfolder.rglob("*.CSV"))
        else:
            bak_path = subfolder / bak_folder
            csv_files = list(bak_path.glob("*.csv")) + list(bak_path.glob("*.CSV")) if bak_path.exists() else []
        res["total"] = len(csv_files)
        for f in csv_files:
            tasks.append((f, subfolder, res["folder_name"], sample_size, not fast))
    progress_bar = ProgressBar(total_files, title="Processing CSV files") if show_progress else None
    processed = 0
    cpu = os.cpu_count() or 1
    requested = jobs if (jobs and jobs > 0) else DEFAULT_JOBS
    capped = min(requested, cpu * 2, total_files)
    if capped < requested:
        print(
            f"{Colors.YELLOW}ℹ Limiting jobs from {requested} to {capped} "
            f"(CPU={cpu}, files={total_files}) for stability{Colors.NC}"
        )
    max_workers = max(1, capped)
    ex = None
    futures = []
    try:
        ex = ProcessPoolExecutor(max_workers=max_workers)
        futures = [ex.submit(_detect_one, t) for t in tasks]
        for fut in as_completed(futures):
            file_path, encoding, confidence, folder_path, folder_display_name = fut.result()
            res = folder_result_map[folder_path]
            res["files"].append({"path": file_path, "name": file_path.name, "encoding": encoding, "confidence": confidence})
            if encoding and not str(encoding).startswith("error") and encoding != "unknown":
                res["detected"] += 1
                res["encodings"][encoding] += 1
            else:
                res["errors"] += 1
            processed += 1
            if progress_bar:
                progress_bar.update(processed, f"{folder_display_name}/{file_path.name}")
    except KeyboardInterrupt:
        if progress_bar:
            print()
        print(f"{Colors.YELLOW}↩ Ctrl+C detected. Shutting down gracefully...{Colors.NC}")
        try:
            for fut in futures:
                fut.cancel()
        except Exception:
            pass
        try:
            ex.shutdown(wait=False, cancel_futures=True)  # type: ignore
        except TypeError:
            ex.shutdown(wait=False)
        except Exception:
            pass
        return [folder_result_map[f] for f in folders_with_csv if folder_result_map[f]["total"] > 0]
    finally:
        if ex is not None:
            try:
                ex.shutdown(wait=False)
            except Exception:
                pass
    if progress_bar:
        progress_bar.finish()
    print()
    return [folder_result_map[f] for f in folders_with_csv if folder_result_map[f]["total"] > 0]