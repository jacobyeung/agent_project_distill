"""Bind complete native source and prepared populations to post-condition evidence."""
from pathlib import Path
import hashlib
import json
from copy import deepcopy
STREAMS=('pose','vqa','routing','pointing')

def plain(value):
    if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
    if isinstance(value,list):return [plain(v) for v in value]
    return value

def authenticate(value):
    from student_pilot.p3_provenance import pinned
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:pinned({k:value[k] for k in ('path','sha256')})
        else:
            for v in value.values():authenticate(v)
    elif isinstance(value,list):
        for v in value:authenticate(v)

def sources(cfg):
    from student_pilot.p3_provenance import load,pinned
    result={}
    def database(pin):
        receipt=load(pinned(pin))
        return dict(receipt=pin,population=receipt.get('rows_metadata',receipt.get('database')),count=receipt['count'])
    for stream in STREAMS:
        pin=cfg['streams'][stream];receipt=load(pinned(pin))
        if stream=='pose' and receipt.get('schema')=='c1-pose-mix-v1':
            entries=[]
            for source in receipt['sources']:
                if source['kind']!='rows':raise ValueError('R1_CENSUS_POSE_SOURCE_NOT_ROWS')
                entries.append(database(source['receipt']))
        else:entries=[database(pin)]
        if stream=='routing' and cfg.get('s1_routing'):
            pool=load(pinned(cfg['s1_routing']['selection']))
            # All pool input populations precede selection and stream removals.
            for name,source in sorted(pool['sources'].items()):
                if source.get('source'):
                    from student_pilot.r2_scene_bindings import rows
                    pin=source['source']
                    count=sum(1 for _ in rows(pin))
                    entries.append(dict(population=pin,count=count,pool_source=name))
        if any(v['population'] is None for v in entries):raise ValueError('R1_CENSUS_SOURCE_POPULATION_MISSING:'+stream)
        result[stream]=entries
    authenticate(result)
    return result

def source_rows(entries):
    from student_pilot.r2_scene_bindings import rows
    for entry in entries:
        count=0
        for row in rows(entry['population']):
            count+=1;yield row
        if count!=entry['count']:raise ValueError('R1_CENSUS_SOURCE_COUNT_DIFFERS')

def store_pins(cfg):
    from student_pilot.p3_provenance import load,pinned
    receipt=load(pinned(cfg['preparation']))
    result={s:plain(receipt['streams'][s]) for s in STREAMS}
    authenticate(result)
    return result

def discovery(kit):
    from z import load
    control=load(Path(kit)/'k/a.json')
    return control.get('discovery') is True and control.get('GO') is False

def evaluate(cfg,stream,entries,admitted,classify):
    from student_pilot.row_removals import row_keys
    from sv import STATUSES
    counts=dict.fromkeys((*STATUSES,'source','admitted','unresolved'),0)
    counts['source']=sum(1 for _ in source_rows(entries))
    hits=[];errors=[];protected_rows=0
    # Independent complete census; never sample, and never feed summaries to native.
    for row in admitted():
        counts['admitted']+=1
        try:flags=classify(row,stream)
        except ValueError as error:
            errors.append(str(error));counts['unresolved']+=1;flags={}
        for name,hit in flags.items():counts[name]+=int(hit)
        if any(flags.values()):
            protected_rows+=1
            native_keys=row_keys(row)
            if not native_keys:errors.append('R1_CENSUS_ROW_KEY_MISSING:'+stream)
            hits.extend(native_keys)
    keys=sorted(set(hits))
    result=dict(stream=stream,source_rows=counts['source'],admitted_rows=counts['admitted'],
                protected_rows=protected_rows,room_functions='Rooms.status/room, Binding.room, Withheld')
    if protected_rows:errors.insert(0,'R1_CENSUS_PROTECTED_ADMITTED:'+stream)
    return dict(result=result,counts=counts,refusals=list(dict.fromkeys(errors))),keys

def emit(kit,root,cfg,source,admitted,stores,job,*,phase='final'):
    from student_pilot.carrier_c1_run import identity
    from student_pilot.p3_provenance import file_pin
    from rv import location,put,encoded
    from sv import classifier
    from z import write
    live,_=location(Path(kit),Path(root),job)
    diagnose=discovery(kit);classify=classifier(cfg);value=identity(cfg)
    output=dict(schema='r1-protected-census-v1',phase=phase,config_identity=value,streams={})
    authenticate(source);authenticate(stores)
    failures=[]
    for i,stream in enumerate(STREAMS):
        record,keys=evaluate(cfg,stream,source[stream],lambda:admitted(stream),classify)
        status=('WOULD_REFUSE' if diagnose else 'REFUSE') if record['refusals'] else 'PASS'
        name=('c' if phase=='final' else 'd')+str(i)+'.json'
        raw=encoded(keys);put(live/name,raw)
        record.update(status=status,config_identity=value,source_pins=source[stream],
                      store_pins=stores[stream],protected_keys=dict(file=name,sha256=hashlib.sha256(raw).hexdigest(),count=len(keys)))
        output['streams'][stream]=record
        if record['refusals']:failures.extend(record['refusals'])
        # Publish accumulated evidence before an armed kit's first refusal.
        output['status']=('WOULD_REFUSE' if diagnose else 'REFUSE') if failures else 'PASS'
        put(live/('c4.json' if phase=='final' else 'd4.json'),encoded(output))
        if record['refusals'] and not diagnose:
            (Path(root)/('c5.json' if phase=='final' else 'd6.json')).write_bytes(encoded(output))
            raise ValueError(record['refusals'][0])
    path=Path(root)/('c5.json' if phase=='final' else 'd6.json')
    path.write_bytes(encoded(output));pin=file_pin(path)
    if sum((live/v['protected_keys']['file']).stat().st_size for v in output['streams'].values())+(live/('c4.json' if phase=='final' else 'd4.json')).stat().st_size>=1_000_000:
        raise ValueError('R1_SCENE_EVIDENCE_TOO_LARGE')
    return pin

def final_sources(root,cfg):
    from student_pilot.p3_provenance import load,pinned
    from student_pilot.carrier_c1_run import Rows
    from z import checked
    root=Path(root)
    host=load(root/'p/q/host.json')
    h=host.get('staging_plan_sha256')
    if not isinstance(h,str) or len(h)!=64:raise ValueError('R1_CENSUS_SOURCE_MANIFEST_MISSING')
    manifest=load(checked(root/'p/i/staging.json',h))
    entry=manifest.get('entries',{}).get('ss.json')
    if not isinstance(entry,dict):raise ValueError('R1_CENSUS_SOURCE_MANIFEST_MISSING')
    source=load(checked(root/'p/q/ss.json',entry['sha256'],entry['bytes']))
    # Native VQA augmentation can add source rows before stream materialization.
    source=deepcopy(source)
    for stream in ('vqa','pointing'):
        receipt=load(pinned(cfg['streams'][stream]))
        if receipt.get('source_receipt'):
            pin=receipt['source_receipt'];raw=load(pinned(pin))
            source[stream]=[dict(receipt=pin,population=raw['database'],count=raw['count'])]
    return source

def publish(kit,root,cfg,job):
    from student_pilot.p3_provenance import load,pinned
    from student_pilot.carrier_c1_run import Rows
    root=Path(root);source=final_sources(root,cfg)
    reader=Rows(load(pinned(cfg['preparation'])),None)
    def admitted(stream):
        for i in range(reader.count(stream)):yield reader.row(stream,i)[0]
    try:return emit(kit,root,cfg,source,admitted,store_pins(cfg),job)
    finally:reader.close()

def _verify(kit,root,cfg):
    from student_pilot.carrier_c1_run import identity
    from student_pilot.p3_provenance import file_pin
    from z import load,checked
    root=Path(root);path=root/'c5.json'
    if not path.is_file() or path.is_symlink():raise ValueError('R1_CENSUS_RECEIPT_MISSING')
    value=load(path)
    if value.get('schema')!='r1-protected-census-v1' or value.get('phase')!='final':raise ValueError('R1_CENSUS_RECEIPT_INVALID')
    expected=identity(cfg);stores=store_pins(cfg);expected_sources=final_sources(root,cfg)
    if value.get('config_identity')!=expected:raise ValueError('R1_CENSUS_IDENTITY_DIFFERS')
    if set(value.get('streams',{}))!=set(STREAMS):raise ValueError('R1_CENSUS_STREAMS_INCOMPLETE')
    from rv import location
    import os
    live,_=location(Path(kit),root,os.environ['SLURM_JOB_ID'])
    checked(live/'c4.json',file_pin(path)['sha256'])
    for stream in STREAMS:
        r=value['streams'][stream]
        if r.get('config_identity')!=expected:raise ValueError('R1_CENSUS_IDENTITY_DIFFERS')
        if r.get('store_pins')!=stores[stream]:raise ValueError('R1_CENSUS_STORE_PINS_DIFFER:'+stream)
        if r.get('source_pins')!=expected_sources[stream]:raise ValueError('R1_CENSUS_SOURCE_PINS_DIFFER:'+stream)
        authenticate(r['source_pins'])
        key=r['protected_keys'];p=live/key['file']
        if Path(key['file']).name!=key['file']:raise ValueError('R1_CENSUS_RECEIPT_INVALID')
        keys=load(checked(p,key['sha256']))
        if keys!=sorted(set(keys)) or len(keys)!=key['count']:raise ValueError('R1_CENSUS_KEYS_DIFFER')
        if r.get('status')!='PASS':
            if not (discovery(kit) and r.get('status')=='WOULD_REFUSE'):raise ValueError('R1_CENSUS_NOT_PASS:'+stream)
        elif not isinstance(r.get('result'),dict) or r['result'].get('protected_rows')!=0 or r['refusals'] or keys:
            raise ValueError('R1_CENSUS_NOT_PASS:'+stream)
        if r.get('status')=='PASS':
            counts=r['counts'];result=r['result']
            from sv import STATUSES
            if any(counts.get(s,0) for s in (*STATUSES,'unresolved')):raise ValueError('R1_CENSUS_NOT_PASS:'+stream)
            if result.get('stream')!=stream or result.get('admitted_rows')!=stores[stream]['count'] or counts.get('admitted')!=stores[stream]['count'] or result.get('source_rows')!=sum(e['count'] for e in expected_sources[stream]) or counts.get('source')!=result['source_rows']:
                raise ValueError('R1_CENSUS_COUNT_DIFFERS:'+stream)
    return file_pin(path)

def verify(kit,root,cfg):
    from student_pilot.r1_persisted import scope
    # Receipt bodies retain their authenticated original pins. Resolve those
    # pins only through the native job's content-addressed staged bytes.
    folder=Path(root)/'p/q/u'
    paths={}
    if folder.is_dir():
        for p in folder.iterdir():
            h=p.name
            if len(h)==64 and all(c in '0123456789abcdef' for c in h):
                if p.is_symlink() or not p.is_file():raise ValueError('R1_CENSUS_STAGED_PIN_INVALID')
                paths[h]=str(p)
    with scope(paths):
        return _verify(kit,root,cfg)
