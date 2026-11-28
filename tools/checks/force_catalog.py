import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema_specifications import REGISTRY as META
from referencing import Registry, Resource

root = Path(sys.argv[1]).resolve()
vla = root / "policy-harness"
provider = root / "therblig-vla"
contracts = vla / "contracts/v1"
catalog_dir = provider / "therbligs"


def git(repo, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), *args])


def digest(b):
    return hashlib.sha256(b).hexdigest()


def dictionaries(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from dictionaries(child)


def marks(s):
    return s.strip().strip(chr(96))


schemas = {p.name: json.loads(p.read_text()) for p in (contracts / "schemas").glob("*.schema.json")}
base = "https://contract.invalid/v1/"
registry = (
    Registry()
    .combine(META)
    .with_resources((base + name, Resource.from_contents(value)) for name, value in schemas.items())
)


def validator(name):
    return Draft202012Validator(
        {"$ref": base + name + ".schema.json"}, registry=registry, format_checker=FormatChecker()
    )


catalog_schema = json.loads((catalog_dir / "catalog.schema.json").read_text())
Draft202012Validator.check_schema(catalog_schema)
catalog = yaml.safe_load((catalog_dir / "catalog.v0.yaml").read_text())
Draft202012Validator(catalog_schema).validate(catalog)
examples = {p.stem: json.loads(p.read_text()) for p in (contracts / "examples").glob("*.json")}
rows = {r["code"]: r for r in catalog["rows"]}
bp = examples["body-profile.g1-inspire"]
assert catalog["body_profile"] == bp["body_id"] + "@" + bp["profile_revision"] == "g1-inspire@3"
resources = {r["resource_id"]: r for r in bp["resources"]}
sensors = {r["sensor_id"]: r for r in bp["sensors"]}
assert len(resources) == len(bp["resources"]) and len(sensors) == len(bp["sensors"])
channel_names = "little ring middle index thumb_bend thumb_rotate".split()
hands = {"right": "RH", "left": "LH"}


def consistent_channels(sensor):
    allowed = resources[sensor["resource_id"]]["axes"]
    channels = sensor.get("channels", [])
    return len(set(c["channel_id"] for c in channels)) == len(channels) and all(
        c["axis_id"] in allowed and c["range"]["min"] <= c["range"]["max"] for c in channels
    )


assert all(consistent_channels(s) for s in sensors.values())
required_codes = set("G H TL P A U DA PP RL".split())
assert {r["code"] for r in rows.values() if r.get("information_evidence")} == required_codes


def matches(table, rid, req):
    def qualifies(s):
        if (
            s["resource_id"] != rid
            or resources[rid]["kind"] != req["resource_kind"]
            or s.get("available") is not req["available"]
        ):
            return False
        if (
            req["information_kind"] not in s["information"]
            or s.get("measurement_method") != req["measurement_method"]
        ):
            return False
        if (
            s.get("sensing_location") != req["sensing_location"]
            or s.get("contact_localization") is not req["contact_localization"]
        ):
            return False
        return (
            consistent_channels(s)
            and [
                c["channel_id"]
                for c in s.get("channels", [])
                if c["quantity"] == req["quantity"] and c["units"] == req["units"]
            ]
            == req["channel_ids"]
        )

    return {sid for sid, s in table.items() if qualifies(s)}


tested_pairs = variants = 0
for code, r in rows.items():
    assert all(a["validation_status"] == "NEEDS_VALIDATION" for a in r.get("information_alternatives", []))
    if code not in required_codes:
        continue
    assert len(r["information_evidence"]) == 1
    e = r["information_evidence"][0]
    req = e["sensor_requirement"]
    assert (
        e["kind"] == "F"
        and e["evidence_profile"] == "hand-actuator-axial-force@1"
        and e["validation_status"] == "DATASHEET_DECLARED"
    )
    assert (
        req["binding"] == "EACH_BOUND_RESOURCE"
        and req["channel_ids"] == channel_names
        and req["quantity"] == "FORCE"
    )
    assert (
        req["sensing_location"] == "ACTUATOR_AXIAL"
        and req["contact_localization"] is False
        and req["units"] == "count"
    )
    for word in ("连杆", "定位", "未报告", "拇指旋转", "相对", "超调", "低速", "刷新率"):
        assert word in " ".join(e["caveats"])
    for side, rid in hands.items():
        assert rid in {t["track"] for t in r["tracks"]}
        assert matches(sensors, rid, req) == {side + ".hand.force"}
        tested_pairs += 1
    for variant in r.get("template_variants", []):
        bound = {t["track"] for t in variant.get("tracks", r["tracks"])} & set(hands.values())
        assert bound and all(matches(sensors, rid, req) for rid in bound)
        variants += 1
    for property_, wrong in [
        ("available", False),
        ("measurement_method", "ACTUATOR_CURRENT_PROXY"),
        ("sensing_location", "CONTACT_SURFACE"),
        ("contact_localization", True),
    ]:
        bad = copy.deepcopy(sensors)
        bad["left.hand.force"][property_] = wrong
        assert not matches(bad, "LH", req)
    bad = copy.deepcopy(sensors)
    bad["left.hand.force"]["channels"][0]["axis_id"] = "little_r"
    assert not matches(bad, "LH", req)
print(
    f"C4: 9/9 required hand-F rows; {tested_pairs} left/right bindings, {variants} variants and all 24 channel/axis joins; no other hand, proxy or surface stream qualifies; fallbacks and foot-contact retained"
)
