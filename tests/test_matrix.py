"""compliance-matrix report: principle -> article -> enforcing gate -> coverage status."""

import json

from compliance_spine.matrix import _articles, build_matrix


def test_matrix_covers_all_principles():
    m = build_matrix()
    assert len(m.rows) == 18
    assert m.enforced == 17  # all but the human-owner meta-principle (enforced by the detector)
    assert m.with_article == 18  # every principle maps to at least one article


def test_matrix_maps_gates_articles_and_regulation():
    by_rank = {r.rank: r for r in build_matrix().rows}
    assert by_rank[1].gate == "no-pii-in-logs" and "Art 5" in by_rank[1].articles
    assert by_rank[8].regulation == "EU AI Act"
    assert by_rank[11].gate is None and by_rank[11].status == "no-gate"


def test_article_extraction():
    assert _articles("GDPR Art 5(1)(e); Chapter V; Annex III") == [
        "Art 5(1)(e)",
        "Chapter V",
        "Annex III",
    ]


def test_renders_markdown_and_json():
    m = build_matrix()
    md = m.render_markdown()
    assert "| # | Requirement |" in md
    assert "Coverage:" in md
    data = json.loads(m.to_json())
    assert data["summary"]["total"] == 18
    assert data["summary"]["enforced"] == 17
