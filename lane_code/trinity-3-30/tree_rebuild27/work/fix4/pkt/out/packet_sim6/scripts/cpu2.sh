# CPU rehearsal on trinity-1-18 with the stand-in driver: p1cpu python and its CPU build of the library,
# torchvision from w27fix/ovl2. fla is not on the path (no usable triton on this node).
# usage: cpu2.sh <run name>
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w28fix; SRC=$F/src; K0=$W/w27fix/n_go; K=$F/n_go
P1=/scratch/jjyeung/envs/p1cpu/bin/python; VS=/scratch/jjyeung/envs/vllm/lib/python3.12/site-packages
date -u +%FT%TZ; hostname -s
ls $W/w27fix/ovl2/torchvision/__init__.py 2>&1 | sed "s#$W/##"
I=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/utils/import_utils.py
grep -n "def is_torch_cuda_available" -A8 $I | head -12; grep -n "def is_flash_linear_attention_available" -A14 $I | head -18
RUN=$F/work/$1; if [ -e $RUN ]; then echo RUN_EXISTS; exit 1; fi; mkdir -p $RUN/tmp/tmpd
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export HF_HOME=/tmp/a15sim/hf XDG_CACHE_HOME=/tmp/a15sim/cache TMPDIR=/tmp/a15sim/tmpd TRITON_CACHE_DIR=/tmp/a15sim/cache/triton SLURM_JOB_ID=0
PATHS="path=$W/w27fix/ovl2"
run() {
  local c=$1 k=$2 role=$3 tag=$4; shift 4
  echo "## $tag" >> $RUN/e.txt
  CUDA_VISIBLE_DEVICES=63 nice -n 10 timeout 280 bash $SRC/ns4.sh $RUN/tmp a15sim $P1 -I -s -B $SRC/t.py "$c" "$k" "/tmp/a15sim/c_$tag" "$role" sim $PATHS "$@" >> $RUN/r.txt 2>> $RUN/e.txt
  echo "rc $tag $?" >> $RUN/r.txt
}
MT=meta=$F/work/meta16
run job $K0 old job_old $MT
run job $K new job_new $MT
run job $K0 old job_old_recorded $MT trace
run job $K new job_new_recorded $MT trace
run job_noguard $K0 old job_noguard_old $MT
run order $K new order_new $MT
run api $K0 old api_old
run api $K new api_new
run api_noguard $K new api_noguard
run api_uncached_noguard $K new api_uncached_noguard
run fresh $K new fresh_new
run fresh_import $K new fresh_import_new
run fresh_noguard $K new fresh_noguard
run fresh $K0 old fresh_old
run job $K new tb_selection $MT fail=selection
run job $K new tb_admit $MT fail=admit
run job $K new tb_forward $MT fail=forward
run job $K new tb_uncaught $MT fail=uncaught
run job $K new tb_bound $MT fail=bound
date -u +%FT%TZ
echo "pycache in kits: $(find $K $K0 -name __pycache__ | wc -l)"
echo "AS_EXPECTED $(grep -c '"as_expected": true' $RUN/r.txt) of $(grep -c '"as_expected": ' $RUN/r.txt)"
echo DONE
