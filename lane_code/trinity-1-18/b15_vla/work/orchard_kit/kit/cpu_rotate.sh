#!/bin/bash
# CPU test of the save rules on the tiny random Qwen3.5 of cpu_smoke.sh with the Test L recipe (arm_testL.yaml, head hook):
#   1. rotation: 7 steps, rolling state every 2 steps, exports at 3 and 7. Expect one state dir left (steps_6) named by
#      state/current, steps_2 and steps_4 removed in turn, final_model hard-linked to the step-7 export, sizes in summary.jsonl.
#   2. resume: an incomplete newer state (vl_meta step -1) is ignored; resume_state=latest picks steps_6, and step 7 must
#      equal the uninterrupted run bit for bit.
#   3. disk guards: state_gb_est and export_gb_est above the free space: the step-2 state is skipped, the step-3 export
#      stops the run with exit code 5 and a disk STOP_REASON.
#   4. early-loss stop: early_loss_factor 1e-6 stops at step 2 with exit code 3; preflight.sh refuses an impossible need.
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
MIX=${1:-vll_libero_spatial_d1_s0}; CFG=${CFG:-arm_testL.yaml}
O=$V/out/cpu_rotate; W=$V/work; mkdir -p $O; export CUDA_VISIBLE_DEVICES= STARVLA_DISABLE_DEEPSPEED=1 VLL_CPU_FP32=1 OMP_NUM_THREADS=4
exec > >(tee -a $O/log.txt) 2>&1
echo "== $(date -u +%FT%TZ) cpu_rotate mix=$MIX kit=$(head -c 16 $K/KIT_SHA256)"
train_env; cd $SV
TINY=$W/tiny_Qwen3.5; L=$W/data/lerobot; R=$W/rotate_runs/$$; mkdir -p $R
common=(--seed=0 --run_root_dir=$R --framework.qwenvl.base_vlm=$TINY --framework.qwenvl.attn_implementation=sdpa --framework.qwenvl.vl_hidden_dim=64
        --datasets.vla_data.data_root_dir=$L --datasets.vla_data.data_mix=$MIX --datasets.vla_data.per_device_batch_size=2
        --datasets.vla_data.num_workers=2 --datasets.vla_data.pin_memory=false --trainer.num_warmup_steps=1
        "--trainer.state_steps=[]" --trainer.trace_param_sums=true --trainer.trace_module_every=0
        --trainer.state_gb_est=0.01 --trainer.export_gb_est=0.01 --trainer.disk_margin_gb=1 --trainer.early_loss_factor=0)
run() { timeout 1200 python -B $K/vl_train.py --config_yaml $K/$CFG "$@"; }
run "${common[@]}" --run_id=rot --trainer.max_train_steps=7 --trainer.state_every=2 "--trainer.save_steps=[3,7]" > $O/rot_$$.log 2>&1; echo "rot rc=$?"
mkdir -p $R/rot/state/steps_8 && echo '{"step": -1, "writing": 8}' > $R/rot/state/steps_8/vl_meta.json  # a torn newer save
cp -r $R/rot $R/res  # the resumed run continues in a copy of the run dir
run "${common[@]}" --run_id=res --trainer.max_train_steps=7 --trainer.state_every=2 "--trainer.save_steps=[7]" --trainer.resume_state=latest > $O/res_$$.log 2>&1; echo "res rc=$?"
run "${common[@]}" --run_id=disk --trainer.max_train_steps=3 --trainer.state_every=2 "--trainer.save_steps=[3]" --trainer.state_gb_est=1e6 --trainer.export_gb_est=1e6 > $O/disk_$$.log 2>&1; echo "disk rc=$? (expect 5)"
run "${common[@]}" --run_id=early --trainer.max_train_steps=3 "--trainer.save_steps=[]" --trainer.final_export=false --trainer.early_loss_factor=1e-6 > $O/early_$$.log 2>&1; echo "early rc=$? (expect 3)"
bash $K/preflight.sh $R 999999 impossible; echo "preflight rc=$? (expect 1)"; bash $K/preflight.sh $R 1 small; echo "preflight rc=$? (expect 0)"
grep -m1 -o "Resumed full state from [^ ]*" $O/res_$$.log
python3 - $R <<'PY'
import json, os, sys
R = sys.argv[1]; ok = True
def check(name, cond, detail=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, detail)
st = os.path.join(R, "rot", "state")
ls = sorted(os.listdir(st)); cur = os.readlink(os.path.join(st, "current")) if os.path.islink(os.path.join(st, "current")) else None
check("one rolling state left", [d for d in ls if d.startswith("steps_") and d != "steps_8"] == ["steps_6"] and cur == "steps_6", f"{ls} current->{cur}")
summ = [json.loads(l) for l in open(os.path.join(R, "rot", "summary.jsonl"))]
rolled = [(s["rolled"], os.path.basename(s["removed"])) for s in summ if "rolled" in s]
check("steps_2 then steps_4 removed", rolled == [(4, "steps_2"), (6, "steps_4")], rolled)
sizes = [(s["kind"], s["steps"], s.get("gb")) for s in summ if "kind" in s]
check("sizes recorded", any(k == "export" for k, *_ in sizes) and any(k == "state" for k, *_ in sizes), sizes)
fm, e7 = os.path.join(R, "rot", "final_model", "pytorch_model.pt"), os.path.join(R, "rot", "checkpoints", "steps_7_pytorch_model.pt")
check("final_model hard-linked to step-7 export", os.path.exists(fm) and os.stat(fm).st_ino == os.stat(e7).st_ino, f"nlink={os.stat(e7).st_nlink}")
a = [json.loads(l) for l in open(os.path.join(R, "rot", "trace.jsonl"))]
b = [json.loads(l) for l in open(os.path.join(R, "res", "trace.jsonl"))][len(a):]
check("resume ran step 7 only", [r["step"] for r in b] == [7], [r["step"] for r in b])
check("resume step 7 bit-exact", b and a[-1]["batch_fp"] == b[-1]["batch_fp"] and a[-1]["loss"] == b[-1]["loss"] and a[-1]["param_sums"] == b[-1]["param_sums"],
      (a[-1]["loss"], b[-1]["loss"] if b else None))
ds = [json.loads(l) for l in open(os.path.join(R, "disk", "summary.jsonl"))]
check("state skipped when short", any(s.get("state_skipped") == 2 for s in ds), [s for s in ds if "state_skipped" in s][:1])
check("export refused when short", any("export_refused" in s for s in ds) and "disk" in json.load(open(os.path.join(R, "disk", "STOP_REASON.json")))["reason"])
check("no state dir written when short", not os.path.exists(os.path.join(R, "disk", "state", "steps_2")))
er = json.load(open(os.path.join(R, "early", "STOP_REASON.json")))
check("early-loss stop at step 2", er["step"] == 2 and "early loss" in er["reason"], er)
print("ROTATE_TEST_OK" if ok else "ROTATE_TEST_FAIL")
PY
echo CPU_ROTATE_DONE
