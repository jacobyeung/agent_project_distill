cd /scratch/jjyeung/orch_n30/geo_k1
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp MPLCONFIGDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp/mpl
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/k1_convert.py --model pi3x --pred pred_gpu/pi3x --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json --towers /scratch/jjyeung/k1/run_tower_sam_2 --out /scratch/jjyeung/orch_n30/geo_k1/geom > logs/convert_pi3x.log 2>&1
echo EXIT $? >> logs/convert_pi3x.log
ARMS=""; for a in $(ls -d /scratch/jjyeung/orch_n30/geo_k1/geom/pi3x_*/); do n=$(basename $a); ARMS="$ARMS --arm $n=$a"; done
echo ARMS $ARMS >> logs/convert_pi3x.log
cd harness
for i in 0 1 2 3; do /scratch/jjyeung/envs/planner_local_v1/bin/python -B k1_price.py --out out_pi3x --fits e3_FITS.json --no-reference --shard $i/4 $ARMS > ../logs/price_pi3x_$i.log 2>&1 & done
wait
echo PRICE_DONE >> ../logs/convert_pi3x.log
