K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K && P=/scratch/jjyeung/envs/p1cpu/bin/python
cp -n c2_rows_meta.json c2_rows_meta.full41.json
$P -B kit/score_c1.py out/30_c1rest32.jsonl out/10_bake32.jsonl out/31_c1all64.jsonl > scores/C1_combined.txt 2>&1; echo "c1 rc $?"; cut -c1-3000 scores/C1_combined.txt | grep -E 'astra|argon'
$P -B kit/score_c2.py out/41_c2audit.jsonl > scores/C2_41.txt 2>&1; echo "c2 rc $?"; cat scores/C2_41.txt | head -80
$P -B - <<'PY'
import json
d = json.load(open('excl/dev_scene_exclusions.json'))
print('scene0666 in dev rooms', 'd1/scene0666' in d['rooms'], 'scene0642', 'd1/scene0642' in d['rooms'])
print([x for x in d['natives'] if 'scene0666' in x or 'scene0642' in x])
PY
