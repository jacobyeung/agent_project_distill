"""Fixed object programs. Grounder supplies reader responses and instance metadata."""
import re
from itertools import combinations
import numpy as np
from common import Missing

def key(x):return str(x).strip().lower()
def options(item):
 out={}
 for x in item['options']:
  m=re.fullmatch(r'([A-Z])[.)]\s*(.+)',x.strip());
  if not m:raise ValueError('Malformed option: '+x)
  out[m[1]]=key(m[2])
 return out

def operands(item):
 q=item['question'];t=item['question_type']
 if t=='object_counting' and 'altogether among the ' in q:
  m=re.fullmatch(r'How many objects are there altogether among the (.+?)\(s\) and (.+?)\(s\) in this room\?',q)
  if not m:raise ValueError('Unparsed multi-name counting')
  return [key(n) for n in m.groups()]
 if t=='object_counting':m=re.fullmatch(r'How many (.+?)(?:\(s\))? do we have in this room\?',q)
 elif t=='object_size_estimation':m=re.search(r'(?:height\) of the|dimension of the|size of the) (.+?), measured in ',q)
 elif t=='object_abs_distance':m=re.search(r'between the (.+?) and the (.+?) \(in meters\)',q)
 elif t=='object_rel_distance':
  m=re.search(r'(?:closest to|farthest from|furthest from) the (.+?)\?',q)
  if not m:raise ValueError('Unparsed relative-distance reference')
  return [key(m[1])]+list(options(item).values())
 elif t=='obj_appearance_order':
  m=re.search(r'categories in the video:\s*(.+?)\?',q)
  if not m:raise ValueError('Unparsed appearance operands')
  return [key(v) for v in m[1].split(',')]
 else:raise ValueError('Unsupported type: '+t)
 if not m:raise ValueError('Unparsed operands: '+q)
 return [key(v) for v in m.groups()]

def parse_order(text,expected=None):
 m=re.search(r'nearest-to-farthest order from (.+?) is:\s*(.+?)\.\s',text.replace('\n',' ')+' ',re.I)
 if not m:return None
 order=[key(x) for x in re.split(r',\s*then\s+|,\s*',m[2])]
 if len(order)!=4 or len(set(order))!=4:return None
 if expected is not None and set(order)!=set(expected):return None
 return key(m[1]),order

def run(item,ground,direct_prediction=None,trace='',variant='fallback'):
 names=operands(item);typ=item['question_type'];members={};refusals=[]
 def get(name):
  obj=ground(name);members[name]=obj.get('frames',[])
  if not obj.get('seen'):refusals.append(name+': '+obj.get('refusal','not seen'))
  return obj
 def out(prediction,reason=None,**kwargs):
  return dict(prediction=prediction,refusal_code=reason,member_frames=members,**kwargs)
 def fallback(reason):return out(None if variant in ('strict','full') else direct_prediction,reason,fallback=variant not in ('strict','full'))
 if typ=='object_counting':
  counts=[get(n).get('count') for n in names];n=sum(counts) if all(c is not None for c in counts) else None
  return out(n,None if n is not None else 'instance count unavailable')
 if typ=='obj_appearance_order':
  objs={n:get(n) for n in names}
  if any(not o.get('seen') or not o.get('frames') or o.get('first') is None for o in objs.values()):return fallback('not seen')
  order=sorted(names,key=lambda n:(objs[n]['first'],objs[n]['tie_index']))
  matches=[a for a,text in options(item).items() if [key(n) for n in text.split(',')]==order]
  if len(matches)!=1:return fallback('no option matches')
  return out(matches[0],first_seen={n:objs[n]['first'] for n in names},first_ties={n:objs[n]['tie_index'] for n in names})
 if typ=='object_rel_distance':
  opts=options(item);ref=names[0];far=item.get('subtype') in ('farthest','furthest') or bool(re.search(r'\b(farthest|furthest)\b',item['question']))
  if variant=='full':candidates=list(opts.values())
  else:
   parsed=parse_order(trace,opts.values())
   if parsed is None or parsed[0].removeprefix('the ')!=ref:return fallback('trace order unavailable')
   candidates=parsed[1][-2:] if far else parsed[1][:2]
  objs={n:get(n) for n in [ref]+candidates}
  if any(not o.get('box_available') for o in objs.values()):return fallback('ground refused')
  gaps={n:ground.gap(ref,n) for n in candidates}
  if any(v is None for v in gaps.values()):return fallback('gap refused')
  winner=(max if far else min)(candidates,key=lambda n:gaps[n]);answer=next(k for k,v in opts.items() if v==winner)
  return out(answer,gaps=gaps,changed=answer!=direct_prediction)
 objs=[get(n) for n in names]
 if any(not o.get('box_available') for o in objs):return out(None,'box unavailable')
 if typ=='object_abs_distance':
  value=ground.gap(*names);return out(value,None if value is not None else 'gap refused')
 if typ=='object_size_estimation':
  unit=item['unit'];factors={'m':1.,'cm':100.,'mm':1000.,'ft':1/0.3048,'in':1/0.0254}
  if unit not in factors:raise Missing('Unregistered unit '+unit)
  return out(max(objs[0]['printed_lengths'])*factors[unit])
 raise ValueError(typ)

def first_seen(items,grounds):
 records=[];pairs=[]
 for item in items:
  if item['question_type']!='obj_appearance_order':continue
  truth=item['gt']['first_pos_f32'];pred={}
  true_order=[key(n) for n in options(item)[item['answer']].split(',')];rank={n:i for i,n in enumerate(true_order)}
  if set(rank)!=set(truth):raise ValueError('GT order option differs from first-seen object set')
  for name,gt in truth.items():
   o=grounds[item['qid']](key(name));f=o.get('first');pred[name]=(f,o.get('tie_index'))
   records.append(dict(qid=item['qid'],scene=item['scene'],object=name,truth=gt,prediction=f,exact=f==gt,within_one=f is not None and abs(f-gt)<=1))
  for a,b in combinations(truth,2):
   pa,pb=pred[a],pred[b];eligible=truth[a]!=truth[b]
   ok=pa[0] is not None and pb[0] is not None and ((pa<pb)==(rank[a]<rank[b]))
   pairs.append(dict(qid=item['qid'],a=a,b=b,gt_tie=not eligible,correct=bool(ok)))
 n=len(records);pp=[p for p in pairs if not p['gt_tie']]
 return dict(objects=records,pairs=pairs,n_objects=n,exact=sum(r['exact'] for r in records)/n if n else None,within_one=sum(r['within_one'] for r in records)/n if n else None,pair_correct=sum(p['correct'] for p in pairs)/len(pairs) if pairs else None,pair_denominator=len(pairs),non_tied_pair_correct=sum(p['correct'] for p in pp)/len(pp) if pp else None,non_tied_pair_denominator=len(pp))
