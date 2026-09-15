#!/usr/bin/env python3
"""Confidentiality leak-guard.

The spine is built for a specific customer in a regulated domain, but *nothing* about
that customer or domain may appear in this repository. This scanner enforces that.

Design constraint: the guard must not itself contain the sensitive terms in plaintext —
that would be the very leak we are preventing. So the built-in denylist ships as
**SHA-256 hashes** of forbidden words. The scanner hashes each word it finds and checks
membership; it never needs the plaintext. For real deployments, an additional *plaintext*
pattern file can be supplied out-of-band via ``$COMPLIANCE_LEAK_PATTERNS_FILE`` (kept in
``.gitignore``), so the operative denylist lives outside the committed artifact.

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

# SHA-256 of forbidden domain/customer terms (and their morphological variants).
# Plaintext intentionally absent — see module docstring.
BUILTIN_HASHES: frozenset[str] = frozenset(
    {
        "ac7d227cddb99c2a7fc6783c00a46e91cbc108253574b38719368a15667a3d9e",
        "0ea7d8b72b0546bfb22597fb562e224789bb3857b376658f57dc892c52626eb3",
        "750708b8956e0ca04acb740ec7e84e8c238db36c487a04e8498e71dcb90cde08",
        "64e8937abc6d71cf2d2f0fe05e52c33666883443ae4e8af7924c71198caa1f9d",
        "cfbbd2ea7d87c01ee41e299c33ae1357602740885696af9032035fbb4ab4ac39",
        "9475a5970e0d3b96f19fca06c19d9235df6728836503a1d498b0124578aa113d",
        "a2ade46ab94c5a38b4ccfe8cec780bfa874b07679da6305233eb25901c6ebdbb",
        "bb04632546c0070fc84ea66f0c71bafd5c4c1e2aec2ee9c660950b9bd3024e2e",
        "c5f1fbef57e5803841b1a8cc532271469c7441cdc2fef0db92dc0c12bde1aa55",
        "c61a0a0563bb3bf01151fb143d34b5009f1b75c5683d6c856b20ca5126f1754f",
        "870dc23d21836b97b58a7753922edc8512764e83c02586f3d8f14c11f760550b",
        "0aab52b4dbcce29dd7b86753b2ea2e80affd952cd4d2945cb6549a5684789147",
        "ac9dc1b107be038f29390517684068cdaff0b0efb0cc9a924dd835e9cdbf8d6f",
        "e2fcb7e7588aff3cb93a40f86bb70e74a4ca95b66fefc206dd18b04ca1e9f43f",
        "58c66935b76a93c2b1e8e0dd811a7a02f3ef965b6ffd2a7caa079302e0645887",
        "27bc7eb20add5b3e9f1f2560e9dc51dca2664a4468bded633d99cc3bbb2a0854",
        "c5e27cb498c5858e9026a862fa524e8238bf1372ca49dc3e8797cc3c0c82eed4",
        "ff8c85029f98cd0bfa5576a13d6ad62e1a18acf6b6c589c9cad56d00302cc46b",
        "ec30c219d7c20fb799ea16b1b8df45e4cc45424c7fd08482ec322a068b2a1f3b",
        "e9ae161e9a33ecf59afe24f94858c2fa16cf39674c0691f66f779a837a0fcf8a",
        "77ebfe9993f116e089f21a982b4afcb67e3761529a29b52d5c88c65b467514e4",
    }
)

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
    path = os.environ.get("COMPLIANCE_LEAK_PATTERNS_FILE")
    if not path or not Path(path).is_file():
        return []
    patterns: list[re.Pattern[str]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
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
