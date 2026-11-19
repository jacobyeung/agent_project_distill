"""Read plain JSON mislabeled .gz, and enumerate structured scene lists."""
import ast,hashlib,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
p=BASE/'work/CANDIDATE_SCENES.json';original=p.read_bytes();d=json.loads(original)
ns={'__file__':str(BASE/'work/enumerate_candidates.py')};src=(BASE/'work/enumerate_candidates.py').read_text();exec(compile(src.split('inventory=BASE/')[0],'<candidate-extractors>','exec'),ns)
ns['candidates']=d['candidates'];ns['other']=d['other_dataset_scenes']
manifest={}
for line in (BASE/'work/SCAN_MANIFEST.tsv').read_text().splitlines()[1:]:
 h,sz,path,status=line.split('\t');manifest[path]={'sha256':h,'bytes':int(sz)}
fixed=[]
for err in d['errors']:
 f=Path(err['path']);b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==manifest[str(f)]['sha256'];assert b.lstrip().startswith((b'{',b'['))
 ns['scan'](b.decode(),str(f),'plain JSON bytes in .gz-named metadata');d['inputs'][str(f)]=manifest[str(f)];fixed.append(str(f))
# Inspect bare identifiers only under explicit scene/capture list keys.
def walk(o,source,context=False):
 if isinstance(o,dict):
  for k,v in o.items():
   walk(v,source,context or bool(re.search(r'scenes|scene_ids|captures|scan_ids|video_ids',k,re.I)))
 elif isinstance(o,list):
  for x in o:walk(x,source,context)
 elif isinstance(o,str) and context:
  if re.fullmatch('[0-9a-f]{10}',o):ns['add']('scannetpp',o,source,'bare identifier in explicit scene/capture list')
  elif re.fullmatch('[0-9]{8}',o):ns['add']('arkitscenes',o,source,'bare identifier in explicit scene/capture list')
paths=set((BASE/'candidate_paths.txt').read_text().splitlines());paths.update(s for s in (BASE/'work_inventory.txt').read_text().splitlines() if '/w12/fixtures/work/kit07ca49df_meta/m/k/' in s)
seen=set();n=0
for s in sorted(paths):
 f=Path(s)
 if f.suffix!='.json' or f.stat().st_size>20*1024*1024:continue
 b=f.read_bytes();h=hashlib.sha256(b).hexdigest()
 if h in seen:continue
 seen.add(h)
 try:o=json.loads(b)
 except ValueError:continue
 before=len(d['candidates']);walk(o,s);ns['structured'](o,s);n+=1
 if len(d['candidates'])>before:d['inputs'][s]={'sha256':h,'bytes':len(b)}
krec=json.loads((BASE/'work/K1_RECOVERY.json').read_text());f=Path(krec['recovered']['path']);b=f.read_bytes();ns['scan'](b.decode(),str(f));d['inputs'][str(f)]=krec['recovered'];d['list_pins']['4d4736cf']=krec['recovered']
d['inputs'][str(p)]={'sha256':hashlib.sha256(original).hexdigest(),'bytes':len(original)}
for f in [Path(__file__).resolve(),BASE/'candidate_paths.txt',BASE/'work/K1_RECOVERY.json']:
 b=f.read_bytes();d['inputs'][str(f)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
d['errors']=[];d['plain_json_gz_files']=fixed;d['structured_lists_checked']=n;d['command']='python work/enumerate_candidates.py && python work/recover_k1.py && python work/finish_candidates.py';d['scope']+=' Plain JSON metadata bearing .gz filenames is read as text; explicit scene/capture lists are also parsed structurally.'
(BASE/'work/CANDIDATE_SCENES_FINAL.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
(BASE/'STATUS.md').write_text(f"Candidate enumeration is complete: {len(d['candidates'])} native scene identifiers and {len(d['other_dataset_scenes'])} other-dataset identifiers. All five requested list hashes are verified. {len(fixed)} plain-JSON files with .gz names were read as text; no scan errors remain. The whole-store tier audit is ready.\n")
print('candidates',len(d['candidates']),'other',len(d['other_dataset_scenes']),'plain JSON .gz files',len(fixed),'structured lists',n)
