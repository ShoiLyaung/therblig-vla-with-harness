import copy
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
harness = root / "policy-harness"
provider = root / "therblig-vla"
contracts = harness / "contracts/v1"
catalog_dir = provider / "therbligs"
sys.path.insert(0, str(harness / "tests/contract"))
from evidence_rules import (
    bound_primary,
    bp,
    cap,
    cards,
    context,
    counter,
    dictionaries,
    examples,
    expect,
    information_kinds,
    iv,
    profiles,
    publish,
    register_body,
    resolve,
    resource_kinds,
    sensors,
)

catalog_schema = json.loads((catalog_dir / "catalog.schema.json").read_text())
Draft202012Validator.check_schema(catalog_schema)
catalog = yaml.safe_load((catalog_dir / "catalog.v0.yaml").read_text())
Draft202012Validator(catalog_schema).validate(catalog)
rows = {r["code"]: r for r in catalog["rows"]}
expected_channels = ["little", "ring", "middle", "index", "thumb_bend", "thumb_rotate"]
axis_roles = ["little", "ring", "middle", "index", "thumb_flex", "thumb_rotate"]
wanted = dict(zip(expected_channels, axis_roles))
codes = "G H TL P A U DA PP RL".split()
kinds = {
    "V": "VISUAL_SEMANTIC",
    "G": "POSE",
    "F": "FORCE_TACTILE",
    "P": "PROPRIOCEPTION",
    "T": "TASK_CONTEXT",
    "Q": "REFERENCE_STANDARD",
}
for code in codes:
    s = rows[code]["information_evidence"][0]["sensor_requirement"]
    assert s["channel_axis_roles"] == wanted and s["channel_ids"] == expected_channels
    assert s["raw_type"] == "INTEGER" and s["raw_range"] == {"min": 0, "max": 1000}
    d = copy.deepcopy(s)
    d["raw_units"] = d.pop("units")
    for rid, expected_id in [("LH", "left.hand.force"), ("RH", "right.hand.force")]:
        assert bound_primary(bp, register_body(bp), "hand", d, {"hand": rid})["sensor_id"] == expected_id
assert rows["x.locomote"].get("information_evidence") is None
for card in cards.values():
    role, primary, alts = publish(card)[0]
    code = card["extensions"]["x-therblig"]["code"]
    row = rows[code]
    p = row["information_evidence"][0]
    direct = copy.deepcopy(p["sensor_requirement"])
    assert direct.pop("binding") == "EACH_BOUND_RESOURCE"
    direct["raw_units"] = direct.pop("units")
    assert primary == {"profile_id": p["evidence_profile"], **direct} and role == "hand"
    assert alts == [
        {
            "profile_id": f["evidence_profile"],
            "input_kinds": [kinds[k] for k in f["substitutes"]],
            "validation_status": f["validation_status"],
        }
        for f in row["information_alternatives"]
    ]
    for hand, arm, sid in [("LH", "LA", "left.hand.force"), ("RH", "RA", "right.hand.force")]:
        assert resolve(card, bp, {"hand": hand, "arm": arm, "camera": "E"}, context) == [("PRIMARY", sid)]
    assert card["capability_revision"] == "3" and card["protocol_version"] == "1.0.0"
assert all(iv["capability_ref"][k] == cap[k] for k in iv["capability_ref"])
for n in ("execution.running", "execution.canceled-after-correction"):
    assert examples[n]["invocation_id"] == iv["invocation_id"]
assert {"hand.acquire_slow", "hand.retain"} <= set(cap["body_requirements"]["required_profiles"])
assert iv["safety"]["profile_id"] == rows["G"]["realization"]["active_s0_profile"] == "hand.acquire_slow"
assert (
    cap["limits"]["safety_profiles"] == ["hand.acquire_slow"]
    and profiles["hand.acquire_slow"]["allowed_verbs"] == []
)
print(
    "K1/K2: four revision-3 cards verified from public inputs alone on both hands; payload-derived checksums and frozen invocation/execution links match; active closure profile gated"
)
catv = Draft202012Validator(catalog_schema)
ac = copy.deepcopy(catalog)
ar = next(r for r in ac["rows"] if r["code"] == "G")["information_alternatives"][0]
ar["validation_status"] = "VALIDATED"
expect("catalog VALIDATED without record", catv.is_valid(ac), False)
ar["validation_record_ref"] = " "
expect("blank record", catv.is_valid(ac), False)
ar["validation_record_ref"] = "fixture.ref"
expect("validated with ref shape", catv.is_valid(ac), True)
pc = copy.deepcopy(catalog)
next(r for r in pc["rows"] if r["code"] == "G")["information_evidence"][0]["validation_status"] = "VALIDATED"
expect("validated primary without ref", catv.is_valid(pc), False)
for field, typo in [("resource_kind", "END_EFECTOR"), ("information_kind", "FORCE_TACTILE_RAW")]:
    b = copy.deepcopy(catalog)
    next(r for r in b["rows"] if r["code"] == "G")["information_evidence"][0]["sensor_requirement"][field] = (
        typo
    )
    expect("invalid " + field, catv.is_valid(b), False)
pp = catalog_schema["$defs"]["PrimaryEvidence"]["properties"]["sensor_requirement"]["properties"]
assert (
    set(pp["resource_kind"]["enum"]) == resource_kinds
    and set(pp["information_kind"]["enum"]) == information_kinds
)
probe_selector = dict(
    profile_id="fixture.pressure@1",
    resource_kind="SENSOR",
    information_kind="FORCE_TACTILE",
    measurement_method="DEDICATED_SENSOR",
    sensing_location="CONTACT_SURFACE",
    contact_localization=True,
    available=True,
    quantity="PRESSURE",
    raw_type="NUMBER",
    raw_units="Pa",
    raw_range={"min": 0, "max": 5},
    channel_ids=["cell01"],
)
catalog_elem = copy.deepcopy(rows["G"]["information_evidence"][0])
catalog_elem["sensor_requirement"] = {
    **{k: v for k, v in probe_selector.items() if k not in ("raw_units", "profile_id")},
    "units": "Pa",
    "binding": "EACH_BOUND_RESOURCE",
}
cat_element_validator = Draft202012Validator(
    {"$defs": catalog_schema["$defs"], "$ref": "#/$defs/PrimaryEvidence"}
)
assert cat_element_validator.is_valid(catalog_elem)
catalog_elem["sensor_requirement"]["sensing_location"] = "ACTUATOR_AXIAL"
assert not cat_element_validator.is_valid(catalog_elem)
faq = "https://www.inspire-robots.com/support/FAQ/dexterous%20hands/"
article = "https://www.inspire-robots.com/news/industry%20news/2024-12-27/247.html"
paper = "https://arxiv.org/html/2603.08988v1#S2"
bodyrefs = []
for name, e in examples.items():
    bodyrefs.extend((name, obj["body_ref"]) for obj in dictionaries(e) if "body_ref" in obj)
assert len(bodyrefs) == 14 and all(
    ref == {"body_id": bp["body_id"], "profile_revision": "3"} for name, ref in bodyrefs
)
active_files = [
    root / "README.md",
    root / "docs/brief.md",
    *sorted((root / "docs/design").glob("*.md")),
    *sorted((harness / "docs").glob("*.md")),
    *sorted((provider / "docs").glob("*.md")),
    *sorted((contracts / "schemas").glob("*.json")),
    *sorted((contracts / "examples").glob("*.json")),
    contracts / "openapi.yaml",
    catalog_dir / "catalog.schema.json",
    catalog_dir / "catalog.v0.yaml",
]
oldrev = re.compile(r'g1-inspire@1\b|"profile_revision"\s*:\s*(?:"1"|1\b)')
assert not [p for p in active_files if oldrev.search(p.read_text())]

active_files = [
    *active_files
]  # Current design and contracts; verbatim historical excerpts stay in the reference archive.
forbidden = re.compile(
    r"9\.8|9\.81|fingertip-equivalent|指尖等效|hand-fingertip-force@1|reference_point|0\.00980665|raw_g", re.I
)
assert not [(p.name, l) for p in active_files for l in p.read_text().splitlines() if forbidden.search(l)]
freq = re.compile(r"\b(?:163\s*Hz|66\s*ms)\b", re.I)
timelines = [(p, l) for p in active_files for l in p.read_text().splitlines() if freq.search(l)]
assert len(timelines) >= 2 and all("第三方" in l and "Correll" in l for p, l in timelines)
notes = [l for p in active_files for l in p.read_text().splitlines() if "0.5 N" in l]
assert notes and all("未经" in l and ("厂商" in l or "手册" in l) for l in notes)
vendor_numeric_hz = re.compile(r"\d[\d.,–—-]*\s*(?:k?Hz\b|赫兹)", re.I)
assert all(
    "第三方" in l or (p.name == "walkthroughs.md" and "S1 双工具相对位姿闭环" in l)
    for p in active_files
    for l in p.read_text().splitlines()
    if vendor_numeric_hz.search(l)
)
overview = (root / "docs/design/README.md").read_text()
assert all(u in overview for u in [faq, article, paper]) and "英文手册链接不可达，未读" in overview
assert all(s in overview for s in ["3×3", "12×8", "10×8", "8×14", "5–17", "16 位", "0–4096"])
assert "低速" in (root / "docs/design/walkthroughs.md").read_text().split("## W1 ")[1].split("## W2 ")[0]
assert "g1-inspire@3" in (root / "docs/design/walkthroughs.md").read_text() and all(
    "frame_id" not in c
    for s in sensors.values()
    if s["sensor_id"].endswith((".hand.force", ".hand.current"))
    for c in s["channels"]
)
print(
    "C3/C5/C6: obsolete scale/location assertions absent; all timing mentions are third-party; scalar calibrations only; W1 low-speed guard and DFTP-only array inventory present"
)
oldpins = [
    "sha256:a0adf7f4c692f5a6b3b2e74e5bb3d700ba8500e777a3da78ab1d8bb1821885f6",
    "sha256:e9e4c34a7ffb48aceb04496eb604530053d504d1ae2e769ae83e5c19d3d2233a",
    "sha256:201645cfffaa8a400072dbc6d9463c614df416f8f7b04ecd77506baa2df67530",
    "sha256:fca0d5dd2e7b813061ce3c8a337eeaab34336a6fa50ae8e3a2fa45fea3b9d39a",
]

for p in active_files:
    assert not any(old in p.read_text() for old in (*oldpins, "generic/contact_evidence_available@1")), p
for p in [*sorted((contracts / "schemas").glob("*.json")), *sorted((harness / "docs").glob("*.md"))]:
    assert not re.search(
        r"therblig|transport.?(loaded|empty)|pre.?position|disassembl|unavoidable|avoidable|fatigue|Inspire|RH56|Correll|因时",
        p.read_text(),
        re.I,
    ), p
print("ALL CHECKS PASSED. Explicit decision cases:", dict(counter))
