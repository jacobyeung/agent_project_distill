"""Enumerate on-disk scene identifiers without trusting any extra alias mapping."""
import collections,csv,gzip,hashlib,json,re,sqlite3,time
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); M=Path('/scratch/jjyeung/n30_mirror')
inputs={}; candidates={}; other={}; pins={}; errors=[]; seen={}; counts=collections.Counter()
expected={'bdb5d402','634820b4','969cdb56','3119aa4a','4d4736cf'}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def add(ds,sc,src,kind):
 ds={'d1':'scannet','d2':'scannetpp','scannetppv2':'scannetpp','d3':'arkitscenes'}.get(ds,ds)
 valid={'scannet':r'scene\d+_\d+','scannetpp':r'[0-9a-f]{10}','arkitscenes':r'\d+'}
 if ds in valid and re.fullmatch(valid[ds],str(sc)):
  key=ds+'/'+str(sc)
  if key not in candidates:candidates[key]={'source':src,'kind':kind,'literal':str(sc)}
# Native dataset-qualified literals and native captures embedded in file names.
qualified=re.compile(r'(?<![A-Za-z0-9])(?P<ds>scannetppv2|scannetpp|scannet|arkitscenes|d[123])(?:/|__)(?P<sc>scene\d+_\d+|[0-9a-f]{10}|\d+)(?![A-Za-z0-9])')
scn=re.compile(r'(?<![A-Za-z0-9])scene\d+_\d+(?![A-Za-z0-9])')
field=re.compile(r'"(?:scene|scene_id|scan_id|video_id|canonical)"\s*:\s*"([^"\n]+)"')
def scan(text,src,kind='literal in metadata'):
 for m in qualified.finditer(text):add(m['ds'],m['sc'],src,kind)
 for m in scn.finditer(text):add('scannet',m[0],src,kind)
 # Native scene fields have distinguishable formats; opaque v-tokens are never candidates.
 for m in field.finditer(text):
  s=m[1]
  if re.fullmatch('[0-9a-f]{10}',s):add('scannetpp',s,src,'native scene field')
  elif re.fullmatch(r'\d{8}',s):add('arkitscenes',s,src,'native video/scene field')
 # Dataset-labelled paths/lists can contain bare ScanNet++ capture ids.
 if 'scannetpp' in src.lower():
  for s in re.findall(r'(?<![A-Za-z0-9])[0-9a-f]{10}(?![A-Za-z0-9])',text):add('scannetpp',s,src,'ScanNet++ source literal')

def structured(obj,src,ctx=''):
 if isinstance(obj,dict):
  ds=obj.get('dataset',obj.get('data_source',''))
  if isinstance(ds,str):
   for key in ('scene','scene_id','scan_id','video_id','id'):
    if isinstance(obj.get(key),(str,int)):add(ds,str(obj[key]),src,'dataset and scene fields')
  if isinstance(obj.get('other_corpora'),dict):
   for ds,ids in obj['other_corpora'].items():
    if isinstance(ids,list):
     for sid in ids:
      if isinstance(sid,str):other.setdefault(ds+'/'+sid,{'source':src,'kind':'other_corpora scene list'})
  for k,v in obj.items():structured(v,src,k if k in ('scannet','scannetpp','scannetppv2','arkitscenes','d1','d2','d3') else ctx)
 elif isinstance(obj,list):
  for x in obj:structured(x,src,ctx)
 elif isinstance(obj,(str,int)) and ctx:add(ctx,str(obj),src,'dataset-labelled scene list')

inventory=BASE/'work_inventory.txt'; paths=[Path(s) for s in inventory.read_text().splitlines()]
inputs[str(inventory)]={'sha256':digest(inventory),'bytes':inventory.stat().st_size}
manifest=BASE/'work/SCAN_MANIFEST.tsv'
with manifest.open('w') as mf:
 mf.write('sha256\tbytes\tpath\tparse_status\n')
 for p in paths:
  scan(str(p),str(inventory),'path in local inventory')
  if p.suffix not in ('.json','.jsonl','.csv','.tsv','.txt','.md','.py','.gz'):continue
  # gzip metadata only, not arbitrary compressed binaries.
  if p.suffix=='.gz' and not any(x in p.name for x in ('.json','.csv','.txt','.tsv')):continue
  if not (str(p).startswith(str(W)+'/') or str(p).startswith(str(M)+'/') or '/sb_alias/work/' in str(p)):continue
  h=digest(p);sz=p.stat().st_size;counts['files_hashed']+=1;counts['bytes_hashed']+=sz
  if h[:8] in expected:pins.setdefault(h[:8],{'path':str(p),'sha256':h,'bytes':sz})
  if h in seen:
   mf.write(f'{h}\t{sz}\t{p}\tduplicate-content\n');continue
  seen[h]=str(p);counts['unique_contents']+=1
  before=len(candidates)+len(other);status='scanned'
  try:
   op=gzip.open(p,'rt',errors='replace') if p.suffix=='.gz' else p.open(errors='replace')
   with op as f:
    tail=''
    while s:=f.read(2*1024*1024):
     scan(tail+s,str(p));tail=s[-1024:]
   # Structured parsing for named scene lists and kit metadata supports other datasets.
   if p.suffix=='.json' and sz<20*1024*1024 and (re.search(r'scene|split|metadata|alias|exclu|withheld|bench',p.name,re.I) or '/m/k/' in str(p)):
    try:structured(json.loads(p.read_text()),str(p))
    except (ValueError,RecursionError):status='text-only'
   if p.suffix=='.csv' and 'arkit' in p.name.lower():
    with p.open() as f:
     for r in csv.DictReader(f):
      if 'video_id' in r:add('arkitscenes',r['video_id'],str(p),'CSV video_id')
  except Exception as e:
   errors.append({'path':str(p),'error':repr(e)});status='ERROR'
  if len(candidates)+len(other)>before:inputs[str(p)]={'sha256':h,'bytes':sz}
  mf.write(f'{h}\t{sz}\t{p}\t{status}\n')
  if counts['files_hashed']%10000==0:print(dict(counts),'candidates',len(candidates),flush=True)
 # Explicitly scan every rows_a2 SQLite store and v7.
 for p in paths:
  if p.suffix!='.sqlite' or not ('/rows_a2/' in str(p) or str(p)==str(M/'rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')):continue
  h=digest(p);sz=p.stat().st_size;inputs[str(p)]={'sha256':h,'bytes':sz}
  with sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
   for i,raw in c.execute('select i,row from rows order by i'):
    scan(raw,str(p));counts['sqlite_rows']+=1
  mf.write(f'{h}\t{sz}\t{p}\tsqlite-rows\n')
inputs[str(manifest)]={'sha256':digest(manifest),'bytes':manifest.stat().st_size}
inputs[str(Path(__file__).resolve())]={'sha256':digest(Path(__file__)),'bytes':Path(__file__).stat().st_size}
res=dict(schema='local-scene-candidates-v1',command='python work/enumerate_candidates.py',inputs=inputs,candidates=candidates,other_dataset_scenes=other,list_pins=pins,counts=dict(counts),errors=errors,scope='Native scene literals in the local path inventory and all JSON/JSONL/CSV/TSV/TXT/MD/PY metadata (including prior archive indexes), plus gzip text metadata and all rows_a2/v7 SQLite rows. Equal file contents parsed once. Archives themselves are not recursively unpacked. No numeric ranges are generated.')
(BASE/'work/CANDIDATE_SCENES.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
(BASE/'STATUS.md').write_text(f'Candidate enumeration found {len(candidates)} native indoor scene identifiers and {len(other)} other dataset identifiers in local metadata and rows. Exact list hashes found: {sorted(pins)}. The scan records all file digests in work/SCAN_MANIFEST.tsv and each candidate origin in work/CANDIDATE_SCENES.json. Tier C is pending exact-token inversion and overlap checks.\n')
print('DONE',len(candidates),len(other),pins,dict(counts),'errors',errors,flush=True)
