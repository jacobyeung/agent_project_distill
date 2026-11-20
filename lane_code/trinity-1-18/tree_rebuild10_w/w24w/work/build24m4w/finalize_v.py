from pathlib import Path
import sys,json,difflib,re,ast
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4w';sys.path.insert(0,str(D))
from seal import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin,source_files
base=z.load(D/'BASELINE.json');files=inventory(T);tree=digest(files);seals=z.load(D/'SEALS.json')
assert tree==seals['tree']
changed=sorted(n for n,h in files.items() if base['inventory'][n]!=h)
assert changed==['student_pilot/carrier_c1_run.py','student_pilot/extent_receipt.py','student_pilot/r1_routing.py','student_pilot/r2_intake.py']
diff=[]
for rel in ('student_pilot/extent_receipt.py','student_pilot/carrier_c1_run.py','student_pilot/r1_routing.py','student_pilot/r2_intake.py'):
 old=(L/'attic/build24m4v_apply/work/tree_r1c'/rel).read_text();new=(T/rel).read_text()
 diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert ''.join(diff)==(L/'out/TREE_CHANGE_24M4V.patch').read_text()
old=(L/'attic/build24m4v_apply/work/tree_r1c/student_pilot/extent_receipt.py').read_text()
new=(T/'student_pilot/extent_receipt.py').read_text()
assert old[old.index('        if not required'):]==new[new.index('        if not required'):]
names=z.load(D/'SOURCES.json')['names'];configs={}
for name in NAMES:
 k=kit(name);assert verify(k)==seals['kits'][name]
 for rel in ('k/a.json','BUILD.json'):assert z.load(k/rel)['GO']==(name=='n_go')
 control=z.load(k/'k/a.json');check_archive(file_pin(k/control['source']['path']),files)
 for rel in ('k/7.json','k/c0.json'):
  v=z.load(k/rel);assert v['files']==files and v['tree_sha256']==tree
  assert all(files[n]==h for n,h in {**v['sources'],**v['operation_sources']}.items())
 for rel in ('k/c.json','k/n.json'):
  v=z.load(k/rel);before=z.load(L/'attic/build24m4w'/k.relative_to(L)/rel)
  assert v['r1_training'].pop('extent_pool_sources')==names
  assert v['extent_receipt']==before['extent_receipt']
  assert v['extent_receipt']['sha256']==z.sha(D/'c072905b.json')
  v['code']=before['code'];assert v==before,(name,rel)
 configs[name]=dict(source_list=names,extent_receipt_unchanged=True)
for name in ('x.py','ps.py','nd.py','pc.py','rcj.sh','P_SAMPLE_I.json'):
 assert z.sha(L/'out/rcj'/name)==base['rcj'][name]
latest={};all_runs=[]
for name in ('SUITE_RUNS.json','RERUN_RUNS.json','RERUN2_RUNS.json','RERUN3_RUNS.json','FINAL_RUNS.json'):
 for v in z.load(D/name):latest[v['name']]=v;all_runs.append(v)
assert all(v['returncode']==0 for v in latest.values()),latest
checks={}
for name in ('TREE_TESTS.json','REAL_TESTS.json','REAL_DIFFERENTIAL.json','CARD_NUMBERS.json','CARD_SAMPLE_TEST.json','APPLY_TEST.json','APPLY_NEGATIVE.json','DELTA_REPLAY.json','MODE_B_TESTS.json','REAL_PATH_TESTS.json','INPUT_AUDIT.json'):
 value=z.load(D/name);assert value['status']=='PASS',name;checks[name]=dict(status='PASS',sha256=z.sha(D/name))
assert files['student_pilot/s1_scene_census.py']==base['inventory']['student_pilot/s1_scene_census.py']
census=sum(len(v['access']['compare_calls']) for v in z.load(D/'REAL_PATH_TESTS.json')['records'])
assert census==80
for v in z.load(D/'REAL_PATH_TESTS.json')['records']:
 assert all(x['result']=='PASS' for x in v['access']['compare_calls'])
 assert v['result']['compare_sha256']==files['student_pilot/s1_scene_census.py']
upload=z.load(L/'out/UPLOADS_24M4V.json');assert upload['total_files']==36
for item in upload['files']:
 p=L/item['relative_path'];assert z.sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
failures=[dict(**v,output=(L/v['log']).read_text(),resolved_by=latest[v['name']]['log']) for v in all_runs if v['returncode']]
for name in ('tree_tests.log','tree_tests2.log','tree_tests3.log'):
 failures.append(dict(name=name,output=(D/name).read_text(),resolved_by='tree_tests4.log'))
failures.extend([
 dict(name='Initial real P sample chain',output=z.load(D/'P_SAMPLE_CHAIN.json'),resolution='All 20 unchanged P unit variants retain the baseline refusal; the exact 80 non-boundary rows pass. REAL_DIFFERENTIAL.json compares all 100 rows.'),
 dict(name='Raw Rows constructor tamper control',output='AssertionError: Tampered database accepted',resolution='Rows.connect trusts its caller; the unchanged chain pinned() boundary rejects changed DB bytes. The final control tests that actual boundary, not the raw constructor.'),
 dict(name='Copy setup',output="OSError: [Errno 18] Invalid cross-device link: w24u/work/tree_r1c/.gitignore -> private copy",resolution='The test copies files across the workspace mounts and verifies every base seal before applying.'),
])
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_targeted_test_failures=[],
 limitations=['The complete N database is unavailable locally. Full-chain refusal count must be measured by the next CPU job.',
 'The offline v1 count uses source-family classification; the CPU card reads canonical provenance on every exempted row.',
 'The source field is trusted only after existing pinned-input authentication. Bare Extents.check and Rows.connect do not authenticate arbitrary caller-created rows.']))
write(D/'FINAL_SUITE_RUNS.json',list(latest.values()))
validation=dict(status='PASS',tree_sha256=tree,kits=seals['kits'],changed_tree_files=changed,
 receipt_sha256=z.sha(D/'c072905b.json'),configs=configs,checks=checks,suite_groups=len(latest),targeted_tree_tests=18,
 census_compare_unchanged=True,native_census_comparisons=census,mode_b_byte_identical=True,
 rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()},ordinary_upload_files=36,
 scope='Local native and synthetic suites, published real P rows and complete published key inventory; no complete N DB replay.',
 full_N_database_checked=False,GO=False,uploaded=False,launched=False,
 report_style=dict(skill='no-archaeology',retained_comparison='Fail-before evidence explicitly requested by the build brief.'))
write(D/'VALIDATION.json',validation)
card=z.load(D/'CARD_NUMBERS.json');largest=max(upload['files'],key=lambda v:v['bytes'])
notes=[
 'The scoped tree is '+tree+'; the base is C″ de202f58. c072905b remains pinned without byte changes.',
 'Fail-before: the exact published P row vsi590k_256181 from job 173725 p_sample.json raises EXTENT_ROW_UNAUDITED; the identical call and row pass with the configured list. BEFORE.json and REAL_TESTS.json retain the evidence.',
 'The patch is in student_pilot/extent_receipt.py:25,35,44; carrier_c1_run.py:1071 reads r1_training.extent_pool_sources. The original gate after the early return is byte-identical.',
 'The nine names are ARKIT_gaps, ARKIT_gen_r2, T0_gaps, T0_gen_r2, T1H1_gaps, T1H1_gen_r2, T1H2_gaps, T1H2_gen_r2 and U_Faithful, exactly the ELIGIBLE names in P selection 5db993b1.',
 'Only routing rows with a matching s1_source.name, no a0_ QID and no boundary r1_source take the exemption. Empty or absent lists preserve the original gate. Other streams, sources and boundary rows retain the original checks.',
 's1_pool.py:225,239,247 authenticates the selection, indices and source; s1_routing.py:413 assigns s1_source from that selection. The chain authenticates DB bytes; r1 composition authenticates its base; r2_intake.py:83-89 authenticates row membership. A non-pool row cannot change source under those pins.',
 'This guarantee belongs to the existing authenticated-input boundary: bare Extents.check and Rows.connect do not authenticate caller-created dictionaries. The tampered-DB chain test refuses before Rows.',
 'r1_routing.py:160 and r2_intake.py:123 report extent_exempted beside refusal counts. rcj/ch.py:107 reports exempted, still-checked and required-gate counts for review.',
 'The three real-row controls pass: a0_ without its entry refuses; the P pool row passes; an unprefixed row without s1_source refuses. The real 80-row chain reports 14 exempted, 66 still checked and zero refusals.',
 'All 100 published P rows were checked differentially. The 20 P unit variants retain their original content-mismatch refusals; they are not substitutes for the unavailable N rows.',
 'The complete published N key inventory contains 10,945 exemptible rows and 32,156 still-checked rows, including 718 a0_ pool variants. Full-chain zero refusals remain for the next CPU job to establish.',
 'The offline source-family count is 3,362 ScanNet++ v1 rows, or 3,362 / 11,663 = 28.8262% of N distance rows. Published sample canonical provenance corroborates the source labels; the CPU card checks every real canonical value.',
 'P has 12,475 pool QIDs. Exactly 7,232 have receipt entries: 6,485 pool_full and 747 units_full; none has a repair hash or a non-full box status.',
 'Normalizing both sides to vsi590k_[0-9]+ across all derived variants matches 9,324 P QIDs (8,577 distinct base IDs); 1,892 match a repaired variant and zero match a flagged non-full status. Thus 7,232 is the exact-match count, not the all-variant normalized count. Normalization never authenticates admission.',
 'rcj/ch.py:333 runs the three controls in the next chain step; the pool and a0_ examples come from the real DB. If no third class exists there, it uses the embedded exact real slice row vsi590k_169139, identified as sealed_reference. ch.py:379 computes the card from real P/N DB rows.',
 str(len(latest))+' suite groups and 18 targeted tree tests pass. Eight launch-command comparisons and the mode-b publication tests are byte-identical; 80 native census comparisons pass and census source bytes are unchanged.',
 'All kits carry the list. Only kit_n_go has GO=true; no job was launched or uploaded. The apply script passes on a copy of 24m4u, preserves its other helpers, rejects a wrong base and writes a merged upload manifest.',
 'Cursor review: Does anything else in admission, legality, rooms, lists, census, scores, sampling or weights change? Is the exemption reachable only through the nine named sources under the existing authenticated-input boundary, with a0_ and boundary rows still checked?',
]
assert len(notes)<25;(L/'out/TREE_T_24M4V.md').write_text('\n'.join(notes)+'\n')
report=[
 'Route T is built and locally validated as tree '+tree[:8]+'. The patch changes only source-scoped extent checks, config plumbing and exemption counters.',
 'The identical real P row fails before with EXTENT_ROW_UNAUDITED and passes after. The three real-row controls pass; an 80-row native chain reports 14 exempted, 66 still checked and zero refusals.',
 str(len(latest))+' suite groups and 18 targeted tree tests pass, including kit, scan, naming, resolver, guard, arming, qd, planner and rcj. Census bytes and mode-b behavior remain unchanged; 80 native census comparisons pass.',
 'The complete published N keys split into 10,945 exemptible and 32,156 still-checked rows. Full N chain validation awaits the next CPU job; no full-DB result is claimed locally.',
 'The card reports 3,362 source-classified ScanNet++ v1 rows (28.8262% of N distance rows). TREE_T_24M4V.md separates 7,232 exact receipt matches from normalized derived-variant repair matches.',
 'The apply script passes on a copy of 24m4u, preserves its other helpers, verifies base seals and writes merged uploads. The original workspace is unchanged.',
 'UPLOADS_24M4V.json/.list replay exactly against reviewed q e7ac0727, n a7809da0 and qd 221d1782: 36 files, '+str(upload['total_bytes'])+' bytes. None exceeds 5 MB; the largest is '+largest['name']+' at '+str(largest['bytes'])+' bytes.',
 'The N configs keep c072905b unchanged. GO is false except kit_n_go; no upload or launch occurred. Optional GO uploads are separate.',
 'FAILURES.json retains the failed setup/test output and resolutions. VALIDATION.json records the final checks; DELIVERY_24M4V.json identifies the verified archive and checksum.',
]
assert len(report)<12;(L/'out/BUILD24M4V_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',tree=tree,kits=seals['kits'],suite_groups=len(latest),largest_upload=largest['bytes']),indent=2))
