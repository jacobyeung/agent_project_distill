K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K && P=/scratch/jjyeung/envs/p1cpu/bin/python
sed -n '/doubted_either_by/,$p' scores/C2_41.txt | tr -d '\n ' | cut -c1-1500; echo
F=/scratch/jjyeung/orch_n30/fb_pack
ls -la $F $F/k1point $F/point $F/point/out 2>&1 | head -60
grep -h -c . $K/faults/*.jsonl 2>/dev/null; ls $K/faults
$P -B - <<'PY'
import json, collections
fin = collections.Counter(); unp = collections.Counter()
for fn in ('out/31_c1all64.jsonl', 'out/30_c1rest32.jsonl', 'out/10_bake32.jsonl', 'out/41_c2audit.jsonl'):
    for l in open(fn):
        r = json.loads(l); fin[(fn[4:7], r['model'].split('/')[-1], r['finish'])] += 1
        if r['usage']['completion'] > 30000: unp[(fn[4:7], r['model'].split('/')[-1])] += 1
print(dict(fin)); print('completion>30k', dict(unp))
PY
