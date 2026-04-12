from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from openai import LengthFinishReasonError, OpenAI

from charter_clauses.models import Clause, ClauseExtractionResult

SYSTEM_PROMPT = """You are a maritime contracts analyst. You receive plain text from \
Part II of a voyage charter party (ShellVoy-style form plus possible rider clauses).

Task:
- Split the text into individual legal clauses in the order they appear.
- For each clause, capture:
  - id: the clause number as printed (digits; if the same number appears again in a rider \
section, use a suffix like "4-Rider" or "19-Rider" so ids stay unique).
  - title: the clause heading. Combine multi-line headings (e.g. "Condition" + "Of vessel" \
→ "Condition Of vessel"). If there is no separate heading, derive a short neutral title \
from the first words of the clause.
  - text: the full substantive body of that clause, including lettered subparagraphs like \
(a), (b), (i), (ii) as part of the same clause unless they are clearly a separate \
numbered clause in the document.

Rules:
- Skip Part I / particulars if any appear in the input.
- Do NOT include strike-through, deleted, or visibly superseded text. If two versions of \
the same numbered clause appear and one is clearly obsolete or struck through, keep only \
the operative version.
- Do not include page headers, footers, or isolated line numbers.
- Preserve legal meaning; minor whitespace normalization is fine.
"""

CHUNK_USER_WRAPPER = """This is a contiguous section of Part II (page markers may appear). \
Extract every numbered clause that begins or continues in this section. If a clause clearly \
started on a previous page and only continuation text appears here, include that continuation \
as part of the same clause id you would assign for the full clause (you may still output \
the full clause text visible in this chunk only — the application will merge chunks).

---

{text}"""

CHUNK_SYSTEM_EXTRA = (
    "You may receive only a portion of Part II. Extract every clause that appears in this "
    "portion, in order. If a clause is cut off at a chunk boundary, include the visible text "
    "under that clause id; later chunks may continue the same id and will be merged."
)


def _client() -> OpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or empty. Put your key on the same line as "
            "OPENAI_API_KEY= in .env, save the file (Ctrl+S), and run again — or export "
            "OPENAI_API_KEY in your shell."
        )
    base_url = os.getenv("OPENAI_BASE_URL")
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _model_name() -> str:
    return os.getenv("CHARTER_EXTRACTION_MODEL", "gpt-4o-mini")


def _parse_clause_json(data: str) -> ClauseExtractionResult:
    return ClauseExtractionResult.model_validate_json(data)


def _merge_clause_texts(a: str, b: str) -> str:
    """Join two text blobs; avoid duplication when one is a substring of the other."""
    a, b = a.strip(), b.strip()
    if not b:
        return a
    if not a:
        return b
    if b in a:
        return a
    if a in b:
        return b
    return a + "\n\n" + b


def dedupe_clauses_by_id(clauses: list[Clause]) -> list[Clause]:
    """
    Collapse repeated clause ids (e.g. from overlapping LLM chunks) while keeping
    first-seen order. Distinct ids such as '4' vs '4-Rider' remain separate.
    """
    if not clauses:
        return []
    order: list[str] = []
    merged: dict[str, Clause] = {}
    for c in clauses:
        key = c.id.strip()
        if key not in merged:
            order.append(key)
            merged[key] = Clause(
                id=c.id.strip(),
                title=c.title.strip(),
                text=c.text.strip(),
            )
        else:
            prev = merged[key]
            title = prev.title if len(prev.title) >= len(c.title) else c.title.strip()
            text = _merge_clause_texts(prev.text, c.text)
            merged[key] = Clause(id=prev.id, title=title, text=text)
    return [merged[k] for k in order]


def _merge_chunk_clauses(chunks: list[list[Clause]]) -> list[Clause]:
    """Merge clause lists from overlapping chunks; stitch same id at boundaries."""
    flat: list[Clause] = []
    for batch in chunks:
        flat.extend(batch)
    if not flat:
        return []
    out: list[Clause] = [flat[0]]
    for c in flat[1:]:
        prev = out[-1]
        if c.id == prev.id:
            if c.text not in prev.text:
                out[-1] = Clause(
                    id=prev.id,
                    title=prev.title if len(prev.title) >= len(c.title) else c.title,
                    text=prev.text + "\n\n" + c.text,
                )
            continue
        out.append(c)
    return out


def _split_paragraph_chunks(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split long text at paragraph boundaries with overlap."""
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            window = text[start:end]
            cut = window.rfind("\n\n")
            if cut > max_chars // 3:
                end = start + cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


def _openai_parse_chunk(
    client: OpenAI, model: str, chunk: str, idx: int, total: int
) -> list[Clause]:
    system = SYSTEM_PROMPT + "\n\n" + CHUNK_SYSTEM_EXTRA
    user = (
        f"(Part {idx + 1} of {total})\n\n"
        + CHUNK_USER_WRAPPER.format(text=chunk)
    )
    completion = client.beta.chat.completions.parse(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=ClauseExtractionResult,
    )
    msg = completion.choices[0].message
    if msg.refusal:
        raise RuntimeError(f"Model refused: {msg.refusal}")
    parsed = msg.parsed
    if not parsed:
        raise RuntimeError("No parsed result from model")
    return parsed.clauses


def _extract_clauses_openai_chunked(part2_text: str) -> list[Clause]:
    """Multiple parse calls to avoid output token truncation on long Part II."""
    client = _client()
    model = _model_name()
    page_secs = _page_sections(part2_text)
    if len(page_secs) > 1:
        chunk_size = int(os.getenv("OPENAI_CHUNK_PAGES", "5"))
        overlap = int(os.getenv("OPENAI_CHUNK_PAGE_OVERLAP", "2"))
        text_chunks = _chunk_page_sections(page_secs, chunk_size, overlap)
    else:
        max_c = int(os.getenv("OPENAI_CHUNK_CHARS", "12000"))
        ov = int(os.getenv("OPENAI_CHUNK_CHAR_OVERLAP", "4000"))
        text_chunks = _split_paragraph_chunks(part2_text, max_c, ov)

    results: list[list[Clause]] = []
    for i, ch in enumerate(text_chunks):
        results.append(_openai_parse_chunk(client, model, ch, i, len(text_chunks)))
    return _merge_chunk_clauses(results)


def extract_clauses_openai(part2_text: str) -> list[Clause]:
    """Structured output via parse API; chunks automatically when the document is long."""
    min_chars_for_chunk = int(os.getenv("OPENAI_CHUNK_MIN_CHARS", "45000"))
    if len(part2_text) >= min_chars_for_chunk:
        return _extract_clauses_openai_chunked(part2_text)
    client = _client()
    model = _model_name()
    user_content = (
        "Extract all clauses from the following Part II text.\n\n---\n\n" + part2_text
    )
    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format=ClauseExtractionResult,
        )
    except LengthFinishReasonError:
        return _extract_clauses_openai_chunked(part2_text)
    msg = completion.choices[0].message
    if msg.refusal:
        raise RuntimeError(f"Model refused: {msg.refusal}")
    parsed = msg.parsed
    if not parsed:
        raise RuntimeError("No parsed result from model")
    return parsed.clauses


def _page_sections(text: str) -> list[str]:
    """Split text that contains --- Page N --- markers into sections."""
    parts = re.split(r"(?=--- Page \d+ ---)", text)
    return [p.strip() for p in parts if p.strip()]


def _chunk_page_sections(sections: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Build overlapping windows of page sections for smaller context models."""
    if not sections:
        return []
    chunks: list[str] = []
    i = 0
    step = max(1, chunk_size - overlap)
    while i < len(sections):
        chunks.append("\n\n".join(sections[i : i + chunk_size]))
        i += step
    return chunks


def _ollama_chat_json(model: str, system: str, user: str) -> str:
    base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url = f"{base}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama request failed ({url}). Is `ollama serve` running and the model pulled? {e}"
        ) from e
    msg = body.get("message") or {}
    content = msg.get("content")
    if not content:
        raise RuntimeError(f"Unexpected Ollama response: {body!r}")
    return content


def extract_clauses_ollama(
    part2_text: str,
    *,
    chunk_pages: int = 6,
    overlap_pages: int = 2,
) -> list[Clause]:
    """
    Local inference via Ollama. Uses JSON mode. Default: one request for the full text.
    Set OLLAMA_CHUNK=1 to force page-based chunking (use with page_markers in PDF extract).
    """
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    schema_hint = (
        '{"clauses":[{"id":"string","title":"string","text":"string"}]}'
    )
    system = SYSTEM_PROMPT + f"\n\nRespond with a single JSON object matching: {schema_hint}"

    force_chunk = os.getenv("OLLAMA_CHUNK", "").lower() in ("1", "true", "yes")
    sections = _page_sections(part2_text)
    use_chunks = force_chunk and len(sections) > 1

    if not use_chunks:
        user = "Extract all clauses from the following Part II text.\n\n---\n\n" + part2_text
        raw = _ollama_chat_json(model, system, user)
        return _parse_clause_json(raw).clauses

    chunks = _chunk_page_sections(sections, chunk_pages, overlap_pages)
    seen: list[Clause] = []
    for chunk in chunks:
        user = CHUNK_USER_WRAPPER.format(text=chunk)
        raw = _ollama_chat_json(model, system, user)
        seen.extend(_parse_clause_json(raw).clauses)
    out: list[Clause] = []
    for c in seen:
        if out and out[-1].id == c.id:
            if c.text not in out[-1].text:
                out[-1] = Clause(
                    id=out[-1].id,
                    title=out[-1].title,
                    text=out[-1].text + "\n\n" + c.text,
                )
            continue
        out.append(c)
    return out


def extract_clauses_llm(part2_text: str, *, dedupe_by_id: bool = True) -> list[Clause]:
    """Dispatch by CHARTER_LLM_PROVIDER: openai (default) or ollama."""
    provider = os.getenv("CHARTER_LLM_PROVIDER", "openai").lower().strip()
    if provider == "ollama":
        clauses = extract_clauses_ollama(part2_text)
    else:
        clauses = extract_clauses_openai(part2_text)
    if dedupe_by_id:
        clauses = dedupe_clauses_by_id(clauses)
    return clauses


def clauses_to_jsonable(clauses: list[Clause]) -> list[dict[str, str]]:
    return [c.model_dump() for c in clauses]
