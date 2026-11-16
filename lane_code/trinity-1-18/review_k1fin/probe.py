import sys,json,builtins,importlib.util,io
from pathlib import Path
sys.dont_write_bytecode=True
FK='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/finalize_k1.py'
spec=importlib.util.spec_from_file_location('fk',FK); fk=importlib.util.module_from_spec(spec); spec.loader.exec_module(fk)
seen=[]
_o=builtins.open; _rb=Path.read_bytes; _io=io.open
def o(f,*a,**k):
    seen.append(str(f)); return _o(f,*a,**k)
def rb(self): seen.append(str(self)); return _rb(self)
builtins.open=o; Path.read_bytes=rb
m=fk.finalize(fk.load_bundle())
builtins.open=_o; Path.read_bytes=_rb
print('flags',m['production_ready'],m['frame_staging_authorized'])
print('k1_frames accesses',sum('k1_frames' in s for s in seen),'total opens',len(seen))
print(sorted(set(s for s in seen if 'site-packages' not in s and '/lib/python' not in s))[:40])
# token-map gate with a selected canonical removed
orig=fk.PATHS['tokens']; rows=[json.loads(l) for l in open(orig) if l.strip()]
sel=m['captures'][5]['canonical']
dst=Path('mut/tok_dropsel.jsonl'); dst.write_text(''.join(json.dumps(r)+'\n' for r in rows if r['canonical']!=sel))
fk.PATHS['tokens']=dst
try: fk.finalize(fk.load_bundle()); print('tok_dropsel: NO REFUSAL')
except Exception as e: print('tok_dropsel refused:',e)
