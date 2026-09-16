"""`compliance-spine init` scaffolds a *functional* starter spine — every configured gate
already traces to a principle (doctor passes) — without clobbering a tuned policy.
"""

import yaml

from compliance_spine.cli import main
from compliance_spine.intent.loader import IntentRegistry, validate_traceability
from compliance_spine.scaffold import scaffold_spine


def _spine(tmp):
    return tmp / "spine"


def test_scaffold_writes_the_policy_folder_and_schema(tmp_path):
    written = scaffold_spine(tmp_path)
    for rel in (
        "spine/intent/never-delegate.md",
        "spine/gates/gate-config.yaml",
        "spine/data-catalogue.yaml",
        "spine/access-boundaries.yaml",
        "spine/frameworks.yaml",
        "spine/scan-ignore",
        "evidence/schema/decision-record.schema.json",
    ):
        assert (tmp_path / rel).is_file(), rel
        assert rel in written


def test_scaffold_passes_doctor_traceability(tmp_path):
    # the whole point: the starter is immediately valid — no gate without a principle.
    scaffold_spine(tmp_path)
    registry = IntentRegistry.load(path=_spine(tmp_path) / "intent" / "never-delegate.md")
    gate_config = yaml.safe_load(
        (_spine(tmp_path) / "gates" / "gate-config.yaml").read_text(encoding="utf-8")
    )
    assert validate_traceability(registry, gate_config) == []


def test_scaffold_does_not_clobber_without_force(tmp_path):
    scaffold_spine(tmp_path)
    tuned = _spine(tmp_path) / "data-catalogue.yaml"
    tuned.write_text("personal: [my_custom_field]\n", encoding="utf-8")

    again = scaffold_spine(tmp_path)  # no force
    assert again == []  # nothing overwritten
    assert "my_custom_field" in tuned.read_text(encoding="utf-8")

    forced = scaffold_spine(tmp_path, force=True)
    assert "spine/data-catalogue.yaml" in forced
    assert "my_custom_field" not in tuned.read_text(encoding="utf-8")


def test_init_cli_reports_no_clobber(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    assert (tmp_path / "spine" / "gates" / "gate-config.yaml").is_file()

    rc = main(["init", str(tmp_path)])  # second run
    assert rc == 0
    assert "already exists" in capsys.readouterr().out
