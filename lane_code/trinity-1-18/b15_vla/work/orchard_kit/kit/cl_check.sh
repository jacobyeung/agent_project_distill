#!/bin/bash
# Closed-loop check before any training (CPU, headless): random policy on the 10 LIBERO-Spatial tasks (1 episode each,
# expect ~0%) and replay of 10 recorded demos through the client path (>= 9/10 must succeed); videos for 3+ episodes.
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/cl_check; mkdir -p $O $V/logs; export VLA_LOG_DIR=$O
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $O/phase.log; }
if [ ! -x $V/envs/e_tool/bin/python ]; then $V/bin/uv venv -p $(cat $V/st/p310_path) $V/envs/e_tool && $V/bin/uv pip install -p $V/envs/e_tool/bin/python h5py==3.16.0 pyarrow==14.0.1 numpy==1.26.4 > $O/e_tool.log 2>&1; $V/bin/uv pip freeze -p $V/envs/e_tool/bin/python > $V/envs/e_tool.freeze.txt; fi
# renderer: EGL first (mesa on the login node, NVIDIA in jobs), then OSMesa
if [ ! -f $V/st/gl ]; then
  for gl in egl osmesa; do
    if [ $gl = osmesa ] && [ ! -f $V/osmesa/lib/libOSMesa.so ]; then
      curl -sSfL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C $V/bin --strip-components=1 bin/micromamba
      MAMBA_ROOT_PREFIX=$V/mamba $V/bin/micromamba create -y -r $V/mamba -p $V/osmesa -c conda-forge mesalib=24.0.7 > $O/osmesa.log 2>&1
    fi
    ( MUJOCO_GL=$gl sim_env libero; export PYOPENGL_PLATFORM=$gl; [ $gl = osmesa ] && export LD_LIBRARY_PATH=$V/osmesa/lib:${LD_LIBRARY_PATH:-}; cd $O && timeout 300 python -B $K/render_check.py libero_spatial 0 20 ) > $O/render_$gl.log 2>&1 \
      && grep -q EPISODE_OK $O/render_$gl.log && { echo $gl > $V/st/gl; break; }
  done
fi
[ -f $V/st/gl ] || { ph "FAIL no renderer"; exit 1; }
ph "renderer $(cat $V/st/gl): $(grep sec/step $O/render_$(cat $V/st/gl).log)"
( sim_env libero; python -B -c "
import json; from libero.libero import benchmark
s = benchmark.get_benchmark_dict()['libero_spatial'](); json.dump([s.get_task(i).language for i in range(s.n_tasks)], open('$O/suite_langs.json','w'))" ) || { ph "FAIL suite langs"; exit 1; }
( tool_env; python -B $K/mk_replay_spec.py $FULL $V/data/hdf5 $O/suite_langs.json 5 $O/replay_spec.json ) > $O/replay_spec.log 2>&1 || { ph "FAIL replay spec"; tail -5 $O/replay_spec.log; exit 1; }
ph "replay spec: $(tail -2 $O/replay_spec.log | tr '\n' ' ')"
if [ "${CL_MODE:-all}" = all ]; then RR=$(python3 -c "import json; print(json.dumps(json.load(open('$O/replay_spec.json'))['random_range']))")
rps=(); for w in 0 1; do
  ( sim_env libero; nice -n 19 python -B $K/vl_eval.py --policy random --random_range "$RR" --trials 1 --worker $w --workers 2 --out $O/random_w$w.jsonl --video_dir $O/videos_random --videos 1 ) > $O/random_w$w.log 2>&1 &
  rps+=($!)
done; fi; RS=${RS:-}
PORT=$((20000 + RANDOM % 20000))
( train_env; exec python -B $K/vl_replay_server.py $O/replay_spec.json $PORT ) > $O/replay_server.log 2>&1 &
SP=$!
for i in $(seq 1 60); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 2; done
pids=(); for w in 0 1; do
  ( sim_env libero; nice -n 19 python -B $K/vl_eval.py --replay_spec $O/replay_spec.json --worker $w --workers 2 --port $PORT --out $O/replay${RS}_w$w.jsonl --video_dir $O/videos_replay$RS --videos 2 ${RARGS:-} ) > $O/replay${RS}_w$w.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done; kill $SP 2>/dev/null; for p in "${rps[@]:-}"; do [ -n "$p" ] && wait $p; done
python3 - $O "$RS" <<'PY'
import glob, json, sys
O = sys.argv[1]
for name, pat in (("random", "random_w*.jsonl"), ("replay", f"replay{sys.argv[2]}_w*.jsonl")):
    rows = [json.loads(l) for f in glob.glob(f"{O}/{pat}") for l in open(f)]
    s = sum(r["success"] for r in rows)
    print(f"{name}: {s}/{len(rows)} success; per episode:", [(r["task_id"], r.get("episode_index"), r["success"], r["steps"]) for r in rows])
print("videos", sorted(glob.glob(f"{O}/videos_*/*.mp4")))
PY
ph "CL_CHECK_DONE"
