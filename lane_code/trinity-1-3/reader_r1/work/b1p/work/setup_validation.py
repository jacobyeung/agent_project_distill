from pathlib import Path
import shutil,json
W=Path.cwd();B=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1')
s=(B/'work/replay/replay_patched.py').read_text().replace(str(B/'work/p'),str(W/'out/src'))
(W/'work/replay_patched.py').write_text(s)
s=(B/'work/check_replay.py').read_text().replace("W/'in/replay/",f"Path({str(B/'in/replay')!r})/'").replace("W/'work/p/","W/'out/src/")
(W/'work/check_replay.py').write_text(s)
s=(B/'work/run_existing_full.py').read_text().replace("root=W/'work/b04full'",f"root=Path({str(B/'work/b04full')!r})").replace("'in/pkg/p' if '--baseline' in sys.argv else 'work/p'","'out/baseline' if '--baseline' in sys.argv else 'out/src'")
(W/'work/run_existing_full.py').write_text(s)
(W/'work/pytest_tmp').mkdir(exist_ok=True)
# Summarize only timing fields from the provided proof files.
from collections import defaultdict
vals=defaultdict(list)
def visit(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if isinstance(x,(int,float)) and ('_s' in k or 'seconds' in k) and any(z in k for z in ('g3t','tower','geometry')):vals[k].append(x)
   elif isinstance(x,(dict,list)):visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
proof=B/'work/b04full/out/proofs'
for p in proof.glob('*.json'):
 if p.stat().st_size<20_000_000:visit(json.loads(p.read_text()))
for p in proof.glob('PARITY*.jsonl'):
 for line in p.open():visit(json.loads(line))
import statistics
result={k:dict(n=len(v),mean=statistics.mean(v),minimum=min(v),maximum=max(v)) for k,v in vals.items()}
(W/'out/TIMING_PROOFS.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
