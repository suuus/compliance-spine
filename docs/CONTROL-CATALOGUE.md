# Control catalogue — GDPR + EU AI Act reference

The rules the spine enforces, mapped to articles and machine checks. Extend per your
data-catalogue. **Not legal advice** — verify against the current regulation text and your DPO.

## GDPR controls
| Control | Article | Machine check (examples) | Gate id |
|---|---|---|---|
| Data minimisation | Art 5(1)(c) | flag new personal-data fields with no declared purpose | `minimisation` |
| Purpose limitation | Art 5(1)(b) | every PII field tagged to a declared purpose | `purpose-tag` |
| Storage limitation | Art 5(1)(e) | retention TTL present + enforced; no "forever" | `retention-ttl` |
| Lawful basis | Art 6 | processing has a declared lawful basis | `lawful-basis-required` |
| Special-category | Art 9 | explicit basis/consent; stricter minimisation; access-restricted; DPIA | `special-category` |
| Consent | Art 7 | consent captured/withdrawable where basis = consent | `consent` |
| Subject rights (DSAR) | Art 15–22 | access/export/erasure/rectification endpoints exist + tested | `dsar` |
| Automated decisions | Art 22 | human-intervention path + explanation where legal/significant effect | `automated-decision` |
| Privacy by design/default | Art 25 | defaults least-data; opt-in not opt-out | `pbd` |
| Records of processing | Art 30 | RoPA generated + current | `ropa` |
| Security | Art 32 | encryption in transit/at rest; pseudonymisation; no hardcoded secrets | `encryption-required` |
| Breach readiness | Art 33–34 | breach detection + 72h notification path exists | `breach-path` |
| DPIA | Art 35 | auto-triggered on high-risk processing | `dpia-trigger` |
| Transfers | Chap V (44–50) | no data leaves declared region without a transfer mechanism | `cross-border-transfer` |
| No PII in logs | Art 5 / 32 | log scanner blocks personal data / tokens in logs | `no-pii-in-logs` |

## EU AI Act baseline
> Timeline (verify): in force 1 Aug 2024; prohibited from 2 Feb 2025; GPAI from 2 Aug 2025;
> high-risk (Annex III) from 2 Aug 2026; remaining high-risk 2 Aug 2027. Fines up to
> €35M/7% (prohibited), €15M/3% (most obligations), €7.5M/1% (misinformation).

### 1. Classify → tier + role (provider vs deployer). Default to caution.
- **Prohibited (Art 5)** → block.
- **High-risk (Annex III)** → full baseline below.
- **Limited-risk (Art 50)** → transparency duties (disclose AI; label AI-generated content).
- **Minimal** → no specific obligations.

### 2. High-risk baseline obligations (checklist + artifact)
| Obligation | Article | Artifact |
|---|---|---|
| Risk-management system | Art 9 | risk register |
| Data & data governance | Art 10 | data-governance record |
| Technical documentation | Art 11 + Annex IV | Annex IV doc (agent generates skeleton) |
| Record-keeping / logging | Art 12 | inference/decision logs |
| Transparency to deployers | Art 13 | instructions-for-use |
| Human oversight | Art 14 | oversight + halt design |
| Accuracy, robustness, security | Art 15 | test results |
| Quality management system | Art 17 | QMS record |
| Conformity assessment | Art 43 | conformity file |

### 3. GPAI (if a general-purpose model is used) — Art 53+
Technical documentation · copyright policy · training-data summary. Systemic-risk GPAI: extra.

## Reference texts (verify current versions)
- GDPR — Regulation (EU) 2016/679.
- EU AI Act — Regulation (EU) 2024/1689 (Art 5, 9–15, 50, 53; Annex III, Annex IV).
