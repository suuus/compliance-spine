"""Behavioural compliance test templates the test-author agent recommends alongside the gate
stubs. Distilled from real regulated-app compliance test suites: they exercise the *control's
behaviour* (encryption, RBAC, DSAR, retention, consent, immutable audit, Art 22 override), not
just that a gate passes. Each is a pytest skeleton the team fills in with app specifics.
"""

from __future__ import annotations

TEMPLATES: dict[str, str] = {
    "encryption-at-rest-and-in-transit": (
        'def test_personal_data_encrypted_at_rest_and_in_transit():\n'
        '    """GDPR Art 32: sensitive attributes are field-level encrypted at rest, TLS in transit."""\n'
        "    # TODO: assert the stored value for a sensitive field is ciphertext (not plaintext),\n"
        "    #       and that the transport enforces TLS 1.2+ (no disabled cert verification).\n"
        "    raise NotImplementedError\n"
    ),
    "rbac-negative-access": (
        'def test_unauthorized_role_cannot_read_personal_data():\n'
        '    """GDPR Art 32 / 5(1)(f): an unauthorised role is denied access to personal data."""\n'
        "    # TODO: call the personal-data endpoint as an unauthorised role; assert 403 and\n"
        "    #       that the denied access is recorded in the audit log.\n"
        "    raise NotImplementedError\n"
    ),
    "dsar-access-and-portability": (
        'def test_data_subject_access_and_portability():\n'
        '    """GDPR Art 15/20: a subject can retrieve all their personal data in a portable format."""\n'
        "    # TODO: create a subject, exercise the export endpoint, assert every stored personal\n"
        "    #       field is returned in a machine-readable format.\n"
        "    raise NotImplementedError\n"
    ),
    "dsar-erasure": (
        'def test_data_subject_erasure():\n'
        '    """GDPR Art 17: erasure deletes or anonymises the subject\'s data across all stores."""\n'
        "    # TODO: request erasure; assert the subject's personal data is gone/anonymised\n"
        "    #       everywhere, while records that must be retained are anonymised, not deleted.\n"
        "    raise NotImplementedError\n"
    ),
    "retention-enforcement": (
        'def test_retention_job_removes_expired_personal_data():\n'
        '    """GDPR Art 5(1)(e): the scheduled job deletes/anonymises data past its retention window."""\n'
        "    # TODO: seed a record with an expired retention date; run the retention job;\n"
        "    #       assert the personal data is removed or anonymised.\n"
        "    raise NotImplementedError\n"
    ),
    "consent-opt-in": (
        'def test_optional_collection_requires_opt_in():\n'
        '    """GDPR Art 25(2)/7: analytics/telemetry stays off until opt-in, and is withdrawable."""\n'
        "    # TODO: assert no analytics event fires without consent; assert withdrawal stops it.\n"
        "    raise NotImplementedError\n"
    ),
    "audit-log-immutable": (
        'def test_data_access_is_audited_and_immutable():\n'
        '    """GDPR Art 30 / accountability: every access to personal data is logged; logs are immutable."""\n'
        "    # TODO: access a record; assert an audit entry exists; assert prior entries cannot\n"
        "    #       be altered (append-only / tamper-evident).\n"
        "    raise NotImplementedError\n"
    ),
    "automated-decision-human-override": (
        'def test_automated_decision_has_human_override_and_explanation():\n'
        '    """GDPR Art 22: a solely-automated significant decision offers a human path + explanation."""\n'
        "    # TODO: trigger an automated decision; assert a human-override route exists and a\n"
        "    #       contestable explanation / decision log is produced.\n"
        "    raise NotImplementedError\n"
    ),
}


def select(change) -> list[str]:
    """Which behavioural templates apply to a declared change's context."""
    m = change.metadata or {}
    keys: list[str] = []
    if m.get("data_category") in {"personal", "special"}:
        keys += [
            "encryption-at-rest-and-in-transit",
            "rbac-negative-access",
            "dsar-access-and-portability",
            "dsar-erasure",
            "retention-enforcement",
            "audit-log-immutable",
        ]
    if any(m.get(k) for k in ("analytics", "telemetry", "tracking")):
        keys.append("consent-opt-in")
    if m.get("automated_decision"):
        keys.append("automated-decision-human-override")
    seen: set[str] = set()
    return [k for k in keys if not (k in seen or seen.add(k))]
