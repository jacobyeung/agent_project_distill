"""Real preparation-reader guards reject changed R1 and sampler identities."""
import copy,json,os,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=L/'work/merge11/proofs/n1/prepared_guards'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O),S1_CPU_REHEARSAL='1')
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import carrier_c1_run as C
from student_pilot.p3_provenance import file_pin,load,digest,source_files,sha256
from student_pilot.source_seal import inventory
from student_pilot.s1_exclusions import Exclusions
from student_pilot.r2_scene_bindings import SOURCES
from student_pilot.checkpoint_space import plan
from tests.test_r2_build_n1 import configuration,sampling
def put(name,value):
    path=O/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return file_pin(path)
cfg=configuration()
for key in ('r2','r2_identity','r2_membership','r2_build2','b7_inputs'):cfg.pop(key,None)
cfg['routing_opener_init']='reset'
cfg['recipe']=C.recipe_for(cfg);cfg['checkpoint_disk_guard']=plan(cfg['recipe'],retained_archive_copies=1)
cfg['r1_training']['registry']=file_pin(L/'work/merge11/proofs/n1/r1_edges/registry/all.json')
root=O/'sampler';root.mkdir(exist_ok=True);cfg['r2_sampling'],_=sampling(root)
dev=file_pin(T/'student_pilot/r2_dev_merged.json')
benchmark=file_pin(L/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json')
receipts,reports={},{}
for source,stream in SOURCES.items():
    row=dict(qid=source,dataset='d1',scene='fixture_clean',synthetic_cpu_fixture=True)
    population=put('scenes/'+source+'_row.json',row)
    rule=Exclusions(dev,benchmark);rule.expect(source,[row],population);assert rule.keep(row,source)
    report=rule.report();reports[stream]=report
    receipts[source]=put('scenes/'+source+'.json',dict(source_scene_exclusions=report))
reference=put('scenes/reference.json',dict(withhold_file=dev,benchmark_file=benchmark,
    exact_rebuilt_population=True,synthetic_cpu_fixture=True,source_rows={s:receipts[s] for s in SOURCES}))
cfg.update(r2_all_stream_exclusions=True,dev_scene_exclusions=dev,benchmark_scene_exclusions=benchmark,
           scene_coverage={'reference':reference})
cfg['r2_scene_rebuild']=put('scenes/rebuild.json',dict(files={'dev':dev,'benchmark':benchmark},
    scene_coverage=cfg['scene_coverage'],receipts=receipts,reports=reports,
    pool_selection=receipts['vqa']))
sources={str(p.relative_to(T)):sha256(p) for p in source_files([Path(C.__file__)])}
cfg['code']=put('source.json',dict(schema='c1-rehearsal-source-v1',sources=sources,
    content_sha256=digest(sources),tree_sha256=digest(inventory(T))))
records=[]
for name,receipt,reason in [
    ('inputs',dict(r1_training={}), 'Preparation R1 inputs differ'),
    ('sampler',dict(r1_training=cfg['r1_training'],r2_sampling={}), 'Preparation R1 sampler differs')]:
    cfg['preparation']=put(name+'.json',receipt)
    try:C.prepared(cfg)
    except ValueError as error:assert str(error)==reason,str(error);records.append(dict(case=name,refused=str(error)))
    else:raise AssertionError('Changed preparation identity admitted')
put('RESULT.json',dict(status='PASS',cases=records,
    scope='Negative reader checks using bounded synthetic scene/sampler metadata and the real source-closure verifier. No stream payload, frame or model is opened; no full-store or production admission claim.',
    real_functions=['r2_contract.preparation','r2_scene_bindings.verify','carrier_c1_run.validate','carrier_c1_run.authenticate','carrier_c1_run.prepared'],
    standins='Native CPU rehearsal identifies the unavailable pretrained boundary; no validator or producer function is replaced.'))
monitor.save(O);print(json.dumps(records))
