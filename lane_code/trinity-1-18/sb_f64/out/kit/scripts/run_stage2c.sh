#!/bin/bash
# Reruns mem_f64_4 on p1cpu, after the second chain finishes (one dry-run process at a time).
set -u
W=/scratch/jjyeung/orch_n30/sb_f64
cd "$W"
C=out/kit/configs
E=out/evidence
L=work/logs
until grep -q ALL_DONE "$L/stage2b.done" 2>/dev/null; do sleep 30; done
/usr/bin/time -v work/scripts/run_cpu.sh work/scripts/f64_dryrun.py trainmem --config $C/r1_config_f64.json --clips a43 \
  --layers 4 --out "$E/mem_f64_4_local.json" > "$L/mem_f64_4_local.log" 2>&1
echo "mem_f64_4_local rc=$?" >> "$L/stage2c.done"
echo ALL_DONE >> "$L/stage2c.done"
