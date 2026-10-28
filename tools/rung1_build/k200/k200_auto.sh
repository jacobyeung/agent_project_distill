#!/bin/bash
# Detached day automation (trinity-0-13): wait for code-aws inodes, create the K200 frozen dirs (closure f344aa6b installs
# from its pending action in the same poll), submit the CPU preps, then submit the world-64 X preps once the seed-17 X
# encode is admitted. One light login-node action per 10 min while waiting. Log: k200/auto.log. Stops at 17:00 PT.
R=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027
PY=/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
D=/scratch/jjyeung/rung1_push/k200
CL=f344aa6ba407a39f5716fb665757007f0b62dd8ace1d397d1697dd11642a3890
LOG=$D/auto.log
say() { echo "$(date -Is) $*" >> $LOG; }
tell() { say "TELL $*"; timeout 60 lanemsg tell all --from "rung1_build lane automation" "$*" >> $LOG 2>&1 || true; }
late() { [ "$(TZ=America/Los_Angeles date +%H%M)" -ge 1700 ]; }
action() {  # action TAG SCRIPT -> prints the action's output block
  local tag=$1 script=$2 f
  (cd $R/tools && $PY -B r1actions.py sh $tag $script >/dev/null)
  for t in 1 2 3 4; do (cd $R/tools && timeout 600 env R1_MIN_INTERVAL=55 $PY -B r1aws.py run >/dev/null 2>&1); ls $R/actions/sent | grep -q "_$tag.json" && break; sleep 70; done
  f=$(grep -l "_$tag BEGIN" $(ls -t $R/polls/poll_*.txt | head -4) 2>/dev/null | head -1)
  [ -n "$f" ] && sed -n "/=== ACTION a_.*_$tag BEGIN/,/END rc/p" "$f"
}
say "start"
i=0
while :; do
  late && { tell "K200 preps not submitted: code-aws inodes still not free at 17:00 PT; tomorrow's 200-step arms stay held."; exit 1; }
  i=$((i+1)); out=$(action $(printf 'kq%03d' $i) $D/quota_check.sh); line=$(echo "$out" | grep QUOTA_FILES | tail -1); say "$line"
  free=$(echo "$line" | sed -n 's/.*free=\([0-9-]*\).*/\1/p')
  [ -n "$free" ] && [ "$free" -ge 20000 ] && break
  sleep 530
done
p1=$($D/k200_phase1.sh 2>&1); say "phase1: $(echo "$p1" | tr '\n' '|')"
k=$(echo "$p1" | grep -cE "^K200 .*(from|present same)")
if ! echo "$p1" | grep -qE "CLOSURE_(INSTALLED|PRESENT)"; then
  ls $R/actions/pending | grep -q install_f344aa6b && { tell "K200 automation stopped: closure f344aa6b install still failing after inodes freed; see $LOG"; exit 1; }
fi
[ "$k" -eq 9 ] || { tell "K200 automation stopped: $k of 9 frozen dirs created; see $LOG"; exit 1; }
p2=$($D/k200_phase2.sh 2>&1); say "phase2: $(echo "$p2" | tr '\n' '|')"
tell "rung1_build: closure f344aa6b installed, 9 K200 frozen dirs made, 5 CPU preps submitted (27B X encode ~2.5 h; others merge from records). World-64 X preps follow the 9B X encode."
j=0
while :; do
  late && { tell "World-64 X preps not submitted: RG1_X_S17_K200 not admitted by 17:00 PT."; exit 1; }
  j=$((j+1)); out=$(action $(printf 'ka%03d' $j) $D/adm_check.sh)
  echo "$out" | grep -q "K200ADMITTED RG1_X_S17_K200" && break
  sleep 530
done
d=$(cd $R/tools && $PY -B r1actions.py spec $D/SPEC_K200_X9W64.json); n=$(cd $R/tools && $PY -B r1actions.py sbatch $CL $d 32 240G 4:00:00)
for t in 1 2 3; do (cd $R/tools && timeout 600 env R1_MIN_INTERVAL=55 $PY -B r1aws.py run >/dev/null 2>&1); [ -z "$(ls $R/actions/pending | grep '^f_')" ] && break; sleep 70; done
say "X9W64 submitted as $n: $(grep -h "SBATCH_REPLY $n\|NOT_SUBMITTED $n" $(ls -t $R/polls/poll_*.txt | head -3) | head -1)"
tell "rung1_build: world-64 X preps (s17, s18) submitted as $n after the 9B X encode was admitted."
say "done"
