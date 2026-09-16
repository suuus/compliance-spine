"""scan-diff must not treat test fixtures, eval datasets, docs, or the scanner's own detection
source as production code — otherwise the repo (and adopters) fail their own gate on examples.
"""

from compliance_spine.gitdiff import _is_excluded, _load_scan_excludes


def test_default_excludes_cover_fixture_and_doc_paths():
    ex = _load_scan_excludes()
    for path in (
        "tests/test_security_gates.py",
        "zava/datasets/insecure-transport.jsonl",
        "docs/CONTROL-CATALOGUE.md",
        "examples/change-violation.json",
        ".github/copilot-instructions.md",
        "yarn.lock",
    ):
        assert _is_excluded(path, ex), path


def test_production_source_is_not_excluded():
    ex = _load_scan_excludes()
    for path in ("src/app/auth.py", "api/handlers/login.py", "lib/http/client.js"):
        assert not _is_excluded(path, ex), path


def test_repo_scan_ignore_excludes_gate_source():
    # spine/scan-ignore adds the gates' own source (its regexes look like violations).
    ex = _load_scan_excludes()
    assert _is_excluded("src/compliance_spine/gates/builtins/security_hygiene.py", ex)
