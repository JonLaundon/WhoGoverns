"""The operative layer (powers/duties/vetoes) reaching the map contract.

Spiral 1 compiled structure only, so the powers register existed in data/ but was invisible
to any consumer. These pin the join: records land on their holder node, the blocking relation
becomes a traversable CAN_VETO edge, and the colour axis derives from SOURCED fields rather
than a hand-kept list of bodies (which would be an uncited taxonomy in the presentation layer).
"""
import compile as compile_mod

POWERS = [
    {"power_id": "power-fund", "power_type": "funding", "body_id": "b-sos", "holder_type": "office",
     "office_id": "o-sos", "provision_key": "pk-1"},
    {"power_id": "power-court", "power_type": "adjudication", "body_id": "b-court",
     "holder_type": "body", "provision_key": "pk-1"},
    {"power_id": "power-lic", "power_type": "licence", "body_id": "b-reg", "holder_type": "body",
     "provision_key": "pk-1"},
]
BODIES = [
    {"body_id": "b-sos", "functions": []},
    {"body_id": "b-court", "functions": ["judicial"]},
    {"body_id": "b-reg", "functions": ["regulation"]},
    {"body_id": "b-treasury", "functions": []},
]
BY_ID = {p["power_id"]: p for p in POWERS}
BODY_BY_ID = {b["body_id"]: b for b in BODIES}


def _kind(**kw):
    v = {"derived_from_record_id": None, "body_id": "b-reg", "holder_type": "body"}
    v.update(kw)
    return compile_mod.blocker_kind(v, BY_ID, BODY_BY_ID)


def test_fiscal_derives_from_the_underlying_power_not_the_holder():
    """HM Treasury carries no `functions` tag, so the fiscal colour can only come from the
    power being gated — the funding power it consents to. This is the case that proved the
    colour axis had to key on the derived power, not on the holder."""
    assert _kind(body_id="b-treasury", derived_from_record_id="power-fund") == "fiscal"


def test_judicial_derives_from_the_function_tag_or_an_adjudication_power():
    assert _kind(body_id="b-court", derived_from_record_id="power-lic") == "judicial"
    assert _kind(body_id="b-sos", derived_from_record_id="power-court") == "judicial"


def test_regulatory_derives_from_the_sourced_regulation_function():
    assert _kind(body_id="b-reg", derived_from_record_id="power-lic") == "regulatory"


def test_ministerial_catches_office_held_vetoes():
    """Without this, ministerial consents fall through uncoloured."""
    assert _kind(body_id="b-sos", holder_type="office", derived_from_record_id="power-lic") == "ministerial"


def test_unknown_holder_is_left_uncoloured_not_guessed():
    assert _kind(body_id="b-sos", holder_type="body", derived_from_record_id="power-lic") is None


def test_fiscal_beats_ministerial():
    """A funding consent held by a Minister is fiscal first — order matters."""
    assert _kind(body_id="b-sos", holder_type="office", derived_from_record_id="power-fund") == "fiscal"


# --- attachment ---------------------------------------------------------------------------

def _graph():
    return {"nodes": [{"data": {"id": "b-sos", "kind": "body"}},
                      {"data": {"id": "o-sos", "kind": "office", "body_id": "b-sos"}},
                      {"data": {"id": "b-reg", "kind": "body"}}],
            "edges": []}


VETO = {"veto_id": "v-1", "veto_type": "consent_required", "strength": "hard_stop",
        "holder_type": "office", "office_id": "o-sos", "body_id": "b-sos",
        "blocks_holder_type": "body", "blocks_body_id": "b-reg", "provision_key": "pk-1",
        "derived_from_record_id": "power-lic", "decision_affected": "Whether the regulator may act."}
PROVISIONS = [{"provision_key": "pk-1", "instrument_id": "i-1"}]
INSTRUMENTS = [{"instrument_id": "i-1", "year": 1991}]


def test_office_held_records_attach_to_the_office_and_mirror_to_its_department():
    g = _graph()
    compile_mod.attach_operative(g, [POWERS[0]], [], [], PROVISIONS, INSTRUMENTS, BODIES)
    by_id = {n["data"]["id"]: n["data"] for n in g["nodes"]}
    assert by_id["o-sos"]["operative"]["counts"]["powers"] == 1
    # the department's card must still be able to show what its minister holds
    assert len(by_id["b-sos"]["office_operative"]["powers"]) == 1


def test_buckets_are_pluralised_properly():
    """'duty' + 's' is not 'duties' — a bug that silently zeroed every duty and veto count."""
    g = _graph()
    compile_mod.attach_operative(g, [], [], [VETO], PROVISIONS, INSTRUMENTS, BODIES)
    op = {n["data"]["id"]: n["data"] for n in g["nodes"]}["o-sos"]["operative"]
    assert set(op) >= {"powers", "duties", "vetoes", "counts"}
    assert op["counts"]["vetoes"] == 1


def test_can_veto_edge_is_drawn_with_its_kind_and_strength():
    g = _graph()
    compile_mod.attach_operative(g, [], [], [VETO], PROVISIONS, INSTRUMENTS, BODIES)
    edges = [e["data"] for e in g["edges"] if e["data"]["kind"] == "can_veto"]
    assert len(edges) == 1
    assert edges[0]["source"] == "o-sos" and edges[0]["target"] == "b-reg"
    assert edges[0]["strength"] == "hard_stop"
    assert edges[0]["blocker_kind"] == "ministerial"


def test_veto_over_a_party_outside_the_modelled_state_draws_no_edge():
    """An abstraction licence blocks a private abstractor. There is no node to point at, and
    inventing one would be worse than the gap — the edge is simply absent."""
    g = _graph()
    private = dict(VETO, veto_id="v-2", blocks_body_id=None, blocks_office_id=None)
    compile_mod.attach_operative(g, [], [], [private], PROVISIONS, INSTRUMENTS, BODIES)
    assert [e for e in g["edges"] if e["data"]["kind"] == "can_veto"] == []


def test_card_carries_citation_assurance_and_since_year():
    g = _graph()
    compile_mod.attach_operative(g, [], [], [VETO], PROVISIONS, INSTRUMENTS, BODIES)
    card = {n["data"]["id"]: n["data"] for n in g["nodes"]}["o-sos"]["operative"]["vetoes"][0]
    assert card["since"] == 1991                      # joined provision -> instrument
    assert card["decision_affected"]                  # the field a Power record cannot carry
    assert "verification_status" in card              # assurance on the face of the card
