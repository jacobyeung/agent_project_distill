"""Read-only source census. Never builds or claims a production sampling binding."""
import sys, json, hashlib, sqlite3, gzip, csv, base64, resource
from pathlib import Path
from collections import Counter
resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
W=Path(__file__).resolve().parent; O=W/'out'
T=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
sys.path.insert(0,str(T))
import torch
torch.set_num_threads(8)
from student_pilot import p3_provenance as p
inputs={}; original_pinned=p.pinned

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def track(path, expected=None):
 path=Path(path); h=sha(path)
 if expected is not None:assert h==expected,(path,h,expected)
 inputs[str(path)]={'path':str(path),'sha256':h,'bytes':path.stat().st_size}
 return path

def pinned(pin):
 # Preserve native authentication and record the actual successfully opened path.
 path=original_pinned(pin)
 inputs[str(path)]={'path':str(path),'sha256':pin['sha256'],'bytes':path.stat().st_size}
 return path
p.pinned=pinned
from student_pilot.row_removals import Removals
from student_pilot.r1_population import family
from student_pilot.r1_direction_twins import Binding
from student_pilot.r1_coverage import WordingExclusion
from student_pilot.r1_launch22 import validate_removals
from student_pilot.r1_training import row_check
from student_pilot.s1_exclusions import Exclusions
from student_pilot.r0_exclusion import reserve
from student_pilot.carrier_c1_routing import load_exclusions, excluded
cfg=p.load(track(T.parent.parent/'out/N_LAUNCH_CONFIG.json'))
card=p.load(pinned(cfg['r2_sampling']['card']))
for key in ['population','indices']:pinned(cfg['r2_sampling'][key])
for name in ['TREE_SEAL.json','N_CARD_KIT_ROWS.md','kit_n_go/BUILD.json','kit_n_go/k/n.json']:track(T.parent.parent/'out'/name)
track('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/out/BUILD22_REPORT.md')
for name in ['MANIFEST.json','receipt.json','JOB_PATHS.json']:track(Path(cfg['r1_training']['direction_twins']['source_database']['path']).parent/name)
track(__file__)
validate_removals(cfg); removals=Removals(cfg['remove_files'])
print('Authenticating twins and source rooms',flush=True)
twins=Binding(cfg)
pinned(twins.spec['source_map'])
wording=WordingExclusion(cfg['r1_training']['wording_exclusion'],cfg['r1_training']['camera_wording_exclusion'])
scenes=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
held=p.load(pinned(cfg['exclude_qids']))
benchmark=load_exclusions(cfg['exclusions'])
r0=reserve();track(T/'student_pilot/r0_scenes.json')
counts=Counter(); families=Counter(); rawfamilies=Counter(); per_list=Counter(); errors=Counter(); room_counts=Counter()
columns=['source','source_i','qid','row_sha256','family','question_type','facing','answer','question','options_json','target','source_key','native_dimensions_json']
from student_pilot.r1_direction_twins import dimensions

def process(row,source,i,writer):
 fam=family(row,'vqa');rawfamilies[fam]+=1;counts[source+'_rows']+=1
 match=removals.match(row)
 if not removals.keep(row):
  counts['removed']+=1;per_list[match[0]]+=1;return
 counts['after_removals']+=1
 status,canonical,_=twins.strict.status(row)
 if status=='unresolved':
  canonical,_=twins.tiered.canonical(row)
  if canonical:
   room=twins.strict.room(canonical)
   status='r0' if room in twins.strict.r0 else 'k1_heldout' if room in twins.strict.k1 else 'ok'
 room_counts[status]+=1
 if status!='ok':errors['room:'+status]+=1;return
 if scenes.excluded(row):counts['scene_excluded']+=1;return
 if row['qid'] in held.get('vqa',[]):counts['held_qid']+=1;return
 if excluded(benchmark,row['dataset']+'/'+row['scene'],canonical):counts['benchmark_excluded']+=1;return
 try:
  wording.check(row);row_check(row,'vqa');r0.check(row,'vqa')
 except (ValueError,KeyError,TypeError) as e:
  errors[str(e)]+=1;return
 families[fam]+=1;counts['eligible']+=1
 if fam in ('direction','facing_pairs'):
  si=row.get('student_input',{});record=twins.records.get(row['qid'],{})
  writer.writerow([source,i,row['qid'],p.digest(row),fam,row.get('question_type',''),row.get('facing',''),row.get('answer',''),si.get('question',row.get('question','')),json.dumps(si.get('options',[])),row.get('target',row.get('suffix','')),record.get('source_key',''),json.dumps(dimensions(row))])

print('Streaming base source and native filters',flush=True)
dbpath=Path(twins.spec['source_database']['path'])
conn=sqlite3.connect(dbpath.as_uri()+'?mode=ro&immutable=1',uri=True)
with gzip.open(O/'DIRECTION_ROWS.tsv.gz','wt') as f:
 writer=csv.writer(f,delimiter='\t');writer.writerow(columns)
 for i,raw in conn.execute('SELECT i,row FROM rows ORDER BY i'):
  process(json.loads(raw),'store_v7',i,writer)
  if (i+1)%50000==0:print('base rows',i+1,flush=True)
 conn.close()
 for i,row in enumerate(twins.rows()):process(row,'twins',i,writer)
print('Counts',dict(counts),'families',dict(families),'errors',dict(errors),flush=True)
for module in list(sys.modules.values()):
 path=getattr(module,'__file__',None)
 if path and str(path).startswith(str(T)) and Path(path).is_file():track(path)
evidence=json.loads((O/'EVIDENCE_PIN.json').read_text())
for item in evidence['inputs']:inputs[item['path']]=item
track(O/'EVIDENCE_PIN.json');track(O/'EVIDENCE_S400.md')
raw=dict(status='SOURCE_CENSUS_ONLY',inputs=list(inputs.values()),tree_seal=p.load(T.parent.parent/'out/TREE_SEAL.json'),counts=dict(counts),families=dict(families),raw_families=dict(rawfamilies),room_status=dict(room_counts),validation_errors=dict(errors),removals=[dict(pin=pin,listed=n,first_removed=removals.removed[i],all_matches=removals.matches[i]) for i,(pin,n) in enumerate(zip(removals.files,removals.source_counts))],direction_extract={'path':str(O/'DIRECTION_ROWS.tsv.gz'),'sha256':sha(O/'DIRECTION_ROWS.tsv.gz')},card=card,full_native_reader_population='MISSING: launch binding is an incomplete zero-count placeholder; frame-host preparation is not supplied')
(O/'SOURCE_CENSUS.json').write_text(json.dumps(raw,indent=2)+'\n')
(W/'STATUS.md').write_text('Stage 2: Authenticated the v7 database, 7,971 twins, path-(b) bindings, and all 12 launch removal lists. Streamed the sources through native removal, room, scene, wording, and row-text checks; saved compact direction evidence and input hashes. The production population remains an explicitly incomplete placeholder. Parser validation and bounded weighting calculations follow.\n')
