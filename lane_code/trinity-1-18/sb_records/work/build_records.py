from common import *
from collections import deque,Counter
import tarfile
sys.path.insert(0,str(TREE))
from student_pilot import r2_policy as P
from stage2 import get
sourceidx=read(OUT/'SOURCE_INDEX.json');idx=sourceidx['byhash']
projections={
 'faa0cfc43bed88bf0f2dad6da57bc57c7dcfb8c3aba65cecc045a3de327cc85d':'pointing',
 'c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53':'routing',
 '5deb54bc4ef34c46371916feb2ab7fc83a707666cc36c5f2749b144647caa81d':'vqa',
 'b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320':'a2v3',
 '0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571':'a3v2',
 '3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001':'r16'}
projection_files={h:snapshot(next(A.glob('*__'+name+'__rows.scenes.jsonl.gz'))) for h,name in projections.items()}
roots=[get(p) for p in ['78341acb','c1a42588','fd60ac2f','0664bb17','93b21a3a','9a7f3310','524b14f9','30612832','1e7b491b','d6d6a53a']]
queue=deque(roots);seen=set();edges=[]
while queue:
 src=queue.popleft();h=sha(src)
 if h in seen:continue
 seen.add(h)
 try:d=read(src)
 except (ValueError,UnicodeError):continue
 for v in pins(d):
  edge=dict(v,referenced_by=boundpin(src))
  if v['sha256'] in idx:
   p=Path(idx[v['sha256']]);edge.update(status='RECOVERED',copy=boundpin(p))
   if p.suffix=='.json':queue.append(p)
  elif v['sha256'] in projections:
   edge.update(status='RECOVERED_SCENE_PROJECTION',copy=boundpin(projection_files[v['sha256']]),database_full_hash_attested_by=boundpin(snapshot(A/'SOURCES_13.tsv')))
  else:edge['status']='MISSING'
  edges.append(edge)
graph_inputs=[pin(__file__),pin(ROOT/'work/common.py'),pin(OUT/'SOURCE_INDEX.json'),*[pin(p) for p in roots],pin(snapshot(A/'SOURCES_13.tsv'))]
save(OUT/'RECEIPT_GRAPH.json',dict(schema='sb-records-receipt-graph-v1',inputs=graph_inputs,root_inputs=[boundpin(p) for p in roots],edges=edges,
 note='RECOVERED_SCENE_PROJECTION means the supplied projection is usable for membership, not that SQLite bytes were hashed locally. Missing construction assets and weight files are listed separately from the ancestry blockers in each gap.'))
pop=read(OUT/'POPULATIONS.json');pops={x['label']:x for x in pop['populations']}
assert all(x['counts']['unresolved']==0 for x in pops.values())
heads=read(get('fd60ac2f'));artifact=read(get('c1a42588'));cfg=read(snapshot(N/'config.json'));rowsources=read(snapshot(N/'row_sources.json'))
framepool_root=Path('/scratch/jjyeung/orch_n30/sb_framepool/out')
framepool_sources=[snapshot(framepool_root/n) for n in ['FRAMEPOOL.json','FRAMEPOOL_REPORT.md','CAPTURES.tsv','CAPTURE_MEMBERSHIPS.tsv']]
save(OUT/'FRAMEPOOL_CONTEXT.json',dict(schema='sb-records-framepool-context-v1',inputs=[pin(__file__),*[pin(p) for p in framepool_sources],pin(OUT/'POPULATIONS.json')],
 scope='The frame-pool audit finds source-row overlaps in archived samples. These are not checkpoint-consumption evidence. Its missing-database statements describe its supplied-source coverage; this records build additionally uses the recovered scene projections and pinned prepared indices.',
 reported_positive_rows=1193,reported_positive_captures=125,reported_scope='STI-Bench/ReSTI and MindCube; no venue-381879 sample hits',
 source_command='/usr/bin/python3 work/verify_hits.py in sb_framepool, as recorded in FRAMEPOOL_REPORT.md',
 agreed_limits='No evaluation-only explanation is established. Complete inherited and N production membership remain unproven.'))
basepins=[pin(__file__),pin(OUT/'RECEIPT_GRAPH.json'),pin(OUT/'POPULATIONS.json'),pin(OUT/'TOKEN_INVERSION.json'),pin(OUT/'FRAMEPOOL_CONTEXT.json'),pin(snapshot(N/'config.json')),pin(snapshot(N/'init_artifact.json')),pin(TREE/'student_pilot/r2_policy.py')]
missing_depth=dict(heads['provenance']['preparation'],status='MISSING',reason='The depth parent names this preparation receipt. It is absent; its training scene membership cannot be reconstructed.')
missing_m200=dict(path=None,sha256=artifact['config_sha256'],expected_location='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f2ad01ad/runs/49becb79/',filename_status='MISSING: the artifact supplies a config hash but no config filename',status='MISSING',reason='The parent step-200 artifact does not name its membership receipt or training stores. The configuration with this exact hash is needed to identify them.')
missing_depthcfg=dict(path=None,sha256=heads['provenance']['config_sha256'],expected_location='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/97a6a3eb/runs/b19c1200/',filename_status='MISSING: the heads manifest supplies only the configuration hash',status='MISSING',reason='Additional depth-parent configuration identity; the preparation receipt is the directly pinned membership blocker.')
# Preserve every observed overlap with its population; never promote the frame inventory to training membership.
disclosures=[dict(population=name,scope=pops[name]['scope'],overlaps=pops[name]['overlaps']) for name in ['raw_a2v3','m544_frame_universe','readout_training_scenes','m544_admitted_union']]
for slot in P.LINEAGE:
 blockers=[missing_depth,missing_depthcfg] if slot=='depth_init_vc' else [missing_m200,missing_depth,missing_depthcfg]
 extra=[e for e in edges if e['status']=='MISSING' and any(s in e['field'] for s in ['database','source','rows','receipt','division','preparation'])]
 gap=dict(schema='sb-records-gap-v1',component=slot,status='MISSING',record=None,inputs=basepins+[pin(get('c1a42588')),pin(get('fd60ac2f')),pin(get('0664bb17'))],
  reason='Complete inherited training membership is unavailable. Recovered prepared populations do not close the parent chain.',missing_inputs=blockers,additional_unresolved_receipt_references=extra,
  checked_banks=list(P.SCOPE),complete_parent_membership=False,overlaps=None,
  population_disclosures=disclosures if slot!='depth_init_vc' else [],
  depth_parent_overlap_status='UNKNOWN: no membership for the pinned preparation receipt; a zero count is not asserted.',
  membership_sources=[boundpin(get('0664bb17')),*[boundpin(p) for p in projection_files.values()]],
  recovered_indices=[boundpin(get(x)) for x in ['93c4fed5','613a9f9e','f9dc4a2d','3cb1ccf5','d8d33340']],
  recovered_readout=[boundpin(get(x)) for x in ['edaecb6c','d6d6a53a','0471677f']],
  required_disclosure='Any eventual step-544 lineage record must preserve venue 381879 in the recovered frame universe and any training overlap shown by complete ancestry.')
 save(OUT/'gaps'/f'{slot}.json',gap)
# Data evidence distinguishes the exact n1fix2 bindings from the w19 component_rows audit sources.
source_checks={}
for family,spec in rowsources.items():
 source_checks[family]=dict(binding=spec,population_audited='N_routing_'+family if 'N_routing_'+family in pops else None)
 if family in ('recovery','units','absolute_distance'):
  cr=read(snapshot(W/'w19/work/build19/inputs/component_rows.json'))
  source_checks[family]['audit_binding']=cr['proven']['routing_slices'][family]['source']
  source_checks[family]['exact_n1fix2_source_match']=spec['source']['sha256']==cr['proven']['routing_slices'][family]['source']['sha256']
missing_data=[dict(cfg['streams']['pointing'],status='RECOVERED_RECEIPT_ONLY',missing=read(get('93b21a3a'))['database'],reason='The N pointing stream binds the 25,020-row upstream store; the 20,239-row prepared pointing projection is a different store.'),
 dict(path=None,expected_binding='config.json:/streams/routing/required_parameter',parameter='admitted_routing_receipt',status='MISSING',reason='The required admitted routing receipt has no runtime binding.'),
 dict(path=None,expected_binding='config.json:/r1_training/host_receipt',status='MISSING',reason='The N frame-host receipt is null; the inherited frame pool is not a complete post-filter N host membership proof.'),
 dict(path=None,expected_binding='config.json:/r2_scene_rebuild',status='MISSING',reason='No complete post-filter family manifests and independent scene/frame coverage are bound for every family in mix.json.')]
selected=['v7_raw','v7_minus_nzu','v7_minus_component_rows_bound_lists','N_routing_recovery','N_routing_absolute_distance','N_routing_units']
save(OUT/'gaps/data_rows_r2.json',dict(schema='sb-records-gap-v1',component='data_rows_r2',status='MISSING',record=None,inputs=basepins+[pin(snapshot(N/'row_sources.json')),pin(snapshot(N/'mix.json')),pin(snapshot(W/'w19/work/build19/inputs/component_rows.json'))],reason='Clean scene audits exist for named populations; complete exclusions and host membership are not proven for every family N binds.',missing_inputs=missing_data,exclusions_complete=False,
 proven={name:dict(counts=pops[name]['counts'],scene_count=pops[name]['scene_count'],room_count=pops[name]['room_count'],overlaps=pops[name]['overlaps']) for name in selected},
 family_bindings=source_checks,active_families=[c for c in read(snapshot(N/'mix.json'))['cells'] if c['rows_per_step']>0],
 removal_scope='v7_minus_nzu applies n=02315a74, z=caba6a56, u=43853165 using full-row key semantics. The w19 component_rows list includes these plus six kit lists and s. n1fix2/config.json binds only the six kit lists and n; this audit does not claim z/u are bound there.'))
# The independent review identifies a surviving runtime identity binding.
archive=Path('/scratch/jjyeung/n30_mirror/cont_ops/c16_mirror_2245Z.tar')
member='r1route/out2/A/surviving_records/inputs_tower.json'
with tarfile.open(archive,'r:') as t: raw=t.extractfile(member).read()
h=hashlib.sha256(raw).hexdigest();assert h.startswith('025b4688')
tower_binding=KIT/'inputs'/(h+'_inputs_tower.json');tower_binding.write_bytes(raw)
save(OUT/'REVIEW_PIN_RECOVERY.json',dict(schema='sb-records-review-pins-v1',inputs=[pin(__file__),pin(snapshot('/scratch/jjyeung/orch_n30/sb_evrev/REVIEW_VERDICT.md')),pin(tower_binding),pin(OUT/'SOURCE_INDEX.json')],tower=dict(archive=str(archive),member=member,member_sha256=h,copy=boundpin(tower_binding)),genuine_kit_pins=[boundpin(get(x)) for x in ['17aa3e9e','7cc01f36','5f9e4d49','845b1789','cc724d5e']],hash_scope='Archive member digests hash uncompressed member bytes, not entire enclosing tar files.'))
for slot in P.EXTERNAL:
 draft=Path('/scratch/jjyeung/orch_n30/sb_inventory/drafts')/(slot+'.GAP.json')
 inv=Path('/scratch/jjyeung/orch_n30/sb_inventory/out/inventories')/(slot+'.json')
 reason='Release, weights, configuration and code identity are present. The actual run-bound frozen parameter/optimizer inventory is MISSING.' if slot=='geometry_tower' else 'Release and checkpoint identities are present. The actual frozen SAM3 inventory and N mask-cache/runtime binding to that checkpoint are MISSING.'
 files=[snapshot(draft),snapshot(inv)]
 if slot=='geometry_tower':files.extend([tower_binding,TREE/'student_pilot/tower_read.py'])
 save(OUT/'gaps'/f'{slot}.json',dict(schema='sb-records-gap-v1',component=slot,status='MISSING',record=None,inputs=basepins+[pin(p) for p in files],reason=reason,
  missing_inputs=[dict(path=None,filename_status='MISSING: no inventory filename is specified in the recovered evidence',expected_location='N production run or cache-generation evidence bound to init artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef',requirement=reason)],release_identity_status='PRESENT',available_inventory=boundpin(files[1]),
  limitation='The reconstructed CPU/meta inventory demonstrates code behavior; it does not authenticate an actual production run.'))
save(OUT/'gaps/heads_gf1_connector.json',dict(schema='sb-records-gap-v1',component='heads_gf1_connector',status='MISSING',record=None,inputs=basepins+[pin(snapshot('/scratch/jjyeung/orch_n30/sb_inventory/out/inventories/heads_gf1_connector.json'))],
 reason='N configures geometry_connector=none. Leave this slot for the NOT_PRESENT status being added to the policy; the tested policy has no such acceptance branch.',missing_inputs=[dict(path=str(TREE/'student_pilot/r2_policy.py'),sha256=sha(TREE/'student_pilot/r2_policy.py'),requirement='NOT_PRESENT policy support and evidence binding for an absent connector',status='MISSING')],expected_future_status='NOT_PRESENT',exclusions_complete=None))
# No record is manufactured to turn a parser pass into evidence.
registry=read(snapshot(N/'registry.json'));record_bindings={}
for f in (OUT/'records').glob('*.json'):
 data=read(f);target=KIT/'records'/f.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(f,target)
 registry[data['component']]['record']=boundpin(target);record_bindings[data['component']]=boundpin(target)
assert not record_bindings
save(KIT/'registry.json',registry)
save(OUT/'REGISTRY_PROVENANCE.json',dict(schema='sb-records-registry-provenance-v1',inputs=[pin(snapshot(N/'registry.json')),pin(__file__),*[pin(p) for p in (OUT/'gaps').glob('*.json')]],registry=pin(KIT/'registry.json'),records_bound=record_bindings,reason='Every requested slot has an unclosed evidence requirement. All original null bindings are retained.'))
(OUT/'records/README.md').write_text('No component record is issued. Every requested slot has a missing membership link, incomplete all-family exclusion evidence, or a missing run/runtime binding. See ../gaps/ and ../RECORDS_REPORT.md.\n')
status('Stage 3 complete. Nine explicit gap files name recovered evidence and missing ancestry, family/runtime bindings or NOT_PRESENT policy support. No slot meets its evidence bar, so the kit registry retains null record bindings. All observed benchmark overlaps remain in the population audit and lineage disclosures.')
print('gaps',len(list((OUT/'gaps').glob('*.json'))),'records',len(record_bindings),'receipt edges',len(edges),'missing edges',sum(e['status']=='MISSING' for e in edges))
