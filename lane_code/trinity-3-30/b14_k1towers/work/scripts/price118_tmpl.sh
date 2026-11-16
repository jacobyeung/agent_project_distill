# header sets MODEL; runs on trinity-1-18
set -u
G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json; T=/scratch/jjyeung/k1/run_tower_sam_2; PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
ls pred_gpu/$MODEL | wc -l
cat > logs/price_$MODEL.sh <<EOS
cd $G
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 TMPDIR=$G/tmp MPLCONFIGDIR=$G/tmp/mpl
$PY -B k1towers/k1_convert.py --model $MODEL --pred pred_gpu/$MODEL --manifest $M --towers $T --out $G/geom > logs/convert_$MODEL.log 2>&1
echo EXIT \$? >> logs/convert_$MODEL.log
ARMS=""; for a in \$(ls -d $G/geom/${MODEL}_*/); do n=\$(basename \$a); ARMS="\$ARMS --arm \$n=\$a"; done
echo ARMS \$ARMS >> logs/convert_$MODEL.log
cd harness
for i in 0 1 2 3; do $PY -B k1_price.py --out out_$MODEL --fits e3_FITS.json --no-reference --shard \$i/4 \$ARMS > ../logs/price_${MODEL}_\$i.log 2>&1 & done
wait
echo PRICE_DONE >> ../logs/convert_$MODEL.log
EOS
tmux new-session -d -s b14_price_$MODEL "bash $G/logs/price_$MODEL.sh"
sleep 60; cat logs/convert_$MODEL.log | tail -5; tail -n1 logs/price_${MODEL}_0.log
