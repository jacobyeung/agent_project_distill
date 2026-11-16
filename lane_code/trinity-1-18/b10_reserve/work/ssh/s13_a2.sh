hostname -s
cd /scratch/jjyeung/orch_n30/rows_a2/work 2>/dev/null || exit 0
ls -la BULK_SCENES.json streams/assets_scannetppv2.list 2>&1
python3 - <<'PY'
import json,re
d=json.load(open('BULK_SCENES.json'))
s=json.dumps(d)
print('BULK_KEYS', type(d).__name__, list(d)[:5] if isinstance(d,dict) else '')
ids=sorted(set(re.findall(r'scene\d{4}_\d\d',s))|set(re.findall(r'(?<![0-9a-f])[0-9a-f]{10}(?![0-9a-f])',s)))
print('IDS', ' '.join(ids))
PY
echo LISTIDS $(grep -o -E '/[0-9a-f]{10}/' streams/assets_scannetppv2.list | sort -u | tr -d '/' | tr '\n' ' ')
