"""Root resolution — a pinned root must drop the spine into any project, Python or not."""

import pytest

from compliance_spine.config import find_root


def test_pinned_env_root_is_authoritative_without_pyproject(tmp_path, monkeypatch):
    (tmp_path / "spine").mkdir()  # a non-Python repo: spine/ but no pyproject.toml
    monkeypatch.setenv("COMPLIANCE_SPINE_ROOT", str(tmp_path))
    assert find_root() == tmp_path.resolve()


def test_pinned_root_requires_a_spine_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPLIANCE_SPINE_ROOT", str(tmp_path))  # no spine/ here
    with pytest.raises(FileNotFoundError):
        find_root()


def test_start_argument_overrides_env(tmp_path, monkeypatch):
    (tmp_path / "spine").mkdir()
    monkeypatch.delenv("COMPLIANCE_SPINE_ROOT", raising=False)
    assert find_root(tmp_path) == tmp_path.resolve()
