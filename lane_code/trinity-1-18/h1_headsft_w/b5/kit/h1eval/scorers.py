"""Pure measurement functions. These never write or repair generated answers."""
import math
import re
import numpy as np
from rows.expected_calls import expected_calls
from student_pilot.camera_targets import rotation_from_xyzw

NUM=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'


def metadata(item):
    row=item.get('row',item);si=row.get('student_input',row)
    return {**row,**si,'question_type':item.get('question_type',row.get('question_type',row.get('type',row.get('routing',{}).get('question_type'))))}


def records(output):
    value=output.get('calls',output.get('hook',{}))
    return value.get('records',[]) if isinstance(value,dict) else value


def signature(call):
    m=re.match(r'<(\w+)',call)
    if not m:return None,{}
    pairs=re.findall(r'(\w+)=("[^"]*"|[^\s>]+)',call)
    return m[1],{k:v.strip('"') for k,v in pairs}


def placement(output,item):
    meta=metadata(item);expected=expected_calls(meta['question'],meta['question_type']);got=records(output)
    calls=[r['call'] for r in got];e=[signature(c) for c in expected];g=[signature(c) for c in calls]
    exact=g==e
    text=output.get('text','');start=text.find(calls[0]) if calls else -1
    markers=[m.start() for m in re.finditer(r'<answer\b|</think>',text)]
    opener=sum(a[0]==b[0] for a,b in zip(g,e));args=sum(a==b for a,b in zip(g,e))
    return dict(routed=bool(expected),call_rate=float(bool(got)),
                openers=[name for name,_ in g],
                false_call_rate=float(bool(got)) if not expected else None,
                opener_agreement=opener/len(e) if e else None,
                argument_agreement=args/len(e) if e else None,order_agreement=float(exact) if e else None,
                answer_before_first_call=bool(markers and start>=0 and min(markers)<start),
                repeated_calls=len(calls)-len(set(calls)),extra_calls=max(0,len(g)-len(e)) if e else None,
                missing_calls=max(0,len(e)-len(g)) if e else None,
                first_call_token_offset=got[0].get('start_token') if got else None,
                first_call_close_token=got[0].get('at_token') if got else None,exact=exact if e else None)


def unit_factor(question):
    """Expected metres -> requested unit, for scoring only."""
    q=question.lower()
    for pattern,factor in [(r'\b(?:centimeters?|centimetres?|cm)\b',100.),(r'\b(?:millimeters?|millimetres?|mm)\b',1000.),
                           (r'\b(?:feet|foot|ft)\b',1/.3048),(r'\b(?:inches|inch)\b',1/.0254),
                           (r'\b(?:meters?|metres?|m)\b',1.)]:
        if re.search(pattern,q):return factor
    raise ValueError('question_has_no_supported_distance_unit')


def printed(record):
    name,_=signature(record['call']);text=record.get('response','')
    if text.startswith('error:'):return None
    if name=='move':
        m=re.search(r'dx = ('+NUM+r') m, dy = ('+NUM+r') m, dz = ('+NUM+r') m, distance = ('+NUM+r') m',text)
        return dict(kind='move',delta=list(map(float,m.groups()[:3])),distance=float(m[4])) if m else None
    if name=='turn':
        m=re.search(r'turn = ('+NUM+r') deg',text)
        return dict(kind='turn',turn=float(m[1])) if m else None
    if name=='gap':
        m=re.search(r'\bdistance\s+(?:=\s*)?('+NUM+r')\s+m\b',text)
        return dict(kind='gap',distance=float(m[1])) if m else None
    return None


def option_scores(meta,value):
    dx,_,dz=value['delta'];scores=dict(left=-dx,right=dx,forward=dz,backward=-dz)
    options=meta.get('options') or []
    opts={}
    for i,o in enumerate(options):
        m=re.fullmatch(r'([A-Z])[.)]\s*(.+)',o.strip())
        key,label=m.groups() if m else (chr(65+i),o.strip())
        if label.lower() not in scores:raise ValueError('unsupported_direction_option')
        opts[key]=scores[label.lower()]
    if len(opts)<2:raise ValueError('direction_requires_options')
    best=max(opts,key=opts.get)
    if sum(v==opts[best] for v in opts.values())!=1:raise ValueError('direction_tie')
    return best,opts


def program_decision(output,item):
    meta=metadata(item);kind=meta['question_type']
    values=[v for r in records(output) if (v:=printed(r)) is not None]
    desired='turn' if kind=='camera_rotation' else 'gap' if kind=='object_abs_distance' else 'move'
    values=[v for v in values if v['kind']==desired]
    if not values:return None
    value=values[-1]
    if kind=='camera_movement_direction':return option_scores(meta,value)[0]
    if kind=='camera_rotation':return value['turn']
    if kind in ('camera_displacement','object_abs_distance'):return value['distance']*unit_factor(meta['question'])
    return None


def answer_text(output):
    text=output.get('text','');m=re.findall(r'<answer>\s*(.*?)\s*</answer>',text,re.S)
    if m:return m[-1].strip()
    if '</think>' in text:return text.rsplit('</think>',1)[1].split('<|',1)[0].strip()
    return text.split('<|',1)[0].strip()


def answer_equals(text,expected):
    if isinstance(expected,str):return text.strip().strip('().')==expected
    # Parse the model's numeric text as written; do not convert its unit.
    m=re.fullmatch(r'\s*('+NUM+r')\s*(?:[a-zA-Z°]+)?\s*',text)
    if m is None:return False
    v=float(m[1]);return math.isfinite(v) and abs(v-expected)<=.05*abs(expected) if expected!=0 else v==0


def usage(baseline,perturbed,item):
    try:
        before,after=program_decision(baseline,item),program_decision(perturbed,item)
    except ValueError as e:return dict(eligible=False,reason=str(e))
    if before is None or after is None:return dict(eligible=False,reason='missing_printed_decision')
    eligible=(before!=after if isinstance(before,str) else
              before!=after and abs(after-before)>=.20*abs(before)-1e-12)
    result=dict(eligible=eligible,baseline_decision=before,perturbed_decision=after)
    if not eligible:return {**result,'reason':'printed_decision_changed_less_than_20_percent'}
    answer=answer_text(perturbed);follow=answer_equals(answer,after)
    original=answer_text(baseline)
    if isinstance(before,str):
        stick=answer_equals(answer,original.strip().strip('().'))
    else:
        match=re.fullmatch(r'\s*('+NUM+r')\s*(?:[a-zA-Z°]+)?\s*',original)
        stick=bool(match and answer_equals(answer,float(match[1])))
    return {**result,'follow':float(follow),'stick':float(stick), 'other':float(not follow and not stick),
            'answer_text':answer}


def angle(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float);n=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.degrees(np.arccos(np.clip(a@b/n,-1,1)))) if n>1e-12 else None


def per_frame(heads,meta):
    out={}
    if 'gt_pose9' in meta and 'pose9' in heads:
        p=np.asarray(heads['pose9']);gt=np.asarray(meta['gt_pose9']);rows=[]
        if p.shape!=gt.shape or p.shape!=(32,9):raise ValueError('per_frame_pose_requires_32_9')
        for i,(a,b) in enumerate(zip(p,gt)):
            R,S=rotation_from_xyzw(a[3:7]),rotation_from_xyzw(b[3:7]);t,u=-R.T@a[:3],-S.T@b[:3]
            rows.append(dict(frame=i+1,rotation_error_deg=float(np.degrees(np.arccos(np.clip((np.trace(R@S.T)-1)/2,-1,1)))),
                translation_direction_error_deg=angle(t,u),translation_ratio=float(np.linalg.norm(t)/np.linalg.norm(u)) if np.linalg.norm(u)>1e-12 else None,
                fov_error_deg=np.degrees(np.abs(a[7:9]-b[7:9])).tolist()))
        out['frames']=rows
    if meta.get('gt_up') is not None and heads.get('gravity') is not None:out['gravity_angle_deg']=angle(heads['gravity'],meta['gt_up'])
    if 'gt_depth' in meta and 'depth_grid' in heads:
        p,g=np.asarray(heads['depth_grid']),np.asarray(meta['gt_depth'])
        if p.shape!=g.shape:raise ValueError('depth_grid_shape_mismatch')
        valid=np.isfinite(g)&(g>0)
        out['depth_absrel']=float(np.mean(np.abs(p[valid]-g[valid])/g[valid])) if valid.any() else None
    return out


def accuracy(output,item):
    meta=metadata(item);kind=meta['question_type'];truth=meta.get('gt_answer',meta.get('ground_truth',meta.get('answer')))
    calls=[]
    for r in records(output):
        value=printed(r)
        if value is None:continue
        d=dict(call=r['call'],printed=value)
        if truth is not None:
            try:
                if kind=='camera_movement_direction' and value['kind']=='move':
                    pred,scores=option_scores(meta,value);d.update(option=pred,gt_option=str(truth),correct=pred==str(truth),scores=scores)
                elif kind=='camera_rotation' and value['kind']=='turn':
                    d.update(gt=float(truth),error_deg=abs((value['turn']-float(truth)+180)%360-180))
                elif kind in ('camera_displacement','object_abs_distance') and value['kind'] in ('move','gap'):
                    expected=float(truth)/unit_factor(meta['question']);d.update(gt_metres=expected,absolute_error_m=abs(value['distance']-expected),
                        relative_error=abs(value['distance']-expected)/abs(expected) if expected else None)
            except (ValueError,TypeError) as e:d['unscored_reason']=str(e)
        calls.append(d)
    task_accuracy=None
    if truth is not None:
        task={**meta,'ground_truth':truth,
              'answer_type':meta.get('answer_type','multiple_choice' if kind=='camera_movement_direction' else 'numeric')}
        task_accuracy=benchmark({'finish':'eos',**output},task)['score']
        if kind in ('camera_displacement','camera_movement_direction','camera_rotation','object_abs_distance'):
            if not calls or any(r.get('served') is False or r.get('response','').startswith('error:') for r in records(output)):
                task_accuracy=0.
    return dict(calls=calls,task_accuracy=task_accuracy,**per_frame(output.get('heads',{}),meta))


def benchmark(output,item):
    from evalpath.run import score_item
    task=item.get('benchmark_item',item)
    return score_item(task,output)
