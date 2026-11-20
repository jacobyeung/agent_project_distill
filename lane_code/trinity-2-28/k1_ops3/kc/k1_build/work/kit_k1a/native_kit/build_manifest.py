"""Bind an explicit admitted row list to source pool records and a dense RGB registry."""
import sys,json,gzip,argparse,collections,re,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B,pipeline as P

def build(request):
 registry=B.load(B.checked(request['scene_registry']))
 admitted=B.load(B.checked(request['admitted_ids']))
 if not isinstance(admitted,list) or len(admitted)!=len(set(admitted)):raise ValueError('Need unique admitted candidate IDs')
 needed=set(admitted);found={};by=collections.defaultdict(list)
 for source in request['pool_sources']:
  path=B.checked(source)
  opener=gzip.open if path.suffix=='.gz' else open
  with opener(path,'rt') as f:
   for line in f:
    r=json.loads(line);key=r.get('candidate_id')
    if key not in needed:continue
    if key in found:raise ValueError('Duplicate source candidate')
    if r['type'] not in P.TYPES:raise ValueError('Admitted list contains unsupported type')
    scene=r['canonical'];capture=registry.get(scene)
    if capture is None:raise ValueError('Dense training frames not bound: '+scene)
    if r['frame_indices']!=capture['anchor_indices']:raise ValueError('Row/dense anchor mismatch')
    operands=[]
    for e in r.get('events',[]):
     match=re.fullmatch(r'<ground obj="([^"]+)" mode="box">',e['call'])
     if match:operands.append(match[1])
    # The source renderer uses meters/m2. Conversion rows require a separate explicit adapter.
    question=r['question']
    if r['type']==P.TYPES[0] and not re.search(r'\bmeters?\b|\bmetres?\b',question,re.I):raise ValueError('Only canonical-meter source rows are supported')
    if r['type']==P.TYPES[1] and not re.search(r'square meters?|square metres?',question,re.I):raise ValueError('Only square-meter source rows are supported')
    try:gt=float(r['gt_answer'])
    except (TypeError,ValueError):raise ValueError('Source GT label is not numeric')
    row=dict(id=key,source_qid=r['qid'],source_pin=source,type=r['type'],question=question,operands=operands,unit='m' if r['type']==P.TYPES[0] else 'm2',gt_value=gt,gt_instances=capture.get('row_gt_instances',{}).get(key,{}))
    if row['operands'] and set(row['gt_instances'])!=set(row['operands']):raise ValueError('GT operand instance identities are unbound')
    if key in registry.get('_fallback_rows',{}):row['fallback']=registry['_fallback_rows'][key]
    by[scene].append(row);found[key]=True
 if set(found)!=needed:raise ValueError('Admitted source row coverage incomplete')
 captures=[]
 for scene,rows in sorted(by.items()):
  c=copy.deepcopy(registry[scene]);c['canonical']=scene;c['rows']=rows
  c.pop('row_gt_instances',None);captures.append(c)
 m=dict(schema='o3-training-cache-v1',synthetic=False,captures=captures,exclusions=B.load(B.checked(request['exclusions'])),gpu=request['gpu'],sources={k:request[k] for k in ['scene_registry','admitted_ids','pool_sources']})
 from run import validate_manifest
 return validate_manifest(m)

if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__);p.add_argument('--request',required=True);p.add_argument('--out',required=True);a=p.parse_args();B.write(a.out,build(B.load(a.request)))
