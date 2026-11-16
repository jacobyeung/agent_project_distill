#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=general
#SBATCH --qos=general_qos
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=24
#SBATCH --mem=320G
#SBATCH --time=00:59:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/vla_libero/logs/slurm_%j.out
# Pre-launch GPU test of one arm on 1 H100 (ZeRO-2 with the optimizer offloaded to CPU; production runs ZeRO-2 on 4 GPUs
# without offload): first batch, optimizer steps, full-state save at step 2, then the determinism control (a second
# uninterrupted run to step 3 from the same seeded init), then resume from the step-2 state, and step-3 comparisons of
# straight vs straight_b (run-to-run noise) and straight vs resumed (resume); then (SERVER_SMOKE=1) one closed-loop
# LIBERO episode through the real policy server on the step-3 weights.
# DET=1 (default) runs all three with VLL_DETERMINISTIC=1 (vl_train.py: torch deterministic algorithms, warn only; cuDNN
# deterministic; CUBLAS_WORKSPACE_CONFIG=:4096:8; FLASH_ATTENTION_DETERMINISTIC=1). RESUME_TWICE=1 adds a second resume.
# The test warms up for TWARM=1 step, so its early-loss stop is off (trainer.early_loss_factor=0).
# Disk: refuses to start unless node-local /tmp has STATE_GB + EXPORT_GB + 10 GiB free (one state, one export).
# usage: sbatch -J jjy_vll_t<arm> gpu_test.sh ARM
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
ARM=$1; P=$V/out/gpu_test_${ARM}_${SLURM_JOB_ID:-local}; mkdir -p $P
export B=/tmp/vll_${SLURM_JOB_ID:-local}; R=$B/runs; mkdir -p $R $B/xdg; cp -r $K $B/kit && export K=$B/kit;  # jobs run a private snapshot of the kit
 export XDG_CACHE_HOME=$B/xdg TRITON_CACHE_DIR=$B/triton
exec > >(tee -a $P/job.log) 2>&1
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $P/phase.log; }
ph "start host=$(hostname) arm=$ARM kit=$(head -c 16 $K/KIT_SHA256 2>/dev/null) det=${DET:-1}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv; free -g | head -2; df -h $B | tail -1 | tee -a $P/phase.log
pf=$(bash $K/preflight.sh $B $(( ${STATE_GB:-125} + ${EXPORT_GB:-20} + 10 )) gpu_test); pfrc=$?; ph "$pf"; [ $pfrc = 0 ] || { ph "FAIL preflight"; exit 4; }
bash $K/stage.sh $ARM || { ph "FAIL stage"; exit 1; }
ph "staged $(cat $B/models/Qwen3.5-$ARM/B1_CHECK.json 2>/dev/null | head -c 300)"
sed "s#KITDIR#$K#" $K/acc_z2_offload.yaml > $B/acc.yaml
[ "${DET:-1}" = 1 ] && export VLL_DETERMINISTIC=1
common=(--seed=17 --run_root_dir=$R --framework.qwenvl.base_vlm=$B/models/Qwen3.5-$ARM --datasets.vla_data.data_root_dir=$B/data/lerobot
        --datasets.vla_data.data_mix=${MIX:-vll_libero_spatial_d5_s0} --datasets.vla_data.per_device_batch_size=${TBS:-4} --datasets.vla_data.num_workers=2
        --trainer.max_train_steps=3 --trainer.num_warmup_steps=${TWARM:-1} "--trainer.state_steps=[2]" --trainer.state_every=0 --trainer.trace_param_sums=true
        --trainer.early_loss_factor=0 --trainer.state_gb_est=${STATE_GB:-125} --trainer.export_gb_est=${EXPORT_GB:-20})
launch() { ( cd $SV && train_env && exec accelerate launch --config_file $B/acc.yaml --num_processes 1 --mixed_precision bf16 --main_process_port 29518 \
             $K/vl_train.py --config_yaml $K/${CFG:-arm_testL.yaml} "$@" ); }
launch "${common[@]}" --run_id=straight "--trainer.save_steps=[${SAVE3:-3}]" > $P/straight.log 2>&1; ph "straight rc=$? $(tail -c 300 $R/straight/trace.jsonl 2>/dev/null | tail -1 | cut -c1-200)"
du -sh $R/straight/state/steps_2 $R/straight/checkpoints/* 2>/dev/null | tee -a $P/phase.log
launch "${common[@]}" --run_id=straight_b "--trainer.save_steps=[]" --trainer.final_export=false "--trainer.state_steps=[]" > $P/straight_b.log 2>&1; ph "straight_b rc=$?"
launch "${common[@]}" --run_id=resumed "--trainer.save_steps=[]" --trainer.final_export=false --trainer.resume_state=$R/straight/state/steps_2 > $P/resumed.log 2>&1; ph "resumed rc=$?"
if [ "${RESUME_TWICE:-0}" = 1 ]; then
  launch "${common[@]}" --run_id=resumed_b "--trainer.save_steps=[]" --trainer.final_export=false --trainer.resume_state=$R/straight/state/steps_2 > $P/resumed_b.log 2>&1; ph "resumed_b rc=$?"
fi
for r in straight straight_b resumed resumed_b; do for f in trace.jsonl config.yaml dataset_statistics.json summary.jsonl; do cp $R/$r/$f $P/${r}_$f 2>/dev/null; done; done
python3 - $R <<'PY' | tee $P/resume_compare.txt
import json, os, sys
R = sys.argv[1]
tr = {n: [json.loads(l) for l in open(f"{R}/{n}/trace.jsonl")] for n in ("straight", "straight_b", "resumed", "resumed_b")
      if os.path.exists(f"{R}/{n}/trace.jsonl")}
for n, rows in tr.items():
    print(f"{n:10s} steps", [(r["step"], round(r["loss"], 6), r["batch_fp"], r.get("gpu_peak_gib")) for r in rows])
rel = lambda x, y: abs(x - y) / max(abs(x), 1e-12)
TOL_L, TOL_P = 1e-3, 1e-4
s3 = lambda n: [r for r in tr[n] if r["step"] == 3][0]
a3 = s3("straight")
moved = {k: rel([r for r in tr["straight"] if r["step"] == 2][0]["param_sums"][k], a3["param_sums"][k]) for k in a3["param_sums"]}
print("straight step2->3 param-sum change max %.2e" % max(moved.values()))
res = {}
for n in ("straight_b", "resumed", "resumed_b"):
    if n not in tr:
        continue
    b3 = s3(n); ok_b = a3["batch_fp"] == b3["batch_fp"]; dl = rel(a3["loss"], b3["loss"])
    dp = {k: rel(a3["param_sums"][k], b3["param_sums"][k]) for k in a3["param_sums"]}
    res[n] = (ok_b and dl <= TOL_L and all(v <= TOL_P for v in dp.values()), max(dp.values()), dl)
    print(f"straight vs {n}: step3 batch equal {ok_b} loss rel diff {dl:.2e} param-sum rel diff max {max(dp.values()):.2e}",
          {'.'.join(k.split('.')[-5:-1]) if '.' in k else k: f"{v:.2e}" for k, v in dp.items()})
det_ok, det_max, _ = res["straight_b"]; res_ok, res_max, _ = res["resumed"]
print("DETERMINISM_OK" if det_ok else "DETERMINISM_DIFF", "(straight twice, same tolerance)")
print("RESUME_OK" if res_ok else "RESUME_MISMATCH", "(tolerance: same batch, loss rel 1e-3, param sums rel 1e-4)")
if res_ok:
    print("CAUSE resume exact within tolerance")
elif det_ok:
    print("CAUSE RESUME_DEFECT: two uninterrupted runs agree within tolerance, the resumed run does not")
elif res_max <= det_max:
    print(f"CAUSE NONDETERMINISM: the resume differs by {res_max:.2e}, no more than two uninterrupted runs differ ({det_max:.2e})")
else:
    print(f"CAUSE UNRESOLVED: run-to-run noise {det_max:.2e} < resume difference {res_max:.2e}; a resume defect is not ruled out")
PY
if [ "${CKPT_PROBE:-0}" = 1 ]; then  # 1-step memory probes at batch PBS (default TBS): plain, then gradient checkpointing
  c2=("${common[@]}"); c2=("${c2[@]/--trainer.max_train_steps=3/--trainer.max_train_steps=1}")
  c2=("${c2[@]/--datasets.vla_data.per_device_batch_size=${TBS:-4}/--datasets.vla_data.per_device_batch_size=${PBS:-${TBS:-4}}}")
  for gc in false true; do
    launch "${c2[@]}" --run_id=probe_gc_$gc "--trainer.save_steps=[]" "--trainer.state_steps=[]" --trainer.final_export=false --trainer.gradient_checkpointing=$gc > $P/probe_gc_$gc.log 2>&1
    ph "probe bs=${PBS:-${TBS:-4}} gc=$gc rc=$? $(cut -c1-300 $R/probe_gc_$gc/trace.jsonl 2>/dev/null) $(grep -m1 -o 'OutOfMemoryError.\{0,120\}' $P/probe_gc_$gc.log)"
    cp $R/probe_gc_$gc/trace.jsonl $P/probe_gc_${gc}_trace.jsonl 2>/dev/null
  done
fi
if [ "${SERVER_SMOKE:-1}" = 1 ] && [ -f $R/straight/checkpoints/steps_3_pytorch_model.pt ]; then
  LIMIT_TASKS=1 VW=1 VIDEOS=1 SEND_STATE=${SEND_STATE:-1} bash $K/eval_ckpt.sh $R/straight/checkpoints/steps_3_pytorch_model.pt $P/server_smoke libero_spatial:1 > $P/server_smoke.log 2>&1
  ph "server smoke rc=$? $(tail -2 $P/server_smoke.log | tr '\n' ' ')"
fi
df -h $B | tail -1 | tee -a $P/phase.log
ph "GPU_TEST_DONE (node-local $B is job-private /tmp: Slurm's job_container/tmpfs removes it when the job ends)"
