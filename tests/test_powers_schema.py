"""The Spiral 2 powers-layer schemas (Annex A6) enforce the decisions that define them:
the modality cross-check, and veto-as-a-derived-projection (never a free-standing primitive).
"""
import json
import os

from jsonschema import Draft202012Validator

SCHEMAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")


def _validator(name):
    with open(os.path.join(SCHEMAS, name), encoding="utf-8") as fh:
        return Draft202012Validator(json.load(fh))


def _ok(name, rec):
    return not list(_validator(name).iter_errors(rec))


CITATION = {"provision": "s.13", "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/13"}

POWER = {
    "power_id": "power-wsra-water-industry-act-1991-s13-001",
    "holder_type": "body", "body_id": "uk-state-body-water-services-regulation-authority",
    "power_label": "Power to modify licence conditions", "power_type": "rulemaking",
    "power_basis": "statutory",
    "modality": "power", "legal_effect": "may", "summary": "Ofwat may modify conditions of a water company's licence.",
    "source_id": "source-act-water-industry-act-1991", "provision_key": "water-industry-act-1991-s13",
    "citation": CITATION, "record_status": "extracted",
}

VETO = {
    "veto_id": "veto-secretary-of-state-water-industry-act-1991-s24-001",
    "holder_type": "office", "office_id": "office-secretary-of-state-for-environment-food-rural-affairs",
    "body_id": "uk-state-body-department-for-environment-food-rural-affairs",
    "veto_label": "Special administration order gate", "veto_type": "approval_required",
    "modality": "veto", "strength": "hard_stop", "summary": "A special administration order requires the SoS.",
    "source_id": "source-act-water-industry-act-1991", "provision_key": "water-industry-act-1991-s24",
    "citation": {"provision": "s.24", "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/24"},
    "derived_from_record_id": "power-secretary-of-state-water-industry-act-1991-s24-001",
    "decision_affected": "Whether a water company is placed into special administration.",
    "record_status": "extracted",
}


def test_valid_power_and_veto_pass():
    assert _ok("power.schema.json", POWER)
    assert _ok("veto.schema.json", VETO)


def test_modality_must_agree_with_record_type():
    bad = {**POWER, "modality": "duty"}       # a Power that claims to be a duty
    assert not _ok("power.schema.json", bad)  # const 'power' rejects it


def test_veto_requires_its_underlying_power_and_target():
    # A veto is a DERIVED projection: without the canonical power it flags from, or without
    # the decision it blocks, it is not a valid record (decision 2026-07-14).
    assert not _ok("veto.schema.json", {k: v for k, v in VETO.items() if k != "derived_from_record_id"})
    assert not _ok("veto.schema.json", {k: v for k, v in VETO.items() if k != "decision_affected"})


def test_derived_from_must_reference_a_power_id():
    bad = {**VETO, "derived_from_record_id": "duty-something-001"}  # must be a power-*
    assert not _ok("veto.schema.json", bad)


def test_unknown_field_rejected():
    assert not _ok("power.schema.json", {**POWER, "made_up_field": True})


def test_power_basis_is_required_and_constrained():
    # decision #21: legal basis is never silently assumed — the field is mandatory,
    # and only the four recognised bases are allowed (Spiral 2 populates 'statutory').
    assert not _ok("power.schema.json", {k: v for k, v in POWER.items() if k != "power_basis"})
    assert not _ok("power.schema.json", {**POWER, "power_basis": "made_up"})
    assert _ok("power.schema.json", {**POWER, "power_basis": "prerogative"})
