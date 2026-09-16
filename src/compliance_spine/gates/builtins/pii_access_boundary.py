"""Gate: no component accesses personal data outside its declared purpose / access boundary
(never-delegate #9, GDPR Art 5(1)(b) purpose limitation). Fail-closed, code-scanning.

It reads two companions:
  - spine/data-catalogue.yaml   -> which data elements are personal / special-category
  - spine/access-boundaries.yaml -> which components must not access PII directly

A changed file is "restricted" when a boundary component name appears as a path segment or as a
file stem (e.g. src/analytics/report.py or services/analytics.py -> "analytics"). The gate flags
a restricted file that
references a catalogued PII element as an attribute (`.email`), a key/column (`"email"`,
`['email']`) or a kwarg (`email=`) — the pattern the user described: *accessing data X in
component Y where X is PII and Y must not touch PII directly.*
"""

from __future__ import annotations

import re
from functools import cache

import yaml

from compliance_spine.config import paths
from compliance_spine.gates.base import Gate, GateSpec


@cache
def _catalogue() -> frozenset[str]:
    data = yaml.safe_load(paths().data_catalogue.read_text(encoding="utf-8")) or {}
    elements: set[str] = set()
    for group in ("personal", "special"):
        elements.update(str(x).lower() for x in (data.get(group) or []))
    return frozenset(elements)


@cache
def _restricted() -> frozenset[str]:
    data = yaml.safe_load(paths().access_boundaries.read_text(encoding="utf-8")) or {}
    return frozenset(str(x).lower() for x in (data.get("forbid_pii_direct_access") or []))


@cache
def _access_re() -> re.Pattern[str] | None:
    elements = _catalogue()
    if not elements:
        return None
    alt = "|".join(sorted((re.escape(e) for e in elements), key=len, reverse=True))
    return re.compile(
        rf"\.\s*(?P<a>{alt})\b"          # attribute access:   obj.email
        rf"|['\"](?P<b>{alt})['\"]"      # string key / column: "email", ['email']
        rf"|\b(?P<c>{alt})\s*=",         # kwarg / assignment:  email=
        re.IGNORECASE,
    )


def _component(path: str, restricted: frozenset[str]) -> str | None:
    for segment in re.split(r"[\\/]", path.lower()):
        if segment in restricted:
            return segment
        stem = segment.rsplit(".", 1)[0]  # a file segment: analytics.py -> analytics
        if stem != segment and stem in restricted:
            return stem
    return None


class PiiAccessBoundaryGate(Gate):
    name = "pii-access-boundary"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        subject = {"change": change.id, "data_category": change.data_category}
        restricted = _restricted()
        access_re = _access_re()
        if access_re is None or not restricted:
            return True, [], subject

        findings: list[str] = []
        for f in change.files:
            component = _component(f.path, restricted)
            if component is None:
                continue
            for lineno, line in enumerate(f.content.splitlines(), start=1):
                for m in access_re.finditer(line):
                    element = (m.group("a") or m.group("b") or m.group("c")).lower()
                    findings.append(
                        f"{f.path}:{lineno}: restricted component '{component}' "
                        f"accesses personal-data element '{element}'"
                    )
        return (not findings, findings, subject)
