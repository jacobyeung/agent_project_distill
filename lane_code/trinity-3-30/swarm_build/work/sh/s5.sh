K=/scratch/jjyeung/orch_n30/sb_cachk; free -g | awk '/Mem/{print "avail",$7}'; ls $K/out/v2/price 2>&1 | head
cat > $K/work/price_s5.sh <<'Y'
set -euo pipefail
K=/scratch/jjyeung/orch_n30/sb_cachk; cd $K; export PYTHONNOUSERSITE=1
echo "start $(date -u +%FT%TZ)"
bash kit_v2/run_cpu.sh p1cpu mc_price.py $K/out/v2/track/S_A0_D64 $K/out/v2/price/S_A0_D64 all
echo "priced $(date -u +%FT%TZ)"
bash kit_v2/run_cpu.sh p1cpu mc_summary.py final
echo "done $(date -u +%FT%TZ) rc=$?"
Y
tmux new-session -d -s sb_carryprice "bash $K/work/price_s5.sh > $K/work/price_s5.log 2>&1; echo EXIT \$? >> $K/work/price_s5.log"
sleep 45; tail -5 $K/work/price_s5.log
