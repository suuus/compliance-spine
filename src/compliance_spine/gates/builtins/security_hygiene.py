"""Security & privacy hygiene gates (Structure layer) — code/path-scanning, fail-closed.

These encode the checkable engineering rules from the CNIL/OWASP/NIST-inspired GDPR guidance
(GDPR Art 5(1)(f), Art 25, Art 32). Like ``no-pii-in-logs`` they inspect source directly, so
they run on a raw diff with no declared metadata. Each is a heuristic tuned for precision —
it flags a clear violation signal, not a vague smell — and fails closed on what it does catch.
"""

from __future__ import annotations

import re

from compliance_spine.gates.base import Gate, GateSpec

# Personal-data field tokens that must never appear in a URL (shared by pii-in-url).
_PII_URL = (
    "email|e_mail|ssn|bsn|nino|national_id|nationalid|passport|phone|msisdn|iban"
    "|dob|date_of_birth|birthdate|firstname|first_name|lastname|last_name|full_name|address"
)


def _scan_lines(change):
    for f in change.files:
        for lineno, line in enumerate(f.content.splitlines(), start=1):
            yield f.path, lineno, line


# --------------------------------------------------------------------------------------------
# 1. Weak password hashing (Art 32) — Argon2id/bcrypt, never MD5/SHA-family for credentials.
# --------------------------------------------------------------------------------------------
_WEAK_HASH = re.compile(
    r"\b(?:hashlib\.)?(?:new\(\s*['\"])?(md5|sha1|sha224|sha256|sha384|sha512)\b"
    r"|createHash\(\s*['\"](md5|sha1|sha256|sha512)['\"]"
    r"|MessageDigest\.getInstance\(\s*['\"](MD5|SHA-?1|SHA-?256)['\"]",
    re.I,
)
_PW_CONTEXT = re.compile(r"\b(?:password|passwd|pwd|passphrase|credential)\w*", re.I)
# Strong KDFs legitimately name a hash as their PRF (e.g. PBKDF2-HMAC-SHA256) — don't flag those.
_STRONG_KDF = re.compile(r"argon2|bcrypt|scrypt|pbkdf2|hkdf", re.I)


class WeakPasswordHashGate(Gate):
    name = "weak-password-hash"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for path, lineno, line in _scan_lines(change):
            if _STRONG_KDF.search(line):
                continue
            m = _WEAK_HASH.search(line)
            if m and _PW_CONTEXT.search(line):
                algo = next(g for g in m.groups() if g)
                findings.append(
                    f"{path}:{lineno}: password/credential hashed with weak algorithm "
                    f"'{algo.lower()}' — use Argon2id or bcrypt (Art 32)"
                )
        return (not findings, findings, {"change": change.id})


# --------------------------------------------------------------------------------------------
# 2. PII in URL path/query (Art 5(1)(f), Art 25) — leaks into CDN logs, history, referers.
# --------------------------------------------------------------------------------------------
_ROUTE_PII = re.compile(rf"/(?:<|\{{|:)(?:\w+:)?\s*({_PII_URL})\b", re.I)
_QUERY_PII = re.compile(rf"[?&]\s*({_PII_URL})=", re.I)


class PiiInUrlGate(Gate):
    name = "pii-in-url"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for path, lineno, line in _scan_lines(change):
            for rx, where in ((_ROUTE_PII, "path segment"), (_QUERY_PII, "query parameter")):
                m = rx.search(line)
                if m:
                    findings.append(
                        f"{path}:{lineno}: personal data '{m.group(1).lower()}' in a URL "
                        f"{where} — use the body or an authenticated session (Art 5(1)(f))"
                    )
        return (not findings, findings, {"change": change.id})


# --------------------------------------------------------------------------------------------
# 3. Insecure transport (Art 32) — disabled cert verification or obsolete TLS.
# --------------------------------------------------------------------------------------------
_INSECURE_TRANSPORT = re.compile(
    r"verify\s*=\s*False"
    r"|rejectUnauthorized\s*:\s*false"
    r"|NODE_TLS_REJECT_UNAUTHORIZED\s*[:=]\s*['\"]?0"
    r"|ssl\._create_unverified_context"
    r"|\bCERT_NONE\b"
    r"|CURLOPT_SSL_VERIFYPEER\s*,\s*(?:0|false)"
    r"|\bTLSv1\.1\b|\bTLSv1\b(?!\.)|\bSSLv[23]\b|PROTOCOL_TLSv1\b|PROTOCOL_SSLv[23]"
    r"|curl\b[^\n]*\s-(?:k|-insecure)\b",
    re.I,
)


class InsecureTransportGate(Gate):
    name = "insecure-transport"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for path, lineno, line in _scan_lines(change):
            m = _INSECURE_TRANSPORT.search(line)
            if m:
                findings.append(
                    f"{path}:{lineno}: insecure transport '{m.group(0).strip()}' — require "
                    f"TLS 1.2+ with certificate verification (Art 32)"
                )
        return (not findings, findings, {"change": change.id})


# --------------------------------------------------------------------------------------------
# 4. Permissive CORS (Art 32) — wildcard origin on an API.
# --------------------------------------------------------------------------------------------
_CORS_WILDCARD = re.compile(
    r"access-control-allow-origin['\"]?\s*\]?\s*[:,=]\s*['\"]\*"
    r"|\borigin\s*:\s*['\"]\*['\"]"
    r"|allow_origins\s*=\s*\[[^\]]*['\"]\*['\"]"
    r"|CORS\([^)]*origins?\s*=\s*['\"]\*",
    re.I,
)


class PermissiveCorsGate(Gate):
    name = "permissive-cors"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for path, lineno, line in _scan_lines(change):
            if _CORS_WILDCARD.search(line):
                findings.append(
                    f"{path}:{lineno}: wildcard CORS origin '*' — use an explicit "
                    f"allowlist, never '*' on an authenticated API (Art 32)"
                )
        return (not findings, findings, {"change": change.id})


# --------------------------------------------------------------------------------------------
# 5. Error leakage (Art 5(1)(f), Art 32) — stack traces / debug output to the client.
# --------------------------------------------------------------------------------------------
_RESP_CTX = (
    r"return\b|res\.|resp\.|response\.|reply\.|\bsend\b|jsonify\b|render\b|\bwrite\b|getWriter"
)
_LEAK = re.compile(
    rf"(?:{_RESP_CTX})[^\n]*(traceback\.format_exc|\.format_exc\(|\bstack\b|printStackTrace"
    r"|\bstacktrace\b)",
    re.I,
)
_DEBUG_ON = re.compile(
    r"\bdebug\s*=\s*True\b|\bDEBUG\s*=\s*True\b|app\.debug\s*=\s*True\b|FLASK_DEBUG\s*=\s*1\b",
)


class ErrorLeakageGate(Gate):
    name = "error-leakage"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for path, lineno, line in _scan_lines(change):
            if _LEAK.search(line):
                findings.append(
                    f"{path}:{lineno}: stack trace / internal error returned to the client — "
                    f"log it server-side against a correlation id (Art 5(1)(f))"
                )
            elif _DEBUG_ON.search(line):
                findings.append(
                    f"{path}:{lineno}: debug mode enabled — leaks stack traces and internals "
                    f"to clients (Art 25/32)"
                )
        return (not findings, findings, {"change": change.id})


# --------------------------------------------------------------------------------------------
# 6. Secret file committed (Art 32) — never commit key/credential files to source.
# --------------------------------------------------------------------------------------------
_SECRET_PATH = re.compile(
    r"(?:^|/)\.env(?:\.[\w-]+)?$"
    r"|\.(?:pem|key|pfx|p12|p8|keystore|jks)$"
    r"|(?:^|/)id_(?:rsa|dsa|ecdsa|ed25519)$"
    r"|(?:^|/)secrets?/",
    re.I,
)
_SECRET_PATH_OK = re.compile(r"\.env\.(?:example|sample|template|dist)$|\.pub$", re.I)


class SecretFileCommittedGate(Gate):
    name = "secret-file-committed"
    scans_code = True

    def check(self, change, spec: GateSpec) -> tuple[bool, list[str], dict]:
        findings: list[str] = []
        for f in change.files:
            if _SECRET_PATH.search(f.path) and not _SECRET_PATH_OK.search(f.path):
                findings.append(
                    f"{f.path}: secret file committed to source — keep it in a KMS / secrets "
                    f"manager and .gitignore the pattern (Art 32)"
                )
        return (not findings, findings, {"change": change.id})
