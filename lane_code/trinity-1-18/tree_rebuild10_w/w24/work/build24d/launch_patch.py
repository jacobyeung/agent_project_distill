from pathlib import Path
import base64,hashlib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path.insert(0,str(D));from patch import reseal
k=L/'work/build24/kits/n'
(k/'b/h.py').write_text('''import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,checked,seal,write
k=Path(__file__).resolve().parents[1];seal(k)
if len(sys.argv)!=3:raise ValueError('E84')
r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
p=q['config'];cfg=load(checked(p['path'],p['sha256']))
if cfg.get('world_size')!=4 or cfg.get('r1_training',{}).get('init_policy')!='step400_export_weights_fresh_v1':raise ValueError('E85')
write(sys.argv[2],cfg)
''')
p=k/'k/j.json';doc=json.loads(p.read_text());shell=base64.b64decode(doc['payload']).decode()
marker='"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py"'
line='"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"\nrc=${PIPESTATUS[0]}\nif [[ "$rc" == 0 ]]; then\n'
assert shell.count(marker)==1
shell=shell.replace(marker,line+marker).replace('rc=${PIPESTATUS[0]}\nfi\n/usr/bin/python3 -B "$Q_KIT/b/o.py"','rc=${PIPESTATUS[0]}\nfi\nfi\n/usr/bin/python3 -B "$Q_KIT/b/o.py"')
raw=shell.encode();doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(doc))
# Retain the training and config-producer diagnostics in the result bundle.
p=k/'b/o.py';s=p.read_text().replace("('q.log','rooms.log','rooms.json'", "('q.log','rooms.log','rooms.json','h.log','t.log'");p.write_text(s)
print(reseal(k))
