#!/bin/bash
# Codex dispatch with node-local receipts, for fan-outs. Same arguments as agent/scripts/codex_dispatch.sh:
#   codex_local.sh <review|implement|mech> <dir> <prompt-file> [--net] [--model X] [--effort Y] [--label NAME] [--skip-git-check] [--writable-root DIR ...]
# Receipts: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/<stamp>_<label>/final_message.md on the node it runs on.
# Spend log: .../codex_runs/CODEX_SPEND.log (local; add it when totalling Codex spend). RUST_LOG=warn keeps transcripts small.
set -u
SRC=/home/jjyeung/agent_project_distill/agent/scripts/codex_dispatch.sh
L=/scratch/jjyeung/orch_n30/codex_local
mkdir -p "$L/agent/scripts" "$L/agent/scratch/codex_runs" || exit 3
if [[ ! -f "$L/agent/scripts/codex_dispatch.sh" || "$SRC" -nt "$L/agent/scripts/codex_dispatch.sh" ]]; then
  cp -p "$SRC" "$L/agent/scripts/codex_dispatch.sh.tmp.$$" && mv -f "$L/agent/scripts/codex_dispatch.sh.tmp.$$" "$L/agent/scripts/codex_dispatch.sh" || exit 3
fi
export RUST_LOG=${RUST_LOG:-warn}
cd "$L" || exit 3
exec bash "$L/agent/scripts/codex_dispatch.sh" "$@"
