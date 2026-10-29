#!/usr/bin/env bash
# rung-1 native preparation of FXG_S17 on trainer f5cad828 (records from FXP_S17's encode shards, as A1GX from A1).
set -euo pipefail
source /scratch/jjyeung/prestage_gx_20261028/harness/fx_env_gx.sh
F=$FX/runs/aws128p_20261025/frozen/FXG_S17
cd "$TRAINER"
prep="python -B $ANYHOST_JOBS/prep_rung1.py"
$prep protocol "$F"
$prep merge "$F" 16 "$FX/runs/aws128p_20261025/frozen/FXP_S17/shards"
$prep seal "$F"
$prep request "$F"
$prep admit "$F"
