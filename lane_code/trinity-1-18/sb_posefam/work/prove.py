"""Run the sealed N scene rule on complete raw-source scene projections.

This is a conservative admission proof, not a fabricated preparation receipt.
Missing targets/frame paths prevent the dense/prefix pass and exact N order.
"""
import ast
from collections import Counter
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sqlite3
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'work/code'))
OUT = ROOT/'out'
SNAP = json.loads((ROOT/'work/SNAPSHOT.json').read_text())
inputs = dict(SNAP['inputs'])

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

def load(label):
    return json.loads((ROOT/'work/inputs'/label).read_text())

def add_input(path, label):
    path=Path(path)
    inputs[label]=dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
    return inputs[label]['sha256']

for key, pin in inputs.items():
    assert sha(ROOT/pin['snapshot'])==pin['sha256'], key
add_input(ROOT/'work/SNAPSHOT.json','snapshot_manifest')
add_input(Path(__file__),'proof_script')
add_input(Path(sys.executable).resolve(),'python_interpreter')
add_input(ROOT/'work/build_files.txt','build_file_inventory')
add_input(ROOT/'work/other_candidates.txt','other_file_inventory')

# Execute exact function ASTs from the copied sealed module. Avoid its unrelated
# GPU/torch imports; no function bodies or filtering predicates are changed.
from student_pilot import p3_provenance as prov
router=types.ModuleType('student_pilot.carrier_c1_routing')
router.__package__='student_pilot'
router.__dict__.update(load=prov.load,pinned=prov.pinned)
path=ROOT/'work/code/student_pilot/carrier_c1_routing.py'
nodes=ast.parse(path.read_text()).body
names={'alias_key','alias_names','load_exclusions','excluded','canonical_keys'}
selected=[n for n in nodes if isinstance(n,ast.FunctionDef) and n.name in names or
          isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALIAS' for t in n.targets)]
exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),router.__dict__)
sys.modules[router.__name__]=router
from student_pilot.s1_exclusions import Exclusions
from student_pilot.r0_exclusion import reserve
path=ROOT/'work/code/student_pilot/carrier_c1_run.py'
tree=ast.parse(path.read_text())
excluded=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='excluded_row')
prepare=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
deferred=next(n for n in prepare.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_exclusions')
namespace=dict(__package__='student_pilot',routing=router)
exec(compile(ast.Module(body=[excluded,deferred],type_ignores=[]),str(path),'exec'),namespace)

cfg=load('config_b20.json')
oldcfg=load('config_n1fix2.json')
spec=load('mix.json')
bench=load('benchmark.json')
er=load('eval_rooms.json')
receipts=[load('a2_receipt.json'),load('a3_receipt.json')]
assert cfg['streams']['pose']['sha256']==inputs['inputs/mix.json']['sha256']
assert oldcfg['streams']['pose']==cfg['streams']['pose']
assert spec['division']['sha256']==inputs['inputs/division.json']['sha256']
for s,r,label in zip(spec['sources'],receipts,['a2','a3']):
    assert s['receipt']['sha256']==inputs['inputs/'+label+'_receipt.json']['sha256']
    assert inputs['inputs/'+label+'_receipt.json']['sha256']==inputs['inputs/'+label+'_receipt_rc3.json']['sha256']
    assert s['receipt']['sha256'] in (ROOT/'work/inputs/P_SHA256SUMS.txt').read_text()

def local_pin(label, cfgkey):
    p=ROOT/'work/inputs'/label
    assert sha(p)==cfg[cfgkey]['sha256']
    return dict(path=str(p),sha256=sha(p))

rule=Exclusions(local_pin('dev.json','dev_scene_exclusions'),local_pin('benchmark.json','benchmark_scene_exclusions'))
namespace['scene_filter']=rule

captures={}
for capture in ('41159526','41159521'):
    token='v'+hashlib.sha256(('rung1 scene arkitscenes/'+capture).encode()).hexdigest()[:12]
    key='d3/'+capture
    assert ['d3',token] in bench['rung1_tokens']
    assert key in bench['scenes']
    member=bench['members'][key]
    assert member['group']=='arkitscenes/venue381879'
    assert er['arkit_rooms'][capture]==member['group']
    assert {'VSI-Bench','ReVSI'}<=set(member['benchmarks'])
    captures[token]=dict(capture=key,token=token,room=member['group'],benchmarks=member['benchmarks'])

rows=[]
for label in ('a2','a3'):
    matches=list((ROOT/'work/inputs').glob(label+'_projection*'))
    assert len(matches)==1
    with gzip.open(matches[0],'rt') as f: values=[json.loads(x) for x in f]
    assert all(v['i']==i for i,v in enumerate(values))
    assert len(values)==receipts[len(rows)]['count']
    rows.append(values)

targets=[]
kept=set()
for source,values in enumerate(rows):
    name='pose/'+str(source)
    rule.expect(name,values,dict(projection_sha256=inputs['inputs/'+('a2' if source==0 else 'a3')+'_projection.scenes.jsonl.gz']['sha256']))
    for row in values:
        accepted=rule.keep(row,name)
        if accepted: kept.add((source,row['i']))
        if row['dataset']=='d3' and row['scene'] in captures:
            info=captures[row['scene']]
            matches=rule.matches(row)
            # A benchmark hit is deferred by prepare_exclusions regardless of
            # the earlier legacy predicate, then rejected by the final rule.
            hit,overlap=namespace['prepare_exclusions'](row,set(),set())
            assert not hit and matches['benchmark'] and not accepted
            targets.append(dict(source=source,source_name=('a2v3','a3v2')[source],
                raw_index=row['i'],qid=row['qid'],dataset=row['dataset'],scene=row['scene'],**info,
                final_filter_matches=matches,matched_benchmark_keys=sorted(rule.identifiers(row)&rule.names['benchmark']),
                admitted=False,drop_reason='BENCH_v2_final_scene_filter',
                first_actual_drop='MISSING: dense/frame-prefix selection requires full row and target payloads',
                r0_matches_on_projection=reserve().matches(row),
                proof='If a source row reaches the final scene filter, N rejects it; any earlier removal also excludes it.'))
assert len(targets)==23 and all(t['source']==0 for t in targets)
assert Counter(t['capture'] for t in targets)=={'d3/41159526':12,'d3/41159521':11}
assert len({t['qid'] for t in targets})==23
report=rule.report()
assert all(x=='PASS' for x in report['comparisons'].values())

def save_order(filename, order):
    p=OUT/filename
    p.write_text(prov.encoded(order)+'\n')
    return dict(path=str(p.relative_to(ROOT)),sha256=sha(p),count=len(order),
                encoding='native p3_provenance.encoded(array) plus newline',inputs_sha256={k:v['sha256'] for k,v in inputs.items()})

upper=save_order('raw_scene_filter_upper_bound_order.txt',[list(x) for x in sorted(kept)])
# Independently reproduce P's pinned order under N's final rule. This does not
# promote P's preselection into an N preparation receipt.
pr=load('p_receipt.json')['streams']['pose']
pm=load('p_mix_order.json'); po=load('p_scene_order.json')
assert pr['receipt']['sha256']==cfg['streams']['pose']['sha256']
assert pr['order']['sha256']==inputs['inputs/p_scene_order.json']['sha256']
assert pr['scene_source']['order']['sha256']==inputs['inputs/p_mix_order.json']['sha256']
for i,r in enumerate(receipts): assert pr['sources'][i]['database']==r['database']
assert len(pm)==pr['scene_source']['count'] and len(po)==pr['count']
pmset=set(map(tuple,pm)); poset=set(map(tuple,po))
conditional=[x for x in pm if tuple(x) in kept]
replayed=save_order('P_order_under_N_scene_filter.txt',conditional)
for t in targets:
    pair=(t['source'],t['raw_index'])
    t['P_step544_pre_scene_present']=pair in pmset
    t['P_step544_admitted_present']=pair in poset
assert all(not t['P_step544_pre_scene_present'] and not t['P_step544_admitted_present'] for t in targets)

# Join the available build-21 fixture by qid, never by unrelated raw indices.
fixture=load('fixture_receipt.json')['streams']['pose']
fo=load('fixture_order.json')
assert fixture['receipt']['sha256']!=cfg['streams']['pose']['sha256']
assert len(fo)==fixture['count']
assert fixture['order']['sha256']==inputs['inputs/fixture_order.json']['sha256']
fqids={}; fixture_db=[]
for i,s in enumerate(fixture['sources']):
    p=Path(s['database']['path'])
    actual=add_input(p,'fixture_database_'+str(i));assert actual==s['database']['sha256']
    with sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True) as conn:
        mapping={idx:json.loads(raw)['qid'] for idx,raw in conn.execute('SELECT i,row FROM rows ORDER BY i')}
    fqids.update({(i,idx):qid for idx,qid in mapping.items()})
    fixture_db.append(dict(pin=s['database'],rows=len(mapping)))
admitted_fqids={fqids[tuple(x)] for x in fo}
fixture_hits=sorted(admitted_fqids&{t['qid'] for t in targets})
assert not fixture_hits

inventory=(ROOT/'work/build_files.txt').read_text().splitlines()
order_candidates=[p for p in inventory if Path(p).name in ('pose_scene_order.json','pose_mix_order.json')]
other_databases=[]
for name in (ROOT/'work/other_candidates.txt').read_text().splitlines():
    p=Path(name)
    if p.suffix=='.sqlite':
        actual=add_input(p,'other_database_'+p.stem)
        assert actual not in {r['database']['sha256'] for r in receipts}
        other_databases.append(dict(path=name,sha256=actual,bytes=p.stat().st_size,
                                    filename_is_database_hash=(actual==p.stem),
                                    matches_raw_pose_database=False))
missing=[dict(kind='full raw SQLite',expected=r['database'],
              expected_recovery='/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/preceipts/rc3/u/ap/f02f16ad/s/'+name+'/rows.sqlite',
              status='MISSING',available='Complete scene projection, not frames/targets') for name,r in zip(('a2v3','a3v2'),receipts)]
missing.append(dict(kind='N production preparation receipt and admitted pose order',status='MISSING',
                    expected_receipt=cfg['preparation_output']+'/receipt.json',
                    expected_order=cfg['preparation_output']+'/pose_scene_order.json',
                    expected_recovery='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20 or w21 production preparation fixture',
                    note='No N-bound order recovered in searched build inventory; output path is inherited and must be authenticated against N config.'))

result=dict(schema='sb-posefam-proof-v1',status='23_EXCLUDED_BY_N_BENCH_FILTER; EXACT_N_ORDER_MISSING',
    command='OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 '+sys.executable+' -B work/prove.py',
    inputs=inputs,tree_sha256=load('tree_seal.json')['tree_sha256'],
    N_config_sha256=inputs['inputs/config_b20.json']['sha256'],
    code_trace=[dict(file='student_pilot/carrier_c1_run.py',function='prepare / prepare_exclusions',lines=[464,505],
                     role='Load scene rule, defer scene matches, prepare pose mix'),
                dict(file='student_pilot/c1_pose_mix.py',function='_row_selected / prepare',lines=[66,73,123,235],
                     role='Dense rows, frame prefix, division, validation, legacy exclusion, source-index order'),
                dict(file='student_pilot/carrier_c1_sweep.py',function='dense_pose_row',lines=[145,155],
                     role='Needs full camera targets and frame paths, unavailable in projection'),
                dict(file='student_pilot/carrier_c1_run.py',function='prepare',lines=[620,625],
                     role='Apply final scene filter to all streams including pose'),
                dict(file='student_pilot/s1_exclusions.py',function='Exclusions / selection / apply',lines=[42,128,191,224,334,345],
                     role='Match BENCH/dev names and room aliases, preserve source-index order, write pose_scene_order.json'),
                dict(file='student_pilot/carrier_c1_run.py',function='excluded_row / Rows.row',lines=[340,348,1104,1128],
                     role='Reserve-room exclusion during preparation and reader checks'),
                dict(file='student_pilot/r1_rooms.py',function='verify_audit / census',lines=[86,125,130,175],
                     role='K1/R0 audit scopes routing slices and VQA; not the pose population'),
                dict(file='student_pilot/r1_routing.py',function='compose',lines=[53,90],role='Explicit Rooms.admit call')],
    N_pose_receipt=cfg['streams']['pose'],sources=[dict(source=i,receipt=spec['sources'][i]['receipt'],database=r['database'],
      raw_rows=len(rows[i]),frame_prefix=spec['sources'][i]['frame_prefix']) for i,r in enumerate(receipts)],
    filters=dict(benchmark=cfg['benchmark_scene_exclusions'],dev=cfg['dev_scene_exclusions'],
                 rule='Copied, seal-verified s1_exclusions.Exclusions.expect/keep/report on original projected dataset/scene; no invented canonical row fields.',
                 execution='Exact AST function bodies for routing helpers and prepare_exclusions; unchanged s1_exclusions module. No GPU imports.'),
    counts=dict(raw_rows=sum(map(len,rows)),target_rows=len(targets),target_survivors=0,
                by_capture=dict(Counter(t['capture'] for t in targets))),
    targets=targets,raw_scene_filter_census=report,raw_scene_only_upper_bound=upper,
    exact_N_admitted_order=dict(status='MISSING',sha256='MISSING',count='MISSING',
        reason='Full raw target/frame payloads are absent, so dense selection, frame_prefix, pose_row_check, and full-row reserve checks cannot be replayed.'),
    P_control=dict(pinned_pre_scene_rows=len(pm),pinned_admitted_rows=len(po),
        target_pre_scene_rows=sum(t['P_step544_pre_scene_present'] for t in targets),
        target_admitted_rows=sum(t['P_step544_admitted_present'] for t in targets),
        replay=replayed,replay_equals_P_admitted=(conditional==po),
        scope='N final scene filter applied to P preselection. This is not an authenticated N admitted order.'),
    fixture_join=dict(order_candidates=order_candidates,pose_receipt=fixture['receipt'],databases=fixture_db,
        admitted_rows=len(fo),target_qid_matches=fixture_hits,
        scope='Foreign capacity fixture; different pose receipt and source database hashes; cannot prove N production membership.'),
    other_database_search=other_databases,
    room_rule=dict(scene_rule='BENCH physical_groups and rung1_tokens are loaded; supplied canonical/physical_group/room/alias fields are matched; ScanNet room prefix is inferred.',
        ARKit_limit='s1_exclusions does not infer an unlisted ARKit capture-to-venue mapping; these two captures have explicit BENCH tokens and independently verified venue membership.',
        r0='carrier_c1_run.excluded_row invokes r0_exclusion.reserve for pose and Rows.row rechecks it for r1_training.',
        full_room_authority='r1_rooms.Rooms.admit is called by r1_routing.compose, not by the pose preparation loop; its audit covers routing slices/VQA, not all raw pose.',
        venue_exception='r2_policy.record new_training requires PROVEN_CLEAN and exclusions_complete; no lineage venue exception applies.'),
    limitations=['Scene-only survivors are an upper bound, never an admitted population.',
                 'The mandatory BENCH rejection is proved for each target; its first actual rejection in an N run is MISSING.',
                 'Raw database hashes are receipt/attestation pins; local gzip projection bytes are independently hashed.',
                 'This pose-family proof does not close the entire data_rows_r2 record.'],missing=missing)
(OUT/'POSEFAM.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(ROOT/'STATUS.md').write_text('Stage 3: N’s sealed final scene rule rejects all 23 venue-381879 qids in the complete raw projections. The independent census agrees. The exact N admitted order remains MISSING because raw frame/target payloads are absent. P’s preselection and admitted order contain none of the 23; the foreign build-21 capacity fixture also joins to zero and cannot supply N membership.\n')
print(json.dumps(dict(counts=result['counts'],census=report['sources'],P_replay_equal=conditional==po,
                      upper_bound=upper['count'],fixture_matches=fixture_hits,exact_N_order='MISSING'),indent=2))
