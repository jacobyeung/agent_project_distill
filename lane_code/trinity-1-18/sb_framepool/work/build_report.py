import json,hashlib,re,csv,collections,ast
from pathlib import Path
from scan_rows import sha,C,target
ROOT=Path.cwd();OUT=ROOT/'out';OUT.mkdir(exist_ok=True)
REG=json.load(open('work/metadata_fixed.json'))['files'];META=json.load(open('work/metadata_row_results.json'))['streams'];BYMETA={s['sha256']:s for s in META}
DIRECT=json.load(open('work/row_results.json'))['streams']+json.load(open('work/archive_store_results.json'))['streams']
LOCAL=json.load(open('work/local_store_inventory.json'))['files'];EVAL=json.load(open('work/evaluation_results.json'));VER=json.load(open('work/verified_hits.json'))
inputs={};used={}
def inp(p):
 inputs[str(p)]={'sha256':sha(p)}
 return inputs[str(p)]
def take(h):
 e=REG[h];used[h]=dict(sha256=h,locations=e['locations'],bytes=e['bytes']);return json.load(open(e['blob']))
def prefix(p):return next(h for h in REG if h.startswith(p))
for p in ['work/captures.json','work/row_results.json','work/archive_store_results.json','work/metadata_fixed.json','work/metadata_summary.json','work/metadata_row_results.json','work/local_store_inventory.json','work/evaluation_results.json','work/verified_hits.json','work/files.txt','work/all_archive_catalog.json','work/reviewer_note_files.txt','work/A2_DENSE_READY.md']:
 inp(p)
inputs.update(C['inputs'])
POL='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1/student_pilot/r2_policy.py';inp(POL)
ALIAS='/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json';inp(ALIAS)
AUDIT='/scratch/jjyeung/orch_n30/sb_alias2/out/ROOM_AUDIT_TIERED.json';inp(AUDIT);audit=json.load(open(AUDIT))
source_hashes={s['source']['sha256'] for s in DIRECT}|{e.get('sha256') for e in LOCAL if e.get('format')=='sqlite'}
def availability(pin):
 h=pin['sha256'];o=dict(pin)
 if h in REG:
  used[h]=dict(sha256=h,locations=REG[h]['locations'],bytes=REG[h]['bytes']);o.update(status='PRESENT',locations=REG[h]['locations'])
  if REG[h]['kind']=='json':
   try:
    d=json.load(open(REG[h]['blob']))
    if isinstance(d,list):o.update(entries=len(d),representation='integer indices' if all(isinstance(x,int) for x in d[:10]) else 'source/index pairs' if all(isinstance(x,list) for x in d[:10]) else 'records')
   except ValueError:pass
 elif h in source_hashes:o.update(status='PRESENT',locations=[s['source']['path'] for s in DIRECT if s['source']['sha256']==h])
 else:o.update(status='MISSING',expected_location=pin['path'])
 return o
def pins(d,key=''):
 if isinstance(d,dict):
  if 'sha256' in d and 'path' in d:yield key,d
  else:
   for k,v in d.items():yield from pins(v,key+'/'+k)
 elif isinstance(d,list):
  for i,v in enumerate(d):yield from pins(v,key+'/'+str(i))
streams=[]
for s in DIRECT:
 x=dict(s);x['id']='file:'+s['source']['sha256'][:16];x['source_sha256']=s['source']['sha256'];x['scope']='supplied file only; run consumption not established'
 x['classification']='fixture' if s['rows']==3 and '/fixtures/' in s['source']['path'] else 'row_store_or_slice'
 x['missing']=[];streams.append(x)
# Full-family membership metadata and the corresponding actual metadata samples.
family_hash=prefix('26196837');families=take(family_hash)['families'];family_results=[]
token_lookup={}
for c in C['captures']:
 for name in [c['token'],c['scene_list_key'],c['canonical_scene'],c['canonical_scene'].replace('scannetpp/','scannetppv2/')]:token_lookup[name]=c['token']
for name,f in sorted(families.items()):
 h=f['slice_sha256'];s=BYMETA.get(h);member_tokens=sorted({token_lookup[t] for t in f['scenes'] if t in token_lookup})
 rec=dict(family=name,declared_full_rows=f['rows'],declared_full_scenes=f['scene_count'],target_capture_membership=member_tokens,source_sha256=family_hash,slice_sha256=h,full_per_capture_row_counts='MISSING',full_row_source='MISSING full-family row file; supplied COUNTS.json gives scenes but no per-scene counts')
 family_results.append(rec)
 if s:
  used[h]=dict(sha256=h,locations=REG[h]['locations'],bytes=REG[h]['bytes'])
  x=dict(s);x.update(id='slice:'+name,source_sha256=h,kind='archived_training_metadata_sample',classification='training_source_sample',family=name,declared_full_rows=f['rows'],full_family_target_captures=member_tokens,coverage='complete' if s['rows']==f['rows'] and not s['unresolved_rows'] else 'partial',file_coverage=s['coverage'],scope='training-source metadata sample; optimizer consumption MISSING',missing=[] if s['rows']==f['rows'] else [rec['full_row_source']],command='/usr/bin/python3 work/scan_metadata_rows.py; /usr/bin/python3 work/verify_hits.py')
  streams.append(x)
# Prepared streams: preserve exact database pins and do not infer counts from index lists.
prep_names={'0664bb17418d':'step544_469ddece','fe76f3971a62':'head_359fcc3c','888da8e20ed2':'R1_P_6ed2c7aa','49caeb70cac7':'R1_673bc60f'}
for pre,label in prep_names.items():
 h=prefix(pre);d=take(h)
 for name,s in d['streams'].items():
  pp=[];seen=set()
  for key,p in pins(s):
   if (p['path'],p['sha256']) in seen:continue
   seen.add((p['path'],p['sha256']));a=availability(p);a['field']=key;pp.append(a)
  streams.append(dict(id=label+':'+name,kind='prepared_production_stream',classification='production_stream',source_sha256=h,receipt_locations=REG[h]['locations'],rows_declared=s['count'],rows=0,resolved_rows=0,hits=None,counts={},coverage='partial',missing=[x for x in pp if x['status']=='MISSING'],pins=pp,scope='production row database unavailable; receipt totals are not per-capture row evidence',reported_benchmark_rows_dropped=s.get('benchmark_rows_dropped'),reported_overlap_rows=s.get('reported_overlap_rows'),command='/usr/bin/python3 work/build_report.py'))
# Configured upstream stream receipts, including P staged configuration copies.
config_results=[]
for pre in ['c805975943a4','215282897449','9fd188164999','31abe0871f35','9a1d0646aa2c','cb6c1a944280','8b7558ad9d4e']:
 h=prefix(pre);d=take(h);config_results.append(dict(sha256=h,locations=REG[h]['locations'],streams={n:availability(p) for n,p in d['streams'].items()}))
# Pool masks and row removals cannot be promoted to training rows.
pool_h=prefix('d1e6715');pool=take(pool_h);pools=[]
for name,s in sorted(pool['sources'].items()):
 source=availability(s['source']);sel=availability(s['selection']) if 'selection' in s else {'status':'MISSING','reason':s.get('reason')};n=sel.get('entries')
 pools.append(dict(name=name,source=source,selection=sel,declared_rows=s['declared_rows'],retained_rows_reported=s.get('retained'),selection_entries=n,admission_status=s['status'],reported_scene_coverage=s.get('scene_coverage'),per_capture_counts='MISSING',coverage='partial'))
filters=[]
for h,e in REG.items():
 locs=[p for p in e['locations'] if '/w12/fixtures/work/kit07ca49df_meta/m/k/' in p and (Path(p).name.startswith('remove_') or Path(p).name.startswith('pool_exclusion_'))]
 if not locs:continue
 used[h]=dict(sha256=h,locations=locs,bytes=e['bytes']);lines=Path(e['blob']).read_text().splitlines();s=BYMETA.get(h)
 filters.append(dict(sha256=h,locations=locs,records=len(lines),kind='removal_or_exclusion_metadata',target_counts=s['counts'] if s else {},resolved_rows=s['resolved_rows'] if s else 0,coverage='partial' if lines and (not s or s['unresolved_rows']) else 'complete',meaning='removal instructions, not admitted training rows; qid-only entries need absent source tables'))
# Include reachable row payloads in requested row lanes, even when compressed or archived.
existing={s.get('source_sha256') for s in streams}
for s in META:
 if s['sha256'] in existing:continue
 locs=[p for p in s['locations'] if re.search(r'/(rows_r1|rows_r2|rows_a2)/',p) and re.search(r'/(rows(?:_full|_slice)?|slice_[^/]+)\.jsonl',p)]
 if not locs:continue
 h=s['sha256'];used[h]=dict(sha256=h,locations=s['locations'],bytes=REG[h]['bytes']);x=dict(s);x.update(id='rows:'+h[:16],source_sha256=h,kind='row_payload',classification='row_store_or_slice',missing=[],scope='supplied file only; run consumption not established',command='/usr/bin/python3 work/scan_metadata_rows.py');streams.append(x)
# Evaluation joins are per capture and per pinned image, never physical-room substitution.
for e in EVAL['sets']:used[e['sha256']]=dict(sha256=e['sha256'],locations=e['locations'],bytes=REG[e['sha256']]['bytes'])
captures=[];memberships=[]
for c0 in C['captures']:
 c={k:v for k,v in c0.items() if k not in ['plan_entry','per_stream_counts']};tok=c['token'];c['native_key']=c['scene_list_key'];c['lists']={'BENCH_v2_scene_list':c['bench_v2_scene_list'],'BENCH_v2_hashed_token_list':c['bench_v2_token_list'],'required_policy_scope_banks':sorted(set(c['benchmarks'])&{'VSI-Bench','VSTI','ReVSI'})};c['per_stream_counts']={}
 for s in streams:
  observed=s['counts'].get(tok,0) if s.get('hits') is not None else None
  c['per_stream_counts'][s['id']]={'observed_rows':observed if observed is not None else 'MISSING','full_count':observed if s['coverage']=='complete' else 'MISSING','coverage':s['coverage'],'full_family_scene_list_contains_capture':tok in s.get('full_family_target_captures',[]) if s['kind']=='archived_training_metadata_sample' else None}
 c['evaluation_sets']=[dict(sha256=e['sha256'],scene_items=e['counts'].get(tok,0),frame_items=e['frame_reference_counts'].get(tok,0),coverage=e['coverage']) for e in EVAL['sets'] if e['counts'].get(tok) or e['frame_reference_counts'].get(tok)]
 c['evaluation_attribution']='MISSING: no located item set references this exact capture or a target frame hash; unresolved aliases remain'
 c['full_family_scene_memberships']=[f['family'] for f in family_results if tok in f['target_capture_membership']]
 captures.append(c)
 groups=[]
 if 'STI-Bench/ReSTI' in c['benchmarks']:groups.append('STI-Bench/ReSTI')
 if 'MindCube' in c['benchmarks']:groups.append('MindCube')
 if c['room']=='arkitscenes/venue381879':groups.append('VSI-Bench/ReVSI venue381879')
 for g in groups:memberships.append(dict(token=tok,canonical_scene=c['canonical_scene'],benchmark_group=g))
assert len(captures)==146 and len(memberships)==148
positive_slices=[s for s in streams if s['kind']=='archived_training_metadata_sample' and s['hits']]
positive=collections.Counter()
for s in positive_slices:positive.update(s['counts'])
assert sum(positive.values())==1193 and len(positive)==125
for c in captures:
 assert c['bench_v2_scene_list'] and c['bench_v2_token_list']
result=dict(schema='framepool-audit-v1',command='/usr/bin/python3 work/build_report.py',inputs=inputs,input_members=used,verdict='OVERLAP_FOUND_IN_TRAINING_SOURCE_SAMPLES; PRODUCTION_CONSUMPTION_MISSING',capture_counts={'distinct':146,'reviewer_group_memberships':148,'STI-Bench/ReSTI':126,'MindCube':20,'venue381879':2},frame_universe={k:C[k] for k in ['frame_count','frame_scenes','frame_fields','plan_aliases_verified']},bench_v2_counts=C['bench_v2_counts'],policy={'file':POL,'sha256':inputs[POL]['sha256'],'required_checked_banks':['VSI-Bench','VSTI','ReVSI'],'STI-Bench/ReSTI_and_MindCube_in_scope':False,'lineage_exception':'Only in-scope venue 381879 overlap is accepted by record(); checked_banks must contain at least SCOPE, not equal it. This exception does not establish absence of training overlap.'},captures=captures,reviewer_memberships_148=memberships,streams=streams,full_family_metadata=family_results,configured_streams=config_results,pool_selections=pools,removal_metadata=filters,evaluation=EVAL,positive_summary={'observed_records':1193,'distinct_captures':125,'sealed_vqa':919,'pool_abs_distance':115,'pool_room':67,'pool_route_planning':92,'meaning':'counts in archived metadata row samples; not optimizer-step counts; overlap among related source versions is not deduplicated'},coverage={'overall':'partial','v7':'complete for 204413 reachable rows; zero target matches','source_samples':'full-family scene membership metadata plus at-most-2000-row samples; partial per-capture counts except complete small families','production_streams':'MISSING pinned row stores prevent step544/R1 consumption verdict','eval':'No exact target capture or frame references found in 150 candidate item files; unresolved aliases and absent official STI/MindCube item banks leave attribution partial','reviewer_script':'MISSING frame-universe counting script and capture list under /scratch/jjyeung/orch_n30/sb_evrev/notes; only recompute_recovery.py was found, which audits recovery rows, not this frame universe','sb_alias_per_row_map':'MISSING standalone per-row scene map under /scratch/jjyeung/orch_n30/sb_alias2/out and its sb_alias2.tar inventory; reused TIERED_ALIAS_MAP.json with each v7 row and cross-checked ROOM_AUDIT_TIERED.json','inventory':'work/files.txt and work/all_archive_catalog.json enumerate the named local mirror/W roots; fixture SQLite files and metadata stubs do not satisfy production pins'},sb_alias_audit={'rows':audit['rows'],'complete':audit['complete'],'resolved_rows':audit['resolved_rows'],'hits':audit['hits']},reproduction={'capture_counts':'/usr/bin/python3 work/captures.py','local_rows':'/usr/bin/python3 work/scan_rows.py','archive_rows':'/usr/bin/python3 work/scan_archive_stores.py','metadata':'/usr/bin/python3 work/repair_metadata.py; /usr/bin/python3 work/summarize_metadata.py; /usr/bin/python3 work/scan_metadata_rows.py','positive_verification':'/usr/bin/python3 work/verify_hits.py','evaluation':'/usr/bin/python3 work/eval_join.py','report':'/usr/bin/python3 work/build_report.py'})
for p in sorted(Path('work').glob('*.py')):result['inputs'][str(p)]={'sha256':sha(p)}
(OUT/'FRAMEPOOL.json').write_text(json.dumps(result,indent=2)+'\n')
with open(OUT/'CAPTURES.tsv','w') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['token','native_key','dataset','canonical_scene','room','benchmarks','why','listed_by','sibling_of','BENCH_v2','frames','observed_sample_rows'])
 for c in captures:w.writerow([c['token'],c['native_key'],c['native_dataset'],c['canonical_scene'],c['room'],';'.join(c['benchmarks']),c['why'],';'.join(c['listed_by']),';'.join(c['sibling_of']),True,c['frame_count'],positive[c['token']]])
with open(OUT/'CAPTURE_MEMBERSHIPS.tsv','w') as f:
 w=csv.DictWriter(f,fieldnames=['token','canonical_scene','benchmark_group'],delimiter='\t');w.writeheader();w.writerows(memberships)
lines=[
'Training-source rows on the target captures: sealed-VQA slices 919; pool distance 115, room 67, route planning 92; v7 0. Production step-544/R1 coverage is partial.',
'',
'The positive counts are 1,193 records in archived metadata samples across 125 captures. They establish source-row overlap; optimizer consumption by step-544 or R1 is MISSING.',
'The archive labels many sealed rows “benchmark_trained_diagnostic” and disables benchmark score nomination. These flags do not prove which checkpoint consumed them.',
'An evaluation-only explanation is not supported. A clean benchmark claim requires the missing production membership evidence.',
'',
'`CAPTURES.tsv` and `FRAMEPOOL.json` list every token, native key, dataset, canonical capture, physical room, benchmark, direct/sibling reason, list membership, and per-stream count.',
'`CAPTURE_MEMBERSHIPS.tsv` reproduces 148 group memberships: 126 STI-Bench/ReSTI + 20 MindCube + 2 venue-381879 captures. There are 146 distinct captures.',
'The overlap is ScanNet scene0122_00 (d1/vba9dd8cbb0da) and scene0122_01 (d1/vda951d1116f5), each in both STI-Bench/ReSTI and MindCube.',
'The venue captures are native d3/41159526 → frame token d3/vc6a4b809b958 and d3/41159521 → d3/vf3e2ed14c783. Both are siblings of benchmark capture 41159525.',
'BENCH v2 contains all 146 targets. Its 511 are physical groups, not captures: it contains 1,212 scene entries. No target requires a missing BENCH entry.',
'Tokens reproduce `v + sha256("rung1 scene " + native_dataset + "/" + scene)[:12]`; ScanNet++ uses `scannetppv2` in that string.',
'`r2_policy.py` requires checked banks to include VSI-Bench, VSTI, and ReVSI. STI-Bench/ReSTI and MindCube are outside that scope; BENCH v2 is broader.',
'The policy permits lineage overlap at venue 381879; this is an exception, not a finding that training is clean.',
'',
'| Reachable stream or sample | Target rows / supplied rows | Coverage |',
'|---|---:|---|',
'| v7 VQA | 0 / 204,413 | Complete supplied store |',
'| rows_a2 VQA v2/v3/v4/v5/v6 | 0 / 152,123; 152,123; 163,175; 194,597; 195,471 | Complete supplied stores |',
'| Other local rows_r1/rows_r2 stores and A0 slices | 0 | Per-file counts and copies in JSON; supplied-file coverage only |',
'| Five b12 archived SQLite stores | 0 / 10,593; 3,132; 31,522; 31,476; 31,422 | Complete supplied stores |',
]
for s in positive_slices:lines.append('| '+s['family']+' | '+str(s['hits'])+' / '+str(s['rows'])+' | '+('Complete family' if s['coverage']=='complete' else 'Partial; full family '+str(s['declared_full_rows'])+' rows')+' |')
lines += [
'',
'The positive samples are in `/scratch/jjyeung/n30_mirror/old_lanes_3_30/old_lanes_3_30_b.tar::tree_rebuild/work/rows_slices/slices_v3/`; `COUNTS.json` binds their hashes and full-family scene lists.',
'Full-family per-capture row counts are MISSING where the supplied sample is smaller than its family. A sample zero is not a full-family zero. JSON records both scene-list membership and observed counts.',
'No supplied sample hits either venue-381879 capture; the 15 ARKit sample hits belong to four MindCube captures. Missing production pose/routing rows prevent a venue-level clean verdict.',
'',
'| Production receipt | Pointing / pose / routing / VQA rows declared | Row-level coverage |',
'|---|---:|---|',
'| step-544 kit, run 469ddece | 20,239 / 194,987 / 57,136 / 114,904 | Partial; production databases MISSING |',
'| head preparation, run 359fcc3c | 20,239 / 194,987 / 47,732 / 152,123 | Partial; production databases MISSING |',
'| R1/P staged run 6ed2c7aa | 20,239 / 194,987 / 47,898 / 185,933 | Partial; production databases MISSING |',
'| R1 staged run 673bc60f | 20,239 / 194,987 / 47,898 / 203,812 | Partial; production databases MISSING |',
'',
'JSON gives each missing database’s exact original path and SHA256 from its receipt, plus every surviving index/order location. Pose uses source stores `f02f16ad/s/a2v3/rows.sqlite` and `f02f16ad/s/a3v2/rows.sqlite`; both are MISSING.',
'Surviving scene indices are integers; pose orders are source/index pairs. They do not identify captures without the pinned source databases. Equal row totals in other stores do not establish identity.',
'P’s H1 routing/VQA index pins are also MISSING. W’s real SQLite files lie in test/proof trees; its JSON stubs named `.sqlite` contain no production rows.',
'All 13 pool source payloads are MISSING; 12 selected-index files survive (SCENE_room_sppK is deferred). `pool_exclusion_*.tsv` and `remove_*.jsonl` are exclusion instructions, not training membership proofs.',
'The reachable archive/W metadata, h1_headsft, b08_headrows, r1_ops6, and cont_ops configurations are indexed by hash in the JSON evidence; receipt claims are kept separate from observed counts.',
'',
'The frame universe contains 290,880 frames in 4,697 captures. Frame-map fields are only d, s, i, path, sha256, w, h; the plan gives source videos/URLs, needed indices, and totals. Neither identifies train/evaluation use.',
'The scan found no exact target-capture or frame-hash matches in 150 candidate item files. Official VSI/ReVSI cohorts and R0/DEV item sets were checked; unresolved anonymous scene labels remain partial.',
'Official STI-Bench/ReSTI and MindCube item banks with exact frame references are MISSING from the named reachable inputs. Benchmark room membership alone cannot assign these frames to an evaluation set.',
'B06 dense plans reference target clips but provide no per-stream row join; they are training-frame demand metadata, not evidence of evaluation-only staging.',
'',
'Commands: `/usr/bin/python3 work/captures.py` produces capture/frame/list counts; `work/scan_rows.py` and `work/scan_archive_stores.py` produce store counts.',
'`/usr/bin/python3 work/scan_metadata_rows.py` produces slice counts; `work/verify_hits.py` rechecks all 1,193 positives directly against archive bytes and exact target tokens.',
'`/usr/bin/python3 work/eval_join.py` produces item/frame joins; `work/build_report.py` produces family, pool, receipt, and report counts. Run each script with `/usr/bin/python3` from this workspace.',
'Input SHA256 values, source-member locations, missing pins, coverage, and commands are recorded in `FRAMEPOOL.json`. The metadata reader detects gzip archives by content before using their members.',
'The reviewer’s frame-universe script/capture list is MISSING under the named `sb_evrev/notes`; the surviving `recompute_recovery.py` audits recovery rows. The capture intersection here is independently reproduced.',
'The standalone sb_alias2 per-row map is MISSING in its out directory/archive; v7 was scanned using each row plus TIERED_ALIAS_MAP.json and checked against ROOM_AUDIT_TIERED.json.',
'`sb_framepool.tar.sha256` records the package hash. The package contains the report, JSON, capture tables, scripts, positive-row evidence, and summarized scans.',
]
assert len(lines)<=80,len(lines)
(OUT/'FRAMEPOOL_REPORT.md').write_text('\n'.join(lines)+'\n')
Path('STATUS.md').write_text('The report and per-capture JSON are assembled. The audit reproduces 146 distinct captures / 148 memberships, verifies 1,193 matching records in archived source metadata samples, and finds zero target rows in the reachable v7 store. Production step-544/R1 databases and some indices remain MISSING, so checkpoint consumption and evaluation-only staging are unproven. Final validation and packaging remain.\n')
print('report lines',len(lines),'streams',len(streams),'capture memberships',len(memberships),'JSON bytes',(OUT/'FRAMEPOOL.json').stat().st_size)
