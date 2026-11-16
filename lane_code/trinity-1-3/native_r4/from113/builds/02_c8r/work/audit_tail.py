from collections import Counter
from unittest.mock import patch
import kernels as K
prior=load(B.parent/'01_c8/out/c8/FAMILY_C8.json')
unchanged_assets={k:f['assets'][k]==old['assets'][k] for k in old['assets'] if k not in ('small_objects','worker_entrypoint')}
assert all(unchanged_assets.values())
trainer=W/'obj/t_b01ce449beffe35b.tar'
assert sha(trainer)==f['assets']['trainer']['sha256'] and trainer.stat().st_size==f['assets']['trainer']['bytes']
trainer_sources={}
with tarfile.open(trainer) as t:
 for m in t:
  if m.name in tree:
   assert m.isfile();trainer_sources[m.name]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert trainer_sources==tree
frames={}
with tarfile.open(W/'obj/frames.tar') as t:
 for m in t:
  assert m.isfile() and m.name not in frames and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  frames[m.name]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
expected_frames={k:v if isinstance(v,str) else v['sha256'] for k,v in f['assets']['frames_inventory'].items()}
assert frames==expected_frames
partitions=K.partition((R/'native/out2/nomdg.py').read_text(),(R/'native/out2/geometry.py').read_text())
assert set(partitions)=={'restore','parity','pair','geometry_restore','geometry'}
receipt=R/'orchard_native/MASK_CACHE_C8_BOUND.json'
rebound=B.parent/'01_c8/work/rh_pilot_06/MASK_CACHE_REBOUND.json'
assert receipt.read_bytes()==rebound.read_bytes()
assert f['worker_contract']['mask_cache']['sha256']==sha(receipt)==f['code_pins'][f['worker_contract']['mask_cache']['path']]
local_checks={}
try:L.objects(f['assets'])
except Exception as e:local_checks['objects']=dict(status='EXPECTED_REFUSAL',reason=str(e))
else:raise AssertionError('Pending upload generation admitted')
try:L.scope(f)
except Exception as e:local_checks['scope']=dict(status='ORCHARD-ONLY',reason=str(e),explanation='Historical authority files are not supplied in this namespace')
else:local_checks['scope']=dict(status='PASS')
dump(B/'out/NATIVE_LOCAL_CHECK.json',local_checks)
dump(B/'out/NATIVE_PIN_GRAPH.json',dict(constants_executed=True,partition_executed=True,
 tree_sources_verified=True,archive_inventories_verified=True,
 full_prove_executed=False,reason='No production packet, upload receipt, live pool snapshot, or historical authority paths are supplied.'))
pilot=B.parent/'01_c8/work/rh_pilot_06'
result=load(pilot/'RESULT.json');assert result['whole_worker_complete'] and result['return_chain_verified']
log=[]
for i,line in enumerate((pilot/'worker.log').open(),1):
 try:row=json.loads(line)
 except ValueError:continue
 log.append((i,row))
geolog=[(i,r) for i,r in log if r.get('event')=='geometry_capture_outcome']
assert len(geolog)==84
probe=next(i for i,r in log if r.get('event')=='native_probe_p2' and r['passed'])
report=load(pilot/'runs/c80000001/native/probe/PILOT_REPORT.json')
assert len(report['geometry'])==84 and len(report['items'])==10
import native_metrics as M
M.validate_gravity_guard(report['gravity_guard_report'],{'dev-S1':report['geometry']})
for rel in ('native/out2/nomdg.py','native/out2/perception.py','native/out2/geometry.py','native/out2/routed.py','orchard_native/native_worker.py','orchard_native/kernels.py'):
 assert sha(R/rel)==sha(B.parent/'01_c8/out/c8/sources/sj/orch_cd/evalx/work/milestone'/rel)
facts=dict(objects=objects,tree_digest=tree_digest,tree_files=len(tree),trainer=dict(path=str(trainer),sha256=sha(trainer),sources=len(trainer_sources)),
 frames=dict(path=str(W/'obj/frames.tar'),inventory_count=len(frames),inventory_sha256=C.canonical(frames)),
 artifact=dict(path=str(W/'obj/m544_artifact.json'),sha256=artifact_sha,step=artifact['step']),
 assets_unchanged_from_pilot9=unchanged_assets,partitions=sorted(partitions),mask_receipt_sha256=sha(receipt),
 bootstrap_count=len(f['bootstrap_pins']),code_pin_count=len(f['code_pins']),adapter_count=len(f['worker_contract']['adapter_pins']),
 pilot_geometry_log_lines=[i for i,r in geolog],pilot_probe_line=probe,
 pilot_fixture=True,new_family_whole_worker_executed=False)
dump(B/'out/OBJECT_AUDIT.json',facts)
E='out/OBJECT_AUDIT.json';F='out/c8r/FAMILY_C8R.json';T='out/c8r/code_c8r.tar'
checks={
9:(str(len(f['bootstrap_pins']))+' bootstrap pins equal code pins and exact archive members',F+'; '+T+'; '+E),
12:(str(len(objects))+' exact objects; '+str(sum(x['bytes'] for x in objects.values()))+' bytes below the staging bound',E),
14:('Every local small-object SHA256, size, and available MD5 matches; code MD5 is computed locally, cloud generation remains row 13',E),
15:('Every member digest, size and expanded-byte total matches: '+json.dumps({k:v['members'] for k,v in objects.items()}),E+'; '+T),
18:(tree_digest+'; every tree source also equals its trainer archive member',E+'; '+str(trainer)),
21:('Worker and sitecustomize asset pins equal their exact code members and runtime-spec inputs',E+'; '+F+'; '+T),
22:(asset_checks['model_manifest']['sha256'],str(W/'obj/model_8005668fc14ce5ee.tar')+'; '+F),
26:(asset_checks['frame_puller']['sha256'],T+'; '+F),
27:(str(len(frames))+' frame hashes match the family inventory exactly',str(W/'obj/frames.tar')+'; '+E),
30:('Both guard members have executable mode 0755 and unchanged hashes',T+'; '+F),
33:(asset_checks['sitecustomize']['sha256'],T+'; '+F),
35:(asset_checks['worker_entrypoint']['sha256']+' equals worker member, code pin and bootstrap pin',T+'; '+F),
37:(str(len(f['worker_contract']['adapter_pins']))+' adapter hashes equal exact members and code pins',E+'; '+T+'; '+F),
39:('Both kernel pins match exact members; real AST partition succeeded: '+','.join(sorted(partitions)),E+'; out/NATIVE_PIN_GRAPH.json'),
42:(sha(receipt)+' exact cache-bind bytes; producer '+mask['producer_sha256']+' equals the reader kernel pin; only producer differs from legacy JSON',str(rebound)+'; '+T+'; '+F),
}
rehearsal={
38:('Real cohort/input and selection validation executed; worker, kernels and reader bytes match C8r',f'{pilot}/worker.log:1; {pilot}/worker.log:{probe}; {pilot}/runs/c80000001/native/probe/PILOT_REPORT.json; '+E),
43:('Real masks validation and operand binding executed on the same object and reader; exact rebound receipt is shipped',f'{pilot}/worker.log:{probe}; {pilot}/CACHE_BIND_PROOF.json:22; {pilot}/RESULT.json:15; '+E),
44:('Real raw-cache and frame checks executed for every capture using unchanged geometry/routed sources',f'{pilot}/worker.log:{geolog[0][0]}; {pilot}/worker.log:{geolog[-1][0]}; '+E),
45:('Pilot terminal and return chain passed with complete geometry dispositions; guard report revalidated locally; full tail still pending',f'{pilot}/RESULT.json:15; {pilot}/worker.log:{geolog[-1][0]}; {pilot}/runs/c80000001/native/probe/PILOT_REPORT.json; out/tests/results.log'),
}
live={
1:'Batch checks assigned job digits, exclusive private root, and a fresh token.',
2:'Batch authenticates its literal payload digest; a production C8r packet is not supplied.',
3:'Batch checks unique safe regular members and the payload size bound; a production C8r packet is not supplied.',
4:'Native job validates the actual CONFIG schema, mode, partition, step, token and GPU count.',
5:'Native job checks Orchard host, user, partition and assigned allocation.',
6:'Early admission hashes the actual FAMILY, REVIEW and ORDER; new authority documents are not supplied.',
7:'Native admission compares CONFIG assets, limits and worker contract to FAMILY and requires ACCEPT.',
8:'Native admission authenticates the authorization, plan and exact order line for a fresh token.',
10:'Storage proof verifies the job-private mount and available disk.',
11:'Card checks require an empty exclusive assigned H100.',
13:'Staging validates the live cloud name, prefix, generation, size and digest; code generation/MD5 await upload.',
16:'Staging authenticates runtime, numpy, closure and trainer archives; trainer was recomputed locally, runtime and closure bytes are unavailable here.',
17:'Staging checks safe interpreter links and a unique runtime interpreter.',
19:'Staging authenticates the production bwrap executable; sandbox bwrap is not that runtime proof.',
20:'Staging authenticates FLA bytes and members against its manifest; the manifest pin passes locally.',
23:'Staging verifies base archive and weight inventory; only tokenizer/config inputs are supplied locally.',
24:'Staging verifies the depth-file identities; those weights are unavailable here.',
25:'Staging authenticates export parts, total bytes, headers and artifact; artifact is recomputed locally, tensor transport is unavailable.',
28:'The launched namespace authenticates the real controls, complete code-pin map and checkpoint step.',
29:'Native job requires a fresh exclusive output directory for the assigned token.',
31:'Bootstrap verifies isolated flags, schema, runtime archive and tree digest; constants pass locally, production interpreter boot is unexecuted.',
32:'Bootstrap checks the exact interpreter and overlay identities; local env312 is a rehearsal environment.',
34:'Bootstrap checks seven import origins/pins and required versions; production FLA/runtime imports were not run.',
36:'Worker validates real config admission and assigned Orchard allocation; C8r whole-worker namespace is blocked here.',
40:'Runtime tree validation and authenticated model restoration precede first GPU use; tree bytes pass locally, model load is a CPU fixture.',
41:'Restoration validates config, artifact, receipts, preparation, source seals and init-spec; the actual weight restore was not run here.',
46:'Job probes the new pool before staging, enforces the existing pool cap and fresh token directory, and verifies return copies. Local stand-in tests pass; live quota and cloud credentials remain unchecked.',
}
assert set(checks)|set(rehearsal)|set(live)==set(range(1,47))
earlier='Pilot 9 job 169792, family 3688e987: '+str(W/'p9/metadata/FAMILY.json')+'; '+str(W/'p9/metadata/ORCHARD_NATIVE.json')+'; '+str(W/'p9/logs/worker.log')
rows=[]
for item in G.ROWS[:46]:
 number,site,expected,actual,duplicate,kind=item
 if number in checks:
  actual,source=checks[number];status='PASS'
 elif number in rehearsal:
  actual,source=rehearsal[number];status='PASS-REHEARSAL'
 else:
  status='ORCHARD-ONLY';actual=live[number]+' '+('The new return pool/GCS path is not covered by the earlier job.' if number==46 else 'Earlier job covers the unchanged runtime/base/export/frames/trainer, not the new packet or authorization.')
  source=earlier+'; '+F+'; '+E
 rows.append(dict(check=number,site=site,expected=expected,actual=actual,source=source,status=status))
counts=dict(Counter(r['status'] for r in rows))
dump(B/'out/PIN_AUDIT.json',dict(rows=rows,counts=counts,objects=E,production_admission=False))
text=['# C8r pin table','',
 'PASS means recomputed locally against the exact C8r archive, family and input objects. PASS-REHEARSAL means the operator executed unchanged production paths in the C8 CPU fixture; it does not claim that C8r ran on Orchard. ORCHARD-ONLY names the remaining live/authority check. Missing new authority or upload data is not supplied by an earlier job.',
 '', '| Check | Expected | Actual | Source | Status |','|---|---|---|---|---|']
for r in rows:text.append('| '+str(r['check'])+' | '+r['expected']+' | '+r['actual']+' | '+r['source']+' | '+r['status']+' |')
(B/'out/PIN_TABLE.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(counts=counts,record=str(B/'out/PIN_AUDIT.json'))))
