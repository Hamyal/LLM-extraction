from charter_clauses.pdf_extract import extract_part2_text, normalize_part2_plain_text


def test_normalize_splits_heading_from_number():
    raw = "Heading text here              1. Body starts"
    out = normalize_part2_plain_text(raw)
    assert "\n\n1. Body starts" in out


def test_extract_part2_starts_with_condition_or_part_ii():
    text = extract_part2_text("voyage-charter-example.pdf")
    assert text.startswith("Condition") or text.upper().startswith("PART II")


def test_extract_part2_reasonable_length():
    text = extract_part2_text("voyage-charter-example.pdf")
    assert len(text) > 50_000
