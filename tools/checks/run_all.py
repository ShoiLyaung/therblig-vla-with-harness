"""From the umbrella root, run the contract suite and cross-repository checks."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
CHECKS = Path(__file__).resolve().parent


def main():
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "policy-harness/tests/contract"], cwd=ROOT, check=True
    )
    for suite in ("catalog", "force_catalog", "force_evidence", "design", "scenarios"):
        subprocess.run([sys.executable, "-I", CHECKS / (suite + ".py"), ROOT], cwd=ROOT, check=True)
        print(f"PASS {suite}", flush=True)
    for repo in (".", "policy-harness", "therblig-vla"):
        for args in ([], ["--cached"]):
            subprocess.run(["git", "-C", ROOT / repo, "diff", "--check", *args], check=True)
    print("PASS git diff --check (three repositories, staged and unstaged)")


if __name__ == "__main__":
    main()
