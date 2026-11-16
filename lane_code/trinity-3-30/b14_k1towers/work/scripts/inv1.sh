set -u
echo "== host"; hostname -s; df -h /scratch | tail -1; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
echo "== kit"; ls -la /scratch/jjyeung/geo_bakeoff_kit; cat /scratch/jjyeung/geo_bakeoff_kit/KIT_SEAL.json 2>/dev/null | head -c 3000; echo
for d in /scratch/jjyeung/geo_bakeoff_kit/*/; do echo "-- $d"; ls $d | head -40; done
echo "== kc?"; ls -d /scratch/jjyeung/*kc* /scratch/jjyeung/geo_bakeoff_kit/kc 2>&1 | head
echo "== k1"; ls /scratch/jjyeung/k1 | head -50; ls /scratch/jjyeung/k1/run_tower_sam_2 | head -20; ls /scratch/jjyeung/k1/run_tower_sam_2 | wc -l
echo "== harness"; ls -la /scratch/jjyeung/orch_n30/e3_geom/work/harness | head -60; du -sh /scratch/jjyeung/orch_n30/e3_geom/work/harness 2>/dev/null
echo "== e3 status"; ls /scratch/jjyeung/orch_n30/e3_geom; cat /scratch/jjyeung/orch_n30/e3_geom/STATUS.md 2>/dev/null | head -80
echo "== geo_k1"; ls -la /scratch/jjyeung/orch_n30/geo_k1 2>&1
echo "== tmux"; tmux ls 2>&1
