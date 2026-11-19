W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/work
cat > $W/work/stage.py <<'EOP'
"""Build the symlink stage of N's uploads (same mapping as upload.py): python3 stage.py PKGROOT STAGE"""
import json, os, sys, hashlib
from pathlib import Path
root, stage = Path(sys.argv[1]), Path(sys.argv[2])
v = json.loads((root/'work/build21/UPLOADS.json').read_text()); rows = []
stage.mkdir()
for e in v['files']:
    n = Path(e['opaque_name']); assert not n.is_absolute() and '..' not in n.parts
    local = (root/'work/build21/kits'/n) if n.parts[0] == 'q' else root/'work/build21/upload'/n
    assert local.is_file() and local.stat().st_size == e['bytes'], n
    assert hashlib.sha256(local.read_bytes()).hexdigest() == e['sha256'], n
    t = stage/n; t.parent.mkdir(parents=True, exist_ok=True); os.symlink(local.resolve(), t)
    rows.append([str(n), e['sha256'], e['bytes']])
(stage.parent/(stage.name+'.list.json')).write_text(json.dumps(rows))
print(len(rows), v['total_bytes'])
EOP
nice -n 10 python3 $W/work/stage.py $W/work/conf21c/pkg $W/work/upstage21c && (cd $W/work/upstage21c && nice -n 10 tar -chf $W/work/up21c.tar .) && stat -c %s $W/work/up21c.tar && sha256sum $W/work/up21c.tar $W/work/upstage21c.list.json; tar tf $W/work/up21c.tar | head -5; tar tf $W/work/up21c.tar | wc -l
grep -c . $W/work/upstage21c.list.json; python3 -c "import json;r=json.load(open('$W/work/upstage21c.list.json'));import re;print([x[0] for x in r if re.search('(?i)bench|split|revsi|vsi|distill|qgen|qwen|dataset',x[0])])"
