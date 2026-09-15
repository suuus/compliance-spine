#!/usr/bin/env python3
"""Confidentiality leak-guard.

The spine is built for a specific customer in a regulated domain, but *nothing* about
that customer or domain may appear in this repository. This scanner enforces that.

Design constraint: the guard must not itself fingerprint the domain it protects. An earlier
version shipped SHA-256 of the forbidden terms — but SHA-256 of short dictionary words is
trivially brute-forced from a wordlist, so the committed hashes would themselves leak the
sector. So the built-in denylist ships **empty**, and the operative denylist is supplied
out-of-band as a plaintext pattern file via ``$COMPLIANCE_LEAK_PATTERNS_FILE`` (defaulting to
a git-ignored ``.leakpatterns``). The denylist therefore lives entirely outside the committed
artifact. Callers/tests may still pass an explicit ``hashes`` set to :func:`scan_text`.

Exit code is non-zero if anything matches — wire it into pre-commit and CI as a hard gate.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Intentionally empty: see the module docstring. The real denylist is supplied out-of-band
# via COMPLIANCE_LEAK_PATTERNS_FILE (git-ignored), so nothing in this file can be reversed to
# recover the customer/domain terms.
BUILTIN_HASHES: frozenset[str] = frozenset()

DEFAULT_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
    }
)
SCAN_EXTS = frozenset(
    {
        ".py",
        ".md",
        ".markdown",
        ".rst",
        ".yaml",
        ".yml",
        ".json",
        ".jsonl",
        ".txt",
        ".toml",
        ".cfg",
        ".ini",
        ".sh",
        ".rego",
        ".example",
    }
)
_TOKEN_RE = re.compile(r"[a-z]{3,}")


@dataclass(frozen=True)
class LeakFinding:
    path: str
    redacted: str
    digest: str
    source: str  # "builtin" | "external"

    def render(self) -> str:
        return (
            f"{self.path}: matched {self.source} term "
            f"'{self.redacted}' (sha256 {self.digest[:12]}…)"
        )


def _redact(term: str) -> str:
    return term[0] + "***" if term else "***"


def _load_external_patterns() -> list[re.Pattern[str]]:
    # The operative denylist lives outside the committed artifact: an env-pointed file, or a
    # git-ignored `.leakpatterns` in the working tree (materialised from a secret in CI).
    env = os.environ.get("COMPLIANCE_LEAK_PATTERNS_FILE")
    path = Path(env) if env else Path(".leakpatterns")
    if not path.is_file():
        return []
    patterns: list[re.Pattern[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(re.compile(line, re.IGNORECASE))
    return patterns


def scan_text(
    text: str,
    hashes: frozenset[str] = BUILTIN_HASHES,
    external: list[re.Pattern[str]] | None = None,
) -> list[LeakFinding]:
    findings: list[LeakFinding] = []
    seen: set[str] = set()
    for token in set(_TOKEN_RE.findall(text.lower())):
        digest = hashlib.sha256(token.encode()).hexdigest()
        if digest in hashes and digest not in seen:
            seen.add(digest)
            findings.append(LeakFinding("", _redact(token), digest, "builtin"))
    for pat in external or []:
        m = pat.search(text)
        if m:
            hit = m.group(0)
            digest = hashlib.sha256(hit.lower().encode()).hexdigest()
            findings.append(LeakFinding("", _redact(hit), digest, "external"))
    return findings


def iter_files(root: Path, exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in SCAN_EXTS:
                yield p


def scan_repo(
    root: Path,
    hashes: frozenset[str] = BUILTIN_HASHES,
    exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[LeakFinding]:
    external = _load_external_patterns()
    results: list[LeakFinding] = []
    for path in iter_files(root, exclude_dirs):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for f in scan_text(text, hashes, external):
            results.append(LeakFinding(str(path.relative_to(root)), f.redacted, f.digest, f.source))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Confidentiality leak-guard for the compliance spine."
    )
    parser.add_argument("root", nargs="?", default=".", help="directory to scan (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings = scan_repo(root)
    if findings:
        print(
            f"LEAK-GUARD: {len(findings)} potential confidentiality leak(s) found:",
            file=sys.stderr,
        )
        for f in findings:
            print(f"  - {f.render()}", file=sys.stderr)
        print("\nRemove customer/domain references before committing.", file=sys.stderr)
        return 1
    print("LEAK-GUARD: clean — no customer/domain references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
