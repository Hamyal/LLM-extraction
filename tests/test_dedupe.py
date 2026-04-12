from charter_clauses.llm_extract import dedupe_clauses_by_id
from charter_clauses.models import Clause


def test_dedupe_merges_same_id_in_order():
    clauses = [
        Clause(id="1", title="A", text="First block."),
        Clause(id="2", title="B", text="Only once."),
        Clause(id="1", title="A", text="Extra from overlap."),
    ]
    out = dedupe_clauses_by_id(clauses)
    assert [c.id for c in out] == ["1", "2"]
    assert "First block." in out[0].text
    assert "Extra from overlap." in out[0].text


def test_dedupe_substring_does_not_duplicate():
    clauses = [
        Clause(id="1", title="A", text="Full text here."),
        Clause(id="1", title="A", text="Full text here."),
    ]
    out = dedupe_clauses_by_id(clauses)
    assert len(out) == 1
    assert out[0].text == "Full text here."


def test_dedupe_distinct_rider_ids():
    clauses = [
        Clause(id="4", title="Main", text="x"),
        Clause(id="4-Rider", title="Rider", text="y"),
    ]
    out = dedupe_clauses_by_id(clauses)
    assert [c.id for c in out] == ["4", "4-Rider"]
