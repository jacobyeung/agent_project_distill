"""Rounded box observations and privately audited tool measurements (CPU float64)."""
import re
from decimal import Decimal
import numpy as np
from scipy.spatial.distance import cdist
from . import ground_v312 as old
from .contracts import RUNTIME_STATUSES, heading_available, status_text, response_status

RULE = 'sampled_box_512'
# v3.14: the benchmark's own sampler (5 cm grid over each full box minus its inner half box), minimum over all
# instance pairs of the two categories, as in cal_3d_bbox_distance_between_categories.
RULE_GRID = 'box_grid_5cm'
RULES = (RULE, RULE_GRID)
MAX_INSTANCES = 8
GROUND = re.compile(r'<ground obj="(' + old.NAME + r')" mode="box">')
GAP = re.compile(r'<gap a="(' + old.NAME + r')"((?: b="' + old.NAME + r'")+)' + r' rule="(sampled_box_512|box_grid_5cm)">')
# v3.14 camera-object distance (VSTI camera_obj_*): the camera centre of the asked frame to the 5 cm grid of each
# grounded box, keeping the instances supported in that frame when any are (the benchmark asks about the instance
# visible there), else every instance.
# The call opens with the existing atomic '<gap' token, so it needs no new vocabulary row.
CAMGAP = re.compile(r'<gap camera="([1-9][0-9]*)"((?: b="' + old.NAME + r'")+) rule="box_grid_5cm">')
SAMPLER = dict(rule=RULE, rng='PCG64', seed=0, samples=512, dtype='float64', draw_order='a_then_b', reset='per_pair')
SAMPLER_GRID = dict(rule=RULE_GRID, step=0.05, inner_half_box_removed=True, dtype='float64', instances='min_over_pairs')
SAMPLERS = {RULE: SAMPLER, RULE_GRID: SAMPLER_GRID}
MEASUREMENTS = {
    (RULE, False): "The sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.",
    (RULE, True): "Each sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.",
    (RULE_GRID, False): "The box gap is the smallest distance between points on a 5 cm grid over the two objects' full boxes, taken over every pair of instances.",
    (RULE_GRID, True): "Each box gap is the smallest distance between points on a 5 cm grid over the two objects' full boxes, taken over every pair of instances.",
}


def number(v, places):
    if not np.isfinite(v):
        raise ValueError('nonfinite_box_value')
    text = format(float(v), f'.{places}f')
    return text[1:] if text.startswith('-') and float(text) == 0 else text


def box(centre, lengths, axes):
    c, l, a = (np.asarray(x, dtype=np.float64).copy() for x in (centre, lengths, axes))
    if c.shape != (3,) or l.shape != (3,) or a.shape != (3,3):
        raise ValueError('invalid_box_shape')
    if not all(np.isfinite(x).all() for x in (c,l,a)) or not (l > 0).all():
        raise ValueError('invalid_box_values')
    if np.max(np.abs(a @ a.T - np.eye(3))) > 1e-8:
        raise ValueError('invalid_box_axes')
    return dict(centre=c, lengths=l, axes=a)


def sampled_box_512(a, b):
    """Measure ordered full-precision provider boxes with the benchmark sampler."""
    rng = np.random.Generator(np.random.PCG64(0))
    points = []
    for operand in (a,b):
        x = box(**operand)
        u = rng.uniform(-1.0, 1.0, size=(512,3))
        points.append((u * (x['lengths'] / 2.0)) @ x['axes'] + x['centre'])
    return float(cdist(*points, metric='euclidean').min())


def grid_points(value, step=0.05):
    """sample_points_in_oriented_bbox_uniform: a step grid over the full box, minus the points inside the half box."""
    x = box(**value)
    ext = x['lengths']
    axes = [np.linspace(-e / 2, e / 2, int(np.ceil(e / step))) for e in ext]
    p = np.stack([g.ravel() for g in np.meshgrid(*axes)], 1)
    p = p[np.any(np.abs(p) > ext / 4, axis=1)]
    if not len(p):
        return grid_points(value, step / 2)
    return p @ x['axes'] + x['centre']


def box_grid_5cm(a, b):
    from scipy.spatial import cKDTree
    return float(cKDTree(grid_points(a)).query(grid_points(b), workers=1)[0].min())


def camera_gap(centre, value):
    return float(np.linalg.norm(grid_points(value) - np.asarray(centre, float), axis=1).min())


def measure(rule, As, Bs):
    """Minimum of the rule over every instance pair (single instances reduce to the v3.13 pair measurement)."""
    f = sampled_box_512 if rule == RULE else box_grid_5cm
    return min(f(a, b) for a in As for b in Bs)


def public_fields(value):
    """Horizontal slots in order, then height; positive yaw turns +x toward -z."""
    x = box(**value)
    vertical = int(np.argmax(np.abs(x['axes'][:,1])))
    horizontal = [i for i in range(3) if i != vertical]
    if (abs(abs(x['axes'][vertical,1])-1) > 1e-8
            or np.max(np.abs(x['axes'][horizontal,1])) > 1e-8):
        return tilted_public_fields(x)
    direction = x['axes'][horizontal[0]]
    yaw = int(number(np.degrees(np.arctan2(-direction[2],direction[0])),0))
    yaw = (yaw + 180) % 360 - 180
    return x['centre'], x['lengths'][horizontal+[vertical]], yaw


def tilted_public_fields(x):
    """v3.14: a tilted private box prints as its enclosing gravity-aligned box (the yaw of the axis with the
    longest horizontal projection, then the corner extents along that heading, across it and along +y). The
    private tilted box stays the measured operand; v3.13 refused such boxes as 'box unavailable'."""
    up = np.array([0., 1., 0.])
    flat = x['axes'] * x['lengths'][:, None]
    flat[:, 1] = 0
    i = int(np.argmax(np.linalg.norm(flat, axis=1)))
    d = flat[i] / np.linalg.norm(flat[i])
    yaw = int(number(np.degrees(np.arctan2(-d[2], d[0])), 0))
    yaw = (yaw + 180) % 360 - 180
    t = np.radians(yaw); d = np.array([np.cos(t), 0., -np.sin(t)]); e = np.cross(up, d)
    from itertools import product
    corners = (np.array(list(product((-.5, .5), repeat=3))) * x['lengths']) @ x['axes']
    lengths = np.array([np.ptp(corners @ d), np.ptp(corners @ e), np.ptp(corners @ up)])
    return x['centre'], lengths, yaw


def yaw_box(centre, lengths, yaw):
    theta=np.radians(yaw);c,s=np.cos(theta),np.sin(theta)
    return box(centre,lengths,[[c,0,-s],[s,0,c],[0,1,0]])


def serialize(name, label, frames, best, value):
    old.valid_name(name)
    if not re.fullmatch(r'B[1-9][0-9]*', label):
        raise ValueError('invalid_box_label')
    if not frames or frames != sorted(set(frames)) or best not in frames or any(type(f) is not int or not 1 <= f <= 32 for f in frames):
        raise ValueError('invalid_box_support')
    centre,lengths,yaw = public_fields(value)
    return '\n'.join([f'{name}: frames '+','.join(map(str,frames))+f' (best {best})',
        f'{label}: f1 centre ('+', '.join(number(t,2) for t in centre)+') m',
        'size '+' x '.join(number(t,2) for t in lengths)+' m',
        f'yaw {yaw} deg (0 = +x; positive +x toward -z about +y)'])


def parse(body):
    """Parse the lossy public observation for diagnostics, never tool measurement."""
    f2 = r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}'
    tri = r'\(('+f2+r'), ('+f2+r'), ('+f2+r')\)'
    pattern = (r'('+old.NAME+r'): frames ([1-9][0-9]*(?:,[1-9][0-9]*)*) \(best ([1-9][0-9]*)\)\n'
        r'(B[1-9][0-9]*): f1 centre '+tri+r' m\nsize ('+f2+r') x ('+f2+r') x ('+f2+r') m\nyaw '
        r'(-?(?:0|[1-9][0-9]*)) deg \(0 = \+x; positive \+x toward -z about \+y\)')
    m = re.fullmatch(pattern, body)
    if not m:raise ValueError('malformed_printed_box')
    name, frame_text, best, label = m.groups()[:4]
    v=list(map(float,m.groups()[4:]));frames=list(map(int,frame_text.split(',')))
    # A positive sub-centimetre extent may print zero: it remains a valid observation.
    if any(t < 0 for t in v[3:6]):raise ValueError('negative_printed_size')
    theta=np.radians(v[6]);c,s=np.cos(theta),np.sin(theta)
    value=dict(centre=np.array(v[:3]), lengths=np.array(v[3:6]),axes=np.array([[c,0,-s],[s,0,c],[0,1,0]]))
    if (not -180 <= v[6] < 180 or frames != sorted(set(frames)) or int(best) not in frames
            or any(not 1 <= f <= 32 for f in frames) or re.search(r'-0(?:\.00)?(?=[, )])',body)):
        raise ValueError('noncanonical_printed_box')
    return dict(name=name,label=label,frames=frames,best=int(best),value=value)


def audit_box(value):
    return {k:v.tolist() for k,v in box(**value).items()}


def split_instances(body):
    """A multi-instance response starts with 'NAME: N instances' and holds N four-line box blocks."""
    lines = body.split('\n')
    m = re.fullmatch('(' + old.NAME + r'): ([2-9]|[1-9][0-9]+) instances', lines[0])
    if not m:
        return [body]
    n = int(m[2])
    if len(lines) != 1 + 4 * n:
        raise ValueError('malformed_multi_instance_box')
    blocks = ['\n'.join(lines[1 + 4 * i:5 + 4 * i]) for i in range(n)]
    if any(parse(b)['name'] != m[1] for b in blocks):
        raise ValueError('box_name_mismatch')
    return blocks


class BoxRegistry:
    def __init__(self):
        self.records, self.bindings, self.states = {}, {}, {}

    def invalidate(self, name, state='not seen'):
        self.bindings.pop(name,None); self.states[name]=state

    def ingest(self, body, value, gap_value=None):
        """Register one printed box (value) or, for a multi-instance body, one box per instance (list of values).
        gap_value (same shape as value, optional): the private operand every gap and camera gap measures; the
        fusion policy's predicted-geometry mode passes the largest single view's box here, and without it the
        printed box is the operand (sensor / GT geometry, v3.14 default)."""
        blocks = split_instances(body)
        if len(blocks)>1 and getattr(self,'program_version',None)=='3.13':
            from .program_errors import ProgramRefusal
            raise ProgramRefusal('form_requires_v3.14')
        values = value if isinstance(value, (list, tuple)) else [value]
        if len(blocks) != len(values) or (len(blocks) > 1) != isinstance(value, (list, tuple)):
            raise ValueError('audit_box_instance_count_mismatch')
        gaps = values if gap_value is None else (list(gap_value) if isinstance(gap_value, (list, tuple)) else [gap_value])
        if len(gaps) != len(values):
            raise ValueError('audit_gap_box_instance_count_mismatch')
        records, labels = [], []
        for block, v, gv in zip(blocks, values, gaps):
            record = parse(block)
            if serialize(record['name'],record['label'],record['frames'],record['best'],v) != block:
                raise ValueError('audit_box_response_mismatch')
            record['value'] = box(**v)
            record['gap_value'] = record['value'] if gv is v else box(**gv)
            if record['label'] != f'B{len(self.records)+1}':
                raise ValueError('nonsequential_box_label')
            if records and record['name'] != records[0]['name']:
                raise ValueError('box_name_mismatch')
            self.records[record['label']]=record
            records.append(record); labels.append(record['label'])
        self.bindings[records[0]['name']]=labels
        self.states[records[0]['name']]='ok'
        return records[0] if len(records) == 1 else records

    def ingest_metric(self, name, values, gaps, metadata):
        labels = []
        for value, gap, meta in zip(values, gaps, metadata):
            label = f'B{len(self.records)+1}'
            self.records[label] = dict(name=name, label=label, value=box(**value),
                gap_value=box(**gap), **meta)
            labels.append(label)
        self.bindings[name] = labels
        self.states[name] = 'ok'

    def audit_labels(self, name):
        labels = self.bindings.get(name)
        return labels if labels is None or len(labels) > 1 else labels[0]

    def gap(self, a, bs, rule=RULE):
        names=[a,*bs]
        for n in names:old.valid_name(n)
        if not bs or len(set(names)) != len(names):
            raise old.RowRefusal('duplicate_gap_operand')
        states=[self.states.get(n,'not seen') for n in names]
        for status in RUNTIME_STATUSES:
            if status in states:return status, []
        if rule not in RULES:
            raise ValueError('unknown_distance_rule')
        # One operand pair (absolute distance) measures the private gap operand; several candidates (relative
        # distance) measure the printed boxes, as the fusion policy was priced (gt_ceiling task 6).
        key='gap_value' if len(bs)==1 else 'value'
        sets=[[self.records[l][key] for l in self.bindings[n]] for n in names]
        values=[measure(rule,sets[0],s) for s in sets[1:]]
        printed=[number(d,2) for d in values]
        if len(bs)==1:
            return f'distance {printed[0]} m', values
        lines=[f'{n}: {d} m' for n,d in zip(bs,printed)]
        minimum=min(map(Decimal,printed))
        winners=','.join('"'+n+'"' for n,d in zip(bs,printed) if Decimal(d)==minimum)
        return '\n'.join(lines+[f'min {winners} {minimum:.2f} m']),values


def cam_gap_body(registry, frame, names, centre):
    """Printed camera gaps (and the minimum for several names) plus the unrounded values."""
    if centre is None:return 'frame unavailable', []
    for n in names:old.valid_name(n)
    if not names or len(set(names)) != len(names):
        raise old.RowRefusal('duplicate_gap_operand')
    states=[registry.states.get(n,'not seen') for n in names]
    for status in RUNTIME_STATUSES:
        if status in states:return status, []
    values=[]
    for n in names:
        records=[registry.records[l] for l in registry.bindings[n]]
        here=[r for r in records if frame in r['frames']]
        if not here:raise ValueError('camera_instance_not_visible')
        selected=min(here,key=lambda r:(-r['areas'].get(str(frame),0.),r.get('instance_id',r['label'])))
        values.append(camera_gap(centre,selected['gap_value' if len(names)==1 else 'value']))
    printed=[number(d,2) for d in values]
    if len(names)==1:
        return f'distance {printed[0]} m', values
    minimum=min(map(Decimal,printed))
    winners=','.join('"'+n+'"' for n,d in zip(names,printed) if Decimal(d)==minimum)
    return '\n'.join([f'{n}: {d} m' for n,d in zip(names,printed)]+[f'min {winners} {minimum:.2f} m']),values


def camera_centre_f1(geometry, k):
    """Camera centre of frame k in f1 (the frame of every printed box)."""
    if not heading_available(geometry):
        # Private metric operands stay in the existing world frame; none are printed.
        return np.asarray(geometry.cam(k)[1],float)
    R,t=(np.asarray(v,float) for v in geometry.cam(1))
    up=np.array([0.,0.,1.]);heading=R[:,2]-R[2,2]*up
    if np.linalg.norm(heading)<1e-6:raise ValueError('undefined_level_basis')
    heading/=np.linalg.norm(heading)
    F=np.column_stack((np.cross(heading,up),up,heading))
    return (np.asarray(geometry.cam(k)[1],float)-t)@F


POLICY_ID='fit_gbox_policy_voteb5_best1_v1'
GAP_OPERANDS=('best_view','printed_box')


def _gap_audit(audit, n):
    """Private gap operands of one ground event: required (with one tag per instance) for the policy provider,
    forbidden for every other provider."""
    keys=('full_precision_gap_box','full_precision_gap_boxes','gap_operands')
    if audit.get('box_provider')!=POLICY_ID:
        if any(k in audit for k in keys):raise ValueError('audit_gap_box_without_policy')
        return None
    tags=audit.get('gap_operands')
    if not isinstance(tags,list) or len(tags)!=n or any(t not in GAP_OPERANDS for t in tags):
        raise ValueError('audit_gap_operands_missing')
    boxes_=audit.get('full_precision_gap_box') if n==1 else audit.get('full_precision_gap_boxes')
    if boxes_ is None or (n>1 and len(boxes_)!=n):raise ValueError('audit_gap_box_missing')
    return boxes_


def replay_audit(events):
    """Reproduce every measurement from private boxes and sampler metadata."""
    registry=BoxRegistry();results=[]
    providers={e['audit'].get('box_provider') for e in events if e.get('audit') and e['audit'].get('box_provider')}
    if len(providers)>1:raise ValueError('audit_mixed_box_providers')
    for event in events:
        call=event['call'];response=event['response']
        if not response.startswith('<tool_response>\n') or not response.endswith('\n</tool_response>'):
            raise ValueError('invalid_response_wrapper')
        body=response[len('<tool_response>\n'):-len('\n</tool_response>')]
        if (m:=GROUND.fullmatch(call)):
            failure=re.fullmatch(re.escape(m[1])+r': ('+'|'.join(map(re.escape,RUNTIME_STATUSES))+')',body)
            if response_status(body) == 'heading unavailable' and event['audit'].get('metric_only'):
                audit = event['audit']
                registry.ingest_metric(m[1], audit['metric_values'], audit['metric_gaps'], audit['metric_metadata'])
            elif failure:registry.invalidate(m[1],failure[1])
            else:
                audit=event['audit']
                if not audit.get('box_provider') or audit.get('numpy_version') != np.__version__:
                    raise ValueError('audit_provider_or_runtime_mismatch')
                blocks=split_instances(body)
                if len(blocks)==1:
                    if audit.get('box_label') != parse(body)['label']:raise ValueError('audit_box_label_mismatch')
                    record=registry.ingest(body,audit['full_precision_box'],_gap_audit(audit,1))
                else:
                    if audit.get('box_labels') != [parse(b)['label'] for b in blocks]:raise ValueError('audit_box_label_mismatch')
                    gb=_gap_audit(audit,len(blocks))
                    record=registry.ingest(body,list(audit['full_precision_boxes']),None if gb is None else list(gb))[0]
                if record['name']!=m[1]:raise ValueError('box_name_mismatch')
                for label,meta in zip(registry.bindings[m[1]],audit.get('instance_metadata',[])):
                    registry.records[label].update(meta)
        elif (m:=GAP.fullmatch(call)):
            bs=re.findall(r' b="('+old.NAME+r')"',m[2])
            audit=event['audit']
            if not audit.get('box_provider') or audit.get('numpy_version') != np.__version__:
                raise ValueError('audit_provider_or_runtime_mismatch')
            if audit.get('sampler') != SAMPLERS[m[3]]:raise ValueError('audit_sampler_mismatch')
            labels=[registry.audit_labels(n) for n in [m[1],*bs]]
            if audit.get('ordered_box_labels') != labels:raise ValueError('audit_draw_order_mismatch')
            got,values=registry.gap(m[1],bs,m[3])
            if got!=body:raise ValueError('audit_box_replay_mismatch')
            results.extend(values)
        elif (m:=CAMGAP.fullmatch(call)):
            names=re.findall(r' b="('+old.NAME+r')"',m[2])
            audit=event['audit']
            if audit.get('sampler') != SAMPLER_GRID:raise ValueError('audit_sampler_mismatch')
            if audit.get('ordered_box_labels') != [registry.audit_labels(n) for n in names]:
                raise ValueError('audit_draw_order_mismatch')
            got,values=cam_gap_body(registry,int(m[1]),names,audit['camera_centre_f1'])
            if got!=body:raise ValueError('audit_box_replay_mismatch')
            results.extend(values)
        elif 'mode="instances"' in call:
            registry.invalidate(re.search(r'obj="([^"]+)"',call)[1])
    return results


CAM_MEASUREMENT = ("Each camera gap is the smallest distance from the camera of that frame to points on a 5 cm grid over "
                   "the object's full box, which is how this benchmark defines the answer.")


def render_camera(item, session, token_count):
    raise ValueError('Use derivgen_v7.derivgen.box_v313.render_camera to generate v3.14 traces')

def _disabled_render_camera(item, session, token_count):
    """v3.14 VSTI camera_obj_abs_dist / camera_obj_rel_dist_v*: ground every name as a box, one cam_gap call.
    item['roles'] = dict(frame=k (1-based slot), names=[...]); relative types need options in candidate order."""
    if session.events:raise ValueError('render requires a fresh session')
    if not item.get('gt_authority'):raise old.RowRefusal('independent_gt_authority_missing')
    k,names=int(item['roles']['frame']),list(item['roles']['names'])
    relative=item['type'].startswith('camera_obj_rel_dist')
    if relative and list(old.option_map(item['options']).values())!=names:
        raise old.RowRefusal('candidate_order_not_option_order')
    lines=['<think>',f'I will ground the boxes and ask the tool for their distance from the camera in frame {k}.']
    failure=None;values=[]
    def emit(call):
        body=session.execute(call);lines.extend([call,old.wrap(body)]);return body
    for name in names:
        body=emit(f'<ground obj="{old.valid_name(name)}" mode="box">')
        if response_status(body)!='ok':failure=(name,response_status(body));break
    if not failure:
        emit(f'<gap camera="{k}"'+''.join(f' b="{n}"' for n in names)+' rule="box_grid_5cm">')
        values=replay_audit(session.events)
        if relative:
            printed=sorted(zip([Decimal(number(v,2)) for v in values],names))
            raw=sorted(zip(values,names))
            if raw[0][1]!=printed[0][1]:raise old.RowRefusal('rounding_decision_flip')
            if printed[1][0]-printed[0][0]<Decimal('.02'):raise old.RowRefusal('near_tie')
            content=printed[0][1];answer=old.letter(item['options'],content)
            if str(item.get('gt_answer'))!=answer:raise old.RowRefusal('independent_box_winner_disagreement')
            lines+=[CAM_MEASUREMENT,f'The nearest is {content}, so the answer is {answer}.']
        else:
            answer=content=number(values[0],2);gt=float(item['gt_answer'])
            if abs(float(answer)-gt)>max(.05*abs(gt),.051):raise old.RowRefusal('independent_box_label_disagreement')
            lines+=[CAM_MEASUREMENT,f'The camera gap is {answer} m.']
    else:
        continuation,answer=old.direct_continuation(item);content=old.option_map(item.get('options',[])).get(answer,answer)
        name,status=failure
        lines.append(f'The tool did not find {name}, so I estimate from the frames.' if status=='not seen' else f'The box for {name} is {status}, so I estimate from the frames.')
        lines.append(continuation)
    lines+=['</think>',f'<answer>{answer}</answer>'];suffix='\n'.join(lines);tokens=token_count(suffix)
    if type(tokens) is not int or not 0<=tokens<=5000:raise old.RowRefusal('suffix_cap')
    return dict(qid=item['qid'],type=item['type'],question=item['question'],options=item.get('options',[]),suffix=suffix,
        answer=answer,answer_content=content,suffix_tokens=tokens,events=list(session.events),spec_version='3.14',
        not_seen=bool(failure),simulated_misses=sorted(session.simulated_misses),
        program_audit=dict(target_distance_rule='camera_box_grid_5cm',box_provider=session.box_provider_id,
                           numpy_version=np.__version__,unrounded_replay_m=values,independent_target=item.get('gt_answer')),
        training_admitted=False)


def in_f1(geometry, centre, lengths, axes):
    if not heading_available(geometry):
        return box(centre, lengths, np.asarray(axes).reshape(3,3))
    R,t=(np.asarray(v,float) for v in geometry.cam(1))
    up=np.array([0.,0.,1.]);heading=R[:,2]-R[2,2]*up
    if np.linalg.norm(heading)<1e-6:raise ValueError('undefined_level_basis')
    heading/=np.linalg.norm(heading)
    F=np.column_stack((np.cross(heading,up),up,heading))
    return box((np.asarray(centre)-t)@F,lengths,np.asarray(axes).reshape(3,3)@F)


class FittedBoxProvider:
    provider_id='fit_gbox_best_v1'
    def __init__(self, fitter):self.fitter=fitter
    def __call__(self,name,obj,geometry,best):
        points=np.asarray(obj['points'].get(str(best),[]),float)
        if len(points)<4:return None
        raw=self.fitter(points)
        return in_f1(geometry,raw['centroid'],raw['axesLengths'],raw['normalizedAxes'])


class FusedBoxProvider:
    """v3.14 inference default: one gravity-aligned box over the instance's eligible points fused from every
    sampled frame in which it was lifted (min-area floor rectangle, full fused height), not the best frame alone."""
    provider_id='fit_gbox_fused_full_v1'
    def __init__(self, fitter=None, max_points=20000):
        self.fitter=fitter or fit_gbox_full; self.max_points=max_points
    def __call__(self,name,obj,geometry,best):
        parts=[np.asarray(obj['points'].get(str(k),[]),float).reshape(-1,3) for k in obj['frames']]
        points=np.concatenate(parts) if parts else np.zeros((0,3))
        if len(points)<4:return None
        if len(points)>self.max_points:
            points=points[np.random.default_rng(0).choice(len(points),self.max_points,replace=False)]
        raw=self.fitter(points)
        return in_f1(geometry,raw['centroid'],raw['axesLengths'],raw['normalizedAxes'])


def vote_points(parts, vox=0.05, min_frames=2):
    """Points whose voxel (vox m) holds points of >= min_frames distinct frames (gt_ceiling geomswap.vote)."""
    parts=[p for p in parts if len(p)]
    if not parts:
        return np.zeros((0,3))
    P=np.concatenate(parts)
    f=np.concatenate([np.full(len(p),j) for j,p in enumerate(parts)])
    _,vid=np.unique(np.floor(P/vox).astype(np.int64),axis=0,return_inverse=True)
    vid=vid.ravel()
    pairs=np.unique(np.stack([vid,f],1),axis=0)
    support=np.bincount(pairs[:,0],minlength=vid.max()+1)
    return P[support[vid]>=min_frames]


def _finite(points):
    P=np.asarray(points,float).reshape(-1,3)
    return P[np.isfinite(P).all(1)]


class PolicyBoxProvider:
    """Predicted-geometry fusion policy (gt_ceiling GT_CEILING_DECOMPOSITION 'Tower geometry'), on the lifting
    backend's depth-cut points (obj['points_cut']; required). Printed box: fit_gbox_full over the points that >= 2
    frames agree on (5 cm voxels) plus every point of the largest view (voteb5). gap_box: the largest view alone
    (best1), the operand of single-pair gaps and single-name camera gaps. At most 4,000 points per fit (seed-0
    sample, as priced). A view needs >= 4 finite points; otherwise gap_box returns None and the ground event
    records gap_operand 'printed_box'. Non-finite points are dropped before voting and fitting."""
    provider_id='fit_gbox_policy_voteb5_best1_v1'
    def __init__(self, fitter=None, max_points=4000, vox=0.05, min_frames=2):
        self.fitter=fitter or fit_gbox_full; self.max_points=max_points; self.vox=vox; self.min_frames=min_frames
    def _cut(self,obj):
        if 'points_cut' not in obj:raise ValueError('policy_requires_depth_cut_points')
        return obj['points_cut']
    def _fit(self,points,geometry):
        if len(points)<4:raise ValueError('policy_box_support_under_4')
        if len(points)>self.max_points:
            points=points[np.random.default_rng(0).choice(len(points),self.max_points,replace=False)]
        raw=self.fitter(points)
        return in_f1(geometry,raw['centroid'],raw['axesLengths'],raw['normalizedAxes'])
    def __call__(self,name,obj,geometry,best):
        cut=self._cut(obj)
        B=_finite(cut.get(str(best),[]))
        parts=[_finite(cut.get(str(k),[])) for k in obj['frames']]
        points=np.concatenate([vote_points(parts,self.vox,self.min_frames),B])
        if len(B)<4:
            points=np.concatenate(parts) if parts else np.zeros((0,3))
        return self._fit(points,geometry)
    def gap_box(self,name,obj,geometry,best):
        B=_finite(self._cut(obj).get(str(best),[]))
        return self._fit(B,geometry) if len(B)>=4 else None


GEOMETRY_MODES=('sensor','predicted')


def provider_for(geometry_mode, version='3.14'):
    """The box provider a session uses: sensor or GT geometry keeps the fused box; predicted geometry (own or tower
    heads at inference, and own-value readouts during scheduled sampling) uses the fusion policy."""
    if geometry_mode not in GEOMETRY_MODES:
        raise ValueError('unknown_geometry_mode')
    if version=='3.13':
        return FittedBoxProvider(fit_gbox)
    return PolicyBoxProvider() if geometry_mode=='predicted' else FusedBoxProvider()


class AnnotationBoxProvider:
    """Explicit GT substitution, never selected by inference defaults."""
    provider_id='annotation_full_box_v1'
    def __call__(self,name,obj,geometry,best):
        raw=geometry.obb[int(obj['instance_id'])]
        c=(np.asarray(raw['centroid'])-geometry.origin)@geometry.basis
        a=np.asarray(raw['normalizedAxes']).reshape(3,3)@geometry.basis
        return in_f1(geometry,c,raw['axesLengths'],a)


def ground(session,name):
    entries=session._instances(name)
    session.box_registry.invalidate(name)
    multi=getattr(session,'multi_instance',False)
    status=(('unresolved' if not multi else None) if len(entries)>1
            else 'not seen' if not entries else None)
    if name in session.simulated_misses:
        if not entries:raise old.RowRefusal('simulated_miss_requires_visible_object')
        status='not seen'
    if status:
        session.box_registry.invalidate(name,status)
        return name+': '+status
    blocks,values,gaps,tags,metadata=[],[],[],[],[]
    metric_only = not heading_available(session.geometry)
    gap_box=getattr(session.box_provider,'gap_box',None)
    try:
        for obj in entries:
            # Pin the largest accepted raw mask before inspecting its eligible points.
            best=min(obj['visible'],key=lambda k:(-obj['areas'][str(k)],k))
            value=None
            if best in obj['frames'] and session.box_provider is not None:
                try:
                    value=session.box_provider(name,obj,session.geometry,best)
                except (ValueError,KeyError,TypeError,FloatingPointError):
                    if not multi:raise
                    continue
            if value is None:
                if multi:continue
                raise ValueError('provider_unavailable')
            if session.spec_version == '3.13' and not metric_only:
                axes = box(**value)['axes']
                vertical = int(np.argmax(np.abs(axes[:, 1])))
                horizontal = [i for i in range(3) if i != vertical]
                if (abs(abs(axes[vertical, 1]) - 1) > 1e-8
                        or np.max(np.abs(axes[horizontal, 1])) > 1e-8):
                    raise ValueError('box_not_gravity_aligned')
            gvalue,tag=value,'printed_box'
            if gap_box is not None:
                g=gap_box(name,obj,session.geometry,best)
                if g is not None:gvalue,tag=g,'best_view'
            label=f'B{len(session.box_registry.records)+1+len(blocks)}'
            blocks.append('' if metric_only else serialize(name,label,obj['frames'],best,value));values.append(value);gaps.append(gvalue);tags.append(tag)
            metadata.append(dict(areas=obj['areas'], instance_id=str(obj.get('instance_id',label)), **(dict(frames=obj['frames'], best=best, gap_operand=tag) if metric_only else {})))
        if len(blocks)>MAX_INSTANCES:
            session.box_registry.invalidate(name,'unresolved')
            return name+': unresolved'
        if not blocks:raise ValueError('provider_unavailable')
        if metric_only:
            session.box_registry.ingest_metric(name, values, gaps, metadata)
            sizes = []
            for value in values:
                vertical = int(np.argmax(np.abs(value['axes'][:,2])))
                order = [i for i in range(3) if i != vertical] + [vertical]
                sizes.append('size '+' x '.join(number(v,2) for v in value['lengths'][order])+' m')
            return status_text('heading unavailable',name)+'\n'+'\n'.join(sizes)
        body=blocks[0] if len(blocks)==1 else '\n'.join([f'{name}: {len(blocks)} instances',*blocks])
        session.box_registry.ingest(body,values[0] if len(values)==1 else values,
                                    None if gap_box is None else (gaps[0] if len(gaps)==1 else gaps))
        for label,meta,tag in zip(session.box_registry.bindings[name],metadata,tags):
            session.box_registry.records[label].update(meta)
            if gap_box is not None:session.box_registry.records[label]['gap_operand']=tag
    except (ValueError,KeyError,TypeError,FloatingPointError):
        session.box_registry.invalidate(name,'box unavailable')
        return name+': box unavailable'
    return body


def render(item,session,token_count):
    if session.spec_version == '3.14' or item.get('target_distance_rule') == RULE_GRID:
        raise ValueError('Use derivgen_v7.derivgen.box_v313.render to generate v3.14 traces')
    if session.events:raise ValueError('render requires a fresh session')
    if not item.get('gt_authority'):raise old.RowRefusal('independent_gt_authority_missing')
    roles=item['roles'];relative=item['type']=='object_rel_distance'
    a=roles['target'] if relative else roles['a'];bs=roles['cands'] if relative else [roles['b']]
    if relative and (len(bs)<2 or list(old.option_map(item['options']).values())!=bs):
        raise old.RowRefusal('candidate_order_not_option_order')
    if len(set([a,*bs]))!=len(bs)+1:raise old.RowRefusal('duplicate_gap_operand')
    rule=item.get('target_distance_rule',RULE)
    if rule not in RULES:raise old.RowRefusal('unknown_distance_rule')
    lines=['<think>','I will ground the boxes and ask the tool to measure their sampled-box distances.']
    failure=None;values=[]
    def emit(call):
        body=session.execute(call);lines.extend([call,old.wrap(body)]);return body
    for name in [a,*bs]:
        body=emit(f'<ground obj="{old.valid_name(name)}" mode="box">')
        if response_status(body)!='ok':failure=(name,response_status(body));break
    if not failure:
        body=emit(f'<gap a="{a}"'+''.join(f' b="{b}"' for b in bs)+f' rule="{rule}">')
        values=replay_audit(session.events)
        displayed=[Decimal(number(v,2)) for v in values]
        if relative:
            raw=sorted(zip(values,bs));printed=sorted(zip(displayed,bs))
            if raw[0][1]!=printed[0][1]:raise old.RowRefusal('rounding_decision_flip')
            if raw[1][0]-raw[0][0]<max(.1,.1*raw[1][0]):raise old.RowRefusal('unrounded_near_tie')
            if printed[1][0]-printed[0][0]<max(Decimal('.10'),Decimal('.10')*printed[1][0]):raise old.RowRefusal('near_tie')
            content=printed[0][1];answer=old.letter(item['options'],content)
            if str(item.get('gt_answer'))!=answer:raise old.RowRefusal('independent_box_winner_disagreement')
            lines.append(f'The sampled-box minimum is {content}, so the answer is {answer}.')
        else:
            answer=content=number(values[0],2);gt=float(item['gt_answer'])
            if answer!=number(gt,2) or abs(float(answer)-gt)>.05*abs(gt):
                raise old.RowRefusal('independent_box_label_disagreement')
            lines.append(f'The sampled-box distance is {answer} m.')
    else:
        continuation,answer=old.direct_continuation(item);content=old.option_map(item.get('options',[])).get(answer,answer)
        name,status=failure
        lines.append(f'The tool did not find {name}, so I estimate from the frames.' if status=='not seen' else f'The box for {name} is {status}, so I estimate from the frames.')
        lines.append(continuation)
    lines+=['</think>',f'<answer>{answer}</answer>'];suffix='\n'.join(lines);tokens=token_count(suffix)
    if type(tokens) is not int or not 0<=tokens<=5000:raise old.RowRefusal('suffix_cap')
    audit=dict(target_distance_rule=rule,box_provider=session.box_provider_id,numpy_version=np.__version__,unrounded_replay_m=values,
        independent_target=item.get('gt_answer'),independent_authority=item.get('gt_authority'),
        independent_ordered_boxes=item.get('independent_ordered_boxes'),
        unrounded_discrepancy_m=None if relative or not values else values[0]-float(item['gt_answer']))
    return dict(qid=item['qid'],type=item['type'],question=item['question'],options=item.get('options',[]),suffix=suffix,
        answer=answer,answer_content=content,suffix_tokens=tokens,events=list(session.events),spec_version='3.13',
        not_seen=bool(failure),simulated_misses=sorted(session.simulated_misses),program_audit=audit,training_admitted=False)


import math
def fit_gbox(P):
    """Gravity-aligned box (z up) of a point set: min-area rectangle of the XY hull + z extent -> OBB dict."""
    from scipy.spatial import ConvexHull
    P = P[np.isfinite(P).all(1)]
    if len(P) < 4:
        c = P.mean(0) if len(P) else np.zeros(3)
        return {'centroid': c, 'axesLengths': np.array([0.05, 0.05, 0.05]), 'normalizedAxes': np.eye(3).ravel()}
    xy = P[:, :2]
    try:
        hull = xy[ConvexHull(xy).vertices]
    except Exception:
        hull = xy
    best = None
    for i in range(len(hull)):
        e = hull[(i + 1) % len(hull)] - hull[i]
        if np.linalg.norm(e) < 1e-9:
            continue
        a = math.atan2(e[1], e[0])
        R2 = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
        q = xy @ R2.T
        lo, hi = q.min(0), q.max(0)
        area = np.prod(hi - lo)
        if best is None or area < best[0]:
            best = (area, a, lo, hi)
    _, a, lo, hi = best
    z0, z1 = np.percentile(P[:, 2], 2), np.percentile(P[:, 2], 98)
    cxy = (lo + hi) / 2
    R2 = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
    c = np.array([*(R2.T @ cxy), (z0 + z1) / 2])
    axes = np.array([[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return {'centroid': c, 'axesLengths': np.array([hi[0] - lo[0], hi[1] - lo[1], max(z1 - z0, 0.02)]), 'normalizedAxes': axes.ravel()}


def fit_gbox_full(P):
    """fit_gbox with the full height of the points (0th/100th percentiles) instead of the 2nd/98th."""
    b = fit_gbox(P)
    P = P[np.isfinite(P).all(1)]
    if len(P) < 4:
        return b
    z0, z1 = float(P[:, 2].min()), float(P[:, 2].max())
    c = np.asarray(b['centroid'], float).copy(); c[2] = (z0 + z1) / 2
    L = np.asarray(b['axesLengths'], float).copy(); L[2] = max(z1 - z0, 0.02)
    return {'centroid': c, 'axesLengths': L, 'normalizedAxes': b['normalizedAxes']}
