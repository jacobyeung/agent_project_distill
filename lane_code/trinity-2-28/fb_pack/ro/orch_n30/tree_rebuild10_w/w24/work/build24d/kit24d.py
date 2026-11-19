"""Apply the export-only closure and training-config helper to emitted kits."""
from pathlib import Path
import base64,hashlib,json
L=Path(__file__).resolve().parents[2]
def upgrade(k):
    k=Path(k)
    if (k/'b/z.py').exists():(k/'b/z.py').write_bytes((L/'work/build24/joblib.py').read_bytes())
    if (k/'b/a.py').exists():
        (k/'b/i.py').write_bytes((L/'work/build24d/i.py').read_bytes())
        p=k/'b/a.py';s=p.read_text()
        marker=" with scope(request.pop('_paths',{})):\n  r=run(request,root/'q')"
        if marker in s:s=s.replace(marker," sys.path.insert(0,str(kit/'b'))\n from i import refresh\n with scope(request.pop('_paths',{})):\n  request=refresh(request,root/'i')\n  r=run(request,root/'q')")
        p.write_text(s)
    if not (k/'b/t.py').exists():return
    (k/'b/h.py').write_bytes((L/'work/build24d/h.py').read_bytes())
    p=k/'k/j.json';doc=json.loads(p.read_text());s=base64.b64decode(doc['payload']).decode()
    if '"$Q_KIT/b/h.py"' not in s:
        marker='"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py"'
        line='"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"\nrc=${PIPESTATUS[0]}\nif [[ "$rc" == 0 ]]; then\n'
        assert s.count(marker)==1;s=s.replace(marker,line+marker)
        s=s.replace('rc=${PIPESTATUS[0]}\nfi\n/usr/bin/python3 -B "$Q_KIT/b/o.py"','rc=${PIPESTATUS[0]}\nfi\nfi\n/usr/bin/python3 -B "$Q_KIT/b/o.py"')
        raw=s.encode();doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(doc))
    p=k/'b/o.py';s=p.read_text()
    if "'h.log'" not in s:s=s.replace("('q.log','rooms.log','rooms.json'", "('q.log','rooms.log','rooms.json','h.log','t.log'")
    p.write_text(s)
