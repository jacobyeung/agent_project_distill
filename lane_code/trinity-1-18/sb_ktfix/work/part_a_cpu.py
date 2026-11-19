"""Run Part A on every train capture with stored C64 on both sides: CPU self-comparison only."""
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
import evaluate_v2 as E,evaluate
from replay import price,load_selector
from unittest.mock import patch
from contextlib import ExitStack
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
sha(__file__);pins=code_pins();start=time.monotonic()
roster=E.captures('train');dest=ROOT/'out/fix_validation/part_a';dest.mkdir(parents=True,exist_ok=True)
# The only substituted input is C32: use the identical stored C64 tensor and metadata.
original_capdir=E.capdir;original_npz=E.npz;original_tower=E.stored_tower
by_path={str(original_capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2')/'tower.npz'):c for c in roster}
last={};prices={};head=load_selector()
def tower(c):
 if last.get('capture')!=c['canonical']:
  last.clear();prices.clear();last.update(capture=c['canonical'],tower=original_tower(c))
  print('CAPTURE',c['canonical'],flush=True)
 return last['tower']
def npz_cpu(path):
 c=by_path.get(str(path))
 return tower(c) if c is not None else original_npz(path)
def dir_cpu(c,root):
 return original_capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2' if Path(root)==dest/'captures/A' else root)
def price_cpu(c,g,cache=None,gt=None,**kwargs):
 key=gt is not None
 if key not in prices:prices[key]=price(c,g,cache=cache,gt=gt,head=head,**kwargs)
 return prices[key]
def items_cpu(rows,part,split):
 write_json(dest/'ITEM_RECEIPT.json',dict(role='CPU_SELF_COMPARISON_ONLY',rows=len(rows),rows_sha256=digest(clean(rows))))
with ExitStack() as stack:
 for name,value in dict(OUT=dest,capdir=dir_cpu,npz=npz_cpu,stored_tower=tower,price=price_cpu,items_file=items_cpu).items():stack.enter_context(patch.object(E,name,value))
 stack.enter_context(patch.object(evaluate,'OUT',dest))
 result=E.run_a()
decision=read_json(dest/'DECISION.json');scale=read_json(dest/'A_SCALE.json')
checked=[r for r in result['scales'] if r['relative_error'] is not None]
no_export=[r for r in result['scales'] if r.get('status')=='NO_CONVERT_EXPORT']
summary=dict(role='CPU_SELF_COMPARISON_ONLY: stored C64 versus itself; does not choose context',complete=result['complete'],captures=len(result['pose']),rows_per_arm={a:sum(r['arm']==a for r in result['rows']) for a in sorted({r['arm'] for r in result['rows']})},bars=decision['bars']['A'],scale_checked=len(checked),scale_max_relative_error=max(r['relative_error'] for r in checked),agreement_fraction=scale['agreement_fraction'],no_convert_export=no_export,no_convert_export_rows=sum(r['arm']==E.arm(32,32,'today') and r['capture'] in {s['capture'] for s in no_export} for r in result['rows']),missing=result['missing'],seconds=time.monotonic()-start,code_sha256=digest(pins))
write_json(ROOT/'out/fix_validation/part_a_summary.json',summary)
assert summary['complete'] and summary['captures']==239 and summary['scale_checked']==237
assert {r['capture'] for r in no_export}=={'scannetpp/0f69aefe3d','scannetpp/2c7c10379b'}
assert summary['bars']['context_pays_pose']=='FAIL' and summary['bars']['lifting']['status']=='FAIL'
assert all(n==1037 for n in summary['rows_per_arm'].values())
print(json.dumps(clean(summary)),flush=True)
