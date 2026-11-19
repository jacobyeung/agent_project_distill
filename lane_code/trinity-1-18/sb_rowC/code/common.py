import os,sys,json,hashlib,re,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19')
TREE=W/'work/tree_r1'
sys.path.insert(0,str(TREE));sys.dont_write_bytecode=True
from student_pilot import ground_rows,r1_rooms,r1_counting,r1_training,trace_grammar
from student_pilot.s1_exclusions import Exclusions
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
from evalpath.run import score_item
SRC=ROOT/'in/b12/out/PACKET_b12_v4/count_total.jsonl'
PINS={}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):
 p=Path(p).resolve();d={'path':str(p),'sha256':sha(p)};PINS[str(p)]=d['sha256'];return d
def dump(p,d):
 Path(p).write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def jload(p):pin(p);return json.loads(Path(p).read_text())
def norm(s):return re.sub(r'\s+',' ',str(s).strip().lower().replace('_',' '))
def setup_rooms():
 pins={k:pin(W/'work/build17/inputs'/f'{v}.json') for k,v in r1_rooms.AUTHORITY.items()}
 rooms=r1_rooms.Rooms(pins)
 dp=pin(W/'fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json');assert dp['sha256'].startswith('969cdb56')
 bp=pin(W/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json');assert bp['sha256'].startswith('3119aa4a')
 ex=Exclusions(dp,bp)
 wp=W/'fixtures/work/shared/WITHHELD_ROOMS_80.json';wh=jload(wp);assert PINS[str(wp)].startswith('634820b4')
 # Physical-room equivalence comes from N's pinned resolver, never from inferred aliases.
 prefixes={'d1':'scannet','d2':'scannetpp','scannetppv2':'scannetpp','d3':'arkitscenes'}
 def asroom(name):
  ds,sc=name.split('/',1);ds=prefixes.get(ds,ds)
  if ds=='arkitscenes' and sc.startswith(('venue','capture')):return ds+'/'+sc
  if ds=='scannet' and re.fullmatch('scene[0-9]+',sc):return ds+'/'+sc
  if ds in ('scannet','scannetpp','arkitscenes'):
   can=rooms.aliases.get({'scannet':'d1','scannetpp':'d2','arkitscenes':'d3'}[ds]+'/'+sc,ds+'/'+sc)
   try:return rooms.room(can)
   except ValueError:return None
  return None
 blocked={k:{z for n in names if (z:=asroom(n))} for k,names in ex.names.items()}
 wn=set(wh['rooms'])|{x for vs in wh['aliases'].values() for x in vs};blocked['withheld']={z for n in wn if (z:=asroom(n))}
 def status(row):
  st,can,how=rooms.status(row)
  if st!='ok':return st
  room=rooms.room(can)
  for k,v in blocked.items():
   if room in v:return k
  m=ex.matched(ex.identifiers(row))
  if any(m.values()):return next(k for k,v in m.items() if v)
  return 'ok'
 return rooms,status,blocked

def identity(row):
 si=row['student_input']
 return candidate_identity(dict(qid=row['qid'],scene=row['scene'],frame_indices=si['frame_indices'],type=row['question_type'],question=si['question'],options=si['options'],trace_revision='3.14'))

def native_pack_check(row):
 # The store contains direct rows, whereas ground_rows.pack takes ground records.
 # Bridge only serialization: preserve every thought byte, option, answer, scene and pin;
 # use an empty event list, and wrap the existing final letter/number in answer tags.
 si=row['student_input'];ans=str(row['answer']);tail='\n\n'+ans
 assert row['target'].endswith(tail)
 suffix=row['target'][:-len(tail)]+'\n<answer>'+ans+'</answer>'
 rec=dict(spec_version='3.14',trace_revision='3.14',qid=row['qid'],candidate_id=identity(row),scene=row['scene'],
          frame_indices=si['frame_indices'],type=row['question_type'],question=si['question'],options=si['options'],
          answer=ans,gt_answer=ans,suffix=suffix,events=[],gt_agrees=True,training_admitted=False,not_seen=False)
 if si['options']:rec['answer_content']=next(o[3:] for o in si['options'] if o.startswith(ans+'. '))
 packed=ground_rows.pack(rec,row['provenance']);ground_rows.validate(packed)
 assert packed['target'].split('</think>')[0]==row['target'].split('</think>')[0]
 return packed

def status(text):(ROOT/'STATUS.md').write_text(text+'\n')
