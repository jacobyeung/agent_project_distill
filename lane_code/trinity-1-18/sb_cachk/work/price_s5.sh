set -euo pipefail
K=/scratch/jjyeung/orch_n30/sb_cachk; cd $K; export PYTHONNOUSERSITE=1
echo "start $(date -u +%FT%TZ)"
bash kit_v2/run_cpu.sh p1cpu mc_price.py $K/out/v2/track/S_A0_D64 $K/out/v2/price/S_A0_D64 all
echo "priced $(date -u +%FT%TZ)"
bash kit_v2/run_cpu.sh p1cpu mc_summary.py final
echo "done $(date -u +%FT%TZ) rc=$?"
