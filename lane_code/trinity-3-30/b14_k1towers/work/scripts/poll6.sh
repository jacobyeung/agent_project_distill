G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u; free -g | sed -n 2p
for m in mapanything da3; do echo "== $m"; cat pred_cpu/$m/progress.jsonl; grep -h -o '"error": "[^"]*' pred_cpu/$m/*/FAILED*.json 2>/dev/null | cut -c1-400; done
echo "== smoke"; tail -c 400 logs/smoke_pi3x.log; cat smoke/pi3x/progress.jsonl 2>/dev/null; grep -h -o '"error": "[^"]*' smoke/pi3x/*/FAILED*.json 2>/dev/null | cut -c1-400
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/cpu_check.py $M pred_cpu scannet/scene0201_02
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/cpu_check.py $M smoke scannet/scene0201_02
ls harness/out_ref/captures | wc -l; tail -1 logs/ref_*.log
