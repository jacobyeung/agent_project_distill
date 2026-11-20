"""Provide pair-complete fixture subsets without changing native count gates."""
from collections import Counter
from contextlib import closing,redirect_stdout
from copy import deepcopy
from pathlib import Path
import ast,io,json,os,sqlite3

def bound_population(root,capacity,cfg,J):
    from student_pilot.row_removals import Removals,row_keys
    from student_pilot.r1_rooms import Rooms
    from student_pilot.p3_provenance import digest
    assert os.uname().nodename=='trinity-1-18'
    native=root/'source/student_pilot/r2_scene_bindings.py'
    decoded=next(n for n in ast.parse(native.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='decoded')
    comparison=next(n for n in ast.walk(decoded) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='index')
    limit=ast.literal_eval(comparison.comparators[0]);assert limit==2000
    folder=root/'fixture';folder.mkdir();records=[]
    original_removals=deepcopy(cfg['remove_files'])
    rooms=Rooms(cfg['r1_training']['room_authority'])
    def pin(path):return dict(path=str(path),sha256=J.sha(path))
    def database(path,schema,values):
        assert not path.exists()
        with closing(sqlite3.connect(path)) as db:
            db.execute('PRAGMA journal_mode=PERSIST');db.execute(schema)
            db.executemany('INSERT INTO rows VALUES (?,?,?)',values);db.commit()
        return pin(path)
    def bounded(old_pin,name):
        receipt_path=Path(old_pin['path']);assert receipt_path.is_relative_to(capacity) and J.sha(receipt_path)==old_pin['sha256']
        old=J.load(receipt_path);source_db=Path(old['database']['path'])
        assert source_db.is_relative_to(capacity) and J.sha(source_db)==old['database']['sha256']
        dest=folder/name;dest.mkdir()
        with closing(sqlite3.connect(source_db.as_uri()+'?mode=ro&immutable=1',uri=True)) as src:
            count=src.execute('SELECT COUNT(*) FROM rows').fetchone()[0]
            assert count==old['count'] and count>=limit
            schema=src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='rows'").fetchone()[0]
            selected=src.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT ?',(1000 if name=='vqa' else limit,)).fetchall()
        assert [x[0] for x in selected]==list(range(len(selected)))
        receipt=deepcopy(old)
        if name=='vqa':
            original_spec=deepcopy(cfg['r1_training']['direction_twins'])
            for value in original_spec.values():assert J.sha(Path(value['path']))==value['sha256']
            assert original_spec['source_database']==old['database']
            base_pin=database(dest/'source.sqlite',schema,selected)
            bases={json.loads(raw)['qid']:json.loads(raw) for _,raw,_ in selected}
            chosen=[];twins=[];raw_twins=[]
            with Path(original_spec['binding']['path']).open() as f:
                for line in f:
                    entry=json.loads(line)
                    if entry['source_key'] in bases:chosen.append((line,entry))
            assert len(chosen)==1000 and {e['source_key'] for _,e in chosen}==set(bases)
            by_key={entry['twin_key']:entry for _,entry in chosen}
            assert len(by_key)==1000 and not set(by_key)&set(bases)
            with Path(original_spec['rows']['path']).open() as f:
                for line in f:
                    row=json.loads(line)
                    if row['qid'] not in by_key:continue
                    entry=by_key[row['qid']];source=bases[entry['source_key']]
                    assert digest(row)==entry['twin_sha256'] and 'facing' not in row
                    assert row_keys(row)=={row['qid'],entry['source_key']}
                    assert row['dataset']==source['dataset'] and row['scene']==source['scene']
                    assert rooms.room(rooms.canonical(row)[0])==entry['source_room']==rooms.room(rooms.canonical(source)[0])
                    raw_twins.append(line);twins.append(row)
            assert {x['qid'] for x in twins}==set(by_key) and len(twins)==1000
            with (dest/'binding.jsonl').open('x') as f:f.writelines(line for line,_ in chosen)
            with (dest/'twins.jsonl').open('x') as f:f.writelines(raw_twins)
            spec=dict(original_spec,source_database=base_pin,binding=pin(dest/'binding.jsonl'),rows=pin(dest/'twins.jsonl'))
            cfg['r1_training']['direction_twins']=spec
            selected += [(1000+i,line.rstrip('\n'),'{}') for i,line in enumerate(raw_twins)]
            db_pin=database(dest/'rows.sqlite',schema,selected)
            def staged(p):return dict(path='/tmp/q_22c714e1/p2/q/u/'+p['sha256'],sha256=p['sha256'])
            proof=dict(schema='r1-direction-augmentation-v1',database=staged(db_pin),binding=staged(spec['binding']),source_database=staged(spec['source_database']),rows=staged(spec['rows']),count=2000)
            cfg['r1_training']['direction_augmented']=J.write(dest/'augmentation.json',proof)
            # The existing fixture boundary substitutes four authenticated byte identities only.
            J.write(root/'TWIN_BOUNDARY.json',dict(pins=spec,rows=1000,synthetic=True,native_COUNT_unchanged=7971,
                substituted_constants=['r1_rooms.STORE','r1_direction_twins.ROWS','r1_direction_twins.BINDING','r1_direction_twins.ALIASES']))
            removal=Removals(cfg['remove_files']);paired=[]
            for row in twins:
                source=bases[by_key[row['qid']]['source_key']]
                a,b=removal.match(source),removal.match(row)
                assert a==b;paired.append(dict(source=source['qid'],twin=row['qid'],removal_match=a))
            census=Counter(rooms.status(json.loads(raw))[0] for _,raw,_ in selected)
            assert census.get('unresolved',0)==0
            J.write(root/'TWIN_SUBSET.json',dict(status='PASS',scope='pair, digest, source-room and removal consistency; native fixed binding cardinality remains unsatisfied',
                source_rows=1000,twin_rows=1000,augmented_rows=2000,native_binding_count=7971,
                native_cardinality_satisfied=False,original_pins=original_spec,fixture_pins=spec,augmentation=cfg['r1_training']['direction_augmented'],
                pairs=paired,room_census=dict(census),removals_unchanged=True,source_bytes_preserved=True,twin_bytes_preserved=True))
        else:db_pin=database(dest/'rows.sqlite',schema,selected)
        values=[json.loads(raw) for _,raw,_ in selected]
        receipt.update(count=len(selected),database=db_pin)
        if 'types' in receipt:
            assert len(old['types'])==1;receipt['types']={next(iter(old['types'])):len(selected)}
        if 'head_layouts' in receipt:
            receipt['head_layouts']=dict(Counter(v.get('head_layout',v.get('routing',{}).get('head_layout')) for v in values))
            if set(receipt['head_layouts'])=={None}:
                assert len(old['head_layouts'])==1;receipt['head_layouts']={next(iter(old['head_layouts'])):len(selected)}
        if 'target_filter' in receipt:receipt['target_filter']={'settings':old['target_filter']['settings']}
        removal=Removals(cfg['remove_files']);kept=sum(removal.keep(v) for v in values)
        with redirect_stdout(io.StringIO()):reports=removal.report()
        if 'removals' in receipt:receipt['removals']=reports
        receipt['fixture_subset']=dict(source_receipt=old_pin,source_database=old['database'],rows=len(selected),
            selection='1000 source rows plus their 1000 bound twins' if name=='vqa' else 'first rows in native i order')
        new_pin=J.write(dest/'receipt.json',receipt)
        records.append(dict(source=name,original_receipt=old_pin,original_database=old['database'],original_count=count,
            receipt=new_pin,database=db_pin,count=len(selected),row_and_target_bytes_preserved=True,
            rows_after_removals=kept,removal_report=reports))
        return new_pin
    for stream in ('routing','pointing','vqa'):cfg['streams'][stream]=bounded(cfg['streams'][stream],stream)
    pose=deepcopy(J.load(cfg['streams']['pose']['path']));assert len(pose['sources'])==2
    for i,source in enumerate(pose['sources']):
        assert source['kind']=='rows';source['receipt']=bounded(source['receipt'],'pose'+str(i))
        if 'count' in source:source['count']=limit
    cfg['streams']['pose']=J.write(folder/'pose.json',pose)
    assert cfg['remove_files']==original_removals
    J.write(root/'BOUNDED_POPULATION.json',dict(native_source=str(native),native_sha256=J.sha(native),host=os.uname().nodename,
        native_limit=limit,records=records,native_limit_unchanged=True,complete_fixture_populations=True,
        sampling_capacity_gate_unchanged=True,scope='Synthetic complete fixture subsets; native twin cardinality and sampler capacity cannot fit the scene limit.'))
