#!/usr/bin/env bash
# Old-vs-new startup parity on a local CPU fixture.
# Usage: run_parity.sh RESULTS_DIR [FROZEN_NAME [TRAINER_DIR RUNTIME_RECORD]]   (defaults: FXP_S17 on trainer 299b0c52)
# PARITY_HOME (harness copy), PARITY_ENV (fixture environment), PARITY_CLOSURE_SRC (closure sources) and PARITY_VENV may
# be overridden, e.g. PARITY_ENV=fx_env_gx.sh EXPECT_GEOMETRY=1 for the geometry fixture FXG_S17 on trainer f5cad828.
set -euo pipefail
S=${PARITY_HOME:-/scratch/jjyeung/startup_prestage_20261028}
WT=${PARITY_CLOSURE_SRC:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/startup_cpu_prestage_20261028/work/wt/tools/rung1_build/aws_closure}
source "${PARITY_ENV:-$S/fx_env.sh}"
R="$1"; mkdir -p "$R"
export R1FX_FROZEN="${2:-FXP_S17}"
if [[ -n "${3:-}" ]]; then export TRAINER="$3" R1_TRAINER="$3" ANYHOST_NEUTRAL_RUNTIME="$4"; fi
stamp=$(date +%s)
export ANYHOST_JOBS="$S/closure_src_$stamp" PYTHONPATH="$S/closure_src_$stamp/site_alias"
export PATH="$ANYHOST_JOBS/provenance_bin:${PARITY_VENV:-$S/venv}/bin:/usr/bin:/bin"
mkdir -p "$ANYHOST_JOBS" && cp -r "$WT/." "$ANYHOST_JOBS/"
F=$FX/runs/aws128p_20261025/frozen/$R1FX_FROZEN
RUN=$FX/runs/r1fx_run
for d in "$RUN" "$FX/runs/aws128p_20261025/prestage" "$FX/attach"; do if [[ -e "$d" ]]; then mv "$d" "$FX/aside_$(basename "$d")_$stamp"; fi; done
cd "$TRAINER"
echo "== old"
python -B $S/parity.py rank0 old "$R" 2> "$R/rank0_old.err"
mv "$RUN/attempt-1" "$R/old_node0"
python -B $S/parity.py mirror old "$R" 2> "$R/mirror_old.err"
mv "$RUN/attempt-1" "$R/old_node1"
echo "== build (CPU pre-stage)"
start=$(date +%s.%N)
python -B "$ANYHOST_JOBS/prestage.py" build "$F" > "$R/build.log" 2>&1
echo "build seconds $(python3 -c "import time; print(round(time.time() - $start, 1))")"
cache="$(python -B "$ANYHOST_JOBS/prestage.py" key "$F")"
export R1_PRESTAGE_RECEIPT_SHA256="$(sha256sum < "$cache/RECEIPT.json" | cut -d' ' -f1)"
python -B "$ANYHOST_JOBS/prestage.py" build "$F" > "$R/build_again.log" 2>&1
echo "== attach node0 / node1"
python -B "$ANYHOST_JOBS/prestage.py" attach "$cache" "$FX/attach/node0" 1 > "$R/attach0.log" 2>&1
python -B "$ANYHOST_JOBS/prestage.py" attach "$cache" "$FX/attach/node1" 0 > "$R/attach1.log" 2>&1
echo "== new"
export R1_PRESTAGE_DIR="$cache"
R1_PRESTAGE_LOCAL="$FX/attach/node0" python -B $S/parity.py rank0 new "$R" 2> "$R/rank0_new.err"
mv "$RUN/attempt-1" "$R/new_node0"
R1_PRESTAGE_LOCAL="$FX/attach/node1" python -B $S/parity.py mirror new "$R" 2> "$R/mirror_new.err"
mv "$RUN/attempt-1" "$R/new_node1"
echo "== fallback (attach failed on both nodes: the trainer's own staging and mirror must run)"
mkdir -p "$FX/attach/failed"; echo '{"status": "failed", "error": "parity fallback test"}' > "$FX/attach/failed/STATE.json"
R1_PRESTAGE_LOCAL="$FX/attach/failed" python -B $S/parity.py rank0 fallback "$R" 2> "$R/rank0_fallback.err"
mv "$RUN/attempt-1" "$R/fallback_node0"
R1_PRESTAGE_LOCAL="$FX/attach/failed" python -B $S/parity.py mirror fallback "$R" 2> "$R/mirror_fallback.err"
mv "$RUN/attempt-1" "$R/fallback_node1"
echo "== no cache (hooks off: env unset) is the old path itself"
grep -h AWS_PRESTAGE "$R"/rank0_new.err "$R"/mirror_new.err "$R"/rank0_fallback.err "$R"/mirror_fallback.err | cut -c1-220 || true
python3 $S/compare.py "$R" new
python3 $S/compare.py "$R" fallback
