cd /scratch/jjyeung/orch_n30/geo_k1
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp MPLCONFIGDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp/mpl
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/k1_convert.py --model moge2 --pred pred_gpu/moge2 --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json --towers /scratch/jjyeung/k1/run_tower_sam_2 --out /scratch/jjyeung/orch_n30/geo_k1/geom > logs/convert_moge2.log 2>&1
echo EXIT $? >> logs/convert_moge2.log
ARMS=""; for a in $(ls -d /scratch/jjyeung/orch_n30/geo_k1/geom/moge2_*/); do n=$(basename $a); ARMS="$ARMS --arm $n=$a"; done
echo ARMS $ARMS >> logs/convert_moge2.log
cd harness
for i in 0 1 2 3; do /scratch/jjyeung/envs/planner_local_v1/bin/python -B k1_price.py --out out_moge2 --fits e3_FITS.json --no-reference --shard $i/4 $ARMS > ../logs/price_moge2_$i.log 2>&1 & done
wait
echo PRICE_DONE >> ../logs/convert_moge2.log
