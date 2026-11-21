#!/bin/bash
# n_ops10 fixture tests for nauto_new.py: own-line rule (ORCH NOTE 0659Z) and host-key handling (ORCH ANSWER 0658Z items 5-6)
PY=/scratch/jjyeung/envs/p1cpu/bin/python; N=${1:-/scratch/jjyeung/orch_n30/n_ops10/work/nauto_new.py}
R=/scratch/jjyeung/orch_n30/n_ops10/work/tn_$(date -u +%H%M%S); mkdir -p $R; fails=0
RAW=/scratch/jjyeung/orch_n30/n_ops1/work/mon/last.raw
OLD='06:57:04Z job=173964 {"newest_out":"173236.out","proj_free_G":23,"sacct":"FAILED","state":"FAILED","frames":null,"stage":"submitted","gcs_done":[],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_FAILED'
OWN='07:10:04Z job=174085 {"newest_out":"173236.out","proj_free_G":23,"sacct":"FAILED","state":"FAILED","frames":null,"stage":"submitted","gcs_done":[],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_FAILED'
PEND='07:10:04Z job=174085 {"newest_out":"173236.out","proj_free_G":23,"sacct":"PENDING","state":"PENDING","held_min":1,"frames":null,"stage":"submitted","gcs_done":[],"ck":[]} WARN held 1 min FLAG PROJECT_DISK<150G'
WARN1='2026-11-21T07:10:00Z @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
WARN2='2026-11-21T07:10:00Z @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @'
ACCL='2026-11-21T07:10:00Z SHA256:lXwQfg9riWzIueT7rJbgpMFV4YEZuqAYP9ceieGEFDA.'
OTHL='2026-11-21T07:10:00Z SHA256:AAAAbbbbCCCCddddEEEEffffGGGGhhhhIIIIjjjjKKK.'
run() { # case line hk-lines...
  c=$1; L=$2; shift 2; D=$R/$c; mkdir -p $D/mon $D/a $D/ev; echo 174085 > $D/mon/job; echo 60 > $D/mon/sleep
  cp $RAW $D/mon/last.raw; echo "$L" > $D/mon/last.line; : > $D/mon/hk.log; for h in "$@"; do echo "$h" >> $D/mon/hk.log; done
  echo '{"last_job": "174085", "jobs": {"174085": {"t": "x"}}}' > $D/a/state.json
  NA_M=$D/mon NA_A=$D/a NA_EV=$D/ev NA_HKA=$D/HOSTKEY_ALERT NA_LEDGER=$D/ledger NA_NOTMUX=1 timeout 120 $PY $N > $D/out.txt 2>&1; echo "rc=$?" >> $D/out.txt; }
chk() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails+1)); fi; }
run A "$OLD"; D=$R/A
chk "A old job line -> no flag, no blocker" "! ls $D/ev | grep -q BLOCKER && ! grep -q STATE_FAILED $D/ev/N_WATCH_ALERTS.txt 2>/dev/null && grep -q 'state None' $D/ev/N_WATCH_STATUS.md"
run B "$OWN"; D=$R/B
chk "B own FAILED line -> STATE_FAILED blocker" "ls $D/ev | grep -q 'BLOCKER_nauto_STATE_FAILED_job_174085'"
run C "$PEND" "$WARN1" "$WARN2" "$ACCL"; D=$R/C
chk "C warning with accepted key -> HOSTKEY blocker, no HOSTKEY_ALERT, no mon/stop" "ls $D/ev | grep -q BLOCKER_nauto_HOSTKEY && [ ! -e $D/HOSTKEY_ALERT ] && [ ! -e $D/mon/stop ]"
run D "$PEND" "$WARN1" "$WARN2" "$OTHL"; D=$R/D
chk "D warning with other key -> HOSTKEY blocker + HOSTKEY_ALERT, no mon/stop" "ls $D/ev | grep -q BLOCKER_nauto_HOSTKEY && [ -e $D/HOSTKEY_ALERT ] && [ ! -e $D/mon/stop ]"
run E "$PEND" "$ACCL"; D=$R/E
chk "E accepted fingerprint line only -> alert, no blocker, no gate" "! ls $D/ev | grep -q BLOCKER && [ ! -e $D/HOSTKEY_ALERT ] && grep -q HOSTKEY_LINE $D/ev/N_WATCH_ALERTS.txt"
run F "$PEND" "$WARN2"; D=$R/F
chk "F warning without fingerprint -> blocker + gate" "ls $D/ev | grep -q BLOCKER_nauto_HOSTKEY && [ -e $D/HOSTKEY_ALERT ] && [ ! -e $D/mon/stop ]"
run G "$PEND"; D=$R/G
chk "G pending own line -> no blocker, state PENDING" "! ls $D/ev | grep -q BLOCKER && grep -q 'state PENDING' $D/ev/N_WATCH_STATUS.md"
grep -h 'rc=' $R/*/out.txt | sort | uniq -c
echo "fails=$fails dir=$R"
