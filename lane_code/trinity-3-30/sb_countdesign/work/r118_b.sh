set -u
T=/scratch/jjyeung/n30_mirror/b08_headrows/b08_partA.tar
echo ---PERITEM
tar xOf $T out/CHOICE.per_item.jsonl | python3 -c "
import sys, json
n=0; first=True
for l in sys.stdin:
    r=json.loads(l)
    if first:
        print('KEYS', sorted(r.keys())); first=False
    t=str(r.get('type') or r.get('question_type') or r.get('qtype') or r.get('t'))
    if 'count' in t:
        n+=1; print(json.dumps(r, separators=(',',':'))[:1200])
print('NCOUNT', n)
"
echo ---B10DATA
R=/scratch/jjyeung/orch_n30/b10_reserve
ls -la $R/data_cache $R/data_cache/* 2>&1 | head -30
ls -la $R/out $R/out/qsets 2>&1 | head -60
ls $R/frames/scannetpp 2>/dev/null | wc -l
echo ---GENQ
grep -n -i 'count\|visib\|8 *px\|min_px\|def ' $R/code/gen_questions.py | head -120
echo ---K1LIST
ls -la /scratch/jjyeung/orch_n30/sb_k1list /scratch/jjyeung/orch_n30/gt_rasters /scratch/jjyeung/orch_n30/sb_inventory 2>&1 | head -60
