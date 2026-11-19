#!/bin/bash
set -u -o pipefail
S=/scratch/jjyeung/distill_sync; T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
exec 8>"$S/.sync.lock"; flock -n 8 || { echo "$(date -u +%FT%TZ) lock held"; exit 3; }
echo "$(date -u +%FT%TZ) START head=$(git -C $S/repo rev-parse HEAD)"
nice -n 10 git -C $S/repo -c pack.threads=8 bundle create - lane-code 8>&- | bash $T/tssh.sh trinity-2-28.ib 'mkdir -p /scratch/jjyeung/distill_sync_init && cat > /scratch/jjyeung/distill_sync_init/lane-code.bundle && ls -l /scratch/jjyeung/distill_sync_init/lane-code.bundle && sha256sum /scratch/jjyeung/distill_sync_init/lane-code.bundle' 8>&-
echo "$(date -u +%FT%TZ) END rc=${PIPESTATUS[*]}"
