F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix; G=$F/gpu_test; K=$F/n_go
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=''
sha256sum $G/t.py $G/r.sh | cut -c1-80; bash -n $G/r.sh && echo "r.sh syntax ok"
# CPU smoke of the case logic only (cpu build, no device): every case must reach the device open and fail there.
for c in none guard_import control_import guard_query control_query job_order_guard job_order_control; do
  (cd $F/work && nice -n 10 timeout 100 /scratch/jjyeung/envs/p1cpu/bin/python -B -s $G/t.py $c $K/b 2>/dev/null | cut -c1-420; echo "rc $c ${PIPESTATUS[0]}")
done
find $K -name __pycache__ | wc -l
