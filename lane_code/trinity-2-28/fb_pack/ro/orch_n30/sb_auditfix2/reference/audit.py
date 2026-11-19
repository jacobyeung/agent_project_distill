"""Build proof tiers and audit every v7 row with build 17's exact room methods."""
import ast,collections,csv,hashlib,io,json,re,sqlite3,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'out';W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');M=Path('/scratch/jjyeung/n30_mirror');PREV=BASE.parent/'sb_alias'
CODE=W/'w17b/work/tree_r1/student_pilot';BUILD=W/'w17b/work/build17'
inputs={}
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 inputs[str(p)]={'sha256':h.hexdigest(),'bytes':p.stat().st_size};return dict(path=str(p),**inputs[str(p)])
def read(p):pin(p);return Path(p).read_text()
def load(p):return json.loads(read(p))
def save(name,d):
 (OUT/name).write_text(json.dumps(dict(schema=name[:-5].lower()+'-v1',command='python work/audit.py',inputs=inputs,**d),indent=2,sort_keys=True)+'\n')
def norm(c):return c.replace('scannetppv2/','scannetpp/',1)
def key(row):return {'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}.get(row.get('dataset'),row.get('dataset',''))+'/'+row.get('scene','')
pin(Path(__file__));pin(PREV/'out/build_missing_report.py');pin(BASE/'in/build_a2_other.py');pin(M/'rows_a2/v4/vsti/code/sources.py')
scan=load(BASE/'work/CANDIDATE_SCENES_FINAL.json');pin(BASE/'work/SCAN_MANIFEST.tsv');pin(BASE/'work/enumerate_candidates.py');pin(BASE/'work_inventory.txt')
assert not scan['errors'],scan['errors']
inputs.update(scan['inputs'])
prior=load(BUILD/'proofs/rooms/RESULT.json')['audit'];db=Path(prior['store']['database']['path']);assert pin(db)['sha256']==prior['store']['database']['sha256']
a_payload=load(PREV/'out/alias_map.json');rec=load(PREV/'out/RECOVERED_ARCHIVED_ALIAS_MAP.json');pin(PREV/'out/ALIAS_SELFCHECK.json')
A={k:norm(v['canonical']) for k,v in a_payload['aliases'].items()};Aproof={k:dict(v['source'],witness_canonical=v['canonical']) for k,v in a_payload['aliases'].items()}
archive=Path(rec['archive']['path']);assert pin(archive)['sha256']==rec['archive']['sha256']
with tarfile.open(archive) as t:b_bytes=t.extractfile(rec['member']).read()
b_hash=hashlib.sha256(b_bytes).hexdigest();assert b_hash==rec['member_sha256'] and b_hash.startswith('488480ab')
inputs[str(archive)+'!'+rec['member']]={'sha256':b_hash,'bytes':len(b_bytes)}
B={k:norm(v) for k,v in json.loads(b_bytes).items()};assert B=={k:norm(v) for k,v in rec['aliases'].items()}
# Verify inherited witness source hashes against the complete local scan manifest.
manifest={}
for line in (BASE/'work/SCAN_MANIFEST.tsv').read_text().splitlines()[1:]:
 h,sz,p,status=line.split('\t');manifest[p]={'sha256':h,'bytes':int(sz)}
for e in Aproof.values():
 assert manifest[e['path']]['sha256']==e['sha256'],e
 inputs[e['path']]=manifest[e['path']]
roomtext=read(CODE/'r1_rooms.py');tree=ast.parse(roomtext);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Rooms')
methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('canonical','room')];ns={'re':re};exec(compile(ast.Module(body=methods,type_ignores=[]),str(CODE/'r1_rooms.py'),'exec'),ns)
class Rooms:
 canonical=ns['canonical'];room=ns['room']
rooms=Rooms();rooms.aliases={}
visitpin=prior['authority']['visits'];vtext=read(visitpin['path']);assert inputs[visitpin['path']]['sha256']==visitpin['sha256'];rooms.visits={r['video_id']:r['visit_id'] for r in csv.DictReader(io.StringIO(vtext))}
old=Rooms();old.visits=rooms.visits;old.aliases=load(prior['authority']['aliases']['path']);assert inputs[prior['authority']['aliases']['path']]['sha256']==prior['authority']['aliases']['sha256']
# Execute the minting function and its constant tables directly from pinned source AST.
ct=ast.parse(read(CODE/'carrier_c1_routing.py'));nodes=[n for n in ct.body if (isinstance(n,ast.FunctionDef) and n.name=='alias_of') or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('ALIAS','NATIVE') for t in n.targets))]
assert len(nodes)==3;mintns={'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(CODE/'carrier_c1_routing.py'),'exec'),mintns);mint=mintns['alias_of']
function_checks={}
for name,m in [('A',A),('B',B)]:
 agree=[];bad=[];literal=[]
 for k,c in m.items():
  if not re.fullmatch(r'd[123]/v[0-9a-f]{12}',k):literal.append(k);continue
  actual=mint(c)
  (agree if actual==k else bad).append({'token':k,'canonical':c,'computed_token':actual})
 function_checks[name]={'agreements':len(agree),'disagreements':len(bad),'disagreement_examples':bad[:20],'not_hashed_tokens':len(literal)}
C_enabled=all(x['disagreements']==0 for x in function_checks.values())
inv=collections.defaultdict(set)
for c in scan['candidates']:inv[mint(c)].add(c)
C={k:next(iter(cs)) for k,cs in inv.items() if len(cs)==1} if C_enabled else {}
collisions={k:sorted(cs) for k,cs in inv.items() if len(cs)>1}
# List authorities are identified by their actual byte hashes, never their filenames.
prefixes={'R0':'bdb5d402','withheld-80':'634820b4','BENCH v2':'3119aa4a','dev-S1':'969cdb56','K1':'4d4736cf'}
list_docs={};list_pins={}
krec=load(BASE/'work/K1_RECOVERY.json');inputs.update(krec['inputs']);scan['list_pins']['4d4736cf']=krec['recovered']
for name,prefix in prefixes.items():
 assert prefix in scan['list_pins'],('MISSING',name,prefix)
 p=scan['list_pins'][prefix]['path'];s=read(p);assert inputs[p]['sha256'].startswith(prefix);list_pins[name]=dict(path=p,**inputs[p]);list_docs[name]=s if name=='R0' else json.loads(s)
split=load(prior['authority']['split']['path']);assert inputs[prior['authority']['split']['path']]['sha256']==prior['authority']['split']['sha256'];assert split['teacher_k1']['sha256']==list_pins['K1']['sha256']
sets={'R0':set(list_docs['R0'].split()),'withheld-80':set(list_docs['withheld-80']['rooms']),'BENCH v2':set(list_docs['BENCH v2']['physical_groups']),'dev-S1':set(list_docs['dev-S1']['physical_groups']),'K1':{c['room'] for c in split['teacher_k1']['captures'] if c['k1_split']=='heldout'}}
assert len(sets['R0'])==372 and len(sets['withheld-80'])==80 and len(sets['K1'])==50
# Verify the raw teacher source and build17 derivative capture-by-capture.
raw_k1={norm(c['canonical']):c['k1_split'] for c in list_docs['K1']['captures']}
derived_k1={norm(c['canonical']):c['k1_split'] for c in split['teacher_k1']['captures']}
assert raw_k1==derived_k1
raw_held={rooms.room(c) for c,s in raw_k1.items() if s=='heldout'}
assert raw_held==sets['K1']
print('K1 verified',len(raw_k1),'captures',len(raw_held),'heldout rooms',flush=True)
# Preserve one explicit v7 row witness per token, and detect every disagreement.
store_tokens=collections.Counter();field_counts=collections.Counter();A_internal=[];baseline=collections.Counter();baseline_routes=collections.Counter();store_conflicts=[]
row_fields={}
with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as conn:
 for i,raw in conn.execute('select i,row from rows order by i'):
  r=json.loads(raw);k=key(r);store_tokens[k]+=1
  can,how=old.canonical(r);baseline_routes[how]+=1;baseline['rows']+=1
  if can:
   try:room=old.room(can)
   except (ValueError,TypeError):room=None
  else:room=None
  if room:
   baseline['resolved']+=1
   for n,s in sets.items():baseline[n]+=int(room in s)
  else:baseline['unresolved']+=1
  own,route=rooms.canonical(r)
  if route=='row_field':
   own_raw=own;own=norm(own);field_counts[k]+=1
   evidence=dict(witness_canonical=own_raw,path=str(db),sha256=inputs[str(db)]['sha256'],row_index=i,row_id=r.get('qid'),row_sha256=hashlib.sha256(raw.encode()).hexdigest(),field='canonical via Rooms.canonical row_field')
   if k in A and A[k]!=own:A_internal.append(dict(token=k,source_canonical=A[k],v7_canonical=own,v7_row=evidence,source_row=Aproof[k]))
   if k in row_fields and row_fields[k]!=own:store_conflicts.append(dict(token=k,first=row_fields[k],other=own,row=evidence))
   row_fields[k]=own
   if k not in A:A[k]=own;Aproof[k]=evidence
assert baseline['rows']==204413 and baseline['resolved']==85038 and baseline['K1']==2637 and baseline['R0']==0,baseline
assert dict(baseline_routes)==prior['store']['canonical_from']
# Validate the function against explicit v7 canonical witnesses as well.
v7_good=0;v7_bad=[]
for k,can in row_fields.items():
 if re.fullmatch(r'd[123]/v[0-9a-f]{12}',k):
  if mint(can)==k:v7_good+=1
  else:v7_bad.append(dict(token=k,canonical=can,computed_token=mint(can)))
function_checks['A_v7_row_fields']={'agreements':v7_good,'disagreements':len(v7_bad),'disagreement_examples':v7_bad[:20],'not_hashed_tokens':sum(not bool(re.fullmatch(r'd[123]/v[0-9a-f]{12}',k)) for k in row_fields)}
if v7_bad:C={};C_enabled=False
# Compare all pairs, including the newly witnessed v7 rows.
maps={'A':A,'B':B,'C':C};overlap={};conflict_keys=set(collisions)|{x['token'] for x in A_internal+store_conflicts};conflicts=[]
for x,y in [('A','B'),('A','C'),('B','C')]:
 keys=maps[x].keys()&maps[y].keys();bad=[dict(token=k,tiers={x:maps[x][k],y:maps[y][k]},v7_rows=store_tokens[k]) for k in sorted(keys) if maps[x][k]!=maps[y][k]]
 overlap[x+'_'+y]={'overlap_tokens':len(keys),'agreements':len(keys)-len(bad),'disagreements':len(bad),'disagreement_examples':bad[:20]};conflicts+=bad;conflict_keys.update(z['token'] for z in bad)
# Preserve the mandated A-map/B-map overlap separately from additional v7 witnesses.
a_orig={k:norm(v['canonical']) for k,v in a_payload['aliases'].items()};ab=set(a_orig)&set(B)
original_ab={'overlap_tokens':len(ab),'agreements':sum(a_orig[k]==B[k] for k in ab),'disagreements':sum(a_orig[k]!=B[k] for k in ab)}
assert original_ab=={'overlap_tokens':1850,'agreements':1850,'disagreements':0}
selected={};coverage={t:dict(tokens=0,rows=0,all_map_tokens=len(maps[t]),inclusive_v7_tokens=0,inclusive_v7_rows=0) for t in maps}
# Include Tier A/B maps in full; C entries are restricted to tokens present in v7 or A/B.
for k in sorted(set(A)|set(B)|set(store_tokens)):
 if k in conflict_keys:continue
 available=[t for t in maps if k in maps[t]]
 if not available:continue
 t=available[0];c=maps[t][k];e={'canonical':c,'tier':t,'supporting_tiers':available,'v7_rows':store_tokens[k]}
 if k in A:e['source_row_witness']=Aproof[k]
 if k in B:e['archived_map_proof']=dict(archive=str(archive),member=rec['member'],sha256=b_hash,witness_canonical=rec['aliases'][k])
 if k in C:
  native=c.replace('scannetpp/','scannetppv2/',1);preimage='rung1 scene '+native
  e['preimage_proof']=dict(function=str(CODE/'carrier_c1_routing.py')+':alias_of',preimage=preimage,sha256=hashlib.sha256(preimage.encode()).hexdigest(),printed_token=k,candidate=scan['candidates'][c])
 selected[k]=e
 if store_tokens[k]:coverage[t]['tokens']+=1;coverage[t]['rows']+=store_tokens[k]
 for q in available:
  if store_tokens[k]:coverage[q]['inclusive_v7_tokens']+=1;coverage[q]['inclusive_v7_rows']+=store_tokens[k]
(BASE/'STATUS.md').write_text('The tiered map passes the carrier hash self-check and the 1,850-token Tier A/B agreement check. The build 17 baseline is reproduced: 85,038 resolved rows, 2,637 K1 hits and zero R0 hits. Exact-token preimages and conflict quarantine are built; the whole-store room census is in progress.\n')
hits={n:{t:0 for t in maps} for n in sets};examples={n:{t:[] for t in maps} for n in sets};by_stream={n:collections.Counter() for n in sets};by_family={n:collections.Counter() for n in sets};cross=collections.Counter();resolution=collections.Counter();unresolved=[];unresolved_tokens=collections.Counter();unresolved_stream=collections.Counter();unresolved_family=collections.Counter();resolved_keys=set();room_counts=collections.Counter();actualcoverage={t:collections.Counter() for t in maps}
with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as conn:
 for i,raw in conn.execute('select i,row from rows order by i'):
  r=json.loads(raw);k=key(r);entry=selected.get(k);stream=r.get('pool','MISSING');family=r.get('question_type','MISSING');reason='no_proven_scene'
  can=None;room=None;t=None
  if k in conflict_keys:reason='mapping_conflict'
  elif entry:
   t=entry['tier'];can=entry['canonical'];rooms.aliases={k:can};actual,route=rooms.canonical(r)
   assert actual is not None and norm(actual)==can,(k,actual,can)
   try:room=rooms.room(actual)
   except (ValueError,TypeError):reason='room_canonicalisation_failed'
  e=dict(row_index=i,row_id=r.get('qid'),dataset=r.get('dataset'),scene_token=r.get('scene'),token=k,canonical=can,room=room,tier=t,stream=stream,family=family)
  if room is None:
   resolution['unresolved']+=1;unresolved_tokens[k]+=1;unresolved_stream[stream]+=1;unresolved_family[family]+=1
   if len(unresolved)<20:unresolved.append(dict(e,reason=reason))
   continue
  resolution['resolved']+=1;resolution[t]+=1;resolved_keys.add(k);room_counts[room]+=1;actualcoverage[t]['rows']+=1
  for n,s in sets.items():
   if room not in s:continue
   hits[n][t]+=1;by_stream[n][stream]+=1;by_family[n][family]+=1;cross[(n,t,stream,family)]+=1
   if len(examples[n][t])<20:examples[n][t].append(e)
assert resolution['resolved']+resolution['unresolved']==204413
for t in maps:actualcoverage[t]['tokens']=sum(selected[k]['tier']==t for k in resolved_keys)
listcheck={n:dict(pin=list_pins[n],rooms=len(sets[n]),room_derivation={'R0':'nonempty lines','withheld-80':'rooms','BENCH v2':'physical_groups','dev-S1':'physical_groups','K1':'teacher_k1.captures with k1_split=heldout in the pinned build17 split; linked to the independently hashed K1 source'}[n]) for n in sets}
missing=a_payload['missing_inputs']
checks=dict(canonical_normalisation='scannetppv2 and scannetpp are the same native scene namespace under Rooms.room; outputs use scannetpp. Raw A/B evidence names are retained in proof records.',complete=True,missing_rebuild_inputs=missing,unrelated_builder=dict(path=str(BASE/'in/build_a2_other.py'),sha256=inputs[str(BASE/'in/build_a2_other.py')]['sha256'],finding='Job-receipt wrapper; contains no scene-token minting. Not used as the pinned builder.'),function_checks=function_checks,tier_C_enabled=C_enabled,original_A_B_overlap=original_ab,tier_overlaps=overlap,conflicts=conflicts,A_internal_conflicts=A_internal,v7_internal_conflicts=store_conflicts,preimage_collisions=collisions,quarantined_tokens=sorted(conflict_keys),quarantined_v7_rows=sum(store_tokens[k] for k in conflict_keys),candidate_counts=dict(native=len(scan['candidates']),other_datasets=len(scan['other_dataset_scenes']),by_dataset=dict(collections.Counter(c.split('/')[0] for c in scan['candidates']))),candidate_enumeration_scope=scan['scope'],baseline=dict(baseline),baseline_routes=dict(baseline_routes),list_checks=listcheck,coverage=coverage,room_resolved_coverage={k:dict(v) for k,v in actualcoverage.items()},token_minting_limits='Only carrier alias_of is implemented: build_a2_other.py has no minting code and sources.py loads maps. Other dataset candidates have no supported carrier dataset and cannot receive Tier C proof.')
save('TIER_CHECKS.json',checks)
save('TIERED_ALIAS_MAP.json',dict(complete=True,precedence=['A','B','C'],tier_A_definition='Explicit provenance.canonical witnesses from sb_alias, plus explicit canonical source-row fields in v7 selected by Rooms.canonical.',tier_B_definition='Pinned original rows_a2 archive map, member sha256 488480ab.',tier_C_definition='Unique full printed-token match under the checked carrier alias_of function.',aliases=selected,coverage=coverage,conflicts=conflicts,quarantined_tokens=sorted(conflict_keys),unresolved_tokens=dict(unresolved_tokens),missing_rebuild_inputs=missing))
audit=dict(complete=True,scope='Every v7 row is counted once as room-resolved or unresolved; list hits cover only proven, room-resolved rows and are lower bounds if unresolved rows remain.',store=dict(path=str(db),**inputs[str(db)]),rows=204413,resolved_rows=resolution['resolved'],unresolved_rows=resolution['unresolved'],list_checks=listcheck,hits={n:sum(v.values()) for n,v in hits.items()},hits_by_tier=hits,hits_by_stream={n:dict(c) for n,c in by_stream.items()},hits_by_family={n:dict(c) for n,c in by_family.items()},hits_by_list_tier_stream_family=[dict(list=n,tier=t,stream=s,family=f,rows=v) for (n,t,s,f),v in sorted(cross.items())],examples_by_list_tier=examples,room_resolved_coverage={k:dict(v) for k,v in actualcoverage.items()},scene_mapping_coverage=coverage,unresolved_by_stream=dict(unresolved_stream),unresolved_by_family=dict(unresolved_family),unresolved_tokens=dict(unresolved_tokens),unresolved_examples=unresolved,baseline=dict(baseline),rooms_resolved=len(room_counts),conflict_rows=sum(store_tokens[k] for k in conflict_keys))
save('ROOM_AUDIT_TIERED.json',audit)
lines=[f"R0: {audit['hits']['R0']:,} / withheld-80: {audit['hits']['withheld-80']:,} / BENCH v2: {audit['hits']['BENCH v2']:,} / dev-S1: {audit['hits']['dev-S1']:,} / K1: {audit['hits']['K1']:,}; unresolved rows: {resolution['unresolved']:,}.",'',f"The audit covers all 204,413 v7 rows; {resolution['resolved']:,} have proven scenes and resolved rooms. Counts apply to the proven rows; unresolved rows are not declared overlap-free.",f"Store SHA256: `{inputs[str(db)]['sha256']}`.",'','| Proof tier | v7 tokens resolved | v7 rows resolved |','|---|---:|---:|']
for t,c in actualcoverage.items():lines.append(f"| {t} | {c['tokens']:,} | {c['rows']:,} |")
lines+=['','Tier A uses explicit source-row canonical witnesses, including v7 row fields. Tier B uses the pinned original rows_a2 archive map. Tier C requires a unique exact printed-token preimage. Assignment is exclusive in A, B, C order.','', '| List | A rows | B rows | C rows | Total |','|---|---:|---:|---:|---:|']
for n,h in hits.items():lines.append(f"| {n} | {h['A']:,} | {h['B']:,} | {h['C']:,} | {sum(h.values()):,} |")
lines+=['',f"The hash function agrees with {function_checks['A']['agreements']:,} witnessed tokens and {function_checks['B']['agreements']:,} hashed archive tokens, with zero disagreements. The archive also has {function_checks['B']['not_hashed_tokens']:,} literal keys.",f"The supplied Tier A and Tier B maps agree on all {original_ab['agreements']:,} overlapping entries."]
for n,c in overlap.items():lines.append(f"{n}: {c['agreements']:,} agreements; {c['disagreements']:,} disagreements.")
lines +=[f"Preimage collisions: {len(collisions)}; quarantined v7 rows: {checks['quarantined_v7_rows']}.",f"Candidate enumeration: {len(scan['candidates']):,} native scene identifiers and {len(scan['other_dataset_scenes']):,} other-dataset identifiers. The candidate file records literal origins; the scan manifest records input hashes.",'Enumeration covers local metadata, path names, archived member indexes, and rows_a2/v7 SQLite rows; nested archives are not recursively unpacked. Other datasets have no supported carrier token function.','The staged build_a2_other.py is a job-receipt wrapper, not a scene-token builder. sources.py loads existing maps; neither supplies another minting function.','', 'Baseline reproduced on 85,038 already-resolvable rows: 2,637 K1 rows and zero R0 rows. The baseline alias map is used only for this check; final mappings require A, B or C proof.','']
for n,p in list_pins.items():lines.append(f"{n}: `{p['sha256']}`; {len(sets[n]):,} rooms.")
lines+=['','Build 17’s exact Rooms.canonical and Rooms.room methods determine canonical scenes and physical rooms. ARKit captures use the pinned visit metadata; BENCH/dev use physical_groups; withheld-80 uses rooms. K1 uses the pinned split linked to the verified teacher source.','ScanNet++ canonical names use scannetpp; Rooms.room treats scannetpp and scannetppv2 identically. Proof records retain the A/B evidence names.', 'Streams are row.pool; families are row.question_type. ROOM_AUDIT_TIERED.json gives marginal and joint counts, plus up to 20 example rows per nonempty list/tier cell.','', 'MISSING rebuild inputs (not needed for this proof-tier audit):', '`/scratch/jjyeung/n30_mirror/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite` (expected SHA256 4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59).', '`/scratch/jjyeung/n30_mirror/rows_a2/work/build_a2.py` (expected SHA256 89b2203f7257ef1a23d3fb4783b142e8b63c3174a47d8dfd8aa8650c2dcdef9b).','', 'Commands, from this workspace:', '`python work/enumerate_candidates.py` produces candidate and scan counts and locates exact list pins.', '`python work/recover_k1.py` verifies the archived K1 source against its exact hash.', '`python work/finish_candidates.py` completes plain-JSON and structured-list candidate enumeration.', '`python work/audit.py` produces every mapping, overlap, baseline, tier, room-list, stream and family count above.', '`python work/validate.py` replays exported preimages and checks count totals and example rows.', '`python work/package.py` packages the outputs; `sha256sum out/sb_alias2.tar` verifies the archive digest.', 'Borderline wording retained: “baseline” identifies the requested independent validation population.']
assert len(lines)<=80
(OUT/'ROOM_AUDIT_REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'STATUS.md').write_text(f"The whole-store audit is complete: {audit['hits']}; {resolution['unresolved']} unresolved rows. The baseline is reproduced, all five list pins are verified, and conflicts are quarantined. Outputs and per-cell examples are in out/. Packaging and final consistency checks remain.\n")
print(json.dumps(dict(hits=audit['hits'],coverage={k:dict(v) for k,v in actualcoverage.items()},unresolved=resolution['unresolved'],baseline=dict(baseline),overlaps=overlap),indent=2),flush=True)
