import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator as V

root = Path(sys.argv[1]).resolve()
contracts = root / "policy-harness/contracts/v1"
sd = contracts / "schemas"
ed = contracts / "examples"
catalog_dir = root / "therblig-vla/therbligs"
schemas = {p.name.split(".")[0]: json.loads(p.read_text()) for p in sd.glob("*.schema.json")}
examples = {p.stem: json.loads(p.read_text()) for p in ed.glob("*.json")}
catalog_schema = json.loads((catalog_dir / "catalog.schema.json").read_text())
V.check_schema(catalog_schema)
catalog = yaml.safe_load((catalog_dir / "catalog.v0.yaml").read_text())
V(catalog_schema).validate(catalog)
rows = {r["code"]: r for r in catalog["rows"]}
assert list(rows) == "SH FD ST G H TL TE P A U DA I PP RL UD AD PN R x.locomote".split()
assert len(catalog["rows"]) == len({r["label"]["code"] for r in rows.values()}) == 19

analysis = (root / "therblig-vla/docs/therblig-analysis.md").read_text()
table = analysis.split("| code | temporal_form | primary | tracks |", 1)[1].split("\n\n", 1)[0]
actual = [
    [c.strip().strip(chr(96)) for c in line.strip("|").split("|")]
    for line in table.splitlines()[2:]
    if line.startswith("|")
]
for row, cells in zip(rows.values(), actual, strict=True):
    ts = row["tracks"]
    tracks = ", ".join(t["track"] + ":" + t["access"] + ("?" if t["optional"] else "") for t in ts) or "—"
    assert cells[:4] == [row["code"], row["temporal_form"], "+".join(row["layers"]["primary"]), tracks]
    r, l = row["realization"], row["label"]
    assert cells[-1] == " / ".join(
        [
            r["kind"],
            *r["capability_templates"],
            *r["s0_mode_classes"],
            *r["composition_options"],
            f"{l['lane']}:{l['code']} ({l['form']})",
        ]
    )
    for key, accesses in [
        ("active", ("TAKEOVER", "DRIVE")),
        ("maintained", ("DEPEND", "MAINTAINED")),
        ("observed", ("OBSERVE",)),
    ]:
        assert row["train_mask"][key] == list(dict.fromkeys(t["track"] for t in ts if t["access"] in accesses))
    assert all(t["access"] == "OBSERVE" for t in ts if t["track"] == "E")
quotes = re.findall(r"“([A-Za-z][A-Za-z \-]+)”", analysis)
assert quotes == json.loads(Path(__file__).with_name("ferguson-excerpts.json").read_text())
docs = [p for d in ["docs/design", "policy-harness/docs", "therblig-vla/docs"] for p in (root / d).glob("*.md")]
for p in docs:
    data = p.read_text()
    assert re.search(r"^- \[ \]", "\n".join(data.splitlines()[:20]), re.M)
    assert not re.search(r"^- \[[xX]\]", data, re.M)

register = (root / "docs/design/README.md").read_text()
statuses = {
    cells[0]: cells[-1]
    for line in register.splitlines()
    if line.startswith("| D")
    if (cells := [cell.strip() for cell in line.strip("|").split("|")])
}
assert all(statuses.get(f"D{i}") for i in range(1, 13))
cards = {e["capability_id"]: e for n, e in examples.items() if n.startswith("capability.")}
for card in cards.values():
    tag = card["extensions"]["x-therblig"]
    assert tag["catalog_revision"] == catalog["catalog_revision"]
    assert card["capability_id"].split(".", 1)[1] in rows[tag["code"]]["realization"]["capability_templates"]
iv = examples["invocation.pick-red-cup"]
cap = cards[iv["capability_ref"]["capability_id"]]
bp = examples["body-profile.g1-inspire"]
resources = {r["resource_id"]: r for r in bp["resources"]}
for p in rows.values():
    if "information_alternatives" in p:
        assert all(
            a["preferred"] in p["information"]
            and set(a["substitutes"]) <= set(p["information"])
            and a["validation_status"] == "NEEDS_VALIDATION"
            for a in p["information_alternatives"]
        )
for code in ["H", "P", "PP", "RL", "DA", "x.locomote"]:
    assert any(a["preferred"] == "F" for a in rows[code]["information_alternatives"])
for code in ["P", "PP"]:
    assert rows[code]["required_feature_choices"] == [["external_alignment", "in_hand_alignment"]]
    for s, h in [("LEFT", "LH"), ("RIGHT", "RH")]:
        hands = [t for t in rows[code]["tracks"] if t["track"] == h and t["when"]["side"] == s]
        assert all(not t["optional"] for t in hands)
        assert [t["access"] for t in hands if t["when"]["feature"] == "external_alignment"] == ["DEPEND"]
        assert [
            (t["when"]["phase"], t["access"]) for t in hands if t["when"]["feature"] == "in_hand_alignment"
        ] == [("handoff", "TAKEOVER"), ("post_handoff", "DRIVE")]
assert all(t["optional"] for t in rows["RL"]["tracks"] if t["when"].get("feature") == "withdraw")
assert [x["disposition"] for x in rows["x.locomote"]["state_left"] if "L" in x.get("tracks", [])] == [
    "RELEASED"
]
variants = {v["template"]: v for r in rows.values() for v in r.get("template_variants", [])}
sweep = variants["sweep_into_pan"]
exits = {
    track: (x["disposition"], x.get("mode_class")) for x in sweep["state_left"] for track in x.get("tracks", [])
}
expected = {t: ("RELEASED", None) for t in ["LA", "RA", "W", "E"]}
expected.update(
    {
        "LH": ("KEEP_MAINTAINED", "RETENTION"),
        "RH": ("KEEP_MAINTAINED", "RETENTION"),
        "L": ("KEEP_MAINTAINED", "BALANCE"),
    }
)
assert exits == expected and "BALANCE" in rows["U"]["realization"]["s0_mode_classes"]
assert sorted(t for x in sweep["state_left"] for t in x.get("tracks", [])) == sorted(expected)
assert sorted(t["track"] for t in sweep["tracks"]) == sorted(expected)
comb = {
    c["combination_id"]: {(b["resource_id"], b["access"]) for b in c["bindings"]}
    for c in bp["compatible_combinations"]
}
assert {
    ("LA", "DRIVE"),
    ("RA", "DRIVE"),
    ("W", "DRIVE"),
    ("LH", "DEPEND"),
    ("RH", "DEPEND"),
    ("L", "MAINTAINED"),
} not in comb.values()
assert not any(("L", "DRIVE") in c for c in comb.values())
for name, combo, features in [
    ("move_payload_guarded_drawer", "insertion-with-guarded-drawer", ["waist_assist"]),
    ("stage_for_next_use_guarded_drawer", "staging-with-guarded-drawer", []),
    ("release_to_support_guarded_drawer", "release-with-guarded-drawer", ["withdraw"]),
    ("release_to_support_guarded_drawer", "release-in-place-with-guarded-drawer", []),
]:
    active = {
        (t["track"], t["access"])
        for t in variants[name]["tracks"]
        if t["access"] != "OBSERVE"
        and t["when"].get("phase", "handoff") == "handoff"
        and (not t["when"].get("feature") or t["when"]["feature"] in features)
    }
    assert comb[combo] == active and {("LA", "DEPEND"), ("LH", "DEPEND")} <= active
    assert ("RA", "TAKEOVER") not in active
assert ("RA", "DRIVE") in comb["release-with-guarded-drawer"]
assert any(x["disposition"] == "RELEASED" and "RA" in x.get("tracks", []) for x in rows["TE"]["state_left"])
