import json
import re
import subprocess
from pathlib import Path

r = Path.cwd()
code = (r / "docs/design/s0-and-monitor.md").read_text()
walk = (r / "docs/design/walkthroughs.md").read_text()
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
    assert not re.search("只读订阅|订阅活动调用|活动调用订阅|活动调用投影", Path(f).read_text())
for d in [".", "therblig-vla", "policy-harness"]:
    files = subprocess.check_output(
        ["git", "-C", d, "ls-files", "--cached", "--others", "--exclude-standard"], text=True
    ).splitlines()
    for file in files:
        if Path(file).suffix not in {".md", ".json", ".yaml"}:
            continue
        assert not re.search(
            r"BriefReceipt|brief-receipt|receipt_policy|clause_results", (Path(d) / file).read_text()
        ), file

c = Path("policy-harness/contracts/v1/examples")
lost = json.loads((c / "event.required-clause-coverage-lost.json").read_text())
brief = json.loads((c / "monitoring-brief.locomote.json").read_text())
wc = next(c for c in brief["clauses"] if c["clause_id"] == "posture_balance")
assert all(
    x in walk
    for x in [*lost["evidence_refs"], *wc["evidence_selectors"], wc["arguments"]["balance_policy_ref"]]
)
assert "simulation_only.walk.corridor@1" in walk
root_readme = Path("README.md").read_text()
assert (
    "阶段简报／周期刷新" in root_readme
    and "S2 → Monitor 的阶段简报" in root_readme
    and "Monitor → S0" in root_readme
)
