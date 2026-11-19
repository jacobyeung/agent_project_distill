#!/bin/bash
# Stage-2 dry run, one process at a time (each under the 40 GiB / 16-core wrapper).
set -u
W=/scratch/jjyeung/orch_n30/sb_f64
cd "$W"
C=out/kit/configs
E=out/evidence
L=work/logs
run() {
  local name=$1; shift
  /usr/bin/time -v work/scripts/run_cpu.sh work/scripts/f64_dryrun.py "$@" --out "$E/$name.json" > "$L/$name.log" 2>&1
  echo "$name rc=$?" >> "$L/stage2.done"
}
for step in "$@"; do
  case $step in
    fwd_f64_a43) run fwd_f64_a43 forward --config $C/r1_config_f64.json --clips a43 ;;
    fwd_n32_a43) run fwd_n32_a43 forward --config $C/r1_config_n32_pinned.json --clips a43 ;;
    fwd_f64_b169) run fwd_f64_b169 forward --config $C/r1_config_f64.json --clips b169 --limit 1 ;;
    fwd_n32_b169) run fwd_n32_b169 forward --config $C/r1_config_n32_pinned.json --clips b169 --limit 1 ;;
    mem_f64_4) run mem_f64_4 trainmem --config $C/r1_config_f64.json --clips a43 --layers 4 ;;
    mem_n32_4) run mem_n32_4 trainmem --config $C/r1_config_n32_pinned.json --clips a43 --layers 4 ;;
    mem_f64_8) run mem_f64_8 trainmem --config $C/r1_config_f64.json --clips a43 --layers 8 ;;
    mem_n32_8) run mem_n32_8 trainmem --config $C/r1_config_n32_pinned.json --clips a43 --layers 8 ;;
    mem_f64_b169_8) run mem_f64_b169_8 trainmem --config $C/r1_config_f64.json --clips b169 --layers 8 --streams pose,routing ;;
  esac
done
echo ALL_DONE >> "$L/stage2.done"
