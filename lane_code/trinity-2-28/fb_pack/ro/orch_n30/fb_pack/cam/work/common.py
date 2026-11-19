import os,sys,json,re,copy,gzip,hashlib,ast
from pathlib import Path
from collections import Counter,defaultdict
import route as R
from route import ROOT,BASE,TREE,pin,load,write,rows,status
ROUTE=BASE/'fb_pack/route'
SOURCE=ROUTE/'out/rows/camera_wording.jsonl'
SBA=BASE/'sb_rowA'
# Limit numerical libraries before importing the pinned native tree.
import torch
torch.set_num_threads(8)

def start(script):
 R.COMMAND=R.PREFIX+'work/'+script
 for p in [Path(__file__),ROOT/'work'/script,ROOT/'work/route.py',ROOT/'work/intake_reference.py']:
  pin(p)
 # Capture exact tree code and adjacent data actually opened by native checks.
 seen=set()
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes)):
   p=Path(os.fsdecode(args[0]))
   if p.is_absolute() and p.is_relative_to(TREE):seen.add(p)
 sys.addaudithook(audit)
 return seen

def capture(seen):
 for p in list(seen):
  if p.is_file():pin(p)

def shared_errors(raw):
 from student_pilot.r2_adapters import normalize
 from student_pilot.r2_grammar import legacy_program,shared
 row=normalize(raw);target,_=legacy_program(row)
 body=re.search(r'<think>(.*?)</think>',target,re.S).group(1)
 body=re.sub(r'Call: measure ','I will measure ',body)
 for e in row['events']:
  if e['kind'] in ('ground_call','tool_call','calculator_call'):body=body.replace(e['token'].strip(),'<call>')
 return shared.validate_trace(body,form='program',question=row['question'],n_frames=len(row['student_input']['frames']))

ROT_OLD='wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees.'
ROT_NEW='wrapped to the shortest signed turn, with positive turn meaning left and a half turn reported as positive.'
NEG=re.compile(r'(-d[xyz]) = [+-]?\d+(?:\.\d+)? m(?=[;.])')

def rewrite_text(s):
 ids=[]
 if ROT_OLD in s:s=s.replace(ROT_OLD,ROT_NEW);ids.append('CAM-ROT-WORDS-v1')
 if s.startswith('Scoring each option by the matching component:'):
  s,n=NEG.subn(r'\1',s)
  if n:ids.append('CAM-DIR-SYMBOL-v1')
 return s,ids

def form(line):
 if ROT_OLD in line:return 'rotation_signed_range_and_half_turn'
 if line.startswith('Scoring each option by the matching component:'):return 'direction_component_scores'
 return 'UNCLASSIFIED'

def stage_dependencies(e):
 # Localize only authenticated metadata pins. Never follow image references.
 for v in [*e['exclusions'].values(),e['withheld_rooms'],e['dev_scene_exclusions'],e['extent_receipt'],*e['required_exclusion_pins'].values()]:
  src=Path(v['path'])
  if not src.is_absolute():src=ROUTE/src
  src=src.resolve()
  assert str(src).startswith('/scratch/'),src
  R.staged(pin(src,v['sha256']))
 (ROOT/'u').mkdir(exist_ok=True)
 return e
