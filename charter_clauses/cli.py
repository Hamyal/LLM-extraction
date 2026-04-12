from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from charter_clauses.llm_extract import clauses_to_jsonable, extract_clauses_llm
from charter_clauses.pdf_extract import (
    DEFAULT_PART2_FIRST_PAGE,
    DEFAULT_PART2_LAST_PAGE,
    extract_part2_text,
)

# Project root (parent of `charter_clauses/`) so `.env` loads regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract Part II legal clauses from a voyage charter PDF using an LLM.",
    )
    p.add_argument(
        "pdf",
        nargs="?",
        default="voyage-charter-example.pdf",
        help="Path to the charter party PDF (default: %(default)s)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON to this file (default: stdout)",
    )
    p.add_argument(
        "--first-page",
        type=int,
        default=DEFAULT_PART2_FIRST_PAGE,
        help="First page of Part II (1-based, default: %(default)s)",
    )
    p.add_argument(
        "--last-page",
        type=int,
        default=DEFAULT_PART2_LAST_PAGE,
        help="Last page of Part II (1-based, inclusive, default: %(default)s)",
    )
    p.add_argument(
        "--page-markers",
        action="store_true",
        help="Insert --- Page N --- markers (useful with Ollama chunking: OLLAMA_CHUNK=1).",
    )
    p.add_argument(
        "--no-env-file",
        action="store_true",
        help="Do not load a .env file",
    )
    p.add_argument(
        "--no-dedupe-by-id",
        action="store_true",
        help="Disable merging duplicate clause ids (default: merge overlapping chunk duplicates).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.no_env_file:
        load_dotenv(_PROJECT_ROOT / ".env")

    pdf = Path(args.pdf)
    if not pdf.is_file():
        print(f"PDF not found: {pdf}", file=sys.stderr)
        return 1

    part2 = extract_part2_text(
        pdf,
        args.first_page,
        args.last_page,
        page_markers=args.page_markers,
    )
    try:
        clauses = extract_clauses_llm(part2, dedupe_by_id=not args.no_dedupe_by_id)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    payload = {"clauses": clauses_to_jsonable(clauses)}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
