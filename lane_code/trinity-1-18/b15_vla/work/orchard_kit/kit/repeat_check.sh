#!/bin/bash
# Determinism of two uninterrupted CPU runs (tiny Qwen3.5, the Test L recipe): separates CPU float noise from resume error.
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/cpu_hook; W=$V/work; export CUDA_VISIBLE_DEVICES= STARVLA_DISABLE_DEEPSPEED=1 VLL_CPU_FP32=1 OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
train_env; cd $SV; TINY=$W/tiny_Qwen3.5; L=$W/data/lerobot; R=$W/hook_runs
common=(--seed=17 --run_root_dir=$R --framework.qwenvl.base_vlm=$TINY --framework.qwenvl.attn_implementation=sdpa --framework.qwenvl.vl_hidden_dim=64
        --datasets.vla_data.data_root_dir=$L --datasets.vla_data.data_mix=${MIX:-vll_libero_spatial_d1_s0} --datasets.vla_data.per_device_batch_size=2
        --datasets.vla_data.num_workers=2 --datasets.vla_data.pin_memory=false --trainer.max_train_steps=4 --trainer.num_warmup_steps=1
        "--trainer.state_steps=[]" --trainer.state_every=0 --trainer.trace_param_sums=true "--trainer.save_steps=[]")
for k in 1 2; do timeout 900 python -B $K/vl_train.py --config_yaml $K/arm_testL.yaml "${common[@]}" --run_id=rep${k}_$$ > $O/rep${k}_$$.log 2>&1; echo "rep$k rc=$?"; done
python3 - $R/rep1_$$ $R/rep2_$$ <<'PY'
import json, sys
a = [json.loads(l) for l in open(sys.argv[1] + "/trace.jsonl")]; b = [json.loads(l) for l in open(sys.argv[2] + "/trace.jsonl")]
for x, y in zip(a, b):
    print(x["step"], x["loss"] == y["loss"], x["batch_fp"] == y["batch_fp"], {k: x["param_sums"][k] - y["param_sums"][k] for k in x["param_sums"]})
print("REPEAT_EXACT" if all(x["loss"] == y["loss"] and x["param_sums"] == y["param_sums"] for x, y in zip(a, b)) else "REPEAT_DIFF")
PY
