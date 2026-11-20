"""VSI-Bench official items for the routed types (abs distance, room size) in kit_combo2 ITEMS format; operands from the official question text."""
import sys,json,collections
from pathlib import Path
KIT=Path(sys.argv[1]);META=Path(sys.argv[2]);OUT=Path(sys.argv[3])
sys.path.insert(0,str(KIT/'work'/'vendor'))
import tplib as T,pool_common as PC
from phrase import normalize_phrase
ROUTED=('object_abs_distance','room_size_estimation')
items=[];bad=[]
for l in META.open():
    r=json.loads(l)
    if r['question_type'] not in ROUTED:continue
    t=r['question_type'];qid='official_'+str(r['id']);scene=r['dataset']+'/'+r['scene_name']
    q=dict(qid=qid,id=qid,question_type=t,question=r['question'],options=r.get('options') or [],answer=r['ground_truth'],released_answer=float(r['ground_truth']),released_options=[],released_answer_in_options=float(r['ground_truth']),native=scene,room=scene,scene=scene,fixed=False,dataset=r['dataset'],stratum='primary',program=dict(question=r['question'],question_type=t,options=r.get('options') or [],id=qid))
    try:
        names=list(T.parse_vsi(q['program']).values()) if t=='object_abs_distance' else []
        unit=PC.question_unit(r['question'])
        if t=='object_abs_distance' and unit not in PC.TO_CM:raise ValueError('Unknown length unit '+str(unit))
        if t=='room_size_estimation' and unit not in PC.TO_SQM:raise ValueError('Unknown area unit '+str(unit))
        q.update(operands=names,unit=unit,binding_error=None)
    except Exception as e:
        q.update(operands=[],unit=None,binding_error=type(e).__name__+': '+str(e));bad.append(qid)
    items.append(q)
items.sort(key=lambda q:q['qid'])
OUT.write_text(''.join(json.dumps(q)+'\n' for q in items))
c=collections.Counter((q['dataset'],q['question_type']) for q in items)
ph=collections.defaultdict(set)
for q in items:
    for n in q['operands']:ph[q['scene']].add(normalize_phrase(n.lower()))
per=collections.Counter();scn=collections.Counter()
for s,v in ph.items():per[s.split('/')[0]]+=len(v);scn[s.split('/')[0]]+=1
print(json.dumps(dict(items=len(items),binding_errors=bad,by=sorted(([*k,v] for k,v in c.items())),phrases_by_dataset=per,mask_scenes_by_dataset=scn,units=collections.Counter(q['unit'] for q in items))))
