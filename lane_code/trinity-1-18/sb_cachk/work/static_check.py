from pathlib import Path
import sys,json,hashlib,os
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'work/extract/kit_v2'))
import mc_common as C
import mc_dryrun_report as D
import mc_preflight as PF
import torch
torch.set_num_threads(8)
pins={}
def sha(p):
 p=Path(p); h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 pins[str(p)]=h.hexdigest(); return h.hexdigest()
def read(p):
 sha(p); return json.loads(Path(p).read_text())
for p in (ROOT/'work/extract/kit_v2').rglob('*'):
 if p.is_file(): sha(p)
sha(__file__)
st=read(ROOT/'out/v2/STAGING.json'); pop=read(ROOT/'out/v2/POPULATION.json'); fs=read(ROOT/'out/v2/FRAME_SETS.json'); seeds=read(ROOT/'out/v2/seeds/SEEDS.json')
manifest=[]
for line in (ROOT/'out/v2/KIT_MANIFEST.sha256').read_text().splitlines():
 expected,name=line.split(None,1); actual=sha(ROOT/name)
 manifest.append(dict(path=name,equal=expected==actual))
sha(ROOT/'out/v2/KIT_MANIFEST.sha256')
ckpt_sha=sha(C.CHECKPOINT)
sd=torch.load(C.CHECKPOINT,map_location='cpu',weights_only=True,mmap=True)
if 'model' in sd: sd=sd['model']
from collections import Counter
counts=Counter(); bytes_=Counter()
for name,t in sd.items():
 if isinstance(t,torch.Tensor): counts[str(t.dtype)]+=t.numel();bytes_[str(t.dtype)]+=t.numel()*t.element_size()
links=[]
for start in (C.SAM3_ROOT,Path('/scratch/jjyeung/envs/sam3_capretry_native_v1')):
 for d,dirs,files in os.walk(start):
  for n in dirs+files:
   p=Path(d)/n
   if p.is_symlink():
    target=str(p.resolve())
    if target.startswith(('/home/','/data')) or not p.exists(): links.append(dict(path=str(p),target=target,exists=p.exists()))
# Local imports during a CPU-only preflight; CUDA remains hidden.
C.OUT=ROOT/'out/v2'; C.POPULATION=C.OUT/'POPULATION.json'
pop_ok=C.population_digest(pop)==pop['population_id']
result=dict(command='bash kit_v2/run_cpu.sh sam3 ../work/static_check.py',
 archive_kit_equal=True,manifest_files=len(manifest),manifest_mismatches=[x for x in manifest if not x['equal']],
 staging=dict(total_bytes=st['total_bytes'],sum_bytes=sum(i['bytes'] for i in st['items']),check=PF.staging_check(st),bad_symlinks=links,
  limitation='STAGING.json embeds producer absolute paths; regenerate after relocation. OS tools/drivers are node prerequisites.'),
 population=dict(counts=pop['counts'],digest_ok=pop_ok),phrase_provenance_failures=PF.phrase_check(seeds['summary'],C.PHRASE_FOLDS),
 model=dict(checkpoint_sha256=ckpt_sha,keys=len(sd),tensor_elements=dict(counts),tensor_bytes=dict(bytes_),
 estimate=D.memory(64),limitation='Activation/context values are assumptions, not a measured CUDA peak; CPU RSS does not prove GPU peak.'),
 gpu_hours=D.estimate(dict(fs,captures={x['capture']:x for x in fs['captures']}),{x['capture']:x for x in seeds['captures']},pop['track_order'],C.ORDER),input_sha256=pins)
(ROOT/'out/check/STATIC.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
