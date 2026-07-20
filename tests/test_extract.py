"""extract.py — the deterministic extraction core. The LLM supplies judgement; these tests
pin the parts a script must get right every time: holder resolution, amendment detection,
mechanical veto derivation (decision #18), and refuse-invalid-before-write.
"""
import extract
import pytest


def test_resolve_holder_known_and_office_carries_body():
    assert extract.resolve_holder("ofwat")["body_id"].startswith("uk-state-body-")
    sos = extract.resolve_holder("sos-defra")
    assert sos["holder_type"] == "office"
    assert sos["office_id"] and sos["body_id"]  # an office holder still needs its department


def test_resolve_holder_unknown_raises():
    # an unresolved actor must stop the batch, never be written as free text
    with pytest.raises(KeyError):
        extract.resolve_holder("some-body-we-have-not-mapped")


def test_is_amendment_detects_amending_language():
    assert extract.is_amendment("In section 2 of the Water Industry Act 1991, after subsection (2) insert—")
    assert extract.is_amendment("For paragraph (a) substitute—")
    assert not extract.is_amendment("The Authority may impose a financial penalty of such amount as is reasonable.")


UNIT_POWER = {
    "record_id": "power-sos-defra-test-act-s1", "kind": "power", "holder": "sos-defra",
    "label": "Consent to a petition", "subtype": "consent", "legal_effect": "may",
    "summary": "The Secretary of State may consent to a petition.",
    "source_id": "source-act-test", "provision_key": "test-act-s1",
    "provision_ref": "s.1", "citation_url": "https://example/section/1",
    "blocks": {"veto_type": "consent_required", "strength": "hard_stop",
               "decision_affected": "Whether the petition proceeds.",
               "veto_label": "Consent gate over the petition"},
}
UNIT_DUTY = {
    "record_id": "duty-ofwat-test-act-s2", "kind": "duty", "holder": "ofwat",
    "label": "Publish a report", "subtype": "publication", "mandatory": True,
    "summary": "The Authority must publish a report.",
    "source_id": "source-act-test", "provision_key": "test-act-s2",
    "provision_ref": "s.2", "citation_url": "https://example/section/2",
}


def test_build_derives_veto_from_blocking_power_and_validates():
    bundle, issues = extract.build([UNIT_POWER, UNIT_DUTY], "run-test")
    assert not issues
    assert len(bundle["powers"]) == 1 and len(bundle["duties"]) == 1 and len(bundle["vetoes"]) == 1
    veto = bundle["vetoes"][0]
    assert veto["derived_from_record_id"] == "power-sos-defra-test-act-s1"  # points back at its power
    assert veto["veto_id"] == "veto-sos-defra-test-act-s1"                  # id mirrors the power
    assert veto["holder_type"] == "office"                                  # mirrors the power's holder
    assert veto["body_id"] == "uk-state-body-department-for-environment-food-rural-affairs"
    assert not extract.validate_bundle(bundle)                              # all three schema-valid


def test_power_basis_defaults_statutory():
    bundle, _ = extract.build([UNIT_POWER], "run-test")
    assert bundle["powers"][0]["power_basis"] == "statutory"


def test_blocks_on_non_blocking_family_is_flagged():
    bad = {**UNIT_POWER, "record_id": "power-x-test-act-s3", "subtype": "sanction",
           "provision_key": "test-act-s3"}
    _, issues = extract.build([bad], "run-test")
    assert any("not a blocking family" in i for i in issues)


def test_duplicate_record_id_flagged_not_written():
    _, issues = extract.build([UNIT_DUTY, dict(UNIT_DUTY)], "run-test")
    assert any("duplicate record_id" in i for i in issues)
