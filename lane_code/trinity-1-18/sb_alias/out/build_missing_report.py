"""Preserve a provenance-only partial rebuild; refuse the room audit without D0 inputs."""
import ast,collections,hashlib,json,sqlite3,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'out';M=Path('/scratch/jjyeung/n30_mirror');W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
B=W/'w17b/work/build17'; CODE=W/'w17b/work/tree_r1/student_pilot'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def save(name,v): (OUT/name).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
scan=json.loads((BASE/'work/source_scan.json').read_text()); aliases=scan['aliases']
inputs={k:v for k,v in scan['inputs'].items()}
extra=[BASE/'work/source_scan.json',BASE/'work/inspect_sources.py',Path(__file__),B/'proofs/rooms/RESULT.json',CODE/'r1_rooms.py',CODE/'carrier_c1_routing.py',M/'rows_a2/a2_vqa_v3/BUILD_MANIFEST.json',M/'rows_a2/a2_vqa_v2/BUILD_MANIFEST.json',M/'rows_a2/v4/vsti/code/sources.py',M/'rows_a2/v4/vsti/code/generate_fceb45e6.py',M/'rows_r1/out/ADMISSION_PACKET_V7.md',M/'b08_headrows/b08_partB_kit.tar',BASE/'work/b08_alias_map.json',BASE/'work/archive_search.json']
prior=json.loads((B/'proofs/rooms/RESULT.json').read_text())['audit'];db=Path(prior['store']['database']['path']);extra.append(db)
old_pin=prior['authority']['aliases'];extra.append(Path(old_pin['path']))
for p in extra:inputs[str(p)]={k:v for k,v in pin(p).items() if k!='path'}
assert inputs[str(db)]['sha256']==prior['store']['database']['sha256']
old_alias=json.loads(Path(old_pin['path']).read_text());assert sha(old_pin['path'])==old_pin['sha256']
# Execute the exact canonical method, without importing code that might create caches.
tree=ast.parse((CODE/'r1_rooms.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Rooms')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='canonical')
ns={};exec('import re',ns);exec(compile(ast.Module(body=[method],type_ignores=[]),str(CODE/'r1_rooms.py'),'exec'),ns)
class Lookup:pass
old=Lookup();old.aliases=old_alias
new=Lookup();new.aliases={k:v['canonical'] for k,v in aliases.items()}
# Keep the independently pinned existing alias route in the coverage census, never as rebuilt evidence.
combined=Lookup();combined.aliases=dict(old_alias);combined.aliases.update(new.aliases)
recovered=json.loads((BASE/'work/b08_alias_map.json').read_text());assert sha(BASE/'work/b08_alias_map.json').startswith('488480ab')
archive_extra=Lookup();archive_extra.aliases=dict(combined.aliases);archive_extra.aliases.update(recovered)
cnt=collections.Counter();routes=collections.Counter();datasets=collections.defaultdict(collections.Counter)
miss=[];disagree=[];unresolved=[];needed=set();mapped=set();native_alias_checks=collections.Counter();map_diffs=[]
for k,v in aliases.items():
 if k in recovered:
  equal=v['canonical']==recovered[k];native_alias_checks['agree' if equal else 'disagree']+=1
  if not equal and len(map_diffs)<20:map_diffs.append({'token':k,'rebuilt':v['canonical'],'archived':recovered[k]})
with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
 for i,raw in c.execute('select i,row from rows order by i'):
  r=json.loads(raw);key=r['dataset']+'/'+r['scene'];can,how=ns['canonical'](old,r);rebuilt=new.aliases.get(key)
  e=dict(row_id=r['qid'],row_index=i,stream=r.get('pool','MISSING'),family=r.get('question_type','MISSING'),dataset=r['dataset'],token=key,expected_canonical=can,rebuilt_canonical=rebuilt)
  cnt['rows']+=1;routes[how]+=1
  if how=='alias':
   cnt['selfcheck_rows']+=1
   if rebuilt is None:
    cnt['selfcheck_missing']+=1
    if len(miss)<20:miss.append(e)
   elif rebuilt==can:cnt['selfcheck_agreements']+=1
   else:
    cnt['selfcheck_disagreements']+=1
    if len(disagree)<20:disagree.append(e)
  if r['dataset'] in ('d1','d2'):
   needed.add(key)
   if rebuilt:mapped.add(key)
  now,_=ns['canonical'](combined,r)
  if how=='unresolved':
   cnt['previously_unresolved']+=1
   cnt['newly_resolved_by_provenance' if now else 'still_unresolved']+=1
  if now is None:
   datasets[r['dataset']]['unresolved']+=1
   if len(unresolved)<20:unresolved.append(e)
  else:datasets[r['dataset']]['resolved']+=1
  if ns['canonical'](archive_extra,r)[0] is None:cnt['unresolved_even_with_archived_map']+=1
assert cnt['rows']==204413 and cnt['selfcheck_rows']==41259 and cnt['previously_unresolved']==119375
assert dict(routes)==prior['store']['canonical_from']
missing=[dict(status='MISSING',role='D0 v5 base database',expected_original_path='/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite',expected_mirror_path=str(M/'rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'),expected_sha256='4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59',evidence=str(M/'rows_a2/a2_vqa_v3/BUILD_MANIFEST.json')),dict(status='MISSING',role='rows_a2 builder',expected_original_path='/scratch/jjyeung/orch_n30/rows_a2/work/build_a2.py',expected_mirror_path=str(M/'rows_a2/work/build_a2.py'),expected_sha256='89b2203f7257ef1a23d3fb4783b142e8b63c3174a47d8dfd8aa8650c2dcdef9b')]
assert all(not Path(x['expected_mirror_path']).exists() for x in missing)
command='python out/build_missing_report.py (after python work/inspect_sources.py)'
common=dict(status='MISSING',complete=False,command=command,inputs=inputs,missing_inputs=missing)
map_payload=dict(common,schema='provenance-scene-alias-map-v1',aliases=aliases,alias_count=len(aliases),conflicts=scan['conflicts'],source_counts=scan['source_counts'],join_key='dataset + / + scene token',rule='Only explicit source-row provenance.canonical witnesses are admitted; no archived-map-only or hash-enumerated entries are admitted.',token_rule="v + sha256(UTF8('rung1 scene ' + native_dataset + '/' + scene))[:12]; native_dataset=scannet|scannetppv2|arkitscenes; fixed domain prefix, no additional salt in surviving alias_of code",minting_code=str(CODE/'carrier_c1_routing.py')+':830',builder_behavior='sources.py:73 loads the alias map; generate_fceb45e6.py:148-161 copies the supplied alias and provenance canonical, and hashes a separate qid; the original rows_a2 builder is MISSING.')
save('alias_map.json',map_payload)
check=dict(common,schema='scene-alias-selfcheck-v1',counts=dict(cnt),canonical_from_before=dict(routes),test_set_rows=41259,agreements=cnt['selfcheck_agreements'],disagreements=cnt['selfcheck_disagreements'],missing=cnt['selfcheck_missing'],coverage=(cnt['selfcheck_agreements']+cnt['selfcheck_disagreements'])/41259,disagreement_examples=disagree,missing_examples=miss,unresolved_examples=unresolved,coverage_by_dataset={k:dict(v) for k,v in datasets.items()},d1_d2_unique_tokens=len(needed),d1_d2_tokens_with_source_witness=len(mapped),d1_d2_unique_token_coverage=len(mapped)/len(needed),archived_map_crosscheck=dict(native_alias_checks),archived_map_disagreement_examples=map_diffs,archived_map_note='Pinned archived rows_a2 map found in b08_partB_kit.tar!work/auth/alias_map.json; preserved separately, not treated as a source-row witness. Missing counts are distinct from disagreements.')
save('ALIAS_SELFCHECK.json',check)
recovery=dict(common,schema='archived-alias-recovery-v1',aliases=recovered,archive=pin(M/'b08_headrows/b08_partB_kit.tar'),member='work/auth/alias_map.json',member_sha256=sha(BASE/'work/b08_alias_map.json'),source_row_proof='MISSING for entries without a witness in alias_map.json')
save('RECOVERED_ARCHIVED_ALIAS_MAP.json',recovery)
audit=dict(common,schema='whole-store-room-audit-v1',reason='Stopped under the task missing-input rule: required D0 base and rows_a2 builder do not survive at their expected mirror paths or as direct members of the 74 inspected top-level archives.',rows=204413,store=pin(db),hits={name:'MISSING' for name in ['R0','withheld-80','BENCH v2','dev-S1','K1']},unresolved='MISSING',hits_by_stream='MISSING',hits_by_family='MISSING',examples_by_list='MISSING',canonical_coverage_only=dict(still_unresolved=cnt['still_unresolved'],newly_resolved=cnt['newly_resolved_by_provenance'],note='Coverage from the partial provenance map plus the pinned existing aliases; not a completed room audit.'))
save('ROOM_AUDIT.json',audit)
lines=[
'R0: MISSING / withheld-80: MISSING / BENCH v2: MISSING / dev-S1: MISSING / K1: MISSING; unresolved: MISSING (room audit stopped).',
'',
'The required D0 v5 base and rows_a2 builder are missing. The task explicitly requires stopping when build inputs do not survive. No whole-store room-hit counts are certified.',
'',
f'The verified store contains {cnt["rows"]:,} rows; SHA256 `{inputs[str(db)]["sha256"]}`.',
f'The provenance-only partial map contains {len(aliases):,} aliases with source-file hashes, row indices, row IDs, raw-row hashes and explicit `provenance.canonical` witnesses. Conflicts: {len(scan["conflicts"])}.',
f'The 41,259-row alias test set yields {cnt["selfcheck_agreements"]:,} agreements, {cnt["selfcheck_disagreements"]:,} disagreements and {cnt["selfcheck_missing"]:,} missing witnesses; coverage is {100*check["coverage"]:.4f}%. Missing witnesses do not count as agreements.',
f'Of {len(needed):,} d1/d2 tokens in v7, {len(mapped):,} have explicit source-row witnesses ({100*len(mapped)/len(needed):.4f}%).',
f'The partial map resolves {cnt["newly_resolved_by_provenance"]:,} of the 119,375 unresolved canonical rows; {cnt["still_unresolved"]:,} remain unresolved. These are alias-coverage counts, not room-list results.',
'`ALIAS_SELFCHECK.json` contains up to 20 disagreement, missing-witness and unresolved examples. The source scan found zero provenance canonical fields in either the v2 or v3 store.',
'',
'A pinned copy of the original rows_a2 alias map survives in another lane’s archive:',
'`/scratch/jjyeung/n30_mirror/b08_headrows/b08_partB_kit.tar!work/auth/alias_map.json`.',
f'Its SHA256 is `{sha(BASE/"work/b08_alias_map.json")}` and it contains {len(recovered):,} entries.',
f'It agrees exactly with {native_alias_checks["agree"]:,} overlapping witnessed entries; {native_alias_checks["disagree"]:,} disagree. Even adding this copy leaves {cnt["unresolved_even_with_archived_map"]:,} canonical rows unresolved.',
'`RECOVERED_ARCHIVED_ALIAS_MAP.json` preserves this recovery separately. Archived-map entries without source-row witnesses were not promoted into the rebuilt map.',
'',
'The missing D0 database is expected at:',
'`/scratch/jjyeung/n30_mirror/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite`.',
'Its recorded original path is `/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite`.',
'Its required SHA256 is `4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59`.',
'The missing builder is expected at `/scratch/jjyeung/n30_mirror/rows_a2/work/build_a2.py`.',
'Its required SHA256 is `89b2203f7257ef1a23d3fb4783b142e8b63c3174a47d8dfd8aa8650c2dcdef9b`.',
'Both are named by `rows_a2/a2_vqa_v3/BUILD_MANIFEST.json`. The mirror inventory and 74 top-level archive inventories contain neither required input as a direct member; nested archives were not exhaustively searched.',
'',
'The surviving token function is `carrier_c1_routing.py:830` under build 17’s `work/tree_r1/student_pilot/`.',
"It uses `v + sha256(('rung1 scene ' + native_dataset + '/' + scene).encode())[:12]`, with ScanNet++ named `scannetppv2`. The fixed prefix is the only salt in that function.",
'`rows_a2/v4/vsti/code/sources.py:73` loads aliases; `generate_fceb45e6.py:148–161` copies the alias and canonical into each row. Its separate qid hash does not mint scene tokens.',
'',
'Commands that produce the counts: `python work/inspect_sources.py`, then `python out/build_missing_report.py` from the workspace. JSON `inputs` records bind every source used by these outputs.',
'The first command scans source rows; the second reproduces build 17’s exact canonical method, verifies the store hash and baseline counts, and computes the self-check and coverage. It refuses the list audit.',
'Package command: `python out/package_outputs.py`. Verification command: `sha256sum out/sb_alias.tar`.',
'The archive contains the JSON outputs, report and scripts. Its report omits the final archive digest; the adjacent report records it to avoid a self-referential hash.',
'Archive SHA256: recorded in the adjacent final report after packaging.',
]
assert len(lines)<=80
(OUT/'ALIAS_AUDIT_REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'STATUS.md').write_text(f'The task stopped at the missing-input gate: D0 v5 rows.sqlite (4af43b40) and rows_a2/work/build_a2.py (89b2203f) are absent from their expected mirror paths and inspected direct archive members. The partial rebuild has {len(aliases)} witnessed aliases; its self-check has {cnt["selfcheck_agreements"]} agreements, {cnt["selfcheck_disagreements"]} disagreements and {cnt["selfcheck_missing"]} missing witnesses. The partial map leaves {cnt["still_unresolved"]} canonical rows unresolved. A separate archived alias map was recovered. All list-hit outputs are MISSING, as required; no full room audit ran. The report is out/ALIAS_AUDIT_REPORT.md.\n')
print(json.dumps({'aliases':len(aliases),'counts':dict(cnt),'d1_d2_tokens':len(needed),'d1_d2_witnesses':len(mapped),'archived_crosscheck':dict(native_alias_checks)},indent=2))
