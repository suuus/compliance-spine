"""Gate: no personal data in logs, traces, or prompts (never-delegate #1, GDPR data
minimisation / Art 5). Fail-closed static heuristic — if a log statement carries something
that cannot be shown to be non-personal, the gate does not pass.

The heuristic flags a personal-data token only when it appears in a *reference* position —
attribute access (``user.email``), interpolation (``f"{user}"`` / ``${user}``), a key/kwarg
(``email=`` / ``"ssn":``) or a bare argument (``log(user)``) — not when the same word merely
appears in prose (``"user logged in"``). Values wrapped in a redactor are treated as safe.
"""

from __future__ import annotations

import re

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

# Personal-data fields (ambiguous words like ip/sin/health/zip deliberately excluded).
_FIELDS = (
    "email", "emails", "e_mail", "phone", "telephone", "mobile", "msisdn",
    "ssn", "bsn", "nino", "passport",
    "dob", "birthdate", "birthday", "date_of_birth",
    "address", "street", "postcode", "zipcode",
    "firstname", "first_name", "lastname", "last_name",
    "fullname", "full_name", "surname", "given_name", "family_name",
    "iban", "cvv", "creditcard", "credit_card", "card_number",
    "gender", "ethnicity", "religion", "diagnosis",
    "biometric", "fingerprint", "geolocation", "ip_address", "ipaddress",
)
# Objects that typically *contain* personal data.
_CONTAINERS = (
    "user", "customer", "member", "account", "profile", "person",
    "patient", "applicant", "subscriber", "employee",
)
_ALL = _FIELDS + _CONTAINERS
_ALT = "|".join(sorted(_ALL, key=len, reverse=True))
_CONT_ALT = "|".join(sorted(_CONTAINERS, key=len, reverse=True))
_FIELD_ALT = "|".join(sorted(_FIELDS, key=len, reverse=True))

_REDACTORS = (
    "redact", "mask", "anonymize", "anonymise", "pseudonymize", "pseudonymise",
    "hash", "hashed", "sha256", "tokenize", "tokenise", "scrub", "sanitize", "sanitise",
)
_REDACT_RE = re.compile(rf"(?:{'|'.join(_REDACTORS)})\s*\(", re.I)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Reference-position matchers.
_ATTR = re.compile(rf"\b(?:{_CONT_ALT})\s*\.\s*\w|\.\s*(?:{_FIELD_ALT})\b", re.I)
_KV = re.compile(rf"""['"]?\b(?:{_FIELD_ALT})\b['"]?\s*[:=]""", re.I)
_BARE_CONTAINER = re.compile(rf"(?:^|[(,\[])\s*\{{?\s*(?:{_CONT_ALT})\s*[)\],.}}]", re.I)
_INTERP = re.compile(r"\{[^{}]*\}|\$\{[^}]*\}|%\([a-zA-Z_]+\)")
_TOKEN_IN = re.compile(rf"\b(?:{_ALT})\b", re.I)


def _redacted_near(text: str, pos: int) -> bool:
    return bool(_REDACT_RE.search(text[max(0, pos - 24) : pos + 2]))


def _scan_payload(path: str, lineno: int, payload: str) -> list[str]:
    findings: list[str] = []

    def add(msg: str) -> None:
        entry = f"{path}:{lineno}: {msg}"
        if entry not in findings:
            findings.append(entry)

    m = _EMAIL_RE.search(payload)
    if m and not _redacted_near(payload, m.start()):
        add("email address literal in log payload")

    for block in _INTERP.finditer(payload):
        text = block.group()
        if _REDACT_RE.search(text):
            continue
        tok = _TOKEN_IN.search(text)
        if tok:
            add(f"interpolates personal-data token '{tok.group().lower()}'")

    for rx, label in ((_ATTR, "attribute"), (_KV, "field"), (_BARE_CONTAINER, "object")):
        for hit in rx.finditer(payload):
            if _redacted_near(payload, hit.start()):
                continue
            token = _TOKEN_IN.search(hit.group())
            name = token.group().lower() if token else hit.group().strip("(),[].{} \"'")
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
