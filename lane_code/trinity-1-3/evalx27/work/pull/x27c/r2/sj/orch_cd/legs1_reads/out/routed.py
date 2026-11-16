"""Dev-S1 adapter for the frozen tree's own-head evaluator, with explicit coverage."""
import argparse
from copy import deepcopy
import json
import re
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

ARMS=('forced_route','scripted','forced_direct','unflagged')
FLAGS={'forced_route':'Use your spatial tools to answer this question.',
       'scripted':'Use your spatial tools to answer this question.',
       'forced_direct':'Answer this question directly without calling any tools.','unflagged':None}
TREE_ARCHIVE_SHA='c78cb0c9e12985978c0caf4d7109dd24bd4e0754aea98fe0100a9ddb3655b983'

def source_pins():
    return {str(p.relative_to(TREE)):sha(p) for p in sorted(TREE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def trainer_row(task,capture,frames_root,verify=False):
    si=dict(frames=[dict(path=str(local(Path(frames_root)/p['path'])),sha256=p['sha256']) for p in capture['frames']],
            frame_indices=capture['anchor_indices'],timestamps=capture['timestamps'],fps=capture['fps'],
            total_num_frames=capture['total_num_frames'],question=task['question'],options=task['options'])
    # This is an explicit PNG clip identity, not a purported MP4 digest.
    clip=digest({k:si[k] for k in ('frame_indices','fps','total_num_frames')} | {'frames':[p['sha256'] for p in si['frames']]})
    si['video_identity']=dict(video_sha256=clip,kind='devS1-pinned-PNG-clip-v1')
    if verify:
        for p in si['frames']: checked(p)
    return dict(qid=task['id'],dataset=task['dataset'],scene=task['scene'],
                question_type=task['question_type'],student_input=si)

def validate_request(r,live=False):
    if r.get('schema')!='legs1-routed-read-v1' or r.get('arm') not in ARMS: raise ValueError('Routed schema/arm differs')
    if r.get('scope') not in ('supported600','main1525'): raise ValueError('Unknown routed scope')
    if r['max_new_tokens']!=16384 or r['thinking'] is not True or r['decoding']!='greedy' or r['layout']!='duplicate': raise ValueError('Routed protocol differs')
    if r['prompt_flag']!=FLAGS[r['arm']]: raise ValueError('Routed control prompt differs')
    if r['mask_source']!='mdg': raise ValueError('Only checkpoint-native MDG masks are admitted')
    if r['grounding'].get('allow_own_fallback') is not False or r['grounding'].get('depth_source')!='tower_scaled': raise ValueError('Require G3T geometry without fallback')
    if r['fusion_policy']!='fit_gbox_policy_voteb5_best1_v1': raise ValueError('Frozen fusion policy differs')
    if r['artifact']['sha256']=='0'*64 or not re.fullmatch('[0-9a-f]{64}',r['artifact']['sha256']): raise ValueError('Unbound artifact')
    if digest({k:v for k,v in r.items() if k!='binding'})!=r['binding']: raise ValueError('Routed binding differs')
    for name,p in r['inputs'].items(): checked(p)
    if sha(__file__)!=r['driver_sha256'] or source_pins()!=r['tree_sources']: raise ValueError('Runtime source differs')
    if live:
        if r['dry'] or r['parent_standin']: raise ValueError('Dry/parent routed bind cannot launch')
        checked(r['artifact']); checked(r['config']); checked(r['grounding']['geometry_manifest'])
        cfg=load(r['config']['path'])
        if cfg.get('frame_layout')!='duplicate' or cfg.get('training_mode')!='final' or cfg.get('trace_program_version')!='3.14': raise ValueError('Training layout/version differs')
        if not cfg.get('geometry_online') or not cfg.get('mdg'): raise ValueError('Require geometry tower and native MDG configuration')
        if load(r['artifact']['path']).get('step')!=r['step']: raise ValueError('Export step differs')
        from geometry import validate_manifest
        validate_manifest(load(checked(r['grounding']['geometry_manifest'])),r['artifact'])
    return r

def bind(args):
    dest=local(args.dest)
    if dest.exists(): raise ValueError('Routed destination exists')
    a,_=vendor(); _,_,tasks,captures=a.R3.payload(VENDOR/'r3')
    refs=load(ROOT/'out/SCRIPTED_REFERENCES.json')
    chosen=[t for t in tasks if args.scope=='main1525' or 'devrows:'+t['id'] in refs]
    if args.arm=='scripted' and any('devrows:'+t['id'] not in refs for t in chosen): raise ValueError('Scripted native API does not support every selected item')
    if args.step<=0: raise ValueError('Require optimizer step')
    if args.parent_standin and (not args.dry or args.sha256!=PARENT_SHA): raise ValueError('Parent is dry-only')
    config=pin(args.config) if args.config else None
    geometry=pin(args.geometry) if args.geometry else None
    if not args.dry and (config is None or geometry is None): raise ValueError('Live bind needs training config and predicted G3T geometry manifest')
    r=dict(schema='legs1-routed-read-v1',arm=args.arm,scope=args.scope,step=args.step,dry=args.dry,
        parent_standin=args.parent_standin,artifact=dict(path=str(local(args.export)),sha256=args.sha256),
        config=config,mask_source='mdg',grounding=dict(geometry_manifest=geometry,depth_source='tower_scaled',allow_own_fallback=False),
        fusion_policy='fit_gbox_policy_voteb5_best1_v1',tree_archive_sha256=TREE_ARCHIVE_SHA,
        tree_sources=source_pins(),driver_sha256=sha(__file__),max_new_tokens=16384,thinking=True,
        decoding='greedy',layout='duplicate',prompt_flag=FLAGS[args.arm],frames_root=str(local(args.frames_root)),
        inputs={n:pin(p) for n,p in dict(tasks=VENDOR/'r3/TASKS.jsonl',frames=VENDOR/'r3/FRAMES.json',
            references=ROOT/'out/SCRIPTED_REFERENCES.json',route_table=ROOT/'out/ROUTING_POLICY.json').items()},
        keys=['devrows:'+t['id'] for t in chosen],output=str(dest/'results'))
    r['binding']=digest(r); validate_request(r)
    if not args.dry:
        validate_request(r,live=True)
        manifest=load(checked(geometry))
        if manifest.get('schema')!='s1-predicted-geometry-v1':raise ValueError('Wrong predicted geometry schema')
        for t in chosen:
            row=trainer_row(t,captures[t['native']],args.frames_root,verify=True)
            clip=row['student_input']['video_identity']['video_sha256']
            if clip not in manifest['videos']: raise ValueError('Missing G3T geometry for '+t['native'])
            checked(manifest['videos'][clip])
    dest.mkdir(parents=True)
    dump(dest/'request.json',r)
    dump(dest/'BIND_STATUS.json',dict(items=len(chosen),ready=not args.dry,export_bytes_verified=False,
        scope=args.scope,pending=['native export loader, native MDG, geometry schema/frame/scale admission, GPU parity, learned routing',
        'These prompt instructions are controlled development interventions; unflagged is the headline arm.']))
    print(json.dumps(dict(arm=args.arm,items=len(chosen),dry=args.dry,binding=r['binding'])))

def run(args):
    # This entrypoint is written for the operator; the lane runs only smoke and dry bind.
    request=validate_request(load(local(args.dest)/'request.json'),live=True)
    if not args.device.startswith('cuda:'): raise ValueError('Production routed read requires an assigned card')
    install_tree()
    from evalpath import runtime
    from student_pilot import carrier_c1_run as trainer
    from student_pilot.s1_grounding import build_backend
    from student_pilot.scripted_calls import validate_reference
    cfg=load(checked(request['config'])); receipt,manifest=trainer.prepared(cfg,admission=True)
    selected=dict(root=str(TREE),sources={n.removeprefix('student_pilot/'):h for n,h in request['tree_sources'].items() if n.startswith('student_pilot/')})
    spec=runtime.check_init_spec(receipt,request['artifact'])
    model,processor,info=runtime.load_model('routed',cfg,artifact_pin=request['artifact'],snapshot=manifest['root'],
        device=args.device,selected_trainer=selected,init_spec=spec)
    if model.trace_program_version!='3.14': raise ValueError('Loaded trace version differs')
    tasks={ 'devrows:'+t['id']:t for t in rows(checked(request['inputs']['tasks']))}
    captures={c['native']:c for c in load(checked(request['inputs']['frames']))['captures']}
    refs=load(checked(request['inputs']['references']))
    out=Path(request['output']);out.mkdir(parents=True,exist_ok=False)
    dump(out/'LOAD_RECEIPT.json',info)
    from evalpath.run import score_item
    from student_pilot.live_trace313 import replay
    from evalpath.items import assert_prompt_equal
    # Run native pixel, prompt and teacher/cache parity before any scored cell.
    # Scripted choices are interventions, so parity uses an unforced decode.
    from evalpath.parity import LogitTap,p1,p2,p3
    first=tasks[request['keys'][0]]
    probe=trainer_row(first,captures[first['native']],request['frames_root'],verify=True)
    probe['student_input']['question']='Read the camera pose at Frame 1 using <pose frame=1>. Report the camera values.'
    assert_prompt_equal(processor,probe)
    pb=trainer.move(runtime.prompt_batch(processor,probe,cfg,'routed'),args.device)
    pbackend=build_backend(probe,pb,request['artifact'],out/'parity_grounding',request['grounding'])
    tap=LogitTap();pd=runtime.generate(model,processor,pb,'routed',16384,tap=tap,ground_backend=pbackend,mask_source='mdg')
    dump(out/'PARITY_DECODE.json',pd)
    legacy=deepcopy(pd)
    if not legacy['heads'].get('ground_queries'):legacy['heads'].pop('trace313_live',None)
    parity=dict(P1=p1(model,processor,probe,cfg,'routed',pb,pd,tap,True),
                P2=p2(model,pb,legacy,'routed',True),P3=p3(processor,probe,cfg,pb,True),
                camera_call=any(c['call'].startswith('<pose ') for c in pd['calls']),call_errors=pd['errors'])
    parity['pass']=all(parity[k]['pass'] for k in ('P1','P2','P3')) and parity['camera_call'] and not parity['call_errors']
    dump(out/'GPU_PARITY.json',parity)
    if not parity['pass']:raise ValueError('Native GPU prompt/pixel/cache/head parity failed')
    result=[]
    for key in request['keys']:
        start=time.monotonic(); t=tasks[key]
        row=trainer_row(t,captures[t['native']],request['frames_root'],verify=True)
        if request['prompt_flag']:row['student_input']['question']=request['prompt_flag']+'\n'+row['student_input']['question']
        assert_prompt_equal(processor,row)
        batch=trainer.move(runtime.prompt_batch(processor,row,cfg,'routed'),args.device)
        backend=build_backend(row,batch,request['artifact'],out/'grounding'/digest(key),request['grounding'])
        extra={}
        if request['arm']=='scripted': validate_reference(refs[key]);extra['reference_trace']=refs[key]
        decoded=runtime.generate(model,processor,batch,'routed',16384,ground_backend=backend,mask_source='mdg',**extra)
        if decoded.get('heads',{}).get('ground_queries'):
            replayed=replay(decoded)
            if not replayed['byte_equal']:raise ValueError('Native grounded trace replay differs')
        scored=score_item({**t,'ground_truth':t['answer']},decoded); scored.pop('_think_text')
        called=bool(decoded['calls'])
        # Do not credit a forced-direct item which used tools.
        if request['arm']=='forced_direct' and called:
            dump(out/'FORCED_DIRECT_REFUSAL.json',dict(key=key,decode=decoded))
            raise ValueError('Forced-direct control called tools; preserve record and revise control before R2')
        scores={}
        for field,label in [('answer',t['answer']),('released_answer',t.get('released_answer_in_options',t.get('released_answer')))]:
            scores[field]=None if label is None else native_score(t,label,decoded)
        record=dict(key=key,room=t['room'],question_type=t['question_type'],stratum=t['stratum'],scores=scores,
            capped=scored['hit_token_cap'],called=called,call_errors=decoded['errors'],version_errors=0,
            checkpoint_sha256=request['artifact']['sha256'],
            perception_identity=digest(dict(clip=row['student_input']['video_identity'],geometry=request['grounding'],
                artifact=request['artifact'],fusion=request['fusion_policy'])),
            prefill_identity=digest(batch['input_ids'].detach().cpu().tolist()),binding=request['binding'],
            decode=decoded,seconds=time.monotonic()-start)
        with (out/'items.jsonl').open('a') as f: f.write(json.dumps(record,allow_nan=False)+'\n')
        result.append(record)
        if args.first_minute:
            dump(out/'FIRST_ITEM.json',dict(item=key,called=called,errors=decoded['errors'],seconds=record['seconds'],
                native_loader=True,scope='one item only; no full-cell decision'))
            return
    dump(out/'COMPLETE.json',dict(request=pin(local(args.dest)/'request.json'),journal=pin(out/'items.jsonl'),
        parity=pin(out/'GPU_PARITY.json'),items=len(result)))

def native_score(task,label,decoded):
    install_tree()
    from evalpath.run import score_item
    # Preserve the reviewed missing-think-close rule and parsed-cap credit.
    if not re.search(r'</think\s*>',decoded['text'],re.I):return 0.0
    return score_item({**task,'ground_truth':label},decoded)['score']

def merge(args):
    arms={}; receipts={}
    for name in ARMS:
        d=local(getattr(args,name)); r=validate_request(load(d/'request.json'),live=True)
        if r['arm']!=name: raise ValueError('Arm assignment differs')
        c=load(d/'results/COMPLETE.json');checked(c['request']);data=rows(checked(c['journal']))
        if not load(checked(c['parity']))['pass']:raise ValueError('Routed GPU parity failed')
        if len(data)!=len(r['keys']) or {x['key'] for x in data}!=set(r['keys']): raise ValueError('Routed membership incomplete')
        if any(x['binding']!=r['binding'] for x in data):raise ValueError('Journal binding differs')
        arms[name]=data;receipts[name]=pin(d/'results/COMPLETE.json')
    for a,b in zip(arms['forced_route'],arms['scripted']):
        if a['key']!=b['key'] or a['prefill_identity']!=b['prefill_identity']:raise ValueError('R1 must share exact model prefill')
    dump(args.output,dict(arms=arms,receipts=receipts));dump(str(args.output)+'.pin.json',pin(args.output))

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('bind')
    for k in ('export','sha256','frames-root','dest'):q.add_argument('--'+k,required=True)
    q.add_argument('--step',type=int,required=True);q.add_argument('--arm',choices=ARMS,required=True)
    q.add_argument('--scope',choices=['supported600','main1525'],default='supported600')
    q.add_argument('--dry',action='store_true');q.add_argument('--parent-standin',action='store_true')
    q.add_argument('--config');q.add_argument('--geometry')
    q=sub.add_parser('run');q.add_argument('--dest',required=True);q.add_argument('--device',required=True);q.add_argument('--first-minute',action='store_true')
    q=sub.add_parser('merge');q.add_argument('--output',required=True)
    for name in ARMS:q.add_argument('--'+name.replace('_','-'),dest=name,required=True)
    a=p.parse_args();{'bind':bind,'run':run,'merge':merge}[a.command](a)
if __name__=='__main__':main()
