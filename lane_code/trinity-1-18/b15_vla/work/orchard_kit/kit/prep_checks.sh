#!/bin/bash
# Login-node CPU preparation and checks for Test L (after setup_stack.sh data4). Each phase logs to $V/out/prep/<phase>.log.
#   specs    fixed subset lists of the four suites (setup_stack.sh specs) and the kit mixtures (overlay2)
#   pin      LIBERO-Plus 'Camera Viewpoints' task ids per suite, with the task_classification.json sha256 -> plus_camera_ids.json
#   blind    blind-prior specs from every suite's d5_s0 training subset -> blind_<suite>_d5_s0.json
#   parity   state convention, image orientation and prompt strings (parity_check.py) on the 10 replay-spec episodes
#   smoke    closed-loop smoke on all four suites: random policy and blind prior, 1 episode per task (40 each)
# usage: prep_checks.sh [phase ...]
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/prep; mkdir -p $O; export VLA_LOG_DIR=$O
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $O/phase.log; }
SUITES="libero_spatial libero_object libero_goal libero_10"
p_specs() { bash $K/setup_stack.sh overlay2 specs; cat $V/logs/setup_specs.log; }
p_pin() { ( sim_env plus; python -B - <<PY
import hashlib, json, os
f = os.path.join(os.environ["LIBERO_HOME"], "libero/libero/benchmark/task_classification.json")
m = json.load(open(f)); ids = {}
for su in "$SUITES".split():
    ids[su] = sorted(it["id"] - 1 for it in m.get(su, []) if it["category"] == "Camera Viewpoints")
cats = sorted({it["category"] for v in m.values() for it in v})
src = open("$V/src/SRC_SHA256.txt").read()
json.dump({"task_classification_sha256": hashlib.sha256(open(f, "rb").read()).hexdigest(), "source_tarballs": src,
           "categories": cats, "ids": ids, "counts": {k: len(v) for k, v in ids.items()}, "total": sum(map(len, ids.values()))},
          open("$O/plus_camera_ids.json", "w"), indent=1)
print({k: len(v) for k, v in ids.items()}, "total", sum(map(len, ids.values())), "categories", cats)
PY
) ; }
p_blind() { for su in $SUITES; do ( train_env; python -B $K/mk_blind_spec.py $DATA/${su}_no_noops_1.0.0_lerobot $K/subsets/${su}_d5_s0.json $O/blind_${su}_d5_s0.json ); done; }
p_parity() {
  ( train_env; python -B $K/parity_check.py extract $V/out/cl_check/replay_spec.json $DATA $O/parity.npz ) &&
  ( sim_env libero; cd $K && python -B $K/parity_check.py compare $O/parity.npz $V/out/cl_check/replay_spec.json $O/parity.json | tail -40 )
}
p_smoke() {
  RR=$(python3 -c "import json; print(json.dumps(json.load(open('$V/out/cl_check/replay_spec.json'))['random_range']))")
  pids=()
  for su in $SUITES; do
    ( sim_env libero; nice -n 19 python -B $K/vl_eval.py --suite $su --policy random --random_range "$RR" --trials 1 --out $O/smoke_random_$su.jsonl --video_dir $O/videos_smoke --videos 1 ) > $O/smoke_random_$su.log 2>&1 &
    pids+=($!)
    ( sim_env libero; nice -n 19 python -B $K/vl_eval.py --suite $su --policy demo_replay --blind_spec $O/blind_${su}_d5_s0.json --trials 1 --out $O/smoke_blind_$su.jsonl --video_dir $O/videos_smoke --videos 1 ) > $O/smoke_blind_$su.log 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait $p; done
  python3 - $O <<'PY'
import glob, json, sys
for pol in ("random", "blind"):
    for f in sorted(glob.glob(f"{sys.argv[1]}/smoke_{pol}_*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        print(pol, f.split("_", 2)[-1][:-6], f"{sum(r['success'] for r in rows)}/{len(rows)}", "steps", sorted(r["steps"] for r in rows)[:3], "...")
PY
}
PH=("$@"); [ ${#PH[@]} = 0 ] && PH=(specs pin blind parity smoke)
for p in "${PH[@]}"; do ph "start $p"; p_$p > $O/$p.log 2>&1; rc=$?; ph "done $p rc=$rc $(tail -3 $O/$p.log | tr '\n' ' ' | cut -c1-600)"; done
ph PREP_END
