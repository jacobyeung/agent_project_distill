import base64, json, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for p in sorted(src.glob('*.json')):
    v = json.loads(p.read_text())
    if isinstance(v, dict) and 'payload' in v:
        try:
            d = json.loads(base64.b64decode(v['payload']))
        except Exception as e:
            print(p.name, 'nonjson payload', e); continue
        (dst / p.name).write_text(json.dumps(d, indent=1, sort_keys=True) + '\n'); print(p.name, 'decoded', type(d).__name__, list(d)[:12] if isinstance(d, dict) else len(d))
    else:
        print(p.name, 'plain', list(v)[:10] if isinstance(v, dict) else type(v))
