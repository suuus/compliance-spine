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
        "spine/scan-ignore",
        "spine/data-catalogue.yaml",
        "yarn.lock",
    ):
        assert _is_excluded(path, ex), path


def test_default_excludes_cover_colocated_test_conventions():
    # Co-located tests across ecosystems (Jest __tests__/*.test.js, Angular *.spec.ts, pytest
    # test_*.py / *_test.py, Go *_test.go) carry fixture creds/PII by convention — exclude them
    # the same way whole tests/ directories already are.
    ex = _load_scan_excludes()
    for path in (
        "src/backend/__tests__/controllers/auth.test.js",
        "src/backend/__tests__/__mocks__/db.js",
        "src/components/ProductModal.test.tsx",
        "risk-service/src/services/foo.spec.js",
        "app/services/test_pricing.py",
        "app/services/pricing_test.py",
        "internal/handler_test.go",
    ):
        assert _is_excluded(path, ex), path


def test_production_source_is_not_excluded():
    ex = _load_scan_excludes()
    for path in (
        "src/app/auth.py",
        "api/handlers/login.py",
        "lib/http/client.js",
        # 'test' inside a word (contest, latest) must not trip the test excludes.
        "src/contest/routes.js",
        "src/latest.py",
    ):
        assert not _is_excluded(path, ex), path


def test_repo_scan_ignore_excludes_gate_source_and_demo():
    # spine/scan-ignore adds the gates' own source (its regexes look like violations) and the
    # demo (which intentionally embeds a leaky sample).
    ex = _load_scan_excludes()
    assert _is_excluded("src/compliance_spine/gates/builtins/security_hygiene.py", ex)
    assert _is_excluded("scripts/demo.sh", ex)
