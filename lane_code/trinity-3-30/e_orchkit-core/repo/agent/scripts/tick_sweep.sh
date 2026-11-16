#!/usr/bin/env bash

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_root" || exit 1

printf '%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

manifest_rc=0
python - "agent/agentic_information_5.0/handoff_liveness.json" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    manifest = json.loads(path.read_text())
except OSError as exc:
    print(f"MANIFEST ERROR: unable to read {path}: {exc}")
    raise SystemExit(2)
except (UnicodeError, json.JSONDecodeError) as exc:
    print(f"MANIFEST ERROR: corrupt {path}: {exc}")
    raise SystemExit(0)

if not isinstance(manifest, dict) or not isinstance(manifest.get("active_runs"), list):
    print(f"MANIFEST ERROR: {path} must contain an active_runs list")
    raise SystemExit(0)

for index, entry in enumerate(manifest["active_runs"]):
    round_name = f"active_runs[{index}]"
    if isinstance(entry, dict) and isinstance(entry.get("round"), str):
        round_name = entry["round"]
    print(f"== {round_name} ==", flush=True)
    if not isinstance(entry, dict):
        print(f"MANIFEST ERROR: {round_name} is not an object")
        continue
    if "health_check" not in entry:
        print("NO health_check IN MANIFEST")
        continue
    health_check = entry["health_check"]
    if not isinstance(health_check, str) or not health_check or "\n" in health_check or "\r" in health_check:
        print(f"MANIFEST ERROR: invalid health_check for {round_name}")
        continue
    subprocess.run(["timeout", "20", "bash", "-c", health_check], check=False)
PY
manifest_rc=$?

while IFS= read -r run_dir; do
    message="agent/scratch/codex_runs/$run_dir/final_message.md"
    if [[ -f "$message" ]]; then
        last_line=$(tail -n 1 -- "$message")
        printf '%s :: %s\n' "$run_dir" "$last_line"
    fi
done < <(ls -t agent/scratch/codex_runs/ | head -8)

git log --oneline -3

if [[ $manifest_rc -eq 2 ]]; then
    exit 1
fi
exit 0
