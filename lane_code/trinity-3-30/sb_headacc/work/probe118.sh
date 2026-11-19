hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1
p() { echo "## $1"; ls "$1" 2>&1 | head -${2:-25}; }
p /scratch/jjyeung/k1 20
echo "## run_tower_sam_2 count"; ls /scratch/jjyeung/k1/run_tower_sam_2 2>/dev/null | wc -l; ls /scratch/jjyeung/k1/run_tower_sam_2 2>/dev/null | head -5
one=$(ls -d /scratch/jjyeung/k1/run_tower_sam_2/*/ 2>/dev/null | head -1); echo "## one tower_sam capture: $one"; ls -la "$one" 2>&1 | head -30
onec=$(ls -d /scratch/jjyeung/k1/run_convert_2/*/ 2>/dev/null | head -1); echo "## one convert capture: $onec"; ls -la "$onec" 2>&1 | head -20
p /scratch/jjyeung/orch_n30/b04host3/lift_price/harness 40
p /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector 40
p /scratch/jjyeung/orch_n30/e3_geom/work/harness 30
p /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd 20
p /scratch/jjyeung/orch_n30/geo_k1 30
p /scratch/jjyeung/orch_n30/geo_k1/geom 10
p /scratch/jjyeung/orch_n30/b11_presence 20
p /scratch/jjyeung/orch_n30/b11_presence/out 30
p /scratch/jjyeung/devs1_frames 5
echo "## devs1_frames count"; ls /scratch/jjyeung/devs1_frames 2>/dev/null | wc -l
p /scratch/jjyeung/devs1_r2 20
ls -la /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json 2>&1
p /scratch/jjyeung/orch_n30 200 | tr '\n' ' '
echo; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader 2>&1 | tr '\n' ';'
