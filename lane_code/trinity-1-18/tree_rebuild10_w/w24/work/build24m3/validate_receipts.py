from common import *
iv=J.load(D/"INVARIANTS.json")
checks={}
for name in ('NATIVE_HOST_TESTS','CENSUS_VERIFIED_TESTS','CLASSIFIER_TESTS','SCENE_TESTS','PLANNER_SCENE_TESTS','REMOVAL_RECEIPT_TESTS','DELTA_SEALED_TESTS','WRAPPER_TESTS','HOST_REVIEW_TESTS','HIDDEN_PATH_TESTS','ROUTING_TESTS','P_REFRESH_TESTS','SOURCE_PIN_TESTS','PUBLICATION_TESTS','DISCOVERY_CENSUS_SHELL_TESTS','FINAL_EDGE_TESTS','LIVE_TESTS','REVIEW_TESTS','SECURITY_TESTS','FRAME_TESTS','STATIC_TESTS','RESOLVER_TESTS'):
 p=D/(name+'.json');v=J.load(p)
 assert v.get('status')=='PASS' or v.get('successful') is True or v.get('passed') is True,(name,v.get('status'))
 checks[name]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS')
for name in ('KIT_TESTS','NAMING_TESTS'):
 p=D/(name+'.json');v=J.load(p);assert v['successful']
 checks[name]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS',tests=v.get('tests'))
assert all(r['returncode']==0 for r in J.load(D/'FINAL_SUITES.json'))
for name in ('q','n'):
 for test in ('GUARD_TESTS','LEGACY_GUARD_TESTS'):
  p=D/('guard_'+name)/(test+'.json');v=J.load(p);assert v['successful'] and not v['missing']
  checks['guard_'+name+'_'+test]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS',tests=v['tests'])
# Guard, resolver and live helper bytes are unchanged in all four delivery kits.
for name in ('q','n','n_go','qd'):
 before=J.load(D/'BASELINE.json')[name]
 for rel in ('b/g.py','b/z.py','b/resolve.py','b/pc.sh','b/ep.py','b/ep.sh','b/rb.py','b/rg.py'):
  if rel in before:assert J.sha(kit(name)/rel)==before[rel]['sha256'],(name,rel)
for row in J.load(D/'SUITES.json'):
 if row['name'] not in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','kit_tests','naming_tests'):assert row['returncode']==0
assert J.load(D/'CENSUS_VERIFIED_TESTS.json')['kits']==iv['kits']
assert J.load(D/'DELTA_SEALED_TESTS.json')['source_kit_seals']==iv['kits']
for r in J.load(D/'HIDDEN_PATH_TESTS.json')['records']:
 if r['kit']!='old':assert r['final_kit_seal']==iv['kits'][r['kit']]
up=J.load(L/'out/UPLOADS_24M3.json')
assert set(p.name for p in Path(up['stream_root']).iterdir())=={'q','n','qd','u'}
for v in up['files']:
 assert J.sha(v['local_path'])==v['sha256'] and Path(v['local_path']).stat().st_size==v['bytes']
 assert Path(v['local_path']).stat().st_mode&511==int(v['mode'],8)
value=dict(status='PASS',kits=iv['kits'],checks=checks,build_scope='Pointing/list/scene/census/wrapper kits built; future pose cleanup blocked without a native producer.',production_admission='NOT_RUN',
 boundaries=['Synthetic source/admitted SQLite fixtures and actual pinned authority/list bytes','Native host tests use explicit fixture source/authority boundaries','Native scene rebuild/verify replay and complete planner fixture use synthetic frame-host identity and retained native24 inputs','The planner fixture uses one pose row per source and one pointing/routing row, retains complete synthetic VQA/twin stores and omits unused production readout assets','Discovery shell fixtures supply prepared synthetic stores and host receipts; actual post-condition, h.py, rv.py and publications execute','Real hidden-path metadata receipts stay byte-identical; inventoried unavailable payload bodies have explicit fixture boundaries; missing catalog is never fabricated','Header-search SQLite fixtures and shell sleeps are controlled; production scheduler/network/GPU work never ran','Pose delta fixture proves binding and post-condition on explicitly selected rows, not native pose cleanup'],
 native_tree_unchanged=True,scene_verifier_unchanged=True,pose_delta_blocker='out/REMOVAL_RECEIPTS_BLOCKER.md')
J.write(D/'VALIDATION.json',value)
print('Final validation PASS',len(checks),'evidence records; pose cleanup blocker retained')
