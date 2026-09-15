"""Parse ``spine/intent/never-delegate.md`` into structured rules and check that every
gate traces back to one of them (ISEE: Structure must serve Intent).

The never-delegate list is a DPO-owned Markdown document. It is authored by humans, so the
parser is deliberately tolerant: it extracts the ranked items, their titles, the policies
they point to, and the owner, and derives a stable ``slug`` used to link gates to intent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from compliance_spine.config import paths

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NeverDelegateRule:
    """One ranked non-negotiable from the never-delegate list."""

    rank: int
    title: str
    slug: str
    body: str
    enforced_by: tuple[str, ...] = ()
    owner: str | None = None


@dataclass(frozen=True)
class Finding:
    """A traceability / integrity finding from :func:`validate_traceability`."""

    level: str  # "error" | "warning" | "info"
    code: str
    message: str


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_ITEM_RE = re.compile(
    r"^(?P<rank>\d+)\.\s+\*\*(?P<title>.+?)\*\*(?P<rest>.*?)(?=^\d+\.\s+\*\*|\Z)",
    re.S | re.M,
)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_OWNER_RE = re.compile(r"Owner:\s*(?P<owner>.+?)(?:·|\n|$)")
_PLACEHOLDER = re.compile(r"^<.*>$")
# Suffixes stripped when matching a gate's intent_ref anchor to a rule slug.
_ALIAS_SUFFIXES = ("-required", "-risk-tier", "-ttl", "-detection")


def _slugify(text: str) -> str:
    first = re.split(r"[.,;:(]", text, maxsplit=1)[0]
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    return slug or "rule"


def _slug_from_refs(refs: tuple[str, ...]) -> str | None:
    for ref in refs:
        base = ref.rstrip("/").split("/")[-1]
        stem = base.rsplit(".", 1)[0]
        if stem and stem not in {"evidence", "spine"}:
            return stem
    return None


def _alias_base(slug: str) -> str:
    for suffix in _ALIAS_SUFFIXES:
        if slug.endswith(suffix):
            return slug[: -len(suffix)]
    return slug


def load_intent(path: str | Path | None = None) -> list[NeverDelegateRule]:
    """Parse the never-delegate Markdown into ranked rules."""
    md_path = Path(path) if path else paths().intent_file
    text = md_path.read_text(encoding="utf-8")

    # Isolate the ranked list so trailing prose (e.g. "Companion files") is not captured
    # into the final item.
    section_m = re.search(r"^##\s+The list\s*$(?P<body>.*?)(?=^##\s|\Z)", text, re.S | re.M)
    section = section_m.group("body") if section_m else text

    rules: list[NeverDelegateRule] = []
    for m in _ITEM_RE.finditer(section):
        rank = int(m.group("rank"))
        title = m.group("title").strip().rstrip(".")
        rest = m.group("rest")
        block = m.group(0)

        refs = tuple(_BACKTICK_RE.findall(block))
        slug = _slug_from_refs(refs) or _slugify(title)

        owner: str | None = None
        owner_m = _OWNER_RE.search(rest)
        if owner_m:
            candidate = owner_m.group("owner").strip()
            if candidate and not _PLACEHOLDER.match(candidate):
                owner = candidate

        rules.append(
            NeverDelegateRule(
                rank=rank,
                title=title,
                slug=slug,
                body=rest.strip(),
                enforced_by=refs,
                owner=owner,
            )
        )
    rules.sort(key=lambda r: r.rank)
    return rules


# ---------------------------------------------------------------------------
# Registry + traceability
# ---------------------------------------------------------------------------


@dataclass
class IntentRegistry:
    rules: list[NeverDelegateRule] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path | None = None) -> IntentRegistry:
        return cls(rules=load_intent(path))

    def __post_init__(self) -> None:
        self._by_slug = {r.slug: r for r in self.rules}

    def resolve(self, intent_ref: str) -> NeverDelegateRule | None:
        """Resolve a gate ``intent_ref`` (e.g. ``intent/never-delegate#lawful-basis``)."""
        fragment = intent_ref.split("#")[-1].strip()
        if fragment in self._by_slug:
            return self._by_slug[fragment]
        target = _alias_base(fragment)
        for rule in self.rules:
            if _alias_base(rule.slug) == target:
                return rule
        return None


def validate_traceability(
    registry: IntentRegistry,
    gate_config: dict,
) -> list[Finding]:
    """Every gate must trace to a never-delegate principle; report the ones that don't."""
    findings: list[Finding] = []
    gates = gate_config.get("gates", {}) or {}
    for name, spec in gates.items():
        intent_ref = (spec or {}).get("intent_ref")
        if not intent_ref:
            findings.append(
                Finding("error", "gate-no-intent", f"gate '{name}' declares no intent_ref")
            )
            continue
        if registry.resolve(intent_ref) is None:
            findings.append(
                Finding(
                    "error",
                    "gate-unmapped-intent",
                    f"gate '{name}' references intent '{intent_ref}' "
                    "not found in the never-delegate list",
                )
            )
    return findings
