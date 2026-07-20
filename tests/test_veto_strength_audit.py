"""The veto-strength coherence gate (Tier 1 of the 2026-07-20 audit) and vocab/schema agreement.

Background: every one of the 8 vetoes in the Water tranche shipped as `hard_stop` because
vocab/veto_strength.json was a bare list of four terms with no definitions — the extractor
had no rubric, so it defaulted. These tests pin the check that catches that class of defect,
so the build fails rather than the register quietly overstating how blocked the state is.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import validate  # noqa: E402


def _veto(**kw):
    base = {"veto_id": "veto-test", "strength": "hard_stop", "overridable": "no",
            "override_mechanism": None}
    base.update(kw)
    return base


def test_hard_stop_with_override_is_contradiction():
    """The defect that shipped: a hard stop that names its own way around itself."""
    errs = validate.veto_strength_errors([
        _veto(overridable="yes", override_mechanism="Appeal to the Secretary of State under s.43.")
    ])
    assert len(errs) == 1
    assert "contradicts overridable 'yes'" in errs[0]


def test_hard_stop_with_unknown_override_is_unsupported():
    """Asserting the strongest grade while admitting you did not check is not a judgement."""
    errs = validate.veto_strength_errors([_veto(overridable="unknown")])
    assert len(errs) == 1
    assert "unsupported" in errs[0]

    # A missing field is the same defect as an explicit "unknown".
    assert validate.veto_strength_errors([_veto(overridable=None)])


def test_strong_delay_requires_an_override():
    """strong_delay means the actor CAN eventually proceed — so a route must exist."""
    errs = validate.veto_strength_errors([_veto(strength="strong_delay", overridable="no")])
    assert any("requires overridable 'yes'" in e for e in errs)


def test_override_must_be_cited():
    """An override route asserted without a citation is an uncited legal claim (A2.2)."""
    errs = validate.veto_strength_errors([
        _veto(strength="strong_delay", overridable="yes", override_mechanism=None)
    ])
    assert any("requires a cited override_mechanism" in e for e in errs)


def test_well_formed_gradings_pass():
    assert validate.veto_strength_errors([
        _veto(strength="hard_stop", overridable="no"),
        _veto(strength="strong_delay", overridable="yes",
              override_mechanism="Appeal to the Secretary of State under WCA 1981 s.28F(5)."),
        _veto(strength="procedural_risk", overridable="yes",
              override_mechanism="WCA 1981 s.28H(4)-(5): proceed 28 days after notice."),
    ]) == []


def test_live_vetoes_are_coherent():
    """The real record set must stay coherent — this is the regression guard on the audit."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
    import store
    assert validate.veto_strength_errors(store.load("vetoes")) == []


def test_vocab_matches_schema_enums():
    """Core rule 3: the definitions in vocab/ and the enums in schemas/ may not drift apart."""
    assert validate.vocab_schema_errors() == []


def test_defined_vocabs_carry_definitions():
    """A term without a definition is what caused the 8/8 — the powers-layer vocabs must
    carry a definition and an operational test per term, not a bare string."""
    import json
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("veto_strength", "veto_type", "modality", "legal_effect", "power_type", "duty_type"):
        with open(os.path.join(repo, "vocab", name + ".json"), encoding="utf-8") as fh:
            terms = json.load(fh)["terms"]
        assert terms, name
        for t in terms:
            assert isinstance(t, dict), f"{name}: term {t!r} is a bare string, not a definition"
            assert t.get("term") and t.get("definition"), f"{name}: {t} lacks term/definition"
