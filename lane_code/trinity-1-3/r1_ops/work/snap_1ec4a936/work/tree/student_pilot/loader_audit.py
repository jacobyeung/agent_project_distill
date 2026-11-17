"""Audit the native 1000-step sampler against pinned prepared streams."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
from . import carrier_c1_data as data, type_mix
from .p3_provenance import load, pinned, file_pin, write


def examples(stream,source,limit=5,selected=None):
    if source.get('kind')=='mix':
        order=load(pinned(source['order']))[:limit];rows=[]
        for child_index,i in order:
            rows.extend(examples(stream,source['sources'][child_index],1,[i]))
        return rows
    ids=selected if selected is not None else (load(pinned(source['indices']))[:limit] if 'indices' in source else list(range(min(limit,source['count']))))
    if source.get('kind')=='c1r_clips':
        result=[];wanted=set(ids)
        with pinned(source['clips_plan']).open() as f:
            for line in f:
                row=json.loads(line)
                if row['i'] in wanted:
                    encoded=json.dumps(row,sort_keys=True,separators=(',',':'))
                    result.append(dict(source=source['clips_plan'],index=row['i'],question_type=stream,target=row,
                        target_sha256=hashlib.sha256(encoded.encode()).hexdigest()))
                    if len(result)==len(wanted):break
        if len(result)!=len(wanted):raise ValueError('Clip example absent from bound plan')
        return result
    db=Path(pinned(source['database']));conn=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
    out=[]
    try:
        for i in ids:
            raw=conn.execute('SELECT row,target FROM rows WHERE i=?',(i,)).fetchone()
            if raw is None:raise ValueError('Audit row absent')
            r=json.loads(raw[0]);target=r.get('target',json.loads(raw[1]))
            encoded=target if isinstance(target,str) else json.dumps(target,sort_keys=True,separators=(',',':'))
            out.append(dict(database=source['database'],index=i,qid=r.get('qid'),question_type=r.get('question_type',stream),
                target=target,target_sha256=hashlib.sha256(encoded.encode()).hexdigest(),frames=r.get('student_input',{}).get('frames',[])))
    finally:conn.close()
    return out



def question_types(stream,source):
    """Map sampler positions to the actual stored types, including pose-mix order."""
    def read(part,wanted):
        result={}
        if part.get('kind')=='c1r_clips':
            with pinned(part['clips_plan']).open() as f:
                for line in f:
                    row=json.loads(line)
                    if row['i'] in wanted:result[row['i']]=row.get('question_type',stream)
        else:
            db=Path(pinned(part['database']));conn=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
            try:
                for i,encoded in conn.execute('SELECT i,row FROM rows ORDER BY i'):
                    if i in wanted:
                        row=json.loads(encoded);result[i]=row.get('routing',row).get('question_type',stream)
            finally:conn.close()
        if set(result)!=wanted:raise ValueError('Type audit lacks admitted positions')
        return result
    if source.get('kind')=='mix':
        order=load(pinned(source['order']));wanted={}
        for child,i in order:wanted.setdefault(child,set()).add(i)
        parts={child:read(source['sources'][child],ids) for child,ids in wanted.items()}
        if len(order)!=source['count']:raise ValueError('Mix audit count differs')
        return {pos:parts[child][i] for pos,(child,i) in enumerate(order)}
    ids=load(pinned(source['indices'])) if 'indices' in source else list(range(source['count']))
    actual=read(source,set(ids))
    return {pos:actual[i] for pos,i in enumerate(ids)}

def audit(cfg,receipt,*,local_vqa_only=False):
    value=type_mix.bound(receipt,cfg)
    if value is None:raise ValueError('Loader audit requires bound family quotas')
    populations={};types={};traces={};exclusions={}
    for stream,policy in cfg['type_mix']['streams'].items():
        if local_vqa_only and stream!='vqa':continue
        groups,t,samples,excluded=type_mix.populations(stream,receipt['streams'][stream],policy['cells'],cfg['type_mix']['size_selector'])
        expected={n:groups[n] for n in value['effective'][stream]}
        if expected!=value['populations'][stream]:raise ValueError('Staged population differs from preparation')
        populations[stream]={n:len(v) for n,v in groups.items()};types[stream]=t;traces[stream]=samples;exclusions[stream]=excluded
        for name,rows in samples.items():
            for row in rows:row['database']=receipt['streams'][stream]['database']
    if not local_vqa_only:
        for stream,source in receipt['streams'].items():
            if stream not in types:types[stream]=question_types(stream,source)
    counts={s:v['count'] for s,v in receipt['streams'].items()}
    by_family=Counter();by_type=Counter();by_stream=Counter();repeats=Counter();first=None
    reverse={s:{i:n for n,ids in groups.items() for i in ids} for s,groups in value['populations'].items()}
    for step,plan in enumerate(data.mixed_indices(counts,cfg['recipe']['steps'],seed=cfg['recipe']['seed'],training_mode=cfg['training_mode'],
                    mix=cfg['recipe']['mix'],world=cfg['recipe']['world_size'],type_mix=value),1):
        if first is None:first=plan
        for stream,ids in plan:
            if local_vqa_only and stream!='vqa':continue
            for i in ids:
                name=reverse.get(stream,{}).get(i,stream);typ=types.get(stream,{}).get(i,stream)
                by_family[stream+'/'+name]+=1;by_type[stream+'/'+typ]+=1;by_stream[stream]+=1
                if stream in reverse:repeats[stream,i]+=1
    if max(repeats.values(),default=0)>4:raise ValueError('Sampler exceeded four repeats')
    if not local_vqa_only:
        for stream,source in receipt['streams'].items():
            if stream not in populations:
                populations[stream]={stream:source['count']};traces[stream]={stream:examples(stream,source)}
    for stream,groups in populations.items():
        for name,count in groups.items():
            if count and len(traces[stream].get(name,[]))<min(5,count):raise ValueError('Missing bound traces')
            if by_family[stream+'/'+name]>4*count:raise ValueError('Family draws exceed four times eligible rows: '+stream+'/'+name)
    shares=lambda counts_: {k:dict(draws=v,rows_per_step=v/cfg['recipe']['steps'],share_of_stream=v/by_stream[k.split('/')[0]]) for k,v in sorted(counts_.items())}
    return dict(schema='loader-audit-v1',status='LOCAL_VQA_ONLY' if local_vqa_only else 'PASS',
        config_identity=receipt['config_sha256'],planned_steps=cfg['recipe']['steps'],eligible_by_family=populations,
        eligible_by_question_type={s:dict(Counter(t.values())) for s,t in types.items()},
        by_family=shares(by_family),by_question_type=shares(by_type),stream_draws=dict(by_stream),
        maximum_observed_repeats=max(repeats.values(),default=0),tables=value['tables'],excluded=exclusions,
        traces=traces,first_step=first,source_streams=receipt['streams'],full_production_admission=not local_vqa_only)


def main(root):
    import os,sys
    from .checkpoint_space import plan
    from .carrier_c1_run import identity
    root=Path(root);sys.path.insert(0,str(root/'b'))
    from d import effective
    launch=load(root/'k/launch.json');original=load(root/launch['config']['file'])
    cfg=effective(root,original);receipt=load(pinned(cfg['preparation']))
    result=audit(cfg,receipt)
    directory=Path(launch['in_job_admission']['directory'])
    write(directory/'l.json',result)
    for stream,groups in result['traces'].items():
        for name,rows in groups.items():
            for row in rows:print(json.dumps(dict(loader_trace=True,stream=stream,family=name,**row),sort_keys=True),flush=True)
    disk=plan(original['recipe'],original['checkpoint_disk_guard']['reserve_bytes'])
    selection=load(pinned(original['s1_routing']['selection']))
    no_rooms=not any(set(v.get('per_type',{}))&{'room_size_estimation','absolute_size_room'} for v in selection['sources'].values() if v['status']=='ELIGIBLE')
    no_rooms=no_rooms and not any(k.endswith((':room_size_estimation',':absolute_size_room')) and v for k,v in result['excluded'].get('routing',{}).items())
    checks=dict(disk_plan=dict(status='PASS' if disk==original['checkpoint_disk_guard'] else 'FAIL',plan=disk),
        routing_selection=dict(status='PASS' if no_rooms else 'FAIL',materialized_room_rows_zero=no_rooms,pin=file_pin(pinned(original['s1_routing']['selection']))),
        loader_audit=dict(status=result['status'],pin=file_pin(directory/'l.json')),
        required_families=dict(status='PASS' if all(result['eligible_by_family']['routing'].get(k,0)>0 for k in ('recovery','units')) else 'FAIL'))
    import shutil
    executables={}
    for name in ('python', 'bash', 'bwrap', 'tar', 'rsync', 'sha256sum'):
        path=sys.executable if name=='python' else shutil.which(name)
        if path is not None:executables[name]=file_pin(Path(path).resolve())
    checks['staged_binaries']=dict(status='PASS',executables=executables)
    report=dict(status='PASS' if all(v['status']=='PASS' for v in checks.values()) else 'FAIL',checks=checks,
        original_config_identity=identity(original),effective_config_identity=identity(cfg),production_authorized=False)
    write(directory/'a.json',report)
    if report['status']!='PASS':raise ValueError('Required packet proof checks failed')

if __name__=='__main__':
    import sys
    main(sys.argv[1])
