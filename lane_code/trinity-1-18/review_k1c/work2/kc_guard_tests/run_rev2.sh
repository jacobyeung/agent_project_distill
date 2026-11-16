set -u
T=/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard_tests; W=/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard/k1_build/work/kit_k1a/work
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
export XDG_CACHE_HOME=$T/runtime_cache HF_HOME=$T/runtime_cache TRITON_CACHE_DIR=$T/runtime_cache
OWN=/scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/native/probe
for py in sam3_scipy_ovl p1cpu; do
  P=/scratch/jjyeung/envs/$py/bin/python
  echo "### forge $py"; $P -I -s -B $T/rev_forge.py $py 2>&1 | tail -4
  python3 $T/rev_resume.py $py
  for v in a b; do echo "### resume $py $v"
    (cd $T && $P -I -s -B $W/k1_pipeline.py cache --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json --out $T/resume2_${py}_$v --phase convert --max-seconds 900 --preflight-out $T/resume2_${py}_$v.preflight.json --tower-cache /scratch/jjyeung/k1/run_tower_sam_2 --own-cache $OWN > $T/resume2_${py}_$v.log 2>&1; echo rc=$?)
    tail -1 $T/resume2_${py}_$v.log; python3 -c "import json,sys;print('HALTED',json.load(open(sys.argv[1]))['error'][:120])" $T/resume2_${py}_$v/HALTED.json
    grep -c capture_start $T/resume2_${py}_$v/PROGRESS.jsonl; diff <(cat $T/canary/PROGRESS.jsonl) <(head -n $(wc -l < $T/canary/PROGRESS.jsonl) $T/resume2_${py}_$v/PROGRESS.jsonl) >/dev/null && echo progress_prefix_ok
    tail -3 $T/resume2_${py}_$v/PROGRESS.jsonl
  done
done
echo DONE
