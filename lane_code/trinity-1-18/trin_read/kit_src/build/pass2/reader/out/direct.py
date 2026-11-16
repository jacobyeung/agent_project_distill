"""Checkpoint-parametric wrapper around the byte-identical reviewed dev adapters."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from export_check import check_export

PAYLOADS={'main':VENDOR/'r3','away':VENDOR/'r4/DEV_BACKDIR','forward':VENDOR/'r4/DEV_FORWARD_TWINS'}

def model_specs(models,model):
    if model!='cp1m200': raise ValueError('LEG wrapper requires CP1 protocol slot')
    b,s=models['base'],models[model]
    if b['kind']!='snapshot' or b['manifest']['sha256']!=BASE_SHA: raise ValueError('Base snapshot differs')
    if s['kind']!='c1_export' or not re.fullmatch('[0-9a-f]{64}',s['sha256']) or s['sha256']=='0'*64:
        raise ValueError('Unbound checkpoint')
    for p in (b['path'],b['manifest']['path'],s['path']):
        if not Path(p).is_absolute(): raise ValueError('Require absolute paths')
        local(p)

def modules():
    a,r=vendor()
    a.R3.check_model_specs=a.R4.check_model_specs=model_specs
    a.R4.legacy_adapter=lambda:a.R3
    return a,r

def validate_identity(cfg):
    c=cfg.get('legs1')
    if not c or c['wrapper_sha256']!=sha(__file__): raise ValueError('Missing/changed LEG wrapper identity')
    if c['artifact']!={k:cfg['models']['cp1m200'][k] for k in ('path','sha256')}: raise ValueError('Checkpoint provenance differs')
    if c['step']<=0 or c['name']!=f"LEG-S1-m{c['step']}": raise ValueError('Checkpoint step/name differs')
    if c['decision_arm']!='B2048': raise ValueError('Decision arm differs')
    if c['parent_standin'] and c['artifact']['sha256']!=PARENT_SHA: raise ValueError('Wrong parent stand-in')
    for p,h in c['wrapper_dependencies'].items():
        if sha(ROOT/p)!=h: raise ValueError('Wrapper dependency changed')
    return c

def bind(args):
    a,_=modules(); dest=local(args.dest)
    if dest.exists(): raise ValueError('Destination exists')
    models=load(args.models)
    models['cp1m200']=dict(kind='c1_export',path=str(local(args.export)),sha256=args.sha256)
    model_specs(models,'cp1m200')
    if args.step<=0: raise ValueError('Step must be positive')
    if args.parent_standin and (not args.dry or args.sha256!=PARENT_SHA): raise ValueError('Parent stand-in is dry-only')
    verification=None
    if not args.dry:
        verification=check_export(args.export,args.sha256,models['base']['path'],args.step)
    # Preserve the reviewed adapter and kit bytes; bind through their public functions.
    temporary=dest.parent/(dest.name+'.models.json')
    if temporary.exists(): raise ValueError('Model binding file exists')
    dump(temporary,models)
    origin=a.R3 if args.family=='main' else a.R4
    origin.bind(SimpleNamespace(payload=str(PAYLOADS[args.family]),dest=str(dest),kit=args.kit,
        cell='cp1m200',models=str(temporary),frames_root=args.frames_root,dry=True))
    cfg=load(dest/'request.json')
    cfg['build_only']=args.dry
    cfg['legs1']=dict(name=f'LEG-S1-m{args.step}',step=args.step,family=args.family,
        artifact={k:models['cp1m200'][k] for k in ('path','sha256')},decision_arm='B2048',
        protocol_slot='cp1m200',parent_standin=args.parent_standin,wrapper_sha256=sha(__file__),
        wrapper_dependencies={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'out/common.py',ROOT/'out/export_check.py')},
        export_verification=verification,export_bytes_verified=not args.dry)
    cfg['binding']=hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')},sort_keys=True).encode()).hexdigest()
    dump(dest/'request.json',cfg)
    validate_identity(cfg)
    if not args.dry:
        _,_,_,captures=origin.payload(args.payload if hasattr(args,'payload') else PAYLOADS[args.family])
        data,media,_=origin.kit_import(dest/'kit')
        tasks=data.tasks_for(cfg['datasets'][0],cfg['roots'])
        h=origin.make_frames(cfg,tasks,captures,media,local(args.frames_root),dest/'frames')
        dump(dest/'BIND_STATUS.json',dict(tasks=len(tasks),ready=True,dry=False,frames_sha256=h))
    print(json.dumps(dict(bound=str(dest),checkpoint=cfg['legs1']['name'],binding=cfg['binding'],dry=args.dry)))

def launch(args):
    a,_=modules(); cfg=load(local(args.dest)/'request.json'); c=validate_identity(cfg)
    if cfg['build_only'] or not c['export_bytes_verified'] or c['parent_standin']: raise ValueError('Dry/unverified bind cannot launch')
    check_export(c['artifact']['path'],c['artifact']['sha256'],cfg['models']['base']['path'],c['step'])
    a.launch(args)

def merge(args):
    a,r=modules(); cfg=load(local(args.source)/'request.json'); c=validate_identity(cfg)
    a.merge_existing(args)
    d=local(args.dest); complete=load(d/'MERGE_COMPLETE.json')
    for arm,name in complete['exports'].items():
        p=d/'report'/name; data=load(p); data['checkpoint']=c; data['model']=c['name']; dump(p,data)
        complete['export_sha256'][arm]=sha(p)
    dump(d/'MERGE_COMPLETE.json',complete)

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('bind')
    for k in ('export','sha256','models','kit','frames-root','dest'): q.add_argument('--'+k,required=True)
    q.add_argument('--step',type=int,required=True); q.add_argument('--family',choices=PAYLOADS,required=True)
    q.add_argument('--dry',action='store_true'); q.add_argument('--parent-standin',action='store_true')
    q=sub.add_parser('launch'); q.add_argument('--dest',required=True); q.add_argument('--attempt',required=True)
    q=sub.add_parser('merge')
    for k in ('source','dest','kit','attempt'): q.add_argument('--'+k,required=True)
    q.add_argument('--tokenizer-dir'); q.add_argument('--tokenizer-manifest')
    args=p.parse_args(); {'bind':bind,'launch':launch,'merge':merge}[args.command](args)
if __name__=='__main__': main()
