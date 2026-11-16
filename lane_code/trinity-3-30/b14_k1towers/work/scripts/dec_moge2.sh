G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; PY=/scratch/jjyeung/envs/planner_local_v1/bin/python; date -u
tail -n2 logs/convert_moge2.log; for i in 0 1 2 3; do tail -n1 logs/price_moge2_$i.log; done
$PY -c "
import json,collections;s=json.load(open('geom/CONVERT_SUMMARY_moge2.json'));print(collections.Counter(v.split(':')[0]+':'+v.split(':')[1][:50] for v in s['refused']['moge2_scale'].values()))"
ls harness/out_moge2/captures | wc -l
if [ $(ls harness/out_moge2/captures | wc -l) = 296 ]; then
$PY -B k1towers/merge_caps.py harness/out_merged_m harness/out_ref/captures harness/out_moge2/captures
$PY -B k1towers/decide.py harness/out_merged_m out/decide_train_moge2.json | head -60
fi
