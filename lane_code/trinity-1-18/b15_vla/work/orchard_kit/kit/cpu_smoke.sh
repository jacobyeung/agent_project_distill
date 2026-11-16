#!/bin/bash
# CPU smoke of the kit's trainer logic on a tiny random Qwen3.5 (same class as the 9B): first batch, 3 optimizer steps,
# full state at step 2, resume, step-3 comparison, step-indexed sampling; plus the epoch-replay check of stock StarVLA.
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/cpu_smoke; W=$V/work; mkdir -p $O $W; export CUDA_VISIBLE_DEVICES= STARVLA_DISABLE_DEEPSPEED=1 VLL_CPU_FP32=1 OMP_NUM_THREADS=4
exec > >(tee -a $O/log.txt) 2>&1
train_env; cd $SV
BASE=$V/../cache/hf/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a; TINY=$W/tiny_Qwen3.5
[ -f $TINY/config.json ] || python -B - <<PY
import os, shutil
from transformers import AutoConfig, Qwen3_5ForConditionalGeneration
REAL, TINY = "$BASE", "$TINY"; os.makedirs(TINY, exist_ok=True)
c = AutoConfig.from_pretrained(REAL); t = c.text_config; v = c.vision_config
t.hidden_size = 64; t.intermediate_size = 128; t.num_hidden_layers = 4; t.layer_types = t.layer_types[:4]
t.num_attention_heads = 4; t.num_key_value_heads = 2; t.head_dim = 16
t.linear_num_key_heads = 2; t.linear_num_value_heads = 4; t.linear_key_head_dim = 16; t.linear_value_head_dim = 16
t.rope_parameters['mrope_section'] = [2, 1, 1]
v.depth = 2; v.hidden_size = 32; v.intermediate_size = 64; v.num_heads = 2; v.out_hidden_size = 64; v.num_position_embeddings = 64
Qwen3_5ForConditionalGeneration(c).save_pretrained(TINY)
for f in ('tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt', 'chat_template.jinja', 'preprocessor_config.json', 'video_preprocessor_config.json'):
    if os.path.exists(f'{REAL}/{f}'): shutil.copy(f'{REAL}/{f}', f'{TINY}/{f}')
PY
L=$W/data/lerobot; mkdir -p $L
[ -d $L/libero_spatial_d1_s0_lerobot ] || python -B $K/build_subset.py $FULL $L/libero_spatial_d1_s0_lerobot $K/subsets/d1_s0.json
[ -f $O/epoch_done ] || { echo "== epoch check (stock StarVLA loop)"; timeout 900 python -B $K/epoch_check.py $L pilot_libero_spatial_d1_s0 && touch $O/epoch_done; }
R=$W/smoke_runs; mkdir -p $R
common=(--seed=0 --run_root_dir=$R --framework.qwenvl.base_vlm=$TINY --framework.qwenvl.attn_implementation=sdpa --framework.qwenvl.vl_hidden_dim=64
        --datasets.vla_data.data_root_dir=$L --datasets.vla_data.data_mix=pilot_libero_spatial_d1_s0 --datasets.vla_data.per_device_batch_size=2
        --datasets.vla_data.num_workers=2 --datasets.vla_data.pin_memory=false --trainer.max_train_steps=3 --trainer.num_warmup_steps=1
        "--trainer.state_steps=[2]" --trainer.trace_param_sums=true --trainer.state_gb_est=0.01 --trainer.export_gb_est=0.01 --trainer.disk_margin_gb=1)
run() { timeout 900 python -B $K/vl_train.py --config_yaml $K/arm_libero_spatial.yaml "$@"; }
run "${common[@]}" --run_id=straight_$$ "--trainer.save_steps=[3]" > $O/straight.log 2>&1; echo "straight rc=$?"
run "${common[@]}" --run_id=resumed_$$ "--trainer.save_steps=[]" --trainer.resume_state=$R/straight_$$/state/steps_2 > $O/resumed.log 2>&1; echo "resumed rc=$?"
python3 - $R/straight_$$ $R/resumed_$$ <<'PY'
import json, sys
a = [json.loads(l) for l in open(sys.argv[1] + "/trace.jsonl")]; b = [json.loads(l) for l in open(sys.argv[2] + "/trace.jsonl")]
print("straight", [(r["step"], round(r["loss"], 7), r["batch_fp"], round(r["param_sums"]["head"], 6)) for r in a])
print("resumed ", [(r["step"], round(r["loss"], 7), r["batch_fp"], round(r["param_sums"]["head"], 6)) for r in b])
a3, b3 = a[-1], b[-1]
print("RESUME_EXACT" if a3["batch_fp"] == b3["batch_fp"] and a3["loss"] == b3["loss"] and a3["param_sums"] == b3["param_sums"] else "RESUME_DIFF")
PY
ls -la $R/straight_$$ $R/straight_$$/checkpoints $R/straight_$$/state/steps_2 | head -30
echo "== tap check"; python -B $K/tap_check.py $TINY 2>&1 | grep -v -i "fast path is not"
echo CPU_SMOKE_DONE
