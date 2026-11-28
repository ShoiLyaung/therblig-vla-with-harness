import json
import os
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
code = (root / "docs/design/s0-and-monitor.md").read_text()
walk = (root / "docs/design/walkthroughs.md").read_text()
assert all(code.count("MR-%02d" % i) == 1 for i in range(1, 9))
for i, ct in [(1, 7), (2, 5), (3, 7), (5, 3)]:
    table = walk.split("### W%d " % i)[1].split("\n\n")[1]
    assert table.count("\n|") == ct + 1 and all(len(l.split("|")) == 9 for l in table.splitlines())
for f in [
    "docs/design/README.md",
    "policy-harness/docs/protocol-v1.md",
    "policy-harness/docs/harness-design.md",
    "docs/design/s0-and-monitor.md",
    "docs/design/walkthroughs.md",
    "therblig-vla/docs/derivations.md",
]:
    assert not re.search("只读订阅|订阅活动调用|活动调用订阅|活动调用投影", (root / f).read_text())

obsolete_brief = re.compile(rb"Brief[R]eceipt|brief[-]receipt|receipt[_]policy|clause[_]results")


def check_brief_terms(path, data):
    if b"\0" not in data and obsolete_brief.search(data):
        raise AssertionError(f"Obsolete brief design in {path}")


try:
    check_brief_terms("probe.py", b"class Brief" + b"Receipt: pass")
except AssertionError:
    pass
else:
    raise AssertionError("Obsolete Python class passed the brief design check")

for repo in (root, root / "therblig-vla", root / "policy-harness"):
    files = subprocess.check_output(
        ["git", "-C", repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    )
    for name in files.split(b"\0"):
        if not name:
            continue
        path = repo / os.fsdecode(name)
        if path.is_symlink():
            check_brief_terms(path, os.fsencode(os.readlink(path)))
        elif path.is_file():
            check_brief_terms(path, path.read_bytes())

c = root / "policy-harness/contracts/v1/examples"
lost = json.loads((c / "event.required-clause-coverage-lost.json").read_text())
brief = json.loads((c / "monitoring-brief.locomote.json").read_text())
wc = next(c for c in brief["clauses"] if c["clause_id"] == "posture_balance")
assert all(
    x in walk
    for x in [*lost["evidence_refs"], *wc["evidence_selectors"], wc["arguments"]["balance_policy_ref"]]
)
assert "simulation_only.walk.corridor@1" in walk
root_readme = (root / "README.md").read_text()
assert (
    "阶段简报／周期刷新" in root_readme
    and "S2 → Monitor 的阶段简报" in root_readme
    and "Monitor → S0" in root_readme
)
