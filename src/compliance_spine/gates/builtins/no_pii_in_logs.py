"""Gate: no personal data in logs, traces, or prompts (never-delegate #1, GDPR data
minimisation / Art 5). Fail-closed static heuristic — if a log statement carries something
that cannot be shown to be non-personal, the gate does not pass.

The heuristic flags a personal-data token only when it appears in a *reference* position —
attribute access (``user.email``), interpolation (``f"{user}"`` / ``${user}``), a key/kwarg
(``email=`` / ``"ssn":``) or a bare argument (``log(user)``) — not when the same word merely
appears in prose (``"user logged in"``). Values wrapped in a redactor are treated as safe.

The personal-data vocabulary is the built-in defaults below **unioned with the repository's
``spine/data-catalogue.yaml`` (personal + special)** — the same catalogue the pii-access-boundary
gate reads — so an adopter declares what counts as personal data in one place and both code gates
honour it (e.g. adding ``health_conditions`` makes this gate flag it in logs too).
"""

from __future__ import annotations

import re
from functools import cache

import yaml

from compliance_spine.config import paths
from compliance_spine.gates.base import Gate, GateSpec

# Log / trace / print call sites across common languages.
_LOG_CALL = re.compile(
    r"(?:\b(?:logger|logging|log|LOG|_log)\s*\.\s*"
    r"(?:debug|info|warn|warning|error|critical|exception|trace|log)\b"
    r"|\bconsole\s*\.\s*(?:log|info|warn|error|debug)"
    r"|\bprintln?\b|\bprint\b"
    r"|\bSystem\.out\.print(?:ln)?)"
    r"\s*\(",
)

# Built-in personal-data fields. Ambiguous bare words (ip / sin / health / zip) are excluded, but
# unambiguous compound special-category fields (health_conditions, medical_notes) are included.
_DEFAULT_FIELDS = (
    "email", "emails", "e_mail", "phone", "telephone", "mobile", "msisdn",
    "ssn", "bsn", "nino", "passport", "national_id", "nationalid",
    "dob", "birthdate", "birthday", "date_of_birth",
    "address", "street", "postcode", "zipcode",
    "firstname", "first_name", "lastname", "last_name",
    "fullname", "full_name", "surname", "given_name", "family_name",
    "iban", "cvv", "creditcard", "credit_card", "card_number",
    "gender", "ethnicity", "religion",
    "diagnosis", "health_conditions", "medical_notes", "medical_history", "health_record",
    "biometric", "fingerprint", "geolocation", "ip_address", "ipaddress", "last_ip",
)
# Objects that typically *contain* personal data. Person-like only — record objects such as a
# claim or an order are excluded because most of their attributes (id, status, amount) are not
# personal; specific personal / special-category fields on them are caught via the field list.
_DEFAULT_CONTAINERS = (
    "user", "customer", "member", "account", "profile", "person",
    "patient", "applicant", "subscriber", "employee",
)

_REDACTORS = (
    "redact", "mask", "anonymize", "anonymise", "pseudonymize", "pseudonymise",
    "hash", "hashed", "sha256", "tokenize", "tokenise", "scrub", "sanitize", "sanitise",
)
_REDACT_RE = re.compile(rf"(?:{'|'.join(_REDACTORS)})\s*\(", re.I)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_INTERP = re.compile(r"\{[^{}]*\}|\$\{[^}]*\}|%\([a-zA-Z_]+\)")


@cache
def _catalogue_fields() -> tuple[str, ...]:
    """Personal + special-category element names declared in spine/data-catalogue.yaml."""
    try:
        data = yaml.safe_load(paths().data_catalogue.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — a missing/broken catalogue must not break scanning
        return ()
    out: set[str] = set()
    for group in ("personal", "special"):
        out.update(str(x).strip().lower() for x in (data.get(group) or []) if str(x).strip())
    return tuple(sorted(out))


@cache
def _matchers() -> dict[str, re.Pattern[str]]:
    fields = tuple(sorted(set(_DEFAULT_FIELDS) | set(_catalogue_fields())))
    containers = _DEFAULT_CONTAINERS
    field_alt = "|".join(sorted((re.escape(w) for w in fields), key=len, reverse=True))
    cont_alt = "|".join(sorted((re.escape(w) for w in containers), key=len, reverse=True))
    all_alt = "|".join(sorted((re.escape(w) for w in fields + containers), key=len, reverse=True))
    return {
        "attr": re.compile(rf"\b(?:{cont_alt})\s*\.\s*\w|\.\s*(?:{field_alt})\b", re.I),
        "kv": re.compile(rf"""['"]?\b(?:{field_alt})\b['"]?\s*[:=]""", re.I),
        "bare": re.compile(rf"(?:^|[(,\[])\s*\{{?\s*(?:{all_alt})\s*[)\],.}}]", re.I),
        "token": re.compile(rf"\b(?:{all_alt})\b", re.I),
    }


def _redacted_near(text: str, pos: int) -> bool:
    return bool(_REDACT_RE.search(text[max(0, pos - 24) : pos + 2]))


def _scan_payload(path: str, lineno: int, payload: str) -> list[str]:
    m = _matchers()
    token_re = m["token"]
    findings: list[str] = []

    def add(msg: str) -> None:
        entry = f"{path}:{lineno}: {msg}"
        if entry not in findings:
            findings.append(entry)

    hit = _EMAIL_RE.search(payload)
    if hit and not _redacted_near(payload, hit.start()):
        add("email address literal in log payload")

    for block in _INTERP.finditer(payload):
        text = block.group()
        if _REDACT_RE.search(text):
            continue
        tok = token_re.search(text)
        if tok:
            add(f"interpolates personal-data token '{tok.group().lower()}'")

    for key, label in (("attr", "attribute"), ("kv", "field"), ("bare", "object")):
        for found in m[key].finditer(payload):
            if _redacted_near(payload, found.start()):
                continue
            token = token_re.search(found.group())
            name = token.group().lower() if token else found.group().strip("(),[].{} \"'")
            add(f"logs personal-data {label} '{name}'")

    return findings


class NoPiiInLogsGate(Gate):
    name = "no-pii-in-logs"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for f in change.files:
            for lineno, line in enumerate(f.content.splitlines(), start=1):
                for call in _LOG_CALL.finditer(line):
                    findings.extend(_scan_payload(f.path, lineno, line[call.end() :]))
        subject = {"change": change.id, "data_category": change.data_category}
        return (not findings, findings, subject)
