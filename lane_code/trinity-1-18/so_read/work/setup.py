from pathlib import Path
import hashlib
import json

L = Path('/scratch/jjyeung/orch_n30/so_read')
A = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
files = []
for sub in ('b/e2e_reader', 'b/parity_kit', 'h1eval'):
    files.extend(p for p in (A/sub).glob('*.py') if p.is_file())
files.extend(p for p in (A/'h1eval/h10').glob('*.py') if p.is_file())
pins = {}
for p in sorted(set(files)):
    dest = L/'work/src'/p.relative_to(A)
    dest.parent.mkdir(parents=True,exist_ok=True)
    raw = p.read_bytes(); dest.write_bytes(raw)
    pins[str(p.relative_to(A))] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
(L/'work/source_pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print('Copied', len(pins), 'small Python source files;',sum(p['bytes'] for p in pins.values()),'bytes.')
