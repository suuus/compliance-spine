"""Bridge a git diff to a :class:`Change` so the code-scanning gates can run on a commit or
PR. A raw diff carries no declared compliance metadata, so this feeds the gates that inspect
source directly (no-pii-in-logs, encryption/secrets, pii-access-boundary); the declaration
gates stay not-applicable until a change declares its context.
"""

from __future__ import annotations

import subprocess

from compliance_spine.change import Change, ChangeFile

_MAX_BYTES = 1_000_000


def _git_text(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def _git_bytes(*args: str) -> bytes | None:
    result = subprocess.run(["git", *args], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def _changed_paths(name_status: str) -> list[str]:
    paths: list[str] = []
    for line in name_status.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if parts[0].startswith("D"):  # deletion: nothing to scan
            continue
        paths.append(parts[-1])  # rename (Rxxx old new) -> new path is last
    return paths


def _decode(raw: bytes | None) -> str | None:
    if raw is None or len(raw) > _MAX_BYTES or b"\x00" in raw[:8000]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def build_change(pairs: list[tuple[str, str]], change_id: str = "diff") -> Change:
    """Pure constructor: (path, content) pairs -> a Change with empty metadata."""
    return Change(id=change_id, files=[ChangeFile(p, c) for p, c in pairs], metadata={})


def collect_change(staged: bool = True, base: str | None = None, head: str = "HEAD") -> Change:
    """Build a Change from the staged diff, or from ``base..head`` when ``base`` is given."""
    if not staged and base:
        name_status = _git_text("diff", "--name-status", base, head)
        ref = lambda p: f"{head}:{p}"  # noqa: E731
        change_id = f"{base}..{head}"
    else:
        name_status = _git_text("diff", "--cached", "--name-status")
        ref = lambda p: f":{p}"  # noqa: E731 - the staged blob
        change_id = "staged"

    pairs: list[tuple[str, str]] = []
    for path in _changed_paths(name_status):
        text = _decode(_git_bytes("show", ref(path)))
        if text is not None:
            pairs.append((path, text))
    return build_change(pairs, change_id=change_id)
