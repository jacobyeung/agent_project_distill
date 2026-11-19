"""Strict source parser and independent annotation check adapted from sb_rowT."""
import collections,hashlib,json,re,unicodedata
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def jload(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def norm(x):return ' '.join(unicodedata.normalize('NFKC',x).casefold().split())
class Refusal(ValueError):pass

def need(v,why):
 if not v:raise Refusal(why)
LIST_PATTERNS=[
 r'list each distinct (.+?) once, by the frame where it first appears',
 r'locate each distinct (.+?) at its first appearance',
 r'list the distinct (.+?) instances by first appearance',
 r'find each distinct (.+?), using its first-seen frame',
]
QUESTION_PATTERNS=[
 r'How many (.+?) do we have in this room\?',
 r'How many (.+?) are there in this room\?',
 r'How many (.+?) are there in the room shown in the video\?',
 r'Count the (.+?) in this room\. How many are there\?',
 r'Based on the video, give the number of (.+?) in this room\.',
 r'Count the (.+?) in this room\. What is the total\?',
 r'What is the total count of (.+?) in the room depicted by the video\?',
 r'How many objects are there altogether among the (.+?) in this room\?',
 r'What is the total number of (.+?) in this room\?',
 r'Count the (.+?) in this room together\. How many are there in total\?',
 r'How many (.+?) are in this room in total\?',
]
ENTRY=re.compile(r'frame ([0-9]+)(?: \((left|middle|right)\))?')
def parse(r):
 question=r['student_input']['question'];ask=None
 for pat in QUESTION_PATTERNS:
  m=re.fullmatch(pat,question)
  if m:
   ask=m[1];break
 need(ask is not None,'unparsed_question')
 names=[s.removesuffix('(s)') for s in ask.split('(s) and ')]
 need(len(names)==len(set(names)),'duplicate_asked_category')
 cats={};text=r['target'].replace('\\n','\n')
 for line in text.splitlines():
  m=re.fullmatch(r'Step [0-9]+: (.*?): (frame .*?)\.',line)
  if not m:continue
  name=None
  for pat in LIST_PATTERNS:
   h=re.fullmatch(pat,m[1])
   if h:name=h[1];break
  need(name is not None,'unparsed_list_header')
  need(name not in cats,'duplicate_category_section')
  entries=[]
  for entry in m[2].split('; '):
   t=ENTRY.fullmatch(entry);need(t is not None,'unparsed_instance')
   frame=int(t[1]);need(1<=frame<=32,'frame_outside_1_32')
   entries.append((frame,t[2] or ''))
  cats[name]=entries
 need(set(cats)==set(names),'asked_category_missing_or_extra')
 need(all(cats.values()),'empty_category')
 need(re.fullmatch(r'[0-9]+',str(r['answer'])),'noninteger_answer')
 need(sum(map(len,cats.values()))==int(r['answer']),'sum_answer_mismatch')
 need(text.endswith('\n</think>\n\n'+str(r['answer'])),'source_final_answer_mismatch')
 if 'count_arity' in r:need(len(cats)==r['count_arity'],'count_arity_mismatch')
 return [(name,cats[name]) for name in names]

def independent_truth(r,cats):
 """Recount structured annotated identities, separately from text parsing/grouping."""
 p=r['provenance'];expected={};basis=''
 if 'total_categories' in p:
  basis='provenance.total_categories'
  for c in p['total_categories']:
   ids=c['ids'];frames=c['frames']
   need(len(ids)==len(set(ids))==len(frames),'annotation_duplicate_id_or_length')
   expected[c['name']]=collections.Counter(frames)
 elif 'instances' in p:
  basis='provenance.instances';inst=p['instances'];ids=[x['id'] for x in inst]
  need(len(ids)==len(set(ids)),'annotation_duplicate_id_or_length')
  need(len(cats)==1,'single_annotation_multiple_categories')
  expected[cats[0][0]]=collections.Counter(x['frame'] for x in inst)
  need(collections.Counter((x['frame'],x['region']) for x in inst)==collections.Counter(cats[0][1]),'region_annotation_mismatch')
 elif r.get('retrace_a2',{}).get('cited') is not None:
  basis='retrace_a2.cited';need(len(cats)==1,'single_annotation_multiple_categories')
  expected[cats[0][0]]=collections.Counter(r['retrace_a2']['cited'].values())
 else:raise Refusal('MISSING_independent_instance_annotations')
 need(set(expected)=={name for name,_ in cats},'annotation_category_mismatch')
 for name,entries in cats:
  need(expected[name]==collections.Counter(f for f,_ in entries),'annotation_frame_inventory_mismatch')
 need(sum(sum(v.values()) for v in expected.values())==int(r['answer']),'annotation_truth_mismatch')
 return basis

