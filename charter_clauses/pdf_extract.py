from __future__ import annotations

import re
from pathlib import Path

import fitz


# Part II in the reference document: pages 6–39 (1-based), inclusive.
DEFAULT_PART2_FIRST_PAGE = 6
DEFAULT_PART2_LAST_PAGE = 39


def _strip_margin_line_numbers(text: str) -> str:
    """
    Remove standalone line reference numbers (e.g. margin '67', '68') common in
    legal PDFs; they are not part of clause text.
    """
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if re.fullmatch(r"\d{1,4}", s):
            continue
        out.append(line)
    return "\n".join(out)


def _split_heading_from_leading_number(text: str) -> str:
    """
    Many charter PDFs fuse a heading with the first clause number on one line.
    Split patterns like 'Condition              1. Owners' into separate lines.
    """
    return re.sub(r"(\s{4,})(\d+\.\s)", r"\n\n\2", text)


def _strip_inline_line_refs(text: str) -> str:
    """
    Remove 2–4 digit line references that sit between words and newlines (e.g. 'the    68').
    """
    text = re.sub(
        r"(?<=[a-zA-Z.,;:)\]])[\t ]{2,}\d{2,4}(?=\s*\n)",
        "",
        text,
    )
    text = re.sub(r"\s{2,}\d{2,4}(?=\s*\n)", "\n", text)
    return text


def _collapse_blank_runs(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_part2_preamble(text: str) -> str:
    """Remove boilerplate before the first Part II heading (e.g. issue date, form name)."""
    m = re.search(r"(?im)^(PART II|Condition)\b", text)
    if m:
        return text[m.start() :].strip()
    return text


def normalize_part2_plain_text(raw: str) -> str:
    """
    Heuristic cleanup after raw PDF extraction: margin numbers, fused headings,
    inline line references. Improves LLM and downstream parsing quality.
    """
    t = _strip_margin_line_numbers(raw)
    t = _split_heading_from_leading_number(t)
    t = _strip_inline_line_refs(t)
    t = _collapse_blank_runs(t)
    return _strip_part2_preamble(t)


def extract_part2_text(
    pdf_path: str | Path,
    first_page: int = DEFAULT_PART2_FIRST_PAGE,
    last_page: int = DEFAULT_PART2_LAST_PAGE,
    *,
    page_markers: bool = False,
) -> str:
    """
    Extract plain text from Part II (inclusive page range, 1-based).
    Part I (pages before `first_page`) is not read.
    """
    path = Path(pdf_path)
    doc = fitz.open(path)
    try:
        if last_page > doc.page_count:
            raise ValueError(
                f"last_page {last_page} exceeds document length ({doc.page_count} pages)"
            )
        parts: list[str] = []
        for pno in range(first_page - 1, last_page):
            page = doc[pno]
            block = page.get_text(sort=True)
            if page_markers:
                block = f"--- Page {pno + 1} ---\n{block}"
            parts.append(block)
        raw = "\n\n".join(parts)
        return normalize_part2_plain_text(raw)
    finally:
        doc.close()


def page_count(pdf_path: str | Path) -> int:
    doc = fitz.open(Path(pdf_path))
    try:
        return doc.page_count
    finally:
        doc.close()
