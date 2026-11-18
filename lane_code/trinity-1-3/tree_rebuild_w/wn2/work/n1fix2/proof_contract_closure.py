"""Bounded real validators, sampler metadata, intake and reader refusal cases."""
import copy,json,os,sqlite3,sys,types
from pathlib import Path
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/contract_closure'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import r1_training as R,r1_mix as M,carrier_c1_run as C,r2_contract as RC
from student_pilot.p3_provenance import load,file_pin,digest
from tests.test_r2_build_n1 import configuration,sampling
from tests.test_r2_build9_recovery import envelope
from student_pilot.r2_intake import intake
from student_pilot.r1_loader import audit_rows
records=[]
def put(name,value):
    path=O/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return file_pin(path)
def reject(fn,reason):
    try:fn()
    except ValueError as error:assert reason in str(error),(reason,str(error))
    else:raise AssertionError('Expected refusal: '+reason)
def case(name,fn):
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    try:fn();status='PASS'
    except Exception as error:status=type(error).__name__+': '+str(error)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    records.append(dict(name=name,status=status,tmp_before=before,tmp_after=after))
def row_rules():
    assert R.row_check({},'pose')=={}
    assert R.scale_init({}, {}, enabled=False)==set()
    reject(lambda:R.row_check({'question_type':'camera_object_abs_distance'},'routing'),'CAMERA_OBJECT')
    reject(lambda:R.row_check({},'vqa'),'QUALITATIVE_TRACE')
    row=dict(question_type='room_size_estimation',target='<think>\nLocate: a in frame 1.\nLocate: b in frame 2.\nBad line.\n</think>\n\nA')
    reject(lambda:R.row_check(row,'vqa'),'ROOM_TRACE_INVALID')
def configurations():
    cfg=configuration()
    for name,value,reason in [('steps',999,'R1_RECIPE_DIFFERS'),('h1',{'faithful_own_camera_rows':True},'OWN_ROWS'),
                              ('milestones',[100,200,400,800,1000],'MILESTONES')]:
        bad=copy.deepcopy(cfg);bad[name]=value
        if name=='steps':bad['milestones']=[100,200,400,800]
        reject(lambda:R.validate(bad),reason)
    bad=copy.deepcopy(cfg);bad['scheduled_sampling']['max_own_probability']=.5
    reject(lambda:R.validate(bad),'OWN_PROBABILITY')
    reject(lambda:R.boundary(cfg,-1),'PROGRESS_STEP')
    reject(lambda:R.start(dict(init_artifact=dict(artifact=put('bad_export.json',{})))),'EXPORT_FORMAT')
    # Only the pretrained parent identity stands in; the real file-pin verifier runs.
    parent=put('parent_boundary.json',dict(schema='carrier-c1-artifact-v1',step=1))
    with patch.object(R,'PARENT',parent['sha256']):
        reject(lambda:R.start(dict(init_artifact=dict(artifact=parent))),'PARENT_STEP')
    reject(lambda:R.store_parameter(put('bad_store.json',{})),'VQA_RECEIPT')
    from student_pilot.checkpoint_space import plan
    cfg['recipe']=C.recipe_for(cfg);cfg['checkpoint_disk_guard']=plan(cfg['recipe'],retained_archive_copies=1);C.validate(cfg)
    cfg['r1_training']['stop_after_step']=1
    reject(lambda:C.run_steps(None,None,None,None,{},O/'loop',cfg,{},'cpu',start_step=1,distributed=False),'Completed C1 schedules')
def registry():
    from student_pilot.r2_policy import slots,LINEAGE,EXTERNAL
    reject(lambda:R.training_components(put('empty_registry.json',{}),{'geometry_connector':'none'}),'Component registry')
    values=slots();first=next(iter(values));values[first]['component_class']='invalid'
    reject(lambda:R.training_components(put('wrong_registry.json',values),{'geometry_connector':'none'}),'reclassified')
    values=slots();fixture=put('registry/fixture.json',dict(synthetic_cpu_fixture=True))
    for name in (*LINEAGE,*EXTERNAL,'data_rows_r2'):
        spec=values[name]
        spec['record']=put('registry/'+name+'.json',dict(schema=spec['expected_schema'],component=name,
            component_class=spec['component_class'],phase=spec['phase'],inputs=[fixture],frozen=True,
            verdict='EXEMPT_FROZEN' if name in EXTERNAL else 'PROVEN_CLEAN',
            checked_banks=['VSI-Bench','VSTI','ReVSI'],overlaps=[],exclusions_complete=True))
    pin=put('registry/all.json',values)
    reject(lambda:RC.preparation(dict(r1_training={'registry':pin},geometry_connector='none')),'R1_SCENE_AND_SAMPLER_BINDINGS_REQUIRED')
    identity=load(L/'fixtures/work/build6/INIT_INPUT.json')['identity']
    reject(lambda:RC.check_init(dict(init=identity,contract='wrong'),{}),'Next-leg init identity')
def sampler():
    root=O/'sampler';root.mkdir(exist_ok=True)
    binding,counts=sampling(root);card=load(binding['card']['path']);population=load(binding['population']['path'])
    eligible=population['counts'];indices=load(binding['indices']['path'])
    reject(lambda:M.allocate({},eligible),'CARD_INVALID')
    reject(lambda:M.allocate(card,{}),'POPULATION_MISMATCH')
    reject(lambda:M.allocate(card,{**eligible,'pose':-1}),'POPULATION_INVALID')
    bad=copy.deepcopy(card);bad['cells'][0]['rows_per_step']=-1
    reject(lambda:M.allocate(bad,eligible),'NEGATIVE_CELL')
    bad=copy.deepcopy(card);bad['cells'][0]['rows_per_step']=63
    reject(lambda:M.allocate(bad,eligible),'QUOTA_MISMATCH')
    badpop={**population,'complete':False};p=put('sampler/bad_pop.json',badpop)
    reject(lambda:M.validate_binding({**binding,'population':p}),'COMPLETE_FILTERED')
    bad=copy.deepcopy(indices);bad['cells']={};p=put('sampler/bad_indices.json',bad)
    reject(lambda:M.validate_binding({**binding,'indices':p}),'INDICES_DIFFER')
    reject(lambda:list(M.plans(binding,counts,1,world=1)),'PLAN_POSITION')
    bad=copy.deepcopy(indices);bad['cells']['pose'][0]=-1;p=put('sampler/bad_indices.json',bad)
    reject(lambda:list(M.plans({**binding,'indices':p},counts,1)),'INDEX_OVERLAP_OR_COUNT')
    reject(lambda:list(M.plans(binding,{**counts,'pose':counts['pose']+1},1)),'INDEX_COVERAGE')
def admitted_identity():
    rows=load(B/'proofs/extent_admission/units/samples.json');root=O/'intake';root.mkdir(exist_ok=True)
    manifest=envelope(root,rows,'routing','units');value=load(manifest)
    value['extent_receipt']=file_pin(B/'inputs/extents.json');manifest.write_text(json.dumps(value))
    accepted,_=intake(manifest);assert accepted
    row=accepted[0]['row'];covered={row['qid']:digest(row)}
    result=audit_rows([row],'routing','units',coverage=covered);assert result['counts']['admitted']==1
    reject(lambda:audit_rows([row],'routing','units',coverage={row['qid']:'bad'}),'ADMITTED_ROW_IDENTITY')
    put('admitted_identity.json',result)
def row_failure():
    reader=C.Rows(dict(streams={}),None)
    conn=sqlite3.connect(':memory:');reader.connections['routing']=conn
    conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    conn.execute('INSERT INTO rows VALUES(0,?,?)',('{}','{}'))
    reader.counts['routing']=conn.execute('SELECT COUNT(*) FROM rows').fetchone()[0]
    model=types.SimpleNamespace(training_mode='final',r1_training={'schema':'r1-training-v1'})
    try:reject(lambda:C.fetch(reader,'routing',0,model),'R1 row failure forbids')
    finally:reader.close()
for name,fn in [('row_rules',row_rules),('configurations',configurations),('registry',registry),('row_failure',row_failure)]:case(name,fn)
monitor.save(O)
put('RESULT.json',dict(cases=records,standins='Synthetic pretrained-parent metadata identity and model attributes only in pre-forward refusal cases. Other validators, sampler, file pins, intake and reader execute unchanged.',
    scope='Synthetic metadata refusal cases only; no production sampler or model inference qualification.'))
print(json.dumps(records))
if any(r['status']!='PASS' for r in records):raise SystemExit(1)
