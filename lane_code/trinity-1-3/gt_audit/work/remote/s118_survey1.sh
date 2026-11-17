set -u
cd /scratch/jjyeung || exit 1
echo "== host $(hostname -s) $(date -u +%FT%TZ)"
echo "== kit_k1a (maxdepth 3 json/jsonl/py)"; find orch_cd/k1_build/work/kit_k1a -maxdepth 3 \( -name '*.json' -o -name '*.jsonl' -o -name '*.json.gz' -o -name '*.jsonl.gz' -o -name '*.py' \) -printf '%s %p\n' 2>/dev/null | head -120
echo "== e3 harness"; ls -la orch_n30/e3_geom/work/harness 2>&1 | head -40; ls -la orch_n30/e3_geom/out 2>&1 | head -20
echo "== e3 per_item head"; head -c 2500 orch_n30/e3_geom/out/PER_ITEM.jsonl 2>&1; echo
echo "== e3 harness grep paths"; grep -n -E "jsonl|POOL|rows|gt_answer|answer|label" orch_n30/e3_geom/work/harness/harness.py 2>/dev/null | cut -c1-220 | head -60
echo "== k1_ops3 analyses"; ls -la orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/ orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/tables 2>&1 | head -40
echo "== dose_pool out"; ls orch_cd/dose_pool/out 2>&1 | head -60; echo "-- POOL_S1"; ls -la orch_cd/dose_pool/out/POOL_S1 2>&1 | head -60
echo "== gt dirs"; for d in orch_cd/dose_pool/out/t1_gt orch_cd/dose_pool/out/arkit_gt; do ls $d | head -5; ls $d/gt 2>/dev/null | head -3; echo "count $(ls $d/gt 2>/dev/null | wc -l)"; done
echo "== df"; df -h /scratch | tail -1
