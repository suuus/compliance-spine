"""Unit tests for the security & privacy hygiene gates (Art 5(1)(f), 25, 32)."""

import pytest

from compliance_spine.change import Change
from compliance_spine.gates.base import GateSpec
from compliance_spine.gates.builtins import GATE_CLASSES

SPEC = GateSpec(name="x", intent_ref="", severity="high")


def _run(gate_name: str, path: str, content: str, metadata: dict | None = None) -> bool:
    change = Change.from_dict(
        {"id": "c", "files": [{"path": path, "content": content}], "metadata": metadata or {}}
    )
    compliant, _findings, _subject = GATE_CLASSES[gate_name]().check(change, SPEC)
    return compliant


@pytest.mark.parametrize(
    "gate,path,content",
    [
        ("weak-password-hash", "a.py", "pwd_hash = hashlib.md5(password.encode()).hexdigest()"),
        ("weak-password-hash", "a.py", "user.password_hash = hashlib.sha256(pwd).hexdigest()"),
        ("pii-in-url", "r.py", '@app.route("/users/<email>")'),
        ("pii-in-url", "c.py", 'url = f"https://x/s?email={email}"'),
        ("insecure-transport", "c.py", "requests.get(url, verify=False)"),
        ("permissive-cors", "a.py", 'resp.headers["Access-Control-Allow-Origin"] = "*"'),
        ("error-leakage", "a.py", "return jsonify(error=traceback.format_exc())"),
        ("secret-file-committed", ".env", "SECRET=1"),
    ],
)
def test_gate_blocks_violation(gate, path, content):
    assert _run(gate, path, content) is False


@pytest.mark.parametrize(
    "gate,path,content",
    [
        # PBKDF2-HMAC-SHA256 is a valid password KDF — the SHA is the PRF, not a bare hash.
        ("weak-password-hash", "a.py", "dk = hashlib.pbkdf2_hmac('sha256', password, s, 99)"),
        ("weak-password-hash", "a.py", "h = argon2.PasswordHasher().hash(password)"),
        # SHA-256 for a non-credential checksum is fine.
        ("weak-password-hash", "a.py", "etag = hashlib.sha256(body).hexdigest()"),
        ("pii-in-url", "r.py", '@app.route("/users/<uuid:id>")'),
        ("insecure-transport", "c.py", "requests.get(url, verify=True)"),
        ("insecure-transport", "s.py", "ctx.minimum_version = ssl.TLSVersion.TLSv1_3"),
        ("permissive-cors", "a.py", 'h["Access-Control-Allow-Origin"] = "https://app.example.com"'),
        # Logging a traceback server-side is correct; only returning it to the client is a leak.
        ("error-leakage", "a.py", "logger.error(traceback.format_exc())"),
        ("secret-file-committed", ".env.example", "SECRET="),
        ("secret-file-committed", ".ssh/id_rsa.pub", "ssh-rsa AAAA"),
    ],
)
def test_gate_allows_clean(gate, path, content):
    assert _run(gate, path, content) is True


def test_consent_default_blocks_optout_and_allows_optin():
    def run(meta):
        change = Change.from_dict({"id": "c", "files": [], "metadata": meta})
        compliant, _f, _s = GATE_CLASSES["consent-default"]().check(change, SPEC)
        return compliant

    assert run({"analytics": True, "consent": "opt_out"}) is False
    assert run({"telemetry": True}) is False
    assert run({"analytics": True, "consent": "opt_in"}) is True
    assert run({"analytics": False}) is True
