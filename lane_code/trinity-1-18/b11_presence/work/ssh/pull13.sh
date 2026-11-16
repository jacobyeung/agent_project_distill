#!/bin/bash
# Pull run outputs from 1-13 /dev/shm lane to 1-18 lane folder (into from13/, then compare sha lists).
set -o pipefail
L=/scratch/jjyeung/orch_n30/b11_presence
mkdir -p $L/from13
bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh trinity-1-13.ib 'cd /dev/shm/jjyeung/b11_presence/lane && find out/det out/journals out/direct work/logs -type f | sort | xargs -d "\n" sha256sum > work/PULL_MANIFEST.sha256 && tar cf - out/det out/journals out/direct work/logs work/PULL_MANIFEST.sha256' | tar xf - -C $L/from13 && (cd $L/from13 && sha256sum -c --quiet work/PULL_MANIFEST.sha256 && echo PULL_VERIFY_OK)
