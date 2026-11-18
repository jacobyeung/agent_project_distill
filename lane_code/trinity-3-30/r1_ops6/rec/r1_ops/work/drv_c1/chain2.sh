#!/bin/bash
# r1_ops4: C4 Orchard chain m1,u1..scan1, sequential, stop on first unexpected output.
D=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1; cd "$D"
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
run() { timeout 300 bash "$OSSH" 'bash -s' < "$1" > "$2" 2>&1; local rc=$?; echo "$(date -u +%T) $1 rc=$rc $(tail -1 "$2" | cut -c1-160)" >> chain2.log; return $rc; }
need() { grep -q "$2" "$1" || { echo "$(date -u +%T) STOP: $1 lacks '$2'" >> chain2.log; exit 1; }; }
run m1.sh m1.out || exit 1; need m1.out PASS
sleep 61
sleep 61
run u1.sh u1.out || exit 1; need u1.out PASS
sleep 61
run q1.sh q1.out || exit 1; need q1.out PASS
sleep 61
run rv1.sh rv1.out || exit 1; need rv1.out PASS
sleep 61
run ev1.sh ev1.out || exit 1; need ev1.out STARTED
sleep 61
for i in $(seq 1 15); do sleep 60; run evp1.sh evp1.out; grep -q 'e0 rc=' evp1.out && break; done; need evp1.out 'e0 rc=0'
run dv1.sh dv1.out || exit 1; need dv1.out STARTED
sleep 61
for i in $(seq 1 15); do sleep 60; run dvp1.sh dvp1.out; grep -q 'd0 rc=' dvp1.out && break; done; need dvp1.out 'd0 rc=0'; need dvp1.out READY
run scan1.sh scan1_c3.out || exit 1; need scan1_c3.out MANIFEST
sleep 61
sha256sum scan1_c3.out >> chain2.log; grep "^MANIFEST" scan1_c3.out >> chain2.log
echo "$(date -u +%T) CHAIN2 DONE" >> chain2.log
