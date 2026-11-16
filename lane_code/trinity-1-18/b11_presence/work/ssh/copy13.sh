#!/bin/bash
set -o pipefail
L=/scratch/jjyeung/orch_n30/b11_presence
echo "$(date -u +%FT%TZ) copy start" >> $L/work/logs/copy13.log
tar chf - -C $L/work/stage13 . | bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh trinity-1-13.ib 'mkdir -p /dev/shm/jjyeung && tar xf - -C /dev/shm/jjyeung && cd /dev/shm/jjyeung && sha256sum -c --quiet b11_presence/STAGE_MANIFEST.sha256 && echo VERIFY_OK && du -sh exports/m544 b11_presence' >> $L/work/logs/copy13.log 2>&1
echo "$(date -u +%FT%TZ) copy exit $?" >> $L/work/logs/copy13.log
