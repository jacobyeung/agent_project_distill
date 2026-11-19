import hashlib,json,re,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/scratch/jjyeung/orch_n30/sb_rowC')
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
AUDIT=Path('/scratch/jjyeung/orch_n30/sb_auditfix2')
STORE=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
SRC=BASE/'in/b12/out/PACKET_b12_v4/count_total.jsonl'
sys.dont_write_bytecode=True
sys.path.insert(0,str(TREE))
PINS={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):
 p=Path(p).resolve()
 if not p.is_file():raise FileNotFoundError('MISSING: '+str(p))
 PINS[str(p)]=sha(p);return {'path':str(p),'sha256':PINS[str(p)]}
def load(p):
 pin(p);return json.loads(Path(p).read_text())
def dump(p,x):
 Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def rows(p):
 pin(p)
 with Path(p).open() as f:
  for line in f:
   if line.strip():yield json.loads(line)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def code_pins():
 for mod in list(sys.modules.values()):
  p=getattr(mod,'__file__',None)
  if p and (Path(p).resolve().is_relative_to(TREE) or Path(p).resolve().is_relative_to(ROOT/'code')) and Path(p).is_file():pin(p)
def status(s):(ROOT/'STATUS.md').write_text(s+'\n')
def thought(r):return r['target'].split('<think>',1)[1].split('</think>',1)[0]
def identity(row):
 from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
 si=row['student_input']
 return candidate_identity(dict(qid=row['qid'],scene=row['scene'],frame_indices=si['frame_indices'],type=row['question_type'],question=si['question'],options=si['options'],trace_revision='3.14'))
def native_pack_check(row):
 from student_pilot import ground_rows
 si=row['student_input'];ans=str(row['answer']);tail='\n\n'+ans
 assert row['target'].endswith(tail)
 suffix=row['target'][:-len(tail)]+'\n<answer>'+ans+'</answer>'
 rec=dict(spec_version='3.14',trace_revision='3.14',qid=row['qid'],candidate_id=identity(row),scene=row['scene'],frame_indices=si['frame_indices'],type=row['question_type'],question=si['question'],options=si['options'],answer=ans,gt_answer=ans,suffix=suffix,events=[],gt_agrees=True,training_admitted=False,not_seen=False)
 if si['options']:rec['answer_content']=next(o[3:] for o in si['options'] if o.startswith(ans+'. '))
 packed=ground_rows.pack(rec,row['provenance']);ground_rows.validate(packed)
 assert thought(packed)==thought(row)
 return packed
