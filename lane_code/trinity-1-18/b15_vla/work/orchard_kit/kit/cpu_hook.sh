#!/bin/bash
# CPU checks of the Test L recipe ($CFG, default arm_testL.yaml: head hook, proprio, gripper g, masked chunk tails, state slots, self-stop
# trace fields) on the tiny random Qwen3.5 of cpu_smoke.sh: hook_check.py, then vl_train.py for 4 steps with full state
# every 2 steps (one rolling state), resume from state/current, and a step-4 comparison with the uninterrupted run.
# usage: [CFG=arm_testL.yaml] cpu_hook.sh [MIX]   (default vll_libero_spatial_d1_s0)
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
MIX=${1:-vll_libero_spatial_d1_s0}; CFG=${CFG:-arm_testL.yaml}
O=$V/out/cpu_hook; W=$V/work; mkdir -p $O; export CUDA_VISIBLE_DEVICES= STARVLA_DISABLE_DEEPSPEED=1 VLL_CPU_FP32=1 OMP_NUM_THREADS=4
exec > >(tee -a $O/log.txt) 2>&1
echo "== $(date -u +%FT%TZ) cpu_hook mix=$MIX kit=$(head -c 16 $K/KIT_SHA256)"
train_env; cd $SV
TINY=$W/tiny_Qwen3.5; L=$W/data/lerobot
for su in libero_spatial libero_object libero_goal libero_10; do
  [ -d $DATA/${su}_no_noops_1.0.0_lerobot/meta ] || continue
  [ -d $L/${su}_d1_s0_lerobot ] || python -B $K/build_subset.py $DATA/${su}_no_noops_1.0.0_lerobot $L/${su}_d1_s0_lerobot $K/subsets/${su}_d1_s0.json
done
echo "== hook_check"; timeout 1200 python -B $K/hook_check.py $K/$CFG $TINY $L $MIX $O/hook_$$ 2>&1 | grep -v -i "fast path is not" | tail -60
R=$W/hook_runs; mkdir -p $R
common=(--seed=0 --run_root_dir=$R --framework.qwenvl.base_vlm=$TINY --framework.qwenvl.attn_implementation=sdpa --framework.qwenvl.vl_hidden_dim=64
        --datasets.vla_data.data_root_dir=$L --datasets.vla_data.data_mix=$MIX --datasets.vla_data.per_device_batch_size=2
        --datasets.vla_data.num_workers=2 --datasets.vla_data.pin_memory=false --trainer.max_train_steps=4 --trainer.num_warmup_steps=1
        "--trainer.state_steps=[]" --trainer.state_every=2 --trainer.trace_param_sums=true --trainer.state_gb_est=0.01 --trainer.export_gb_est=0.01 --trainer.disk_margin_gb=1 --trainer.trace_module_every=2)
run() { timeout 1200 python -B $K/vl_train.py --config_yaml $K/$CFG "$@"; }
run "${common[@]}" --run_id=straight_$$ "--trainer.save_steps=[4]" > $O/straight_$$.log 2>&1; echo "straight rc=$?"
run "${common[@]}" --run_id=resumed_$$ "--trainer.save_steps=[]" --trainer.resume_state=$R/straight_$$/state/current > $O/resumed_$$.log 2>&1; echo "resumed rc=$?"
python3 - $R/straight_$$ $R/resumed_$$ <<'PY'
import json, os, sys
a = [json.loads(l) for l in open(sys.argv[1] + "/trace.jsonl")]; b = [json.loads(l) for l in open(sys.argv[2] + "/trace.jsonl")]
print("trace keys", sorted(a[-1].keys()))
print("straight", [(r["step"], round(r["loss"], 7), r["batch_fp"], r.get("gate_proprio"), r.get("param_norms", {}).get("head")) for r in a])
print("resumed ", [(r["step"], round(r["loss"], 7), r["batch_fp"], r.get("gate_proprio")) for r in b])
print("slots", {s: json.load(open(f"{sys.argv[1]}/state/{s}/vl_meta.json")) for s in sorted(os.listdir(sys.argv[1] + "/state"))})
a4, b4 = a[-1], b[-1]
print("proprio_norm.json", os.path.exists(sys.argv[1] + "/proprio_norm.json"), "| config head_hook", "head_hook" in open(sys.argv[1] + "/config.yaml").read())
print("HOOK_RESUME_EXACT" if a4["step"] == b4["step"] == 4 and a4["batch_fp"] == b4["batch_fp"] and a4["loss"] == b4["loss"] and a4["param_sums"] == b4["param_sums"] else "HOOK_RESUME_DIFF")
PY
echo CPU_HOOK_DONE
