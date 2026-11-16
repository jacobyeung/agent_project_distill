G=/scratch/jjyeung/orch_n30/geo_k1; K=/scratch/jjyeung/geo_bakeoff_kit; E=/scratch/jjyeung/orch_n30/e3_geom/work/harness
hostname; date -u; nproc; uptime; free -g | head -2; df -h /scratch | tail -1
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader
tmux ls 2>&1
echo == geo_k1; ls -la $G $G/* 2>&1 | head -40
echo == kit; ls $K $K/work $K/runtime 2>&1 | head -30; du -sh $K 2>/dev/null
echo == E3; ls $E | head -40; ls $E/out | head; ls $E/out/captures 2>/dev/null | wc -l
grep -n "^ROOT\|^assert ROOT\|TREE\|^K1\|MANIFEST\|run_tower" $E/harness.py | head -20
cat $E/run.sh | head -30
echo == tree; ls -d /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872 /scratch/jjyeung/envs/planner_local_v1/bin/python 2>&1
echo == k1; ls /scratch/jjyeung/k1 | head; ls /scratch/jjyeung/k1/run_tower_sam_2 | wc -l; ls -la /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
ps -eo user,pcpu,pmem,etime,cmd --sort=-pcpu | head -15 | cut -c1-200
