from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple

# Prefer cchardet, fallback to chardet
try:  # pragma: no cover
    import cchardet as chardet  # type: ignore
except Exception:  # pragma: no cover
    import chardet  # type: ignore


def detect_bom(sample: bytes) -> Optional[str]:
    if sample.startswith(b"\xEF\xBB\xBF"):
        return "utf-8-sig"
    if sample.startswith(b"\xFF\xFE\x00\x00"):
        return "utf-32-le"
    if sample.startswith(b"\x00\x00\xFE\xFF"):
        return "utf-32-be"
    if sample.startswith(b"\xFF\xFE"):
        return "utf-16-le"
    if sample.startswith(b"\xFE\xFF"):
        return "utf-16-be"
    return None


def guess_utf16_no_bom(sample: bytes) -> Optional[str]:
    if len(sample) < 4:
        return None
    even_zeros = sum(1 for i in range(0, len(sample), 2) if sample[i] == 0)
    odd_zeros = sum(1 for i in range(1, len(sample), 2) if sample[i] == 0)
    half = max(1, len(sample) // 2)
    even_ratio = even_zeros / half
    odd_ratio = odd_zeros / half
    if odd_ratio > 0.40 and even_ratio < 0.20:
        return "utf-16-le"
    if even_ratio > 0.40 and odd_ratio < 0.20:
        return "utf-16-be"
    return None


def is_mostly_ascii(sample: bytes, thresh: float = 0.98) -> bool:
    if not sample:
        return False
    ascii_bytes = sum(1 for b in sample if b < 0x80)
    return (ascii_bytes / len(sample)) >= thresh


def is_binary_like(sample: bytes, nul_thresh: float = 0.30) -> bool:
    if not sample:
        return False
    nul_ratio = sample.count(0) / len(sample)
    return nul_ratio >= nul_thresh


def detect_encoding(
        file_path: Path,
        sample_size: int = 65536,
        do_second_pass: bool = True,
        second_pass_factor: int = 4,
        min_confidence_first_pass: float = 0.70,
) -> Tuple[str, float]:
    """Detect the character encoding of a file. Returns (encoding, confidence%)."""
    try:
        fsize = os.path.getsize(file_path)
        if fsize == 0:
            return "unknown", 0.0
        with open(file_path, "rb") as f:
            head = f.read(min(sample_size, fsize))
            bom_enc = detect_bom(head)
            if bom_enc:
                return bom_enc, 100.0
            head_res = chardet.detect(head)
            head_enc = head_res.get("encoding") or "unknown"
            head_conf = float(head_res.get("confidence") or 0.0)
            if fsize <= sample_size:
                if head_enc != "unknown":
                    return head_enc, head_conf * 100.0
                utf16_guess = guess_utf16_no_bom(head)
                if utf16_guess:
                    return utf16_guess, 95.0
                if is_mostly_ascii(head):
                    return "ascii", 99.0
                if is_binary_like(head):
                    return "binary", 100.0
                return "unknown", 0.0
            if head_conf >= min_confidence_first_pass:
                return head_enc, head_conf * 100.0
            try:
                f.seek(max(0, fsize - sample_size))
                tail = f.read(sample_size)
            except Exception:
                tail = b""
            combined = head + tail if tail else head
            comb_res = chardet.detect(combined)
            comb_enc = comb_res.get("encoding") or "unknown"
            comb_conf = float(comb_res.get("confidence") or 0.0)
            if comb_conf >= min_confidence_first_pass and comb_enc != "unknown":
                return comb_enc, comb_conf * 100.0
            if do_second_pass:
                f.seek(0)
                big = f.read(min(fsize, sample_size * second_pass_factor))
                bom2 = detect_bom(big)
                if bom2:
                    return bom2, 100.0
                big_res = chardet.detect(big)
                big_enc = big_res.get("encoding") or "unknown"
                big_conf = float(big_res.get("confidence") or 0.0)
                if big_enc != "unknown":
                    return big_enc, big_conf * 100.0
                utf16_guess2 = guess_utf16_no_bom(big)
                if utf16_guess2:
                    return utf16_guess2, 95.0
                if is_mostly_ascii(big):
                    return "ascii", 99.0
                if is_binary_like(big):
                    return "binary", 100.0
            return "unknown", 0.0
    except Exception as e:  # pragma: no cover
        return f"error: {str(e)}", 0.0
