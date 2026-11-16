#!/bin/bash
# eval_ckpt.sh CKPT.pt OUTDIR CELLS
#   CELLS: comma list of <suite>:<trials per task> (suite libero_spatial | libero_object | libero_goal | libero_10) or
#   plus_camera:<suite> (LIBERO-Plus 'Camera Viewpoints', the pinned task ids in kit/plus_camera_ids.json, 1 trial each).
#   e.g. libero_spatial:20,libero_goal:20   or   libero_spatial:50,libero_object:50,libero_goal:50,libero_10:50
# One policy server (vl_server.py: StarVLA's server with the kit's head hook) on GPU ${VG:-0} serves ${VW:-12} sim clients
# per cell. Episodes resume per (task, trial) from OUTDIR/<cell>/w*.jsonl. Env: BASE_VLM overrides the backbone dir of the
# run config (evaluation outside the training job); VIDEOS=N videos per worker, one episode in VIDEO_EVERY (20);
# SEND_STATE=0 for checkpoints trained without proprio (the pilot recipe).
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
ck=$1 O=$2 cells=$3; mkdir -p $O; export VLA_LOG_DIR=$O
[ -f $ck ] || { echo "FAIL missing $ck"; exit 2; }
port=${VP:-$((6700 + ${VG:-0}))}
ov=(--config_override framework.qwenvl.attn_implementation=sdpa); [ -n "${BASE_VLM:-}" ] && ov+=(--config_override framework.qwenvl.base_vlm=$BASE_VLM)
( train_env; export CUDA_VISIBLE_DEVICES=${VG:-0}; exec python -B $K/vl_server.py --ckpt_path $ck --port $port --use_bf16 --idle_timeout -1 --seed 0 "${ov[@]}" ) > $O/server.log 2>&1 &
spid=$!
for i in $(seq 1 240); do (exec 3<>/dev/tcp/127.0.0.1/$port) 2>/dev/null && break; kill -0 $spid 2>/dev/null || { tail -5 $O/server.log; echo "FAIL server died"; exit 3; }; sleep 5; done
fails=0
for cell in ${cells//,/ }; do
  a=${cell%%:*} b=${cell#*:}; extra=()
  if [ $a = plus_camera ]; then
    sim_env plus; suite=$b; C=$O/plus_camera_$suite
    ids=$(python3 -c "import json,sys; print(','.join(str(i) for i in json.load(open(sys.argv[1]))['ids'][sys.argv[2]]))" $K/plus_camera_ids.json $suite)
    extra=(--plus_category "Camera Viewpoints" --task_ids $ids --trials 1)
  else
    sim_env libero; suite=$a; C=$O/$suite; extra=(--trials $b)
  fi
  [ -n "${LIMIT_TASKS:-}" ] && extra+=(--limit_tasks $LIMIT_TASKS)
  mkdir -p $C; W=${VW:-12}; pids=()
  for w in $(seq 0 $((W - 1))); do
    python -B $K/vl_eval.py --suite $suite "${extra[@]}" --worker $w --workers $W --port $port --out $C/w$w.jsonl \
      --send_state ${SEND_STATE:-1} --video_dir $C/videos --videos ${VIDEOS:-0} --video_every ${VIDEO_EVERY:-20} > $C/w$w.log 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait $p || fails=$((fails + 1)); done
  python3 - $C $cell <<'PY' | tee -a $O/summary.txt
import collections, glob, json, sys
rows = [json.loads(l) for f in glob.glob(sys.argv[1] + '/w*.jsonl') for l in open(f)]
per = collections.defaultdict(lambda: [0, 0])
for r in rows: per[r['task_id']][0] += bool(r['success']); per[r['task_id']][1] += 1
s = sum(v[0] for v in per.values()); n = len(rows)
json.dump({"cell": sys.argv[2], "episodes": n, "success": s, "rate": s / max(n, 1), "per_task": {str(k): v for k, v in sorted(per.items())}},
          open(sys.argv[1] + '/summary.json', 'w'))
print(sys.argv[2], 'episodes', n, 'success', s, 'rate %.4f' % (s / max(n, 1)))
PY
done
kill $spid 2>/dev/null; wait $spid 2>/dev/null
echo "EVAL_DONE $ck $cells client_fails=$fails"; [ $fails = 0 ]
