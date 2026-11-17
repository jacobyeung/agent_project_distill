"""Audit the native 1000-step sampler against pinned prepared streams."""
from collections import Counter
import hashlib
import json
import re
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

def unit_counts(source, allowlist=('ft',)):
    from .vehicle_p import unit_name, UNITS
    ids=set(load(pinned(source['indices']))) if 'indices' in source else set(range(source['count']))
    by_unit=Counter();by_dataset=Counter();by_unit_dataset=Counter()
    db=Path(pinned(source['database']));conn=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        for i,encoded in conn.execute('SELECT i,row FROM rows ORDER BY i'):
            if i not in ids:continue
            row=json.loads(encoded)
            if type_mix.family(row,'routing')!='units':continue
            unit=unit_name(row);dataset=row.get('dataset',row.get('provenance',{}).get('canonical','').split('/')[0])
            by_unit[unit]+=1;by_dataset[dataset]+=1;by_unit_dataset[unit+'/'+dataset]+=1
    finally:conn.close()
    return dict(eligible=sum(by_unit.values()),sampling_eligible=sum(by_unit[u] for u in allowlist if by_unit[u]>=100),by_unit={u:by_unit[u] for u in UNITS},by_dataset=dict(by_dataset),by_unit_dataset=dict(by_unit_dataset))


PREFIXES=('scannetpp/','scannetppv2/','scannet','arkit','unknown')

def row_metadata(row,stream,family):
    raw=row.get('routing',row)
    canonical=raw.get('provenance',{}).get('canonical',row.get('provenance',{}).get('canonical',''))
    prefix=next((p for p in PREFIXES[:-1] if canonical.startswith(p if p.endswith('/') else p+'/')),'unknown')
    answer=str(row.get('answer','')).strip().lower()
    options=row.get('student_input',{}).get('options',row.get('options',[]))
    if isinstance(options,list):
        for option in options:
            match=re.fullmatch(r'([A-Za-z])[.)]\s*(.*)',str(option))
            if match and answer==match[1].lower():answer=match[2].strip().lower();break
    elif isinstance(options,dict):
        answer=str(options.get(answer.upper(),options.get(answer,answer))).strip().lower()
    from .vehicle_p import unit_name
    return dict(family=family,facing=row.get('facing'),away_hard=row.get('facing')=='away' and raw.get('question_type')=='object_rel_direction_hard',
                answer=answer,unit=unit_name(row) if family=='units' else None,prefix=prefix)


def draw_breakdown(metadata,draws,*,routing_available):
    facing=Counter();away=Counter();units=Counter();eligible=Counter();drawn=Counter()
    for stream,rows in metadata.items():
        for pos,row in rows.items():
            n=draws[stream,pos]
            if stream=='vqa' and row['family']=='facing':
                facing[row['facing']]+=n
                if row['away_hard']:
                    away['draws']+=n
                    away['back_draws']+=n*bool(re.search(r'\bback\b',row['answer']))
                    away['exact_back_draws']+=n*(row['answer']=='back')
            if stream=='routing' and row['family']=='units':units[row['unit']]+=n
            if stream=='routing' and row['family']=='absolute_distance':
                eligible[row['prefix']]+=1;drawn[row['prefix']]+=n
    total=sum(facing.values());den=away['draws']
    return dict(facing={k:dict(draws=facing[k],share_of_facing=facing[k]/total if total else None) for k in ('toward','away')},
        away_hard=dict(draws=den,back_draws=away['back_draws'],back_share=away['back_draws']/den if den else None,
            exact_back_draws=away['exact_back_draws'],exact_back_share=away['exact_back_draws']/den if den else None,
            back_definition='Decoded option contains the word back, including back-left and back-right; exact_back counts only back.'),
        units=dict(status='MEASURED' if routing_available else 'NOT_RUN',draws={u:units[u] if routing_available else None for u in ('cm','ft','in')}),
        routing_absolute_distance=dict(status='MEASURED' if routing_available else 'NOT_RUN',
            eligible={p:eligible[p] if routing_available else None for p in PREFIXES},drawn={p:drawn[p] if routing_available else None for p in PREFIXES}))


def print_breakdown(report):
    print(json.dumps(dict(loader_draw_breakdown=report['draw_breakdown']),sort_keys=True),flush=True)


def audit(cfg,receipt,*,local_vqa_only=False):
    value=type_mix.bound(receipt,cfg)
    if value is None:raise ValueError('Loader audit requires bound family quotas')
    populations={};types={};traces={};exclusions={};metadata={}
    for stream,policy in cfg['type_mix']['streams'].items():
        if local_vqa_only and stream!='vqa':continue
        groups,t,samples,excluded=type_mix.populations(stream,receipt['streams'][stream],policy['cells'],cfg['type_mix']['size_selector'],cfg['type_mix'].get('unit_rows'),cfg['type_mix'].get('units_allowlist'),cfg['type_mix'].get('exclude_qid_suffix'),audit_metadata=metadata.setdefault(stream,{}))
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
    return dict(unit_counts=unit_counts(receipt['streams']['routing'],cfg['type_mix'].get('units_allowlist',['ft'])) if not local_vqa_only else {},schema='loader-audit-v1',status='LOCAL_VQA_ONLY' if local_vqa_only else 'PASS',
        config_identity=receipt['config_sha256'],planned_steps=cfg['recipe']['steps'],eligible_by_family=populations,
        eligible_by_question_type={s:dict(Counter(t.values())) for s,t in types.items()},
        by_family=shares(by_family),by_question_type=shares(by_type),stream_draws=dict(by_stream),
        draw_breakdown=draw_breakdown(metadata,repeats,routing_available=not local_vqa_only),
        maximum_observed_repeats=max(repeats.values(),default=0),tables=value['tables'],excluded=exclusions,
        traces=traces,first_step=first,source_streams=receipt['streams'],full_production_admission=not local_vqa_only)


def main(root):
    import os,sys
    from .vehicle_p import required_families
    from .checkpoint_space import plan
    from .carrier_c1_run import identity
    root=Path(root);sys.path.insert(0,str(root/'b'))
    from d import effective
    launch=load(root/'k/launch.json');original=load(root/launch['config']['file'])
    cfg=effective(root,original);receipt=load(pinned(cfg['preparation']))
    result=audit(cfg,receipt)
    print_breakdown(result)
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
        required_families=required_families(original,result))
    import shutil
    executables={}
    for name in ('python', 'bash', 'bwrap', 'tar', 'rsync', 'sha256sum'):
        path=sys.executable if name=='python' else shutil.which(name)
        if path is not None:executables[name]=file_pin(Path(path).resolve())
    checks['staged_binaries']=dict(status='PASS',executables=executables)
    print(json.dumps(dict(required_families=checks['required_families']),sort_keys=True),flush=True)
    report=dict(absent_on_P=checks['required_families']['absent_on_P'],status='PASS' if all(v['status']=='PASS' for v in checks.values()) else 'FAIL',checks=checks,
        original_config_identity=identity(original),effective_config_identity=identity(cfg),production_authorized=False)
    write(directory/'a.json',report)
    if report['status']!='PASS':raise ValueError('Required packet proof checks failed')

if __name__=='__main__':
    import sys
    main(sys.argv[1])
