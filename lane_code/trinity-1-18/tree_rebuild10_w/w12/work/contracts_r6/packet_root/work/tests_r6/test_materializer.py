import copy
import json
import sqlite3
from types import SimpleNamespace as NS
import pytest
from fixtures_contracts import L
from test_contracts import row_case

@pytest.mark.parametrize('case,expected',[
    ('after_failure','contract_call_after_failed_ground'),('missing_response','contract_missing_response'),
    ('manifest','contract_manifest_missing'),('operator','contract_operator_fault'),
    ('unknown','contract_unknown_status'),('clean',None),('legal_retry',None),('manifest_bound',None),
    ('bounded','contract_unknown_status'),('manifest_superset',None),('phrases_superset',None)])
def test_build_defers_one_row_and_keeps_clean_row(case,expected,tmp_path,monkeypatch):
    from student_pilot import s1_routing as M, s1_pool, s1_pool_relocate, s1_exclusions, carrier_c1_run, row_removals,s1_route_policy
    from student_pilot.p3_provenance import file_pin
    from student_pilot.training_contract import audit_training_contract
    kind='object_abs_distance'
    def pin(name,obj):
        p=tmp_path/name;p.write_text(json.dumps(obj));return file_pin(p)
    bad=row_case('unknown' if case=='bounded' else case); clean=row_case('good')
    bad['qid']=case
    pool_rows=([dict(bad,qid=f'bounded-{i}') for i in range(60)] if case=='bounded' else [bad])+[clean]
    deferred_count=60 if case=='bounded' else 1
    assert audit_training_contract([bad])==[expected]
    def native(row):
        return dict(row,dataset='d1',scene='synthetic',student_input=dict(question=row['question'],options=[],fps=1.),
            routing=dict(events=row['events'],answer='2',question_type=kind,category='route',head_layout='ground_aggregate',tool_output_spans=[{}]))
    # The legacy missing-manifest case must also defer before token encoding.
    legacy=native(row_case('manifest'))
    legacy['qid']='legacy'
    db=tmp_path/'legacy.sqlite'
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT)')
        con.execute('INSERT INTO rows VALUES (?,?)',(0,json.dumps(legacy)))
    division=pin('division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,train_scenes=['d1/synthetic'],heldout_scenes=[]))
    old=pin('legacy.json',dict(database=file_pin(db),division=division,types={kind+':route':1},count=1))
    model=pin('model.json',dict(kind='base',root=str(tmp_path)))
    pin('tokenizer.json',{})
    pool=pin('pool.json',dict(implementation={},declared_rows=len(pool_rows),sources={'fixture':dict(status='ELIGIBLE',kind='packed',per_type={kind:len(pool_rows)},source=file_pin(db))},
        source_scene_exclusions={key:{'fixture':{}} for key in ('sources','datasets','expected')}))
    def relocate(*args,**kwargs):
        p=args[2];p.mkdir();(p/'relocation.json').write_text('{}')
        return dict(relocated=pool)
    monkeypatch.setattr(s1_pool_relocate,'relocate',relocate)
    monkeypatch.setattr(s1_pool,'implementation',lambda:{})
    monkeypatch.setattr(s1_pool,'selected_rows',lambda *args:[dict(x,question_type=kind) for x in pool_rows])
    monkeypatch.setattr(M,'compatibility',lambda *args:{kind:dict(disposition='COMPATIBLE')})
    monkeypatch.setattr(s1_route_policy,'validate',lambda cfg:None)
    monkeypatch.setattr(carrier_c1_run,'division_admits',lambda *args:True)
    monkeypatch.setattr(carrier_c1_run,'processor_for_receipt',lambda *args:NS(_routing_tokens={'ids':{}}))
    class Filters:
        def __init__(self,*args):self.expected={};self.files={};self.census=NS(identities=lambda row:None)
        def keep(self,*args):return True
        def expect(self,*args):pass
        def counts(self,*args):pass
        def report(self):return {}
    monkeypatch.setattr(s1_exclusions,'Exclusions',Filters)
    monkeypatch.setattr(s1_exclusions,'totals',lambda *args:None)
    monkeypatch.setattr(row_removals,'Removals',lambda *args:NS(keep=lambda row:True,report=lambda:{}))
    class Frames:
        dataset_fps={}
        fps={}
        pins={}
        def __init__(self,*args):pass
        def resolve(self,raw):
            return dict(question=raw['question'],options=[],frames=[],frame_indices=[],fps=1.,total_num_frames=32),dict(fps_source='fixture')
    monkeypatch.setattr(M,'Frames',Frames)
    monkeypatch.setattr(M.routing,'c1_row',lambda raw,rgb:native(raw))
    monkeypatch.setattr(M.routing,'render',lambda *args:('',[]))
    monkeypatch.setattr(M.routing,'suffix_tokens',lambda *args:([1],[],[]))
    cfg=dict(s1_routing=dict(schema='s1-routing-inputs-v1',selection=pool,frame_map={},frame_plan={}),
        streams=dict(routing=old),dev_scene_exclusions={},benchmark_scene_exclusions={},remove_files=[],recipe={},route_table={kind:'route'})
    if case=='manifest_bound':
        bad.pop('candidate_phrases')
        cfg['s1_routing']['candidate_manifest']=pin('candidates.json',{
            case:dict(phrases=['Chairs','Tables','BUCKETS']),'good':['chair','table']})
    if case in ('manifest_superset','phrases_superset'):
        names=['chair','table']+(['lamp'] if case=='phrases_superset' else [])
        bad['candidate_phrases']=names
        other=['chair','table']+(['lamp'] if case=='manifest_superset' else [])
        cfg['s1_routing']['candidate_manifest']=pin('candidates.json',{case:other,'good':['chair','table']})
    cfg['heading_plane_min']=.17
    receipt=M.build(cfg,tmp_path/'materialized',division,model)
    report=json.loads(open(receipt['materialization']['path']).read())
    assert report['heading_plane_min']==.17
    assert report['contract_deferred_qids']['contract_manifest_missing']['qids']==['legacy'] + ([case] if expected=='contract_manifest_missing' else [])
    if case=='bounded':
        assert report['contract_deferred_qids'][expected]==dict(count=60,qids=[f'bounded-{i}' for i in range(50)])
    elif expected:
        assert case in report['contract_deferred_qids'][expected]['qids']
    stats=report['types'][kind]
    assert stats['r16_deferred']=={'contract_manifest_missing':1}
    assert stats['pool_deferred']==({expected:deferred_count} if expected else {})
    assert stats['pool_program_rows']==(1 if expected else 2)
    if case=='manifest_bound':
        with sqlite3.connect(receipt['database']['path']) as con:
            rows=[json.loads(r[0]) for r in con.execute('SELECT row FROM rows')]
        assert next(row for row in rows if row['qid']==case)['candidate_phrases']==['bucket','chair','table']
    if case in ('manifest_superset','phrases_superset'):
        with sqlite3.connect(receipt['database']['path']) as con:
            rows=[json.loads(r[0]) for r in con.execute('SELECT row FROM rows')]
        assert next(row for row in rows if row['qid']==case)['candidate_phrases']==sorted(names)
    (L/f'work/test_artifacts_r6/materializer_{case}_r4.json').write_text(json.dumps(report,indent=2))
