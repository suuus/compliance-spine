"""Confidentiality leak-guard: mechanism works, and the real repo stays clean."""

import hashlib
import importlib.util
import sys

from compliance_spine.config import paths

# Import the scanner from the ci/ directory (kept standalone so pre-commit can run it
# without installing the package). Register in sys.modules so its dataclasses resolve.
_spec = importlib.util.spec_from_file_location(
    "leak_scan", paths().root / "ci" / "leak_scan.py"
)
leak_scan = importlib.util.module_from_spec(_spec)
sys.modules["leak_scan"] = leak_scan
_spec.loader.exec_module(leak_scan)


def test_detects_injected_term(tmp_path):
    # Inject a benign word's hash rather than embedding a sensitive term in the repo.
    benign = "unicorn"
    hashes = frozenset({hashlib.sha256(benign.encode()).hexdigest()})
    (tmp_path / "doc.md").write_text("the unicorn gallops at dawn", encoding="utf-8")
    findings = leak_scan.scan_repo(tmp_path, hashes=hashes)
    assert len(findings) == 1
    assert findings[0].redacted == "u***"  # redacted, never the full word


def test_clean_text_has_no_findings(tmp_path):
    (tmp_path / "ok.md").write_text("gates, evidence, and governance", encoding="utf-8")
    assert leak_scan.scan_repo(tmp_path, hashes=leak_scan.BUILTIN_HASHES) == []


def test_repository_is_confidentiality_clean():
    """The whole committed repo must be free of customer/domain references."""
    findings = leak_scan.scan_repo(paths().root)
    assert findings == [], f"leak-guard found references: {[f.render() for f in findings]}"
