hostname -s; date -u +%FT%TZ
for p in /scratch/jjyeung/geo_bakeoff_kit /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh /scratch/jjyeung/geo_bakeoff_kit/runtime/base/bin/python3 \
 /scratch/jjyeung/orch_n30/geo_k1/k1towers /scratch/jjyeung/orch_n30/geo_k1/harness/harness.py /scratch/jjyeung/orch_n30/geo_k1/harness/out_merged_mdp \
 /scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3 /scratch/jjyeung/orch_n30/geo_k1/geom/da3_native /scratch/jjyeung/envs/planner_local_v1/bin/python \
 /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/trace_format/room_v314.py \
 /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json /scratch/jjyeung/k1/run_tower_sam_2 \
 /scratch/jjyeung/orch_n30/b10_reserve /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp /scratch/jjyeung/orch_n30/b10_reserve/out/qsets \
 /scratch/jjyeung/orch_n30/b10_reserve/code /scratch/jjyeung/devs1_r2; do
  if [ -e "$p" ]; then echo "OK   $p"; else echo "MISS $p"; fi
done
ls /scratch/jjyeung/orch_n30/b10_reserve 2>&1 | head -30
ls /scratch/jjyeung/orch_n30/b10_reserve/out/qsets 2>&1 | head -20
ls /scratch/jjyeung/orch_n30/b10_reserve/out 2>&1 | head -30
ls /scratch/jjyeung/orch_n30/b10_reserve/code 2>&1 | head -30
ls /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp 2>/dev/null | wc -l
ls /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp/04d0dc245b 2>/dev/null | wc -l
ls /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp/04d0dc245b 2>/dev/null | head -3
sha256sum /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/trace_format/room_v314.py /scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl /scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_rl_f32.jsonl /scratch/jjyeung/orch_n30/geo_k1/k1towers/k1_infer.py /scratch/jjyeung/orch_n30/geo_k1/k1towers/k1_convert.py /scratch/jjyeung/orch_n30/geo_k1/harness/harness.py 2>&1
ls /scratch/jjyeung/geo_bakeoff_kit 2>&1 | head -20
ls /scratch/jjyeung/orch_n30/geo_k1 2>&1 | head -30
ls /scratch/jjyeung/orch_n30/geo_k1/geom/da3_native 2>/dev/null | wc -l
ls /scratch/jjyeung/devs1_r2 2>&1 | head -20
grep -n -i -E 'room|area|occupancy|closing|pad' /scratch/jjyeung/orch_n30/b10_reserve/code/gen_questions.py 2>/dev/null | cut -c1-220 | head -40
df -h /scratch | tail -1; free -g | sed -n 2p
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | head -12
