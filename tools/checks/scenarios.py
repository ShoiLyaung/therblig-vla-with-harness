import copy
import json
import math
import re
import subprocess
from collections import Counter
from graphlib import TopologicalSorter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from jsonschema import Draft202012Validator as V

P = Path("docs/design/scenarios")
D = Path(__file__).resolve().parent
tracks = "E LA RA LH RH W L S2 MON".split()
components = (
    "Planner Context Memory ToolInterface Resolver Executor Verifier S1 S0 Monitor Protocol BodyProfile".split()
)
percepts = "头部视觉 关节位姿 手部轴向计数 电流代理 深度 点云 语音 惯性 足接触 液位与溢出 材料损伤 接收者承载 柔性地标 接口就位与扭矩 可读标签 动态目标轨迹 外部载荷与张力 工作区可见范围".split()
codes = [r["code"] for r in yaml.safe_load(Path("therblig-vla/therbligs/catalog.v0.yaml").read_text())["rows"]]
statuses = ["已覆盖", "需要但被阻塞", "不涉及"]
ok, blocked, na = statuses


class Loader(yaml.SafeLoader):
    pass


def mapping(loader, node):
    keys = [loader.construct_object(k) for k, v in node.value]
    if not all(isinstance(k, str) for k in keys) or len(set(keys)) != len(keys):
        raise ValueError("重复键或非字符串键")
    return yaml.SafeLoader.construct_mapping(loader, node)


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def load(p):
    v = yaml.load(p.read_text(), Loader=Loader)
    assert json.loads(json.dumps(v, allow_nan=False)) == v
    return v


def schema():
    return json.loads((P / "scenario.schema.json").read_text())


def validate(v):
    V(schema()).validate(v)


cases = [load(f) for f in sorted((P / "cases").glob("*.yaml"))]
pins = cases[0]["baseline_refs"]
for key, repo in [("root", "."), ("harness", "policy-harness"), ("provider", "therblig-vla")]:
    for rev in {case["baseline_refs"][key] for case in cases}:
        subprocess.run(["git", "-C", repo, "cat-file", "-e", rev + "^{commit}"], check=True)
import subprocess
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


@lru_cache(maxsize=None)
def pinned(repo, rev, path):
    return subprocess.check_output(["git", "-C", repo, "show", rev + ":" + path], text=True)


def contract_data():
    rev = pins["harness"]
    repo = "policy-harness"

    def read(path):
        return json.loads(pinned(repo, rev, "contracts/v1/" + path))

    names = subprocess.check_output(
        ["git", "-C", repo, "ls-tree", "--name-only", rev + ":contracts/v1/schemas"], text=True
    ).splitlines()
    schemas = [read("schemas/" + n) for n in names if n.endswith(".json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)

    def example(name):
        return read("examples/" + name + ".json")

    run = example("execution.running")
    end = example("execution.canceled-after-correction")
    lookup = {
        k: copy.deepcopy(run[k]) for k in ("protocol_version", "invocation_id", "execution_id", "core_evidence")
    }
    lookup.update(
        status="ADMITTED", checked_at=run["updated_at"], ledger_covered_from=run["admitted_at"] | {"t": 0}
    )
    pending = copy.deepcopy(run)
    pending.update(
        state="STOPPING",
        cancel={k: v for k, v in end["cancel"].items() if k != "completed_at"} | {"state": "ACCEPTED"},
        updated_at=end["cancel"]["accepted_at"],
    )
    fault = copy.deepcopy(end)
    r = fault["result"]
    h = r["evidence"]["controller_summary"]
    fault["state"] = r["terminal_state"] = "FAILED"
    r["reason_code"] = "fault/controller"
    fault["cancel"] = pending["cancel"]
    h.update(stable=False, summary="右侧授权尚未结清，观察轨已归还。", record_id="fault.stop.record")
    for ledger, disp in zip(h["resources"], r["resource_dispositions"], strict=True):
        settled = ledger["resource_id"] == "E"
        ledger["settled"] = settled
        ledger["disposition"] = disp["disposition"] = "RELEASED" if settled else "QUARANTINED"
        ledger.pop("maintained_token", None)
        disp.pop("maintained_token", None)
        disp["s0_record_ref"] = h["record_id"]
    fault["core_evidence"] = {
        "availability": "UNAVAILABLE",
        "reason_code": "fault/telemetry",
        "checked_at": fault["terminal_at"],
    }
    grace = example("event.required-clause-unarmed-grace-expired")
    bar = example("monitoring-brief.maintain-barrier")
    irq = copy.deepcopy(grace)
    irq.update(event_id="event.barrier.right", protection_ref="protect.barrier.right")
    irq["scope"]["task_id"] = bar["phase"]["task_id"]
    cx = irq["detection"]["phase_contexts"][0]
    cx.pop("invocation_id")
    cx.update({k: bar["phase"][k] for k in ("task_id", "goal_revision", "plan_node_id", "attempt")})
    cx.update(brief_id=bar["brief_id"], clause_ids=["right_retention"])
    irq["detection"]["clause_failures"][0].update(brief_id=bar["brief_id"], clause_id="right_retention")
    idle = example("event.baseline-fall-idle")
    receipt = dict(
        protocol_version=idle["protocol_version"],
        producer=idle["producer"] | {"id": "s0.local", "boot_id": "s0.trial"},
        protection_id=idle["protection_ref"],
        event_ref=idle["event_id"],
        level="STOP_LATCHED",
        scope=idle["scope"] | {"resource_ids": ["L", "RA"]},
        applied_at=idle["observed_at"],
        protection_epoch=4,
    )
    verify = example("verification.unknown-occluded")
    level = copy.deepcopy(verify)
    level["predicates"][0]["predicate"] = {"id": "generic/target_level@1", "args": ["cup.target"]}
    samples = {
        ("F01", "lookup_read"): ("InvocationLookup", lookup),
        ("F01", "execution_read"): ("Execution", run),
        ("F01b", "irq"): ("Event", grace),
        ("F02b", "pending"): ("Execution", pending),
        ("F02b", "fault"): ("Execution", fault),
        ("F03", "irq"): ("Event", irq),
        ("F04a", "irq"): ("Event", idle),
        ("F04a", "applied"): ("ProtectionReceipt", receipt),
        ("F04b", "irq"): ("Event", example("event.required-clause-coverage-lost")),
        ("F05", "check"): ("Verification", level),
    }
    grace_receipt = receipt | dict(
        protection_id=grace["protection_ref"],
        event_ref=grace["event_id"],
        scope=grace["scope"],
        level="SOFT_HOLD",
        applied_at=grace["observed_at"],
    )
    samples["F01b", "applied"] = ("ProtectionReceipt", grace_receipt)
    confirmed = copy.deepcopy(level)
    confirmed["checks"]["effect_holds"] = "FALSE"
    confirmed["verdict"] = "FAILED"
    confirmed["failure_attribution"] = "EXTERNAL"
    confirmed["predicates"].append(
        dict(
            predicate={"id": "generic/no_outside_spill@1", "args": ["tray"]},
            value="FALSE",
            evidence_refs=["obs.tray.overflow"],
        )
    )
    samples["F05b", "check"] = ("Verification", confirmed)
    for fid in ["F06b", "F08"]:
        samples[fid, "check"] = ("Verification", verify)
    roots = {
        "InvocationLookup": "invocation.schema.json#/$defs/InvocationLookup",
        "Execution": "execution.schema.json",
        "Event": "event.schema.json#/$defs/Event",
        "ProtectionReceipt": "event.schema.json#/$defs/ProtectionReceipt",
        "Verification": "verification.schema.json",
    }
    for kind, data in samples.values():
        Draft202012Validator({"$ref": roots[kind]}, registry=registry).validate(data)
    return samples, roots


def pointer(instance, path):
    if not path.startswith("/") or re.search(r"~(?![01])", path):
        raise ValueError(path)
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(instance, list):
            if not re.fullmatch("0|[1-9][0-9]*", token):
                raise ValueError(path)
            instance = instance[int(token)]
        elif isinstance(instance, dict):
            instance = instance[token]
        else:
            raise ValueError("指针穿过标量：" + path)
    return instance


adapter_paths = {
    "当前所有权": ["/腿轨执行", "/右臂"],
    "本地停止账本": ["/RH处置"],
    "托盘观测": ["/越界"],
    "本地保护请求": ["/level", "/protection_id", "/event_ref"],
    "重试预算": ["/同条件"],
    "派发记录": ["/同条件新调用", "/状态"],
    "证据复测": ["/工况"],
    "新尝试": ["/入口"],
    "用户输入": ["/意图状态"],
    "检查点": ["/恢复状态"],
    "资源对账": ["/处置"],
    "恢复核验": ["/依据"],
    "再准入": ["/资源"],
    "本地离线审计": ["/旧快照", "/蓝杯阶段"],
    "取消选择": ["/依据", "/执行", "/新封锁待派资源"],
    "观测质量": ["/液面", "/材料可见性"],
    "证据批准": ["/适用性"],
    "解析记录": ["/状态"],
    "承接观测": ["/接收手"],
    "释放守卫": ["/结论"],
    "地标观测": ["/隐藏角"],
}
WIRE, ROOTS = contract_data()
REQUIRED_ASSERTIONS = json.loads((Path(__file__).parent / "required_assertions.json").read_text())
OPTIONAL_ASSERTIONS = {("F02b", "协议", "pending", "Execution", "/state", "STOPPING")}


def normalized(value, mode):
    if mode == "set":
        assert isinstance(value, list) and all(isinstance(x, str) for x in value)
        assert len(set(value)) == len(value)
        value = sorted(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def contract_assertion(x):
    return (
        x["source"],
        x["record"],
        x["record_type"],
        x["path"],
        normalized(x.get("select"), None),
        x.get("compare_as"),
        normalized(x["equals"], x.get("compare_as")),
    )


def read_assertion(instance, x):
    if "select" in x:
        selector = x["select"]
        assert (x["record_type"], selector["array_path"]) == ("Execution", "/result/resource_dispositions")
        resource_rows = pointer(instance, selector["array_path"])
        matches = [row for row in resource_rows if row["resource_id"] == selector["resource_id"]]
        assert len(matches) == 1, selector
        instance = matches[0]
    return pointer(instance, x["path"])


def verify_vectors(v, wire=None):
    if wire is None:
        wire = WIRE
    fs = {f["id"]: f for f in v["faults"]}
    assert set(fs) == {t["when"] for t in v["test_vectors"]} and len(fs) == len(v["test_vectors"])
    for t in v["test_vectors"]:
        fid = t["when"]
        fault = fs[fid]
        for k in ["expected_records", "ordering", "forbidden_outcomes"]:
            assert t[k] == fault[k], (fid, k)
        observations = {}
        by_alias = {}
        wirekeys = set()
        required_seen = set()
        observed_fields = set()
        assert fid in REQUIRED_ASSERTIONS
        for x in t["assertions"]:
            alias = x["alias"]
            rec = x["record"]
            typ = x["record_type"]
            value = x["equals"]
            assert alias not in by_alias
            by_alias[alias] = rec
            optional_key = (fid, x["source"], rec, typ, x["path"], str(value))
            assert x.get("optional_record", False) == (optional_key in OPTIONAL_ASSERTIONS), (
                fid,
                "optionality",
                alias,
            )
            signature = contract_assertion(x)
            assert signature[:-1] not in observed_fields, (fid, "duplicate field assertion", rec, x["path"])
            observed_fields.add(signature[:-1])
            if not x.get("optional_record"):
                required_seen.add(signature)
            assert observations.setdefault(rec, (x["source"], typ)) == (x["source"], typ)
            if x["source"] == "协议":
                assert typ in ROOTS and (fid, rec) in wire, (fid, rec, typ)
                actual, instance = wire[fid, rec]
                assert actual == typ
                found = read_assertion(instance, x)
                assert normalized(found, x.get("compare_as")) == normalized(value, x.get("compare_as")), (
                    fid,
                    x,
                )
                wirekeys.add((fid, rec))
            else:
                assert typ in adapter_paths and x["path"] in adapter_paths[typ], (fid, x)
                assert isinstance(value, list if x["path"] in ("/执行", "/新封锁待派资源") else str)
        assert {contract_assertion(x) for x in REQUIRED_ASSERTIONS[fid]} <= required_seen, (
            fid,
            "mandatory assertions",
        )
        assert wirekeys == {key for key in wire if key[0] == fid}, fid
        graph = {k: set() for k in observations}
        for edge in t["before"]:
            graph[by_alias[edge["then"]]].add(by_alias[edge["first"]])
        TopologicalSorter(graph).prepare()
        # No constraints, including transitive ones, between the two independent deliveries.
        if fid in ("F01b", "F04a"):
            for a, b in [("irq", "applied"), ("applied", "irq")]:
                g = copy.deepcopy(graph)
                g[a].add(b)
                TopologicalSorter(g).prepare()


def verify_boundaries(v, md):
    phases = {x["id"] for x in v["phases"]}
    b = v["verification_boundaries"]
    needed = b["phases"]
    final = b["terminal_success"]
    cps = v["checkpoints"]
    assert needed and set(needed) <= phases and final in needed
    successors = {pred for n in v["dag"]["nodes"] for pred in n["depends_on"] + n.get("depends_on_one_of", [])}
    assert final not in successors, (v["scenario_id"], final)
    assert len(cps) == len(needed) == len(set(needed)) and {c["phase"] for c in cps} == set(needed)
    section = md.split("## 验证检查点\n", 1)[1].split("\n## ", 1)[0]
    assert "声明边界：" + "、".join(needed) + "。终局成功边界：" + final + "。" in section
    rows = [[x.strip() for x in l.strip("|").split("|")] for l in section.splitlines() if l.startswith("|")][2:]
    assert sorted(rows) == sorted(
        [[c[k] for k in ["phase", "SUCCESS", "FAILED", "UNKNOWN", "recovery"]] for c in cps]
    )
    assert all(len({c[k] for k in ["SUCCESS", "FAILED", "UNKNOWN"]}) == 3 for c in cps)


catalog = yaml.safe_load(pinned("therblig-vla", pins["provider"], "therbligs/catalog.v0.yaml"))
tmpl = {s for r in catalog["rows"] for s in r["realization"]["capability_templates"]}
assert catalog["catalog_revision"] == pins["catalog"] and catalog["body_profile"] == pins["body_profile"]
edir = "policy-harness/contracts/v1/examples/"
catalogue = "therblig-vla/therbligs/catalog.v0.yaml"
published = {
    json.loads(f.read_text())["capability_id"].split(".")[-1]: str(f)
    for f in Path(edir).glob("capability.*.json")
}
mrmap = [
    "baseline/fall@1（其他危险依部署登记的基线硬规则）",
    "generic/target_identity@1",
    "generic/motion_envelope@1",
    "generic/posture_balance@1",
    "generic/contact_force_envelope@1",
    "generic/people_workspace@1",
    "generic/progress_duration@1",
    "持续语音观测、认证纠正与基线停止词",
]
walks = ["w1-单臂拾放红杯", "w2-错物与用户纠正", "w3-两臂并行打开抽屉并放入物品", "w5-行走和上肢抓取"]
S = schema()
V.check_schema(S)
reg = Registry().with_resource(S["$id"], Resource.from_contents(S))


def branch(name, v):
    return V({"$ref": S["$id"] + "#/$defs/" + name}, registry=reg).is_valid(v)


def check(ok, msg):
    if not ok:
        raise AssertionError(msg)


def names(a, k):
    lst = [x[k] for x in a]
    assert len(lst) == len(set(lst)), lst
    return set(lst)


def rows(md):
    return [[x.strip() for x in l.strip("|").split("|")] for l in md.splitlines() if l.startswith("|")]


def slug(h):
    return re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")


def target(p, dest):
    u = urlsplit(dest)
    if u.scheme or u.netloc:
        return None
    q = p.parent / unquote(u.path) if u.path else p
    assert not Path(u.path).is_absolute() and q.is_file(), (p, dest)
    if u.fragment and q.suffix == ".md":
        assert unquote(u.fragment).lower() in {
            slug(h) for h in re.findall(r"^#{1,6}\s+(.+?)\s*$", q.read_text(), re.M)
        }, (p, dest)
    return q


def docsection(p, id):
    return (
        p.read_text().split("## " + id + " ", 1)[1].split("\n## ", 1)[0]
        if id.startswith("B")
        else p.read_text()
    )


def ensure_json(value):
    if isinstance(value, dict):
        assert all(isinstance(k, str) for k in value)
        for x in value.values():
            ensure_json(x)
    elif isinstance(value, list):
        for x in value:
            ensure_json(x)
    elif isinstance(value, float):
        assert math.isfinite(value)
    else:
        assert value is None or type(value) in (str, int, bool)


def rejects(call):
    try:
        call()
    except Exception:
        return
    raise AssertionError("negative test accepted")


for text in ["a: 1\na: 2", "x: {y: 1, y: 2}", "a: 2026-01-01", "v: .nan", "1: data"]:
    rejects(lambda: ensure_json(yaml.load(text, Loader=Loader)))
a = cases[0]
b = next(case for case in cases if case["tier"] == "B")
assert branch("A", a) and not branch("B", a) and branch("B", b) and not branch("A", b)
for bad in [
    a | {"tier": "B"},
    b | {"tier": "A"},
    a | {"test_vectors": []},
    b | {"faults": []},
    b | {"typo": 1},
]:
    assert not V(S).is_valid(bad)
print("PASS schema, tier exclusivity, required fields, strict YAML/JSON and negative samples")
wanted = [("A" if i < 9 else "B") + f"{i:02}" for i in range(1, 21)]
assert [x["scenario_id"] for x in cases] == wanted
allg = set()
allmr = set()
allobj = set()
schemas = Path("policy-harness/contracts/v1/schemas")
o_names = {"ModeRequest": "mode-request", "BodyProfile": "body-profile"}


def properties(name):
    k = o_names.get(name, name.lower())
    v = json.loads((schemas / (k + ".schema.json")).read_text())
    return v.get("$defs", {}).get(name, v)["properties"]


matrix = rows((P / "coverage.md").read_text())
gapdoc = (P / "gaps.md").read_text()
gt = {r[0]: r for r in rows(gapdoc) if len(r) == 9 and re.fullmatch(r"[EMC]\d\d", r[0])}


def verify_authorization(v):
    # In the absence of an explicitly scoped alternative all public phases support the claimed outcome.
    rank = {"当前本体未授权": 0, "条件授权": 1, "已授权（待实测）": 2}
    phases = {p["id"]: p for p in v["phases"]}

    def supported(ids):
        assert ids and set(ids) <= set(phases)
        return min(rank[phases[k]["authorization"]] if phases[k]["coverage"] == "已覆盖" else 0 for k in ids)

    a = v["authorization"]
    branches = a.get("scope_branches")
    if not branches:
        assert rank[a["status"]] <= supported(list(phases)), v["scenario_id"]
        return
    assert a["scope"] == "；".join(b["description"] for b in branches)
    assert set().union(*(set(b["phases"]) for b in branches)) == set(phases)
    nodes = {n["id"]: n for n in v["dag"]["nodes"]}
    for b in branches:
        ids = set(b["phases"])
        assert rank[b["status"]] <= supported(ids)
        assert v["verification_boundaries"]["terminal_success"] in ids
        for k in ids:
            n = nodes[k]
            assert set(n["depends_on"]) <= ids
            if "depends_on_one_of" in n:
                assert len(ids.intersection(n["depends_on_one_of"])) == 1
        if rank[b["status"]] == 0:
            assert "未授权" in b["description"]
    assert rank[a["status"]] <= max(rank[b["status"]] for b in branches)
    if v["scenario_id"] == "A02":
        assert a["scope"] == "认证纠正输入后的空手回撤与蓝杯站姿拾放；持物未知载荷恢复分支当前本体未授权"
        assert all(("restore" in b["phases"]) == (b["status"] == "当前本体未授权") for b in branches)


trace = {}
fault_count = 0
for v in cases:
    id = v["scenario_id"]
    tier = v["tier"]
    n = int(id[1:])
    validate(v)
    ensure_json(v)
    assert branch(tier, v) and not branch("A" if tier == "B" else "B", v)
    assert v["baseline_refs"] == pins
    verify_authorization(v)
    phases = names(v["phases"], "id")
    fs = names(v["faults"], "id")
    fault_count += len(fs)
    assert fs == {f for p in v["phases"] for f in p["fault_refs"]}
    for f in v["faults"]:
        assert any(p["id"] == f["at_boundary"] and f["id"] in p["fault_refs"] for p in v["phases"])
    used = {c for p in v["phases"] for c in p["codes"]}
    assert used <= set(codes)
    for g in v["gap_refs"]:
        assert g in gt and id in gt[g][5].split("、")
        allg.add(g)
    for m in v["monitor_needs"]:
        allmr.add(m["mr"])
        assert m["d9"] == mrmap[int(m["mr"][3:]) - 1]
    for prot in v["protocol_checks"]:
        allobj.add(prot["object"])
        assert set(prot["fields"]) <= properties(prot["object"]).keys(), (id, prot)
    pd = next((P / "tier-a").glob(id + "-*.md")) if tier == "A" else P / "tier-b.md"
    md = docsection(pd, id)
    rr = rows(md)
    index_row = next(r for r in rows((P / "README.md").read_text()) if r[0] == id)
    assert index_row[-1] == v["authorization"]["status"]
    assert "**" + v["authorization"]["status"] + "**（" + v["authorization"]["scope"] + "）" in md
    assert id in pd.read_text() and v["authorization"]["status"] in md and all(fid in md for fid in fs)
    mrows = [r[1:] for r in matrix if r[0] == id]
    cc = [
        ok
        if any(p["coverage"] == ok and c in p["codes"] for p in v["phases"])
        else blocked
        if c in used
        else na
        for c in codes
    ]
    legend = dict(zip(statuses, ["实", "阻", "—"]))
    expect = [
        cc,
        [v["coverage"]["components"][k] for k in components],
        [v["coverage"]["perception"][k] for k in percepts],
    ]
    assert mrows == [[legend[x] for x in xs] for xs in expect], id
    assert v["ambiguity"] in (P / "classification.md").read_text()
    if tier == "B":
        assert len([r for r in rr if len(r) == 7]) == len(v["phases"]) + 2
        for p in v["phases"]:
            row = next(r for r in rr if r[0] == p["goal"])
            assert (
                row[1] == "/".join(p["codes"]) + " · " + p["capability"]
                and row[2:5] == [p["s0_modes"], p["verification"], p["monitor_need"]]
                and row[6] == p["authorization"]
            )
            assert set(re.findall(r"F\d+[ab]?", row[5])) == set(p["fault_refs"])
            # Any public template identifier named in a B row must resolve to the pinned catalog.
            for t in re.findall(r"\b[a-z]+_[a-z_]+\b", p["capability"]):
                assert t in tmpl, (id, t)
        continue
    assert len(v["test_vectors"]) == len(fs) and {t["when"] for t in v["test_vectors"]} == fs
    assert {p["phase"] for p in v["checkpoints"]} <= phases and v["success_definition"] in md
    verify_boundaries(v, md)
    verify_vectors(v)
    assert (
        phases == names(v["simo"], "phase") == names(v["dag"]["nodes"], "id") == names(v["occupancy"], "phase")
    )
    nodes = {x["id"]: x for x in v["dag"]["nodes"]}
    graph = {k: x["depends_on"] + x.get("depends_on_one_of", []) for k, x in nodes.items()}
    assert set(TopologicalSorter(graph).static_order()) == phases
    for x in nodes.values():
        assert set(x["depends_on"]) <= phases
        if x["parent"] != "无":
            assert nodes[x["parent"]]["composition"] in ("EXPANDABLE", "PROVIDER_COMPOSITE")
    if "revision_cut" in v["dag"]:
        cut = v["dag"]["revision_cut"]
        assert {cut["previous"], cut["current"]} == {x["graph_revision"] for x in nodes.values()}
        for k, deps in graph.items():
            assert all(nodes[k]["graph_revision"] == nodes[y]["graph_revision"] for y in deps)
        assert not nodes["new"]["depends_on"] and set(nodes["new"]["depends_on_one_of"]) == {
            "retreat",
            "restore",
        }
        assert "restore_release" not in phases and "restore_release" not in nodes
        assert "Result" in nodes["new"]["gate"] and "逐资源处置" in nodes["new"]["gate"]
        replay = next(x for x in v["simo"] if x["phase"] == "restore")["replay_segments"]
        assert [seg["id"] for seg in replay] == ["restore_release"] and replay[0]["lanes"]["RH"][
            "access"
        ] == "TAKEOVER"
    if n <= 4:
        target(Path("entry"), v["extends_walkthrough"])
        assert "#" + walks[n - 1] in md
    for f in v["evidence_refs"]:
        assert Path(f).is_file()
    for k in v["capabilities"]:
        ref = k["reference"]
        name = k["name"]
        if k["status"] != "需新建":
            assert Path(ref).is_file()
        if k["status"] == "已有卡":
            assert published[name] == ref
        if k["status"] == "目录模板":
            assert name in tmpl
    assert names(v["capabilities"], "name") == {p["capability"] for p in v["phases"]}
    for ph, slot in zip(v["phases"], v["simo"], strict=True):
        assert ph["id"] == slot["phase"]
        assert set(slot["lanes"]) == set(tracks)
        form = next(r for r in rr if len(r) == 4 and r[0] == ph["id"] and r[1] == "、".join(ph["codes"]))
        assert form
        for t, x in slot["lanes"].items():
            if x["owner"] != "S1" or x["access"] not in ("DRIVE", "TAKEOVER"):
                assert x["action_mask"] == "屏蔽"
    for f in v["faults"]:
        row = next(r for r in rr if r[0].startswith(f["id"] + " · "))
        assert row[1:] == ["；".join(f[k]) for k in ("expected_records", "ordering", "forbidden_outcomes")]
    for t in v["test_vectors"]:
        aliases = names(t["assertions"], "alias")
        for edge in t["before"]:
            assert edge["first"] != edge["then"] and {edge["first"], edge["then"]} <= aliases
        assert all(x["path"].startswith("/") for x in t["assertions"])
        for x in t["assertions"]:
            typ = x["record_type"]
            if typ in ("Execution", "Event", "Verification"):
                assert x.get("select", {}).get("array_path", x["path"]).split("/")[1] in properties(typ)
    for cp in v["checkpoints"]:
        assert len(set(cp[k] for k in ("SUCCESS", "FAILED", "UNKNOWN"))) == 3 and all(
            cp[k] in md for k in ("SUCCESS", "FAILED", "UNKNOWN")
        )
print(
    "PASS 20 pinned cases; eight complete A cases, twelve B tables;",
    fault_count,
    "faults; DAG, masks, typed oracle, capabilities and eight protocol object joins",
)
assert allg == set(gt) and len(allmr) == 8 and len(allobj) == 8
assert Counter(r[4] for r in gt.values()) == {"可表达": 7, "需小修": 9, "架构变更": 1}
for g, row in gt.items():
    assert row[3] in ("阻塞", "降级", "表述") and row[5].split("、") == [
        v["scenario_id"] for v in cases if g in v["gap_refs"]
    ]
    if g.startswith("M"):
        assert any(len(r) == 2 and r[0] == g for r in rows(gapdoc))
    if g.startswith("C"):
        assert row[-1] == ("延后（v2+）" if g == "C02" else "已裁决")
allowedrepos = {"总仓", "therblig-vla", "policy-harness"}
for g, row in gt.items():
    assert set(row[2].split("、")) <= allowedrepos and row[2]
    if not g.startswith("M"):
        continue
    loc = next(r[1] for r in rows(gapdoc) if len(r) == 2 and r[0] == g)
    links = list(re.finditer(r"\[[^\]]+\]\(([^)]+)\)", loc))
    assert links
    for j, m in enumerate(links):
        dest = target(P / "gaps.md", m.group(1))
        tail = loc[m.end() : links[j + 1].start() if j + 1 < len(links) else None]
        if dest.suffix == ".yaml":
            vals = load(dest)
            anchors = re.findall(r"(checkpoints|phases|faults)\[([^\]]+)\]", tail)
            assert anchors
            for field, ids in anchors:
                assert set(ids.split("/")) <= {
                    i["phase" if field == "checkpoints" else "id"] for i in vals[field]
                }
        else:
            assert g in dest.read_text() and m.group(1).count("#") == 1
source = pinned(".", pins["root"], "docs/design/s0-and-monitor.md")
for i in range(1, 9):
    mr = f"MR-{i:02}"
    base = next(r for r in rows(source) if r[0] == mr)
    ledger = next(r for r in rows(gapdoc) if r[0] == mr)
    terms = re.findall(r"generic/[a-z_]+@\d+", ledger[-1])
    if i == 1:
        assert (
            "baseline/fall@1" in ledger[-1]
            and json.loads(
                pinned("policy-harness", pins["harness"], "contracts/v1/examples/event.baseline-fall-idle.json")
            )["detection"]["rule_ref"]
            == "baseline/fall@1"
        )
    elif i == 8:
        assert all(t in base[-1] + base[1] and t in ledger[-1] for t in ["停止词", "纠正", "语音"])
    else:
        assert terms and all(t in base[-1] for t in terms)
        defs = json.loads(
            pinned(
                "policy-harness", pins["harness"], "contracts/v1/schemas/monitoring-clause-kinds.schema.json"
            )
        )["$defs"]
        assert all(t.split("/")[1].split("@")[0] in defs for t in terms)
assert [r[2] for r in rows(gapdoc) if re.fullmatch(r"D9-F0[1-5]", r[0])] == ["可表达（降级）"] * 5
# Independent destructive mutations on in-memory copies.
av = cases[0]
amd = next((P / "tier-a").glob("A01-*.md")).read_text()
mut = copy.deepcopy(av)
mut["checkpoints"].pop()
rejects(lambda: verify_boundaries(mut, amd))
rejects(
    lambda: verify_boundaries(
        av, amd.replace("| withdraw | 观察到红杯在架且回撤后稳定", "| bogus | 观察到红杯在架且回撤后稳定")
    )
)


def witness_rejected(edit):
    v = copy.deepcopy(av)
    edit(v["test_vectors"][0])
    rejects(lambda: verify_vectors(v))


witness_rejected(lambda t: t["assertions"][1].update(path="/state/nonexistent"))
witness_rejected(lambda t: t["assertions"][0].update(equals="IMPOSSIBLE"))
witness_rejected(lambda t: t["before"].append({"first": "execution_read", "then": "lookup_read"}))
for k in ["expected_records", "ordering", "forbidden_outcomes"]:
    witness_rejected(lambda t: t.update({k: ["不相关"]}))
mut = copy.deepcopy(av)
mut["phases"][0]["authorization"] = "任意放行"
assert not V(S).is_valid(mut)


def bad_retry(edit):
    v = copy.deepcopy(av)
    t = next(t for t in v["test_vectors"] if t["when"] == "F01b")
    edit(t)
    rejects(lambda: verify_vectors(v))


bad_retry(lambda t: next(x for x in t["assertions"] if x["path"] == "/同条件新调用").update(equals="已派发"))
bad_retry(
    lambda t: t["assertions"].remove(next(x for x in t["assertions"] if x["path"] == "/interrupt/disposition"))
)
bad_retry(lambda t: [x.update(optional_record=True) for x in t["assertions"]])
# Both ordering changes must yield the same observation, without weakening equality for ordered arrays.
permuted = copy.deepcopy(WIRE)
permuted["F02b", "fault"][1]["result"]["resource_dispositions"].reverse()
# The RH row is in the middle of three rows: rotate as well to actually move RH.
disps = permuted["F02b", "fault"][1]["result"]["resource_dispositions"]
disps.append(disps.pop(0))
assert [r["resource_id"] for r in disps].index("RH") != [
    r["resource_id"] for r in WIRE["F02b", "fault"][1]["result"]["resource_dispositions"]
].index("RH")
permuted["F04a", "applied"][1]["scope"]["resource_ids"].reverse()
verify_vectors(cases[1], permuted)
verify_vectors(cases[3], permuted)
bad = copy.deepcopy(permuted)
bad["F04a", "applied"][1]["scope"]["resource_ids"] = ["RA"]
rejects(lambda: verify_vectors(cases[3], bad))
bad = copy.deepcopy(permuted)
next(r for r in bad["F02b", "fault"][1]["result"]["resource_dispositions"] if r["resource_id"] == "RH")[
    "disposition"
] = "RELEASED"
rejects(lambda: verify_vectors(cases[1], bad))
for id in ["B15", "B16", "B18"]:
    v = copy.deepcopy(next(v for v in cases if v["scenario_id"] == id))
    v["authorization"]["status"] = "条件授权"
    rejects(lambda: verify_authorization(v))
v = copy.deepcopy(cases[1])
v["authorization"]["scope_branches"][1]["status"] = "条件授权"
rejects(lambda: verify_authorization(v))
v = copy.deepcopy(cases[1])
v["authorization"]["scope"] = "认证纠正及持物恢复"
rejects(lambda: verify_authorization(v))
print(
    "PASS per-fault mandatory outcomes, optional allow-list, retry mutations, resource reorderings, public exclusive join and authorization audit"
)
print(
    "PASS declared terminal boundaries and bidirectional Markdown equality, full protocol witnesses including InvocationLookup, record-level acyclic order, ledger locations and negative mutations"
)
print(
    "PASS all three 20-row matrices, classifications, gap severities/categories/owners, minor locations and eight D9 mappings"
)


def allmd():
    for d in [".", "policy-harness", "therblig-vla"]:
        names = subprocess.check_output(
            ["git", "-C", d, "ls-files", "-co", "--exclude-standard"], text=True
        ).splitlines()
        yield from [Path(d) / n for n in names if n.endswith(".md")]


lcount = 0
for f in allmd():
    for link in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", f.read_text()):
        if target(f, link):
            lcount += 1
badnumbers = re.compile(r"\b\d+(?:\.\d+)?\s*(?:Hz|kHz|ms|N\b|N·m|秒|毫秒|牛顿|赫兹)")
assert not any(badnumbers.search(p.read_text()) for p in P.rglob("*") if p.is_file())
assert not re.search(
    r"therblig|transport.?(loaded|empty)|pre.?position|disassembl|unavoidable|avoidable|fatigue|Inspire|RH56|Correll|Unitree|Qwen|OpenVLA",
    Path("policy-harness/docs/harness-design.md").read_text(),
    re.I,
)
print("PASS", lcount, "relative links with anchors")
