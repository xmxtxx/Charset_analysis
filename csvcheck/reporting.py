from __future__ import annotations
from typing import Dict, List
from .colors import Colors
from .progress import format_time


def display_encoding_distribution(results: Dict, show_details: bool = False) -> None:
    folder_name = results['folder_name']
    total = results['detected']
    if total == 0:
        print(f"{Colors.YELLOW}No CSV files detected in {folder_name}{Colors.NC}")
        return
    print(f"{Colors.BOLD}{Colors.CYAN}Encoding Distribution {folder_name}:{Colors.NC}")
    sorted_encodings = sorted(results['encodings'].items(), key=lambda x: x[1], reverse=True)
    for encoding, count in sorted_encodings:
        percentage = (count / total) * 100
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


def display_summary(all_results: List[Dict], elapsed_time: float) -> None:
    total_folders = len(all_results)
    total_files = sum(r['total'] for r in all_results)
    total_detected = sum(r['detected'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)
    from collections import defaultdict
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
