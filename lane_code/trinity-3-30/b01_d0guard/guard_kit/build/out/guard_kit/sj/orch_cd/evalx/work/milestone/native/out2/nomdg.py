import argparse
from copy import deepcopy
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import perception as P
import reader_policy as Q
import geometry_refusals as GR
from r1 import FAMILIES,accounting,family,rules
from runtime_tree import identity as tree_identity

SCHEMA='legs1-routed-nomdg-v1'
FUSION='fit_gbox_policy_voteb5_best1_v1'


def has_mdg(artifact,cfg):
    present='mdg' in artifact or 'mdg' in cfg
    if present and (not artifact.get('mdg') or not cfg.get('mdg')):
        raise ValueError('Checkpoint/config MDG identity differs; no fallback is permitted')
    return present


def requested(args):
    if getattr(args,'arm',None)=='paired' or getattr(args,'scope',None)=='r1':
        return True
    if getattr(args,'config',None) and getattr(args,'export',None) and local(args.export).is_file():
        return not has_mdg(load(args.export),load(args.config))
    return False


def mask_source(typ):
    if family(typ) not in FAMILIES:
        raise ValueError('Type is outside no-MDG R1')
    return 'svp_sam3' if family(typ)=='object_abs_distance' else None


def adapter_sources():
    names=('routed.py','nomdg.py','perception.py','r1.py','common.py','geometry.py','camera_cohort.py',
           'runtime_tree.py','RUNTIME_TREE.json','frozen_kit.py','camera_report.py','CAMERA_SHORTCUTS.json',
           'read_runtime.py','reader_policy.py','geometry_refusals.py','gravity_guard.py')
    result={name:sha(OUT/name) for name in names}
    for p in sorted(P.KIT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            result[str(p.relative_to(OUT))]=sha(p)
    return result


def tasks_and_captures(inputs):
    tasks=rows(checked(inputs['tasks']))
    if inputs.get('camera_cohort'):
        from camera_cohort import load_tasks
        tasks+=load_tasks(inputs['camera_cohort'],inputs['frames'])
    captures=load(checked(inputs['frames']))['captures']
    if len({t['id'] for t in tasks})!=len(tasks) or len({c['native'] for c in captures})!=len(captures):
        raise ValueError('Duplicate task or capture identity')
    return tasks,{c['native']:c for c in captures}


def item_perception(task,capture,request,geometry,cache):
    from routed import trainer_row
    row=trainer_row(task,capture,request['frames_root'])
    clip=row['student_input']['video_identity']['video_sha256']
    source=mask_source(task['question_type'])
    entry=None
    if source is not None and cache is not None:
        entry=cache['captures'][task['native']]['cache']
    refusal=request.get('geometry_refusals',{}).get(task['id'])
    value=dict(pose='frozen_g3t_checkpoint_scale_gravity',depth='tower_scaled',
               mask_source=source,geometry=geometry['videos'].get(clip) if geometry and refusal else
               geometry['videos'][clip] if geometry else None,
               geometry_manifest=request['grounding']['geometry_manifest'],
               checkpoint=request['artifact'],clip=clip,
               masks=entry,mask_manifest=cache['manifest'] if source and cache else None,
               mask_kit=cache['frozen_kit'] if source and cache else None,
               proposal_setting=P.SETTING if source else None,
               candidate_policy=request['candidate_policy'] if source else None,
               fusion_policy=FUSION,frame_indices=capture['anchor_indices'],
               frame_sha256=[p['sha256'] for p in capture['frames']])
    if refusal:value['geometry_refusal']=refusal
    return value


def operand_refusals(tasks,references,masks):
    if masks is None:
        return {}
    errors={}
    for task in tasks:
        if mask_source(task['question_type']):
            names=P.script_operands(task,references)
            try:
                masks.require_operands(task['native'],names)
            except P.MaskOperandMissing as exc:
                errors[task['id']]=str(exc)
    return errors


def universe_admission(tasks,references,masks):
    if masks is None:
        return {}
    from student_pilot.scene_state import normalize_name
    audit={}
    for task in tasks:
        if family(task['question_type'])!='object_abs_distance':
            continue
        phrases=masks.captures[task['native']]['phrases']
        universe=P.candidate_universe(phrases)
        operands=[]
        for name in P.script_operands(task,references):
            try:
                P.require_phrases(task['native'],[name],phrases)
                admitted=True
            except P.MaskOperandMissing:
                admitted=False
            runtime=normalize_name(name) in universe
            if admitted and not runtime:
                raise ValueError('The runtime universe refuses a cache-admitted operand')
            operands.append(dict(name=name,cache_admitted=admitted,runtime_universe_admitted=runtime))
        audit[task['id']]=dict(native=task['native'],universe=list(universe),operands=operands,
                               geometry_or_policy_success_claimed=False)
    return audit


def refusal_decode(code,scripted=False):
    value=dict(text='',calls=[],errors=1,version_error='version' in code or 'requires_v3.' in code,
               finish='program_refusal',refusal=code,tokens=[],generated_tokens=0,strict_no_answer=True)
    if scripted:
        value.update(script_answer=None,script_mode='native_v314_measurement_no_lm_answer')
    return value


def validate_request(r,live=False):
    from routed import source_pins
    if (r.get('schema'),r.get('arm'),r.get('scope'))!=(SCHEMA,'paired','r1'):
        raise ValueError('No-MDG reads require the paired five-type R1 scope')
    if (r.get('mask_source'),r.get('prompt_flag'),r.get('max_new_tokens'),
        r.get('thinking'),r.get('decoding'),r.get('layout'))!=('by_type',None,16384,True,'greedy','duplicate'):
        raise ValueError('No-MDG natural-generation protocol differs')
    if r.get('decode_budget')!=Q.DECODE_BUDGET or r.get('candidate_universe_policy')!=Q.UNIVERSE:
        raise ValueError('The bound reader budget or candidate universe differs')
    if r.get('geometry_refusal_policy')!=GR.POLICY:
        raise ValueError('The bound geometry refusal policy differs')
    if r.get('fusion_policy')!=FUSION or r['grounding'].get('allow_own_fallback') is not False or r['grounding'].get('depth_source')!='tower_scaled':
        raise ValueError('Require frozen G3T geometry without fallback')
    if not re.fullmatch('[0-9a-f]{64}',r['artifact']['sha256']) or r['artifact']['sha256']=='0'*64:
        raise ValueError('Unbound artifact')
    if digest({k:v for k,v in r.items() if k!='binding'})!=r['binding']:
        raise ValueError('Routed binding differs')
    if r['adapter_sources']!=adapter_sources() or r['tree_sources']!=source_pins():
        raise ValueError('Runtime/adapter source differs')
    if r.get('runtime_tree')!=tree_identity(TREE,r['tree_sources']):
        raise ValueError('Recorded runtime tree differs')
    install_tree()
    import gravity_guard
    if r.get('gravity_guard') != gravity_guard.identity():
        raise ValueError('Gravity guard request identity differs')
    from student_pilot.s1_grounding import default_policy
    if r['candidate_policy']!=default_policy():
        raise ValueError('Frozen candidate policy differs')
    for value in r['inputs'].values():
        checked(value)
    cfg=load(checked(r['config']));artifact=load(checked(r['artifact']))
    if has_mdg(artifact,cfg):
        raise ValueError('MDG checkpoints must retain the original reader')
    if (cfg.get('frame_layout'),cfg.get('training_mode'),cfg.get('trace_program_version'))!=('duplicate','final','3.14'):
        raise ValueError('Training layout/version differs')
    if cfg.get('depth_enabled') is not True or cfg.get('depth_fov_source')!='pose_head':
        raise ValueError('Require checkpoint depth and pose-head FoV for scale/gravity')
    if cfg.get('tool_mode_flag') or cfg.get('s1_route_policy',{}).get('name')!='frozen-table-no-flag-v1':
        raise ValueError('This R1 path requires the authenticated no-flag policy')
    if artifact.get('step')!=r['step'] or artifact.get('trace_program_version')!='3.14':
        raise ValueError('Export step/version differs')
    if r['route_table']!=cfg['route_table']:
        raise ValueError('R1 route table differs from training')
    tasks,captures=tasks_and_captures(r['inputs'])
    chosen=[t for t in tasks if family(t['question_type']) in FAMILIES]
    if r.get('query_journal')!=Q.journal_policy([
            dict(key='devrows:'+t['id'],family=family(t['question_type'])) for t in chosen]):
        raise ValueError('The bound ground-query journal policy differs')
    if r['keys']!=['devrows:'+t['id'] for t in chosen] or not chosen:
        raise ValueError('R1 cohort membership differs')
    if any(r['route_table'].get(t['question_type'])!='route' for t in chosen):
        raise ValueError('Selected type is not routed by the checkpoint')
    g=load(checked(r['grounding']['geometry_manifest'])) if r['grounding']['geometry_manifest'] else None
    masks=P.Masks(r['mask_cache']) if r['mask_cache'] else None
    refs=load(checked(r['inputs']['references']))
    refused=GR.item_refusals(chosen,g) if g else {}
    if r.get('geometry_refusals')!=refused:
        raise ValueError('Bound per-capture geometry refusals differ')
    served=[t for t in chosen if t['id'] not in refused]
    if r.get('mask_operand_refusals')!=operand_refusals(served,refs,masks):
        raise ValueError('Bound mask-operand refusal accounting differs')
    if r.get('candidate_universe_admission')!=universe_admission(served,refs,masks):
        raise ValueError('The bound per-item runtime universe differs')
    if live:
        if r['dry'] or r['parent_standin']:
            raise ValueError('Dry/parent routed bind cannot launch')
        if not r.get('data_receipt'):
            raise ValueError('Live native read needs the mirrored production data receipt')
        from read_runtime import prepared
        prepared(r['config'],r['artifact'],r['data_receipt'])
        if g is None or masks is None:
            raise ValueError('Live read needs checkpoint geometry and the frozen mask cache')
        from geometry import validate_manifest
        validate_manifest(g,r['artifact'],sorted({t['native'] for t in chosen}))
        if g.get('config')!=r['config']:
            raise ValueError('Geometry conditioning config differs')
        from routed import trainer_row
        for t in chosen:
            if t['id'] in refused:continue
            row=trainer_row(t,captures[t['native']],r['frames_root'],verify=True)
            P.script_calls(t,refs)
            P.load_geometry(g,row)
            if mask_source(t['question_type']) and t['id'] not in r['mask_operand_refusals']:
                masks.for_item(t['native'],row,dict(frame_indices=row['student_input']['frame_indices']),
                               operands=P.script_operands(t,refs))
    expected={t['id']:item_perception(t,captures[t['native']],r,g,masks.receipt if masks else None) for t in chosen}
    if r['perceptions']!=expected:
        raise ValueError('Bound per-item perception differs')
    return r


def bind(args):
    from routed import source_pins
    if args.arm!='paired' or args.scope!='r1':
        raise ValueError('A no-MDG checkpoint uses --arm paired --scope r1, not forced-path controls')
    if args.parent_standin or args.step<=0 or not args.config:
        raise ValueError('Require a real step/config identity; no parent stand-in')
    dest=local(args.dest)
    if dest.exists():
        raise ValueError('Routed destination exists')
    artifact=dict(path=str(local(args.export)),sha256=args.sha256)
    cfg=load(args.config)
    if has_mdg(load(checked(artifact)),cfg):
        raise ValueError('MDG checkpoints must retain the original reader')
    install_tree()
    from student_pilot.s1_grounding import default_policy
    r=dict(schema=SCHEMA,arm='paired',scope='r1',step=args.step,dry=args.dry,parent_standin=False,
           artifact=artifact,config=pin(args.config),mask_source='by_type',
           data_receipt=pin(args.data_receipt) if getattr(args,'data_receipt',None) else None,
           grounding=dict(geometry_manifest=pin(args.geometry) if args.geometry else None,
                          depth_source='tower_scaled',allow_own_fallback=False),
           mask_cache=pin(args.mask_cache) if args.mask_cache else None,
           fusion_policy=FUSION,candidate_policy=default_policy(),route_table=cfg['route_table'],
           tree_sources=source_pins(),adapter_sources=adapter_sources(),
           max_new_tokens=16384,thinking=True,decoding='greedy',layout='duplicate',prompt_flag=None,
           decode_budget=dict(Q.DECODE_BUDGET),candidate_universe_policy=Q.UNIVERSE,
           geometry_refusal_policy=GR.POLICY,
           frames_root=str(local(args.frames_root)),output=str(dest/'results'),
           inputs={n:pin(p) for n,p in dict(tasks=VENDOR/'r3/TASKS.jsonl',frames=VENDOR/'r3/FRAMES.json',
                                           references=OUT/'SCRIPTED_REFERENCES.json').items()})
    if getattr(args,'camera_cohort',None):
        r['inputs']['camera_cohort']=pin(args.camera_cohort)
    import gravity_guard
    r['gravity_guard']=gravity_guard.identity()
    r['runtime_tree']=tree_identity(TREE,r['tree_sources'])
    tasks,captures=tasks_and_captures(r['inputs'])
    chosen=[t for t in tasks if family(t['question_type']) in FAMILIES]
    r['query_journal']=Q.journal_policy([
        dict(key='devrows:'+t['id'],family=family(t['question_type'])) for t in chosen])
    g=load(checked(r['grounding']['geometry_manifest'])) if r['grounding']['geometry_manifest'] else None
    cache=load(checked(r['mask_cache'])) if r['mask_cache'] else None
    masks=P.Masks(r['mask_cache']) if r['mask_cache'] else None
    references=load(checked(r['inputs']['references']))
    r['geometry_refusals']=GR.item_refusals(chosen,g) if g else {}
    served=[t for t in chosen if t['id'] not in r['geometry_refusals']]
    r['mask_operand_refusals']=operand_refusals(served,references,masks)
    r['candidate_universe_admission']=universe_admission(served,references,masks)
    r['keys']=['devrows:'+t['id'] for t in chosen]
    r['perceptions']={t['id']:item_perception(t,captures[t['native']],r,g,cache) for t in chosen}
    r['binding']=digest(r)
    validate_request(r,not args.dry)
    dest.mkdir(parents=True)
    dump(dest/'request.json',r)
    dump(dest/'BIND_STATUS.json',dict(items=len(chosen),ready=not args.dry,
         geometry_refusals=r['geometry_refusals'],
         mask_operand_refusals=r['mask_operand_refusals'],
         refused_items=len(r['mask_operand_refusals']),
         missing_types=sorted(set(FAMILIES)-{family(t['question_type']) for t in chosen}),
         R1b='NOT MEASURABLE',R2='NOT MEASURABLE',
         pending=['native export restoration, GPU prompt/pixel/cache parity, learned call rate and scores']))
    print(json.dumps(dict(items=len(chosen),dry=args.dry,binding=r['binding'])))


def geometry_refusal_pair(task,request):
    return GR.refusal_pair(task,request,Q.question_unit(task['question']))


def geometry_score_report(data,tasks,request):
    expected=[dict(key='devrows:'+t['id'],family=family(t['question_type']),
                   label='released_answer' if t['stratum']=='primary' else 'answer',
                   geometry_refused=t['id'] in request['geometry_refusals']) for t in tasks]
    return GR.score_report(data,expected)


def make_record(task,decoded,request,prefill,arm,seconds=0.):
    from routed import native_score
    from evalpath.run import score_item
    scored=score_item({**task,'ground_truth':task['answer']},decoded)
    no_answer=bool(decoded.get('strict_no_answer') or scored['parse_failed']
                   or not re.search(r'</think\s*>',decoded['text'],re.I))
    labels=dict(answer=task['answer'],released_answer=task.get('released_answer_in_options',task.get('released_answer')))
    scores={k:None if label is None else 0. if no_answer else
            native_score(task,label,decoded) for k,label in labels.items()}
    perception=request['perceptions'][task['id']]
    return dict(key='devrows:'+task['id'],arm=arm,room=task['room'],question_type=task['question_type'],
                stratum=task['stratum'],scores=scores,
                capped=scored['hit_token_cap'] or Q.is_capped(decoded),no_answer=no_answer,
                **accounting(decoded),**Q.call_audit(decoded),checkpoint_sha256=request['artifact']['sha256'],
                perception=perception,mask_source=perception['mask_source'],
                perception_identity=digest(perception),prefill_identity=prefill,binding=request['binding'],
                question_unit=Q.question_unit(task['question']),
                decode=Q.journal_decode(decoded,'devrows:'+task['id'] in request['query_journal']['keep_full_keys']),
                seconds=seconds)


def parity_selection(tasks):
    selected = {name: next((key for key in sorted(tasks)
                            if family(tasks[key]['question_type']) == name), None)
                for name in FAMILIES}
    present = {name: key for name, key in selected.items() if key is not None}
    if not present:
        raise ValueError('Parity requires at least one routed family')
    return dict(items=present, absent_families=[name for name in FAMILIES if name not in present],
                probe_key=present.get('camera_displacement', next(iter(present.values()))))


def run(args,request):
    if not args.device.startswith('cuda:'):
        raise ValueError('Production routed read requires an assigned card')
    install_tree()
    from evalpath import runtime
    from evalpath.items import assert_prompt_equal
    from evalpath.parity import LogitTap,p1,p2,p3
    from student_pilot import carrier_c1_run as trainer
    from trace_format.program_errors import ProgramRefusal
    from routed import trainer_row
    import read_runtime
    trace_state=dict(probe=True,row=None,seen=set())
    original_prompt=runtime.prompt_batch
    original_generate=P.generate
    original_record=globals()['make_record']
    def emit(event,**value):
        print(json.dumps(dict(event=event,**value),sort_keys=True),flush=True)
    def trace_label(row):
        typ=family(row['question_type'])
        return 'camera' if typ.startswith('camera_') else {
            'object_abs_distance':'distance','room_size_estimation':'room'}.get(typ)
    def emit_decode(label,row,decoded,tap):
        positions={} if tap is None else tap.positions
        tokens=[]
        for index,token in enumerate(decoded.get('tokens',[])):
            sampled=positions.get(index)
            tokens.append(dict(position=index,id=token,piece=processor.tokenizer.convert_ids_to_tokens(token),
                sampled=sampled is not None,top2=None if sampled is None else sampled['top2'],
                margin=None if sampled is None else sampled['margin']))
        emit('native_decode_trace',scope=label,key=row.get('qid',row.get('id')),
             question_type=row['question_type'],tokens=tokens,finish=decoded.get('finish'),
             generated_tokens=decoded.get('generated_tokens'),
             decode_budget=decoded.get('decode_budget'),**Q.call_audit(decoded),
             calls=[{key:call.get(key) for key in ('call','kind','response')} for call in decoded['calls']])
    def traced_prompt(*values,**options):
        trace_state['row']=values[1] if len(values)>1 else options['row']
        return original_prompt(*values,**options)
    def traced_generate(*values,**options):
        row=trace_state['row']
        label='probe' if trace_state['probe'] else trace_label(row)
        selected=label is not None and label not in trace_state['seen']
        tap=options.get('tap')
        if selected and tap is None:
            tap=LogitTap();options['tap']=tap
        decoded=original_generate(*values,**options)
        if selected:
            emit_decode(label,row,decoded,tap)
            if label!='probe':trace_state['seen'].add(label)
        return decoded
    def traced_record(*values,**options):
        result=original_record(*values,**options)
        if values[4]=='unflagged' and not trace_state['probe']:
            row,decoded=values[:2];label=trace_label(row)
            if label is not None and label not in trace_state['seen']:
                emit_decode(label,row,decoded,None);trace_state['seen'].add(label)
        return result
    make_record=traced_record
    cfg=load(checked(request['config']))
    selected=dict(root=str(TREE),sources={n.removeprefix('student_pilot/'):h for n,h in request['tree_sources'].items() if n.startswith('student_pilot/')})
    model,processor,info=read_runtime.load_model(request['config'],request['artifact'],request['data_receipt'],
        device=args.device,selected_trainer=selected)
    layers=[]
    for name,layer in model.named_modules():
        if not type(layer).__name__.endswith('GatedDeltaNet'):
            continue
        module=sys.modules.get(type(layer).__module__);bindings={}
        for field in ('causal_conv1d_fn','causal_conv1d_update','chunk_gated_delta_rule','fused_recurrent_gated_delta_rule'):
            target=getattr(layer,field,getattr(module,field,None))
            bindings[field]=None if target is None else dict(
                scope='layer' if hasattr(layer,field) else 'module',
                module=getattr(target,'__module__',type(target).__module__),
                name=getattr(target,'__qualname__',type(target).__qualname__))
        layers.append(dict(layer=name,kind=type(layer).__name__,
                           is_fast_path_available=getattr(module,'is_fast_path_available',None),bindings=bindings))
    emit('native_runtime_bindings',routing_token_ids=getattr(processor,'_routing_tokens',{}).get('ids'),
         tokenizer_length=len(processor.tokenizer),layers=layers)
    runtime.prompt_batch=traced_prompt
    P.generate=traced_generate
    tasks,captures=tasks_and_captures(request['inputs'])
    tasks={'devrows:'+t['id']:t for t in tasks}
    refs=load(checked(request['inputs']['references']))
    g=load(checked(request['grounding']['geometry_manifest']));masks=P.Masks(request['mask_cache'])
    out=local(request['output']);out.mkdir(parents=True,exist_ok=False)
    selection=parity_selection(tasks)
    dump(out/'LOAD_RECEIPT.json',dict(info,runtime_tree=request['runtime_tree'],parity_selection=selection))
    first=tasks[selection['probe_key']]
    probe=trainer_row(first,captures[first['native']],request['frames_root'],verify=True)
    assert_prompt_equal(processor,probe)
    pb=move_batch(runtime.prompt_batch(processor,probe,cfg,'routed'),args.device)
    tap=LogitTap();pd=P.generate(model,processor,pb,None,tap=tap)
    dump(out/'PARITY_DECODE.json',pd)
    legacy=deepcopy(pd)
    if not legacy['heads'].get('ground_queries'):
        legacy['heads'].pop('trace313_live',None)
    parity=dict(P1=p1(model,processor,probe,cfg,'routed',pb,pd,tap,True),
                P2=p2(model,pb,legacy,'routed',True),P3=p3(processor,probe,cfg,pb,True),
                 camera_call=any(c['kind']=='head' and c['call'].startswith(('<move ','<turn ','<pose ')) for c in pd['calls']),
                 call_errors=pd['errors'],scope='unscored native own-head parity; external perception replays per item')
    parity['P2']['pass']=parity['P2']['pass'] and parity['P2']['independent_calls']>=1
    emit('native_probe_p2',independent_calls=parity['P2']['independent_calls'],
         passed=parity['P2']['pass'],camera_call=parity['camera_call'])
    import math
    sealed_p1=parity['P1']
    p1_gate=dict(margin_limit=1.0,positions_per_tie=100,minimum_ties=1,
                 checked=sealed_p1['checked'],rounding_level_ties=[],rejected_positions=[])
    for mismatch in sealed_p1['mismatches']:
        cached=mismatch.get('cached') if isinstance(mismatch,dict) else None
        valid=(isinstance(cached,dict)
               and all(key in cached for key in ('top2','logits','margin'))
               and all(key in mismatch for key in
                       ('generated_position','uncached_top2','uncached_logits','uncached_margin')))
        if valid:
            ids=(cached['top2'],mismatch['uncached_top2'])
            logits=(cached['logits'],mismatch['uncached_logits'])
            valid=(all(isinstance(pair,(list,tuple)) and len(pair)==2
                       and all(type(token) is int for token in pair) for pair in ids)
                   and all(isinstance(pair,(list,tuple)) and len(pair)==2
                           and all(type(value) in (int,float) and math.isfinite(value)
                                   for value in pair) for pair in logits)
                   and all(type(value) in (int,float) and math.isfinite(value)
                           for value in (cached['margin'],mismatch['uncached_margin'])))
        if (valid and set(cached['top2'])==set(mismatch['uncached_top2'])
                and cached['margin']<=p1_gate['margin_limit']
                and mismatch['uncached_margin']<=p1_gate['margin_limit']):
            p1_gate['rounding_level_ties'].append(dict(
                generated_position=mismatch['generated_position'],
                cached_ids=cached['top2'],uncached_ids=mismatch['uncached_top2'],
                cached_logits=cached['logits'],uncached_logits=mismatch['uncached_logits'],
                cached_margin=cached['margin'],uncached_margin=mismatch['uncached_margin']))
        else:
            p1_gate['rejected_positions'].append(
                mismatch.get('generated_position') if isinstance(mismatch,dict) else None)
    p1_gate['tie_count']=len(p1_gate['rounding_level_ties'])
    p1_gate['tie_limit']=max(p1_gate['minimum_ties'],sealed_p1['checked']//p1_gate['positions_per_tie'])
    p1_gate['sequence_exact']=sealed_p1['sequence']['exact']
    p1_gate['cached_positions_complete']=sealed_p1['cached_positions_complete']
    p1_gate['pass']=(p1_gate['sequence_exact'] and p1_gate['cached_positions_complete']
                     and not p1_gate['rejected_positions'] and p1_gate['tie_count']<=p1_gate['tie_limit'])
    parity['p1_gate']=p1_gate
    parity['selection']=selection
    camera_required='camera_displacement' in selection['items']
    parity['pass']=p1_gate['pass'] and all(parity[k]['pass'] for k in ('P2','P3')) and (parity['camera_call'] or not camera_required) and not parity['call_errors']
    dump(out/'GPU_PARITY.json',parity)
    if not parity['pass']:
        raise ValueError('Native GPU prompt/pixel/cache/head parity failed')
    trace_state['probe']=False
    count=0
    for key in request['keys']:
        start=time.monotonic();task=tasks[key]
        def serve_pair():
            row=trainer_row(task,captures[task['native']],request['frames_root'],verify=True)
            assert_prompt_equal(processor,row)
            batch=move_batch(runtime.prompt_batch(processor,row,cfg,'routed'),args.device)
            geo=P.load_geometry(g,row)
            backend=None
            refusal=request['mask_operand_refusals'].get(task['id'])
            if mask_source(task['question_type']) and not refusal:
                source=masks.for_item(task['native'],row,batch,operands=P.script_operands(task,refs))
                backend=P.backend(row,batch,geo,source,out/'grounding'/digest(key))
            prefill=digest(batch['input_ids'].detach().cpu().tolist())
            if refusal:
                decoded=refusal_decode(refusal)
            else:
                try:
                    decoded=P.generate(model,processor,batch,geo,backend,budget=request['decode_budget'])
                except ProgramRefusal as exc:
                    decoded=refusal_decode(str(exc))
            if decoded['calls']:
                replay=P.replay(decoded,geo,backend)
                if not replay['byte_equal']:
                    dump(out/'REPLAY_REFUSAL.json',dict(key=key,decode=decoded,replay=replay))
                    raise ValueError('External-perception runtime replay differs')
            pair=[make_record(task,decoded,request,prefill,'unflagged',time.monotonic()-start)]
            script=refusal_decode(refusal,scripted=True) if refusal else P.scripted(task,refs,geo,backend)
            if not P.replay(script,geo,backend)['byte_equal']:
                raise ValueError('Scripted runtime replay differs')
            pair.append(make_record(task,script,request,prefill,'scripted'))
            return pair
        pair=GR.paired_item(task,request,Q.question_unit(task['question']),serve_pair)
        with (out/'items.jsonl').open('a') as stream:
            for record in pair:
                stream.write(json.dumps(record,allow_nan=False)+'\n')
        count+=1
        if args.first_minute:
            dump(out/'FIRST_ITEM.json',dict(key=key,scope='one paired item; not a completed R1 cell',
                 call_rate_observation=pair[0]['called'],call_errors=pair[0]['call_errors'],
                 version_errors=pair[0]['version_errors'],seconds=time.monotonic()-start))
            return
    dump(out/'COMPLETE.json',dict(schema='legs1-r1-complete-v1',synthetic=False,
         request=pin(local(args.dest)/'request.json'),journal=pin(out/'items.jsonl'),
         parity=pin(out/'GPU_PARITY.json'),items=count))


def merge(args):
    d=local(args.paired)
    request=validate_request(load(d/'request.json'),live=True)
    c=load(d/'results/COMPLETE.json')
    if c.get('schema')!='legs1-r1-complete-v1' or c.get('synthetic') is not False or c['request']!=pin(d/'request.json'):
        raise ValueError('R1 completion/request differs or is synthetic')
    if c['items']!=len(request['keys']) or not load(checked(c['parity']))['pass']:
        raise ValueError('R1 completion or GPU parity failed')
    data=rows(checked(c['journal']))
    if len(data)!=2*len(request['keys']):
        raise ValueError('R1 paired journal incomplete')
    bundle=dict(schema='legs1-r1-nomdg-v1',synthetic=False,
                arms={name:[r for r in data if r['arm']==name] for name in ('unflagged','scripted')},
                expected_keys=request['keys'],artifact_sha256=request['artifact']['sha256'],
                binding=request['binding'],perception_by_key={'devrows:'+k:digest(v) for k,v in request['perceptions'].items()},
                receipts=dict(complete=pin(d/'results/COMPLETE.json'),request=pin(d/'request.json')),
                adapter_sources=request['adapter_sources'])
    report=rules(bundle,step=request['step'])
    bundle['unit_scores']=Q.unit_report(data)
    tasks,_=tasks_and_captures(request['inputs'])
    chosen=[t for t in tasks if family(t['question_type']) in FAMILIES]
    bundle['geometry_scores']=geometry_score_report(data,chosen,request)
    bundle['geometry_refusal_policy']=GR.POLICY
    bundle['reader_semantics']=dict(Q.REPORT_SEMANTICS)
    bundle.update({name:report[name] for name in (
        'report_scope','training_decision_allowed','perception_disclosure')})
    dump(args.output,bundle)
    dump(str(args.output)+'.pin.json',pin(args.output))


def admit_bundle(bundle,step,artifact_sha256,raised=()):
    if bundle.get('synthetic') is not False:
        raise ValueError('Synthetic R1 bundle cannot decide a training boundary')
    c=load(checked(bundle['receipts']['complete']))
    req_pin=bundle['receipts']['request']
    r=validate_request(load(checked(req_pin)),live=True)
    if (c.get('schema'),c.get('synthetic'),c['request'])!=('legs1-r1-complete-v1',False,req_pin):
        raise ValueError('R1 completion differs')
    if (r['step'],r['artifact']['sha256'])!=(step,artifact_sha256):
        raise ValueError('Routed checkpoint differs from direct checkpoint')
    if not load(checked(c['parity']))['pass'] or c['items']!=len(r['keys']):
        raise ValueError('R1 parity/completion failed')
    native=rows(checked(c['journal']))
    arms={arm:[row for row in native if row.get('arm')==arm] for arm in ('unflagged','scripted')}
    if len(native)!=2*len(r['keys']) or bundle['arms']!=arms:
        raise ValueError('R1 bundle differs from authenticated journal')
    if (bundle['expected_keys'],bundle['binding'],bundle['artifact_sha256'],bundle['adapter_sources'])!=(
            r['keys'],r['binding'],r['artifact']['sha256'],r['adapter_sources']):
        raise ValueError('R1 bundle differs from bound cohort/source/checkpoint')
    expected={'devrows:'+k:digest(v) for k,v in r['perceptions'].items()}
    if bundle['perception_by_key']!=expected:
        raise ValueError('R1 bundle perception differs')
    tasks,_=tasks_and_captures(r['inputs'])
    chosen=[t for t in tasks if family(t['question_type']) in FAMILIES]
    lookup={arm:{row['key']:row for row in values} for arm,values in arms.items()}
    for task in chosen:
        key='devrows:'+task['id']
        pair=[lookup[arm][key] for arm in GR.ARMS]
        if task['id'] in r['geometry_refusals']:
            if pair!=geometry_refusal_pair(task,r):
                raise ValueError('A geometry-refused item differs from its bound zero-score disposition')
        elif any(row.get('geometry_refusal') for row in pair):
            raise ValueError('A passed capture has an unbound item refusal')
    geometry_scores=geometry_score_report(native,chosen,r)
    if bundle.get('geometry_scores')!=geometry_scores or bundle.get('geometry_refusal_policy')!=GR.POLICY:
        raise ValueError('The geometry-conditioned score report differs')
    report=rules(bundle,raised,step)
    report['geometry_scores']=geometry_scores
    report['geometry_refusal_policy']=GR.POLICY
    if bundle.get('reader_semantics')!=Q.REPORT_SEMANTICS:
        raise ValueError('R1 report omits the bound universe and training-response semantics')
    report['reader_semantics']=dict(Q.REPORT_SEMANTICS)
    if any(bundle.get(name)!=report[name] for name in (
            'report_scope','training_decision_allowed','perception_disclosure')):
        raise ValueError('R1 diagnostic scope or perception disclosure differs')
    from camera_report import decorate
    return decorate(report,bundle,r.get('inputs',{}))


def cache_bind(args):
    kit,variants=P.cache_tools()
    manifest=pin(args.manifest);m=load(manifest['path']);root=local(args.candidates)
    binding=pin(root/'BINDING.json');complete=pin(root/'COMPLETE.json')
    P.validate_cache_header(m,manifest['sha256'],load(binding['path']),load(complete['path']))
    items=pin(args.items)
    if items['sha256']!=m['items_sha256']:
        raise ValueError('Mask prompt-provenance items differ')
    kit.check_prompt_provenance(m,rows(items['path']))
    dense=local(args.dense_candidates);dm=pin(dense.parent/'MANIFEST.json');d=load(dm['path'])
    kit.validate_manifest(d)
    if d['experiment']['name']!='dense' or (d['checkpoint_sha256'],d['receipt_sha256'])!=(m['checkpoint_sha256'],m['receipt_sha256']):
        raise ValueError('Dense-source SAM3 identity differs')
    if m['experiment'].get('dense_source') is not None and variants.dense_source(dense)!=m['experiment']['dense_source']:
        raise ValueError('Dense-source provenance differs')
    dc={c['native']:c for c in d['captures']}
    sam=pin(P.KIT/'vendor/SAM3_RECEIPT.json')
    if sam['sha256']!=m['receipt_sha256']:
        raise ValueError('Frozen SAM3 receipt differs')
    entries={}
    for c in m['captures']:
        native=c['native'];name=c['scene'].replace('/','__')
        entry={k:pin(p) for k,p in dict(cache=root/(name+'.npz'),journal=root/(name+'.journal.jsonl'),
                  dense_cache=dense/(name+'.npz'),dense_journal=dense/(name+'.journal.jsonl')).items()}
        if {k:v for k,v in dc[native].items() if k!='cache_contract'}!={k:v for k,v in c.items() if k!='cache_contract'}:
            raise ValueError('Dense-source capture differs')
        for value,cap,mp,journal in [(entry['cache'],c,manifest,entry['journal']),
                                     (entry['dense_cache'],dc[native],dm,entry['dense_journal'])]:
            raw=kit.validate_cache(kit.load_cache(value['path']),cap,mp['sha256'],False)
            if raw.get('receipt')!=load(sam['path']):
                raise ValueError('Cached SAM3 receipt differs')
            j=rows(journal['path'])
            if not j or j[-1].get('event')!='complete' or j[-1].get('sha256')!=value['sha256']:
                raise ValueError('Candidate commit journal differs')
        if not any(e.get('event')=='reuse_dense' and e.get('sha256')==entry['dense_cache']['sha256']
                   for e in rows(entry['journal']['path'])):
            raise ValueError('Combined cache did not reuse the pinned dense source')
        entries[native]=entry
    result=dict(schema='legs1-frozen-mask-cache-v1',setting=P.SETTING,manifest=manifest,
                binding=binding,complete=complete,items=items,captures=entries,dense_manifest=dm,
                sam_receipt=sam,producer_sha256=sha(__file__),frozen_kit=P.frozen_kit.identity())
    if local(args.output).exists():
        raise ValueError('Mask receipt destination exists')
    dump(args.output,result)


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('cache-bind')
    for name in ('manifest','candidates','dense-candidates','items','output'):
        q.add_argument('--'+name,required=True)
    cache_bind(p.parse_args())


if __name__=='__main__':
    main()
