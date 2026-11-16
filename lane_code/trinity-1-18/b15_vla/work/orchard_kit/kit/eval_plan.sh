#!/bin/bash
# Test L evaluation plan for one trained arm (design record 4.1, vla_schema_v1 section 10 eval):
#   decisive run (STEPS 10000): the 10k export on 500 paired episodes (10 LIBERO-Spatial tasks x init states 0-49, the
#     primary endpoint); the 1k, 2k and 5k exports on init states 0-19 (200 each); LIBERO-Plus camera tasks of
#     LIBERO-Spatial (pinned ids, kit/plus_camera_ids.json) on the 10k export; then both visually blind priors on the
#     same 500 episodes (CPU): random actions inside the subset's action range, and replay of a training demo of the task.
#   shake-down (STEPS 1000): the 1k export on 100 paired episodes (init states 0-9); success is recorded, not gated.
# Units run on the allocation's GPUs, one policy server each; every episode is journaled (resumable only by the
# orchestrator's decision: rerun the same command). One episode in 20 saves a video. usage: eval_plan.sh RUN_DIR OUT_DIR STEPS
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
RD=$1 OUT=$2 STEPS=${3:-10000}; mkdir -p $OUT
NG=$(nvidia-smi -L 2>/dev/null | wc -l); [ $NG -ge 1 ] || NG=1
NC=$(nproc); VW=${VW:-$(( (NC - 4) / NG ))}
ck() { echo $RD/checkpoints/steps_$1_pytorch_model.pt; }
if [ $STEPS -ge 10000 ]; then
  units=("$(ck 10000)|$OUT/step_10000|libero_spatial:50" "$(ck 1000)|$OUT/step_1000|libero_spatial:20"
         "$(ck 2000)|$OUT/step_2000|libero_spatial:20" "$(ck 5000)|$OUT/step_5000|libero_spatial:20"
         "$(ck 10000)|$OUT/step_10000_plus|plus_camera:libero_spatial")
  BLIND=${BLIND:-1}; BT=50
else
  units=("$(ck $STEPS)|$OUT/step_$STEPS|libero_spatial:10"); BLIND=${BLIND:-0}; BT=10
fi
echo "$(date -u +%FT%TZ) eval_plan ${#units[@]} units on $NG GPUs, $VW sim workers each, blind=$BLIND" | tee -a $OUT/plan.log
slot_pid=(); i=0
for u in "${units[@]}"; do
  IFS='|' read -r c o cells <<<"$u"
  while :; do  # first free GPU slot
    for g in $(seq 0 $((NG - 1))); do p=${slot_pid[$g]:-}; if [ -z "$p" ] || ! kill -0 $p 2>/dev/null; then break 2; fi; done; sleep 20
  done
  tag=$(echo $cells | tr ':,' '__')
  ( VG=$g VP=$((6700 + g)) VW=$VW VIDEOS=${VIDEOS:-1000} VIDEO_EVERY=20 bash $K/eval_ckpt.sh $c $o $cells > $OUT/unit_${i}_$tag.log 2>&1; echo "$(date -u +%FT%TZ) unit $i $cells rc=$?" >> $OUT/plan.log ) &
  slot_pid[$g]=$!; i=$((i + 1))
done
wait
if [ $BLIND = 1 ]; then
  B=$OUT/blind; mkdir -p $B/random/libero_spatial $B/demo_replay/libero_spatial
  ( train_env; python -B $K/mk_blind_spec.py $DATA/libero_spatial_no_noops_1.0.0_lerobot $K/subsets/libero_spatial_d5_s0.json $B/spec_libero_spatial.json ) > $B/spec.log 2>&1
  RR=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps([d['min'], d['max']]))" $RD/action_norm.json)
  W=$(( (NC - 2) / 2 )); pids=()
  for w in $(seq 0 $((W - 1))); do
    ( sim_env libero; python -B $K/vl_eval.py --suite libero_spatial --policy random --random_range "$RR" --trials $BT --worker $w --workers $W --out $B/random/libero_spatial/w$w.jsonl ) > $B/random_w$w.log 2>&1 &
    pids+=($!)
    ( sim_env libero; python -B $K/vl_eval.py --suite libero_spatial --policy demo_replay --blind_spec $B/spec_libero_spatial.json --trials $BT --worker $w --workers $W --out $B/demo_replay/libero_spatial/w$w.jsonl ) > $B/replay_w$w.log 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait $p; done
fi
python3 - $OUT <<'PY' | tee -a $OUT/plan.log
import glob, json, os, sys
for d in sorted({os.path.dirname(f) for f in glob.glob(sys.argv[1] + "/**/w*.jsonl", recursive=True)}):
    rows = [json.loads(l) for f in glob.glob(d + "/w*.jsonl") for l in open(f)]
    print(os.path.relpath(d, sys.argv[1]), f"{sum(r['success'] for r in rows)}/{len(rows)}")
PY
echo "$(date -u +%FT%TZ) EVAL_PLAN_DONE" | tee -a $OUT/plan.log
