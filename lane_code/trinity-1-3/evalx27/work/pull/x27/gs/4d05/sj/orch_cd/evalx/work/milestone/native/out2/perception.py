from copy import deepcopy
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace as NS

from common import checked,digest,install_tree,load,local,pin,rows,sha
from r1 import family
import frozen_kit
import reader_policy as Q

SETTING = dict(joint_floor=.05,cap=100,prompts='dense_aliases',mask_threshold=.5,
               resolution=1008,dtype='bf16',link_instance_floor=.3)
SAM_SHA = '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'
FROZEN_DEVS1_MANIFEST = '4346f0827a068ebc9a0cb938e9da1de67307197da4748cc620e791a928e655f9'
KIT = Path(__file__).resolve().parent/'mask_kit'


def cache_tools():
    sys.path.insert(0,str(KIT))
    import kitlib,variantlib
    return kitlib,variantlib


def validate_cache_header(manifest,manifest_sha,binding,complete):
    frozen_kit.verify_local(KIT)
    if manifest.get('density')!=SETTING or manifest.get('checkpoint_sha256')!=SAM_SHA:
        raise ValueError('Frozen SAM3 setting/checkpoint differs')
    if manifest.get('experiment',{}).get('name')!='dense_aliases':
        raise ValueError('Require dense_aliases proposals')
    if any(x.get('manifest_sha256')!=manifest_sha or x.get('stub') is not False
           for x in (binding,complete)):
        raise ValueError('Incomplete or stub SAM3 cache')
    kit,variants=cache_tools()
    if manifest_sha!=FROZEN_DEVS1_MANIFEST:
        kit.validate_manifest(manifest)
        frozen_kit.validate_code(manifest,binding)
        if complete.get('captures')!=len(manifest['captures']):
            raise ValueError('SAM3 capture completion differs')
    else:
        if manifest.get('schema')!='mask-recall-variant-v1' or len(manifest['captures'])!=152:
            raise ValueError('Frozen dev-S1 cache differs')
        if any(c.get('cache_contract')!=SETTING for c in manifest['captures']):
            raise ValueError('Frozen capture setting differs')
    return manifest


class MaskOperandMissing(ValueError):
    def __init__(self,native,names):
        self.code='mask_cache_operand_missing'
        super().__init__(self.code+':'+native+':'+','.join(sorted(names)))


def candidate_universe(phrases):
    kit,_=cache_tools()
    return tuple(sorted({kit.normalize_phrase(name) for name in phrases}))


def require_phrases(native,names,phrases):
    kit,_=cache_tools()
    missing={kit.normalize_phrase(name) for name in names}-set(candidate_universe(phrases))
    if missing:
        raise MaskOperandMissing(native,missing)


class Masks:
    def __init__(self,receipt):
        self.receipt=load(checked(receipt))
        r=self.receipt
        if r.get('schema')!='legs1-frozen-mask-cache-v1' or r.get('setting')!=SETTING:
            raise ValueError('Invalid frozen mask receipt')
        if r.get('frozen_kit')!=frozen_kit.identity():
            raise ValueError('Frozen mask receipt kit identity differs')
        if r.get('producer_sha256')!=sha(Path(__file__).with_name('nomdg.py')):
            raise ValueError('Frozen cache validator source differs')
        self.manifest=load(checked(r['manifest']))
        validate_cache_header(self.manifest,r['manifest']['sha256'],
                              load(checked(r['binding'])),load(checked(r['complete'])))
        self.captures={c['native']:c for c in self.manifest['captures']}
        if len(self.captures)!=len(self.manifest['captures']) or set(r['captures'])!=set(self.captures):
            raise ValueError('Mask receipt capture membership differs')
        if r['items']['sha256']!=self.manifest.get('items_sha256'):
            raise ValueError('SAM3 prompt-provenance item pin differs')
        checked(r['items'])
        if sha(checked(r['sam_receipt']))!=self.manifest['receipt_sha256']:
            raise ValueError('SAM3 receipt identity differs')
        self.dense_manifest=load(checked(r['dense_manifest']))
        if (self.dense_manifest['experiment']['name'],self.dense_manifest['checkpoint_sha256'],
            self.dense_manifest['receipt_sha256'])!=('dense',SAM_SHA,self.manifest['receipt_sha256']):
            raise ValueError('Dense-source identity differs')
        self.dense_captures={c['native']:c for c in self.dense_manifest['captures']}
        kit,_=cache_tools()
        kit.check_prompt_provenance(self.manifest,rows(r['items']['path']))
        self.loaded={}

    def require_operands(self,native,names):
        require_phrases(native,names,self.captures[native]['phrases'])

    def for_item(self,native,row,batch,operands=()):
        from student_pilot.ground_sources import CachedSAM3
        kit,_=cache_tools()
        c=self.captures[native];entry=self.receipt['captures'][native]
        si=row['student_input']
        if c['anchor_indices']!=list(batch['frame_indices']) or [f['sha256'] for f in c['frames']]!=[f['sha256'] for f in si['frames']]:
            raise ValueError('SAM3 and runtime frame indices/RGB hashes differ')
        names=candidate_universe(c['phrases'])
        self.require_operands(native,operands)
        if native not in self.loaded:
            raw=kit.validate_cache(kit.load_cache(checked(entry['cache'])),c,
                                   self.receipt['manifest']['sha256'],False)
            journal=rows(checked(entry['journal']))
            if not journal or journal[-1].get('event')!='complete' or journal[-1].get('sha256')!=entry['cache']['sha256']:
                raise ValueError('SAM3 cache commit journal differs')
            dense=kit.validate_cache(kit.load_cache(checked(entry['dense_cache'])),self.dense_captures[native],
                                     self.receipt['dense_manifest']['sha256'],False)
            dj=rows(checked(entry['dense_journal']))
            if not dj or dj[-1].get('event')!='complete' or dj[-1].get('sha256')!=entry['dense_cache']['sha256']:
                raise ValueError('Dense-source commit journal differs')
            if not any(e.get('event')=='reuse_dense' and e.get('sha256')==entry['dense_cache']['sha256'] for e in journal):
                raise ValueError('Combined cache did not reuse the pinned dense source')
            receipt=load(self.receipt['sam_receipt']['path'])
            if raw.get('receipt')!=receipt or dense.get('receipt')!=receipt:
                raise ValueError('Cached SAM3 receipt differs')
            self.loaded[native]=raw
        source=CachedSAM3.__new__(CachedSAM3)
        source.cache=self.loaded[native]
        source.reader=NS(phrase=kit.normalize_phrase,rle_decode=kit.decode)
        source.live=None
        source.frame_indices=tuple(c['anchor_indices'])
        source.names=names
        source.identity=digest(dict(cache=entry['cache'],manifest=self.receipt['manifest'],
                                    frames=[f['sha256'] for f in c['frames']],setting=SETTING,
                                    candidate_universe=names))
        source.provenance='frozen_dense_aliases_exact_rgb32'
        return source


def load_geometry(manifest,row):
    from student_pilot.ground_profiles import load_geometry as native
    from student_pilot.scene_state import FrameMap
    clip=row['student_input']['video_identity']['video_sha256']
    entry=manifest['videos'][clip]
    geometry=native(checked(entry),FrameMap(tuple(row['student_input']['frame_indices'])),'tower_scaled')
    if geometry.contract.profile!='scaled_g3t_depth' or geometry.depth_scale_count!=1:
        raise ValueError('Require checkpoint-conditioned explicit G3T geometry, scaled once')
    return geometry


def backend(row,batch,geometry,source,audit_dir):
    from student_pilot.ground_profiles import build_profile
    from student_pilot.s1_grounding import default_policy
    from student_pilot.scene_state import FrameMap,SceneState
    scene=SceneState(batch['video_sha256'],FrameMap(tuple(batch['frame_indices'])),geometry.identity)
    value=build_profile('native_selector',scene,geometry,source,depth_source='tower_scaled',
                        audit_dir=audit_dir,ground_candidate_policy=default_policy(),
                        question_type=row['question_type'])
    if value.geometry_error:
        raise ValueError(value.geometry_error)
    value.allow_own_geometry_fallback=False
    value.geometry_source='checkpoint_conditioned_frozen_g3t'
    value.frozen_mask_source=source
    return value


def camera_geometry(geometry,queries):
    import numpy as np
    from student_pilot.camera_targets import quaternion_xyzw
    from student_pilot.carrier_c1_routing import OwnGeometry
    first_R,first_t=geometry.cam(1)
    pose=np.empty((32,9),dtype=np.float64)
    for k in range(1,33):
        rotation,centre=geometry.cam(k)
        pose[k-1,:3]=rotation.T@(first_t-centre)
        pose[k-1,3:7]=quaternion_xyzw(rotation.T@first_R)
        pose[k-1,7:]=geometry.fov_of(k)
    up=first_R.T@np.array([0.,0.,1.])
    def depth(frame,points):
        result=geometry.depth(frame,points)
        queries.append(dict(frame=frame,depth=result.tolist()))
        return result
    return OwnGeometry(pose,up,depth),pose,up


def session(geometry,ground_backend=None):
    from student_pilot.live_trace313 import LiveSession
    owner=ground_backend or NS(geometry=geometry,allow_own_geometry_fallback=geometry is None,
                              geometry_error=None)

    class PerceptionSession(LiveSession):
        def execute(self,call):
            source=getattr(ground_backend,'frozen_mask_source',None)
            names=re.findall(r'\bobj="([^"<>]+)"',call) if call.startswith('<ground') else []
            if source is not None and names:
                require_phrases('runtime',names,source.cache['phrases'])
            return super().execute(call)

        def _instances(self,name):
            if ground_backend is None:
                raise ValueError('mask_source_unavailable_for_type')
            objects=super()._instances(name)
            query=self.queries[-1]
            applied={item['instance_id']:item.get('depth_cut_applied',False)
                     for item in query.get('instances',[])}
            for obj in objects:
                if obj.get('seen') and 'points_cut' not in obj:
                    if applied.get(obj['instance_id']) is not True:
                        raise ValueError('frozen_fusion_requires_depth_cut_receipt')
                    obj['points_cut']=deepcopy(obj['points'])
            return objects

        def bind_state(self,state):
            super().bind_state(state)
            if geometry is not None:
                state.heads.queries=[]
                state.geometry,pose,up=camera_geometry(geometry,state.heads.queries)
                state.geometry_error=None
                state.heads.pose9,state.heads.gravity=pose,up
                state.tool_context.geometry=geometry

    return PerceptionSession(owner,program_version='3.14',geometry_mode='predicted')


def generate(model,processor,batch,geometry,ground_backend=None,tap=None,budget=None):
    from student_pilot.carrier_c1_decode import generate as native,MAX_CALL_TOKENS
    if getattr(model,'trace_program_version',None)!='3.14':
        raise ValueError('Loaded trace version differs')
    if hasattr(getattr(model,'auxiliary_heads',None),'mdg') or getattr(model,'mdg_head',None) is not None:
        raise ValueError('No-MDG path refuses an attached MDG head')
    guard=None
    if budget is not None:
        if MAX_CALL_TOKENS!=Q.DECODE_BUDGET['call_window_tokens']:
            raise ValueError('The sealed decoder call window differs from the budget')
        tokens=getattr(processor,'_routing_tokens',None)
        if tokens is None:
            raise ValueError('Processor lacks the routing opener tokens')
        guard=Q.ThinkingBudget(processor.tokenizer,budget,openers=tokens['ids'].values())
    def process(ids,logits):
        return guard(ids,tap(ids,logits) if tap is not None else logits)
    decoded=native(model,processor,batch,max_new_tokens=Q.DECODE_BUDGET['max_new_tokens'],
                   max_calls=Q.DECODE_BUDGET['max_calls'],logits_processor=process if guard else tap,
                   ground_backend=ground_backend,mask_source='svp_sam3' if ground_backend is not None else None,
                   trace_session=session(geometry,ground_backend))
    return Q.apply_budget(decoded,guard) if guard else decoded


def execute_calls(geometry,ground_backend,calls):
    from student_pilot import carrier_c1_decode as D,trace_format313 as F
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    if ground_backend is not None:
        ground_backend.begin_question()
    s=session(geometry,ground_backend)
    @F.bind_generate
    def execute(model,processor,batch):
        heads=NS(mdg_states=None,mdg_backend=ground_backend,queries=[])
        state=NS(heads=heads,geometry=None,geometry_error=None,tool_context=NS(),
                 ground_backend=ground_backend,mdg=None,verify_session=None,rereader=None)
        F.bind_state(state)
        registry=PrintedPointRegistry()
        records=[]
        for call in calls:
            response,info=D.respond_state(state,call,registry)
            records.append(dict(call=call,response=response,**info))
        return dict(calls=records,heads=dict(pose9=heads.pose9.tolist(),gravity=heads.gravity.tolist(),
                    depth_queries=heads.queries,ground_queries=deepcopy(s.queries),
                    trace313_live=True,trace_program_version='3.14'),
                    errors=sum(r['kind']=='error' for r in records),finish='eos')
    return execute(NS(trace_program_version='3.14'),None,{},trace_session=s)


def replay(decoded,geometry,ground_backend):
    expected=execute_calls(geometry,ground_backend,[c['call'] for c in decoded['calls']])
    original=[dict(call,kind=call.get('original_kind',call['kind'])) for call in decoded['calls']]
    mismatches=sum(any(a.get(k)!=b.get(k) for k in ('call','response','kind','code'))
                   for a,b in zip(expected['calls'],original,strict=True))
    return dict(byte_equal=mismatches==0,mismatches=mismatches,calls=len(decoded['calls']),
                source='same pinned G3T geometry and frozen masks; native response dispatcher')


def script_calls(task,references):
    typ=family(task['question_type'])
    if typ=='room_size_estimation':
        return ['<ground mode="room">']
    if typ=='object_abs_distance':
        ref=references['devrows:'+task['id']]
        names=[]
        for segment in ref['segments'][:-1]:
            match=re.fullmatch(r'<ground obj="([^"<>]+)" mode="box">',segment['call'])
            if not match:
                raise ValueError('Absolute-distance reference must contain box grounds')
            name=match[1]
            if not re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',
                             task['question']+' '+' '.join(task.get('options') or []),re.I):
                raise ValueError('Script operand is not in the question/options')
            names.append(name)
        if len(names)!=2 or len(set(names))!=2:
            raise ValueError('Absolute-distance script requires two literal objects')
        old=f'<gap a="{names[0]}" b="{names[1]}" rule="sampled_box_512">'
        new=f'<gap a="{names[0]}" b="{names[1]}" rule="box_grid_5cm">'
        if ref['segments'][-1]['call'] not in (old,new):
            raise ValueError('Absolute-distance reference operands differ')
        return [f'<ground obj="{n}" mode="box">' for n in names]+[new]
    if typ not in ('camera_displacement','camera_movement_direction','camera_rotation'):
        raise ValueError('Script outside the five routed types')
    match=re.search(r'\bframe\s+(\d+)\s+(?:to|and)\s+(?:frame\s+)?(\d+)\b',task['question'],re.I)
    if not match or any(not 1<=int(n)<=32 for n in match.groups()):
        raise ValueError('Camera script needs an unambiguous frame pair in its question')
    name='turn' if typ=='camera_rotation' else 'move'
    return [f'<{name} from={int(match[1])} to={int(match[2])}>']


def script_operands(task,references):
    return re.findall(r'\bobj="([^"<>]+)"','\n'.join(script_calls(task,references)))


def script_answer(task,record):
    if record['errors']:
        return None
    body=record['calls'][-1]['response']
    typ=family(task['question_type'])
    if typ=='object_abs_distance':
        match=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',body)
    elif typ=='room_size_estimation':
        from trace_format.room_v314 import parse_response
        value=parse_response(body)['area_m2']
        return str(value/.09290304) if re.search(r'\bsquare\s+(?:feet|foot)\b',task['question'],re.I) else f'{value:.2f}'
    elif typ=='camera_displacement':
        match=re.search(r'distance = ([0-9]+\.[0-9]{2}) m$',body)
    elif typ=='camera_rotation':
        match=re.fullmatch(r'turn = ([+-]?[0-9]+) deg',body)
    else:
        values=re.fullmatch(r'dx = ([+-]?[0-9.]+) m, dy = ([+-]?[0-9.]+) m, dz = ([+-]?[0-9.]+) m, distance = [0-9.]+ m',body)
        if not values:
            return None
        x,y,z=map(float,values.groups())
        if abs(x)==abs(z) or max(abs(x),abs(z))<=abs(y):
            return None
        direction=('right' if x>0 else 'left') if abs(x)>abs(z) else ('forward' if z>0 else 'backward')
        options=[o for o in task['options'] if re.search(r'\b'+direction+r'\b',o,re.I)]
        return options[0].split('.')[0] if len(options)==1 else None
    if not match:
        return None
    if typ=='object_abs_distance':
        units=re.findall(r'\b(millimeters?|centimeters?|meters?|metres?|inches|inch|feet|foot)\b',task['question'],re.I)
        if not units:
            raise ValueError('Absolute-distance script requires an explicit question unit')
        unit=units[-1].lower()
        factor=.001 if unit.startswith('millimeter') else .01 if unit.startswith('centimeter') else .0254 if unit in ('inch','inches') else .3048 if unit in ('feet','foot') else 1.
        return str(float(match[1])/factor)
    return match[1]


def scripted(task,references,geometry,ground_backend):
    record=execute_calls(geometry,ground_backend,script_calls(task,references))
    answer=script_answer(task,record)
    trace='\n'.join(c['call']+'\n<tool_response>\n'+c['response']+'\n</tool_response>' for c in record['calls'])
    record.update(text='<think>\n'+trace+'\n</think>\n\n'+(answer or ''),tokens=[],
                  generated_tokens=0,prompt_tokens=0,script_answer=answer,
                  strict_no_answer=answer is None,script_mode='native_v314_measurement_no_lm_answer')
    return record
