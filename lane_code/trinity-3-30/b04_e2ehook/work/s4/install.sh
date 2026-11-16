cat > /dev/shm/jjyeung/b04/host2/b04_e2ehook/parity_kit/chain_113.sh <<'XEOF'
#!/bin/bash
# Card-3 chain on trinity-1-13: after own_depth_p0 ends, run the remaining partitions one by one.
# Before each launch: no HOLD file, no INBOX_TO_DISTILL_ORCH newer than 172517Z naming 1-13, two empty readings 5 min apart.
L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; LOG=$L/work/gpu_launch.log; CARD=3
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
while tmux has-session -t b04_gpu3 2>/dev/null; do sleep 60; done
for job in "own_depth 1" "own_depth 2" "scale_head 0" "scale_head 1" "scale_head 2"; do
  set -- $job; ARM=$1; PART=$2
  [ -s $L/parity_kit/gpu_results/${ARM}_p$PART/items.jsonl ] && [ "$(wc -l < $L/parity_kit/gpu_results/${ARM}_p$PART/items.jsonl)" -ge 212 ] && continue
  if [ -e $L/work/HOLD ]; then echo "$(date -u +%FT%TZ) CHAIN_HOLD file before ${ARM}_p$PART" >> $LOG; exit 0; fi
  newest=$(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1)
  if [ "$(basename $newest)" != INBOX_TO_DISTILL_ORCH_20261116T172517Z.md ] && grep -q "1-13" "$newest"; then
    echo "$(date -u +%FT%TZ) CHAIN_HOLD new main inbox $(basename $newest) names 1-13 before ${ARM}_p$PART" >> $LOG; exit 0; fi
  m1=$(nvidia-smi -i $CARD --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' '); n1=$(nvidia-smi -i $CARD --query-compute-apps=pid --format=csv,noheader | wc -l)
  echo "$(date -u +%FT%TZ) card$CARD first reading mem=$m1 procs=$n1 before ${ARM}_p$PART" >> $LOG
  sleep 330
  if [ -e $L/work/HOLD ]; then echo "$(date -u +%FT%TZ) CHAIN_HOLD file before ${ARM}_p$PART" >> $LOG; exit 0; fi
  if [ "$m1" -gt 10 ] || [ "$n1" -ne 0 ]; then echo "$(date -u +%FT%TZ) CHAIN_STOP card busy at first reading" >> $LOG; exit 0; fi
  bash $L/parity_kit/launch_part_113.sh $CARD $ARM $PART
  tail -1 $LOG | grep -q "_EXIT 0" || { echo "$(date -u +%FT%TZ) CHAIN_STOP ${ARM}_p$PART did not exit 0" >> $LOG; exit 0; }
done
echo "$(date -u +%FT%TZ) CHAIN_DONE" >> $LOG
XEOF
cd /dev/shm/jjyeung/b04/host2/b04_e2ehook && tmux new-session -d -s b04_chain "bash parity_kit/chain_113.sh" && tmux ls; wc -l parity_kit/gpu_results/own_depth_p0/items.jsonl; sha256sum parity_kit/chain_113.sh
grep -n "scale_head\|ARM" parity_kit/gpu_inner.sh | head
