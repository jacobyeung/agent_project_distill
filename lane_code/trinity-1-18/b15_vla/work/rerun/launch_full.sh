set -u; R=/project/community/jjyeung/vla_libero/out/rerun_20261116
if [ -e $R/phase.log ]; then echo "ALREADY STARTED"; tail -5 $R/phase.log; exit 0; fi
mkdir -p $R; cat > $R/rerun_driver.sh <<'DRV'
#!/bin/bash
# Re-run the 11-11 LIBERO CPU proofs (ORCH ANSWER 20261116T1224Z: login node, one at a time, nice 19, OMP 4).
# Shadow V: every top-level entry of the kit dir is symlinked except out/, logs/ and work/run dirs, so all outputs land
# under out/rerun_20261116/ and no 11-11 evidence is overwritten. The sealed kit is used unchanged.
set -uo pipefail
RV=/project/community/jjyeung/vla_libero; R=$RV/out/rerun_20261116; VV=$R/V
mkdir -p $VV/out $VV/logs $VV/work
for e in bin cache cfg data dl envs kit mamba osmesa py src st libero_10_manifest.json libero_goal_manifest.json libero_object_manifest.json; do
  [ -e $VV/$e ] || ln -s $RV/$e $VV/$e; done
for e in data tiny_Qwen3.5; do [ -e $VV/work/$e ] || ln -s $RV/work/$e $VV/work/$e; done
export V=$VV OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $R/phase.log; }
ph "START host=$(hostname) kit=$(cat $RV/kit/KIT_SHA256) df=$(df -h $RV | tail -1 | tr -s ' ')"
( cd $RV/kit && sha256sum -c --quiet SHA256SUMS > $R/sha_check.txt 2>&1 ); ph "sha256sum -c rc=$? $(grep -c FAILED $R/sha_check.txt) failed lines"
STEPS=${STEPS:-"cpu_hook repeat cpu_rotate conformance cl_check parity"}
for s in $STEPS; do
  ph "begin $s"
  case $s in
    cpu_hook)    nice -n 19 bash $RV/kit/cpu_hook.sh > $R/cpu_hook.run.log 2>&1 ;;
    repeat)      nice -n 19 bash $RV/kit/repeat_check.sh > $R/repeat.run.log 2>&1 ;;
    cpu_rotate)  nice -n 19 bash $RV/kit/cpu_rotate.sh > $R/cpu_rotate.run.log 2>&1 ;;
    conformance) nice -n 19 bash $RV/kit/conformance.sh > $R/conformance.run.log 2>&1 ;;
    cl_check)    nice -n 19 bash $RV/kit/cl_check.sh > $R/cl_check.run.log 2>&1 ;;
    parity)      nice -n 19 bash $RV/kit/prep_checks.sh parity > $R/parity.run.log 2>&1 ;;
  esac
  ph "end $s rc=$? $(tail -c 300 $R/$s.run.log | tr '\n' ' ')"
done
ph "ALL_DONE"
DRV
cd $R && setsid nohup bash $R/rerun_driver.sh > $R/driver.out 2>&1 < /dev/null & disown
sleep 20; hostname; cat $R/phase.log; ls $R/V; uptime
