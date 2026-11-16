"""Prepare, run, resume and compare one frozen variant; all data paths are local."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
from variantlib import *
import argparse,subprocess

def planning(a,m):
 name=a.variant;spec=SPECS[name];pins={};prompt_frames=0;encode_frames=0;tile_calls=0;extra_calls=0
 for c in m['captures']:
  p=Path(a.baseline_cache)/(c['scene'].replace('/','__')+'.npz');pins[c['scene']]=sha(p);raw=load_cache(p)
  if spec['mode']=='dense':prompt_frames+=len(c['phrases'])*32;encode_frames+=32
  elif spec['mode'] in ('aliases','dense_aliases'):
   n=sum(len(aliases(ph)) for ph in c['phrases']);prompt_frames+=n*32;encode_frames+=32 if n else 0;extra_calls+=n
  elif 'tiles' in spec['mode']:
   # Student coverage is unknown at plan time. The SAM-ranked count is an upper bound.
   n=sum(min(4,sum(not raw['frames'][str(k)]['phrases'][ph]['instances'] for k in range(32))) for ph in c['phrases']);prompt_frames+=n*4;encode_frames+=n*4;tile_calls+=n*4
 baseline_frames=m['detect_calls']*32;enc_base=len(m['captures'])*32
 minutes=22.4*(.75*prompt_frames/baseline_frames+.25*encode_frames/enc_base)
 if name in ('dense','dense_aliases'):minutes*=1.2
 if name in ('baseline','dense_link05'):minutes=0
 presence_minutes=baseline_frames/8/60 if name=='student_tiles' else 0
 base_bytes=sum((Path(a.baseline_cache)/(c['scene'].replace('/','__')+'.npz')).stat().st_size for c in m['captures'])
 return pins,dict(variant=name,baseline_minutes=22.4,baseline_captures=len(m['captures']),baseline_prompt_frames=baseline_frames,new_prompt_frames=prompt_frames,new_encoded_frames=encode_frames,extra_prompt_calls=extra_calls,tile_images=tile_calls,sam_gpu_minutes_estimate=minutes,student_gpu_minutes_estimate=presence_minutes,total_gpu_minutes_estimate=minutes+presence_minutes,estimate_method='22.4 min * (0.75 prompt-frame ratio + 0.25 encoded-frame ratio); dense adds 20%; tiles/student upper workload; PRES32 8 calls/s; excludes model load',estimated_cache_bytes=base_bytes*(1 if name=='baseline' else 5 if 'tiles' in name else 4 if name.startswith('dense') else 3),cache_hard_cap_bytes=500_000_000,baseline_cache_bytes=base_bytes,unmeasured=True)

def call(cmd):
 print('RUN', ' '.join(map(str,cmd)),flush=True);r=subprocess.run(list(map(str,cmd)))
 if r.returncode:raise SystemExit(r.returncode)

def guarded(cmd,out,review=False):
 from launch_guard import supervise
 out=Path(out)
 if (out/'HALTED.json').exists() and not review:raise ValueError('HALTED; operator review required')
 rc=supervise(list(map(str,cmd)),out)
 if rc:raise SystemExit(rc)

def main(a):
 base=Path(a.manifest);m=json.loads(base.read_text());validate_manifest(m);check_prompt_provenance(m,rows(a.items));root=scratch(a.out);root.mkdir(parents=True,exist_ok=True);name=a.variant;dest=root/name;dest.mkdir(exist_ok=True)
 pins,estimate=planning(a,m);dump(dest/'ESTIMATE.json',estimate);print(json.dumps(estimate),flush=True)
 if a.stage=='plan' and name=='student_tiles' and not a.presence:
  dump(dest/'PLAN.json',dict(baseline_manifest_sha256=sha(base),variant=name,spec=SPECS[name],presence_required_before_manifest_seal=True));return
 presence=a.presence
 if not presence and (dest/'presence/PRESENCE.jsonl').exists():presence=str(dest/'presence/PRESENCE.jsonl')
 if name=='student_tiles' and a.stage in ('gpu','all') and not presence:
  if not a.student_python or not a.student_checkpoint:raise ValueError('Provide --presence or --student-python and --student-checkpoint')
  po=dest/'presence';cmd=[a.student_python,'-I','-s',HERE/'presence_run.py','--manifest',base,'--frames',a.frames,'--checkpoint',a.student_checkpoint,'--out',po]
  if a.review_halt:cmd+=['--review-halt']
  guarded(cmd,po,a.review_halt);presence=str(po/'PRESENCE.jsonl')
 dense=None
 if name in COMBOS:
  if not (root/'dense/candidates/COMPLETE.json').exists():
   if a.stage=='plan':dump(dest/'PLAN.json',dict(baseline_manifest_sha256=sha(base),variant=name,spec=SPECS[name],dense_source_required_before_manifest_seal=True));return
   raise ValueError('Run and complete the dense variant first; the combo manifest pins its output')
  dense=dense_source(root/'dense/candidates')
 vm=make_manifest(m,name,sha(base),pins,sha(presence) if presence else None,dense);mp=dest/'MANIFEST.json'
 if mp.exists() and json.loads(mp.read_text())!=vm:raise ValueError('Variant manifest binding differs; use a new output root')
 if name=='baseline':
  # Preserve baseline manifest bytes so its original cache binding remains valid.
  mp.write_bytes(base.read_bytes())
 else:dump(mp,vm)
 if a.stage=='plan':return
 if a.stage in ('gpu','all') and name!='baseline':
  cmd=[a.gpu_python,'-I','-s',HERE/'variant_cache.py','--manifest',mp,'--baseline-cache',a.baseline_cache,'--out',dest/'candidates']
  if name in ('dense_link05','dense_aliases','dense_tiles'):cmd+=['--reuse-dense',root/'dense/candidates']
  if name!='dense_link05':
   if not all((a.frames,a.checkpoint,a.source)):raise ValueError('GPU inference needs --frames --checkpoint --source')
   cmd+=['--frames',a.frames,'--checkpoint',a.checkpoint,'--source',a.source]
  if presence:cmd+=['--presence',presence]
  if a.review_halt:cmd+=['--review-halt']
  guarded(cmd,dest/'candidates',a.review_halt)
 if a.stage in ('cpu','all'):
  cache=a.baseline_cache if name=='baseline' else dest/'candidates';priced=dest/'priced'
  if not (priced/'COMPLETE.json').exists():
   cmd=[a.cpu_python,'-I','-s',HERE/'price_masks.py','--manifest',mp,'--items',a.items,'--head-pins',a.head_pins,'--exports',a.exports,'--cache',cache,'--out',priced]+(['--gt-captures',a.gt_captures] if a.gt_captures else [])+(['--allow-stub'] if a.allow_stub_read else []);call(cmd)
  else:
   receipt=json.loads((priced/'COMPLETE.json').read_text())
   if receipt['manifest_sha256']!=sha(mp) or receipt['per_item_sha256']!=sha(priced/'PER_ITEM.jsonl') or receipt['diagnostics_sha256']!=sha(priced/'MASK_DIAGNOSTICS.jsonl'):raise ValueError('Pricing receipt mismatch')
  if a.official_direct:
   call([a.cpu_python,'-I','-s',HERE/'route_read.py','--items',a.items,'--per-item',priced/'PER_ITEM.jsonl','--direct',a.official_direct,'--out',dest/'routed_read']+(['--allow-stub'] if a.allow_stub_read else []))
  else:call([a.cpu_python,'-I','-s',HERE/'compare.py','--manifest',mp,'--items',a.items,'--direct',a.direct,'--cache',cache,'--priced',priced,'--baseline-program',a.baseline_program,'--gt-captures',a.gt_captures,'--out',dest/'comparison'])

if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__);p.add_argument('--variant',choices=SPECS,required=True);p.add_argument('--stage',choices=['plan','gpu','cpu','all'],default='plan');p.add_argument('--out',required=True)
 # Development defaults apply only to the shipped dev-S1 manifest; a benchmark manifest names every input explicitly.
 DEV=dict(manifest='MANIFEST.json',items='ITEMS.jsonl',head_pins='HEADS.json',direct='DIRECT_ON16k.json')
 for n in ['manifest','items','head-pins','direct','official-direct','baseline-program','gt-captures']:p.add_argument('--'+n)
 for n in ['baseline-cache','exports']:p.add_argument('--'+n,required=True)
 p.add_argument('--allow-stub-read',action='store_true',help='CPU dry runs on stub candidates only')
 for n in ['frames','checkpoint','source','presence','student-checkpoint','student-python']:p.add_argument('--'+n)
 p.add_argument('--gpu-python',default=sys.executable);p.add_argument('--cpu-python',default='/scratch/jjyeung/envs/p1cpu/bin/python');p.add_argument('--review-halt',action='store_true')
 a=p.parse_args()
 if a.manifest is None:
  for k,v in DEV.items():
   if getattr(a,k) is None:setattr(a,k,str(HERE.parent/'out'/v))
  for k in ('baseline_program','gt_captures'):
   if getattr(a,k) is None:p.error('dev-S1 runs need --'+k.replace('_','-'))
 else:
  if a.items is None or a.head_pins is None:p.error('a benchmark manifest needs explicit --items and --head-pins')
  if a.stage in ('cpu','all') and not a.official_direct and not (a.direct and a.baseline_program and a.gt_captures):p.error('pricing a benchmark manifest needs --official-direct (or --direct, --baseline-program and --gt-captures)')
 main(a)
