#!/bin/bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_ops10/work/nauto_new2.py
R=/scratch/jjyeung/orch_n30/n_ops10/work/tn2_$(date -u +%H%M%S); mkdir -p $R; fails=0; RAW=/scratch/jjyeung/orch_n30/n_ops1/work/mon/last.raw
mk() { echo "09:20:00Z job=174101 {\"proj_free_G\":$1,\"sacct\":\"RUNNING\",\"state\":\"RUNNING\",\"stage\":\"admission\"$2}  FLAG PROJECT_DISK<150G"; }
run() { c=$1; D=$R/$c; mkdir -p $D/mon $D/a $D/ev; echo 174101 > $D/mon/job; echo 60 > $D/mon/sleep; cp $RAW $D/mon/last.raw; echo "$2" > $D/mon/last.line; : > $D/mon/hk.log
  echo '{"last_job": "174101", "jobs": {"174101": {"t": "x"}}}' > $D/a/state.json
  NA_M=$D/mon NA_A=$D/a NA_EV=$D/ev NA_HKA=$D/HKA NA_LEDGER=$D/ledger NA_NOTMUX=1 timeout 120 $PY $N > $D/out.txt 2>&1; echo "rc=$?" >> $D/out.txt; ls $D/ev | grep BLOCKER | sed 's/^[0-9TZ]*_BLOCKER_nauto_//' | tr '\n' ' '; }
chk() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: got [$2] want [$3]"; fails=$((fails+1)); fi; }
chk "21 GiB" "$(run a "$(mk 21)")" "PROJECT_FS_22G_job_174101.md "
chk "9 GiB before gate" "$(run b "$(mk 9)")" "PROJECT_FS_10G_job_174101.md PROJECT_FS_22G_job_174101.md "
chk "7 GiB before gate" "$(run c "$(mk 7)")" "PROJECT_FS_10G_job_174101.md PROJECT_FS_22G_job_174101.md PROJECT_FS_8G_BEFORE_GATE_job_174101.md " 
chk "7 GiB training" "$(run d "$(mk 7 ',"step":12')")" "PROJECT_FS_10G_job_174101.md PROJECT_FS_22G_job_174101.md "
chk "4 GiB before gate" "$(run e "$(mk 4)")" "PROJECT_FS_10G_job_174101.md PROJECT_FS_22G_job_174101.md PROJECT_FS_5G_job_174101.md PROJECT_FS_8G_BEFORE_GATE_job_174101.md "
grep -h rc= $R/*/out.txt | sort | uniq -c; echo "fails=$fails"
