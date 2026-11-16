"""Publish completed proof artifacts without replacing any existing output."""
from pathlib import Path
import ast,collections,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[1];W=L/'work';O=L/'out'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
 with (O/name).open('x') as f:
  if isinstance(value,str):f.write(value)
  else:json.dump(value,f,indent=2);f.write('\n')
def link(label,name):return f'[{label}]({O/name})'
mut=read(W/'mutation_r6/results.json');definitions=read(W/'mutation_r6/definitions.json');old=read(O/'MUTATION_R5.json')['mutations']
assert set(mut)==set(definitions) and set(old)<=set(mut),(len(mut),len(definitions))
for mid,r in mut.items():
 assert r['full_suite'] and '-x' in r['command'] and '-k' not in r['command']
 assert r['killed'] or r['equivalence_verified'],mid
 assert sha(Path(r['changed_file']))==r['changed_sha256'],mid
 original=(W/'row_families_r6/heading_compare.py' if r['rel'].startswith('@') else W/'src_r6'/r['rel']).read_text()
 expected=original.replace(r['old'],r['new']) if r['old'] else original
 assert Path(r['changed_file']).read_text()==expected,mid
 r['final_source_hashes_verified']=True
killed=sum(v['killed'] for v in mut.values());equiv=sum(v['equivalence_verified'] for v in mut.values())
write('MUTATION_R6.json',dict(mutations=mut,killed=killed,equivalent=equiv,total=len(mut),r5_mutants=str(O/'MUTATION_R5.json'),
 source_paths=[str(W/'mutation_r6/definitions.json'),str(W/'mutation_r6/results.json')],pool=dict(trees=1,path=str(W/'mutation_r6/round_pool/tree'),restore='Every source file is copied from the patched tree before each mutant. Each changed file, log and JSON result is retained separately.')))
suites=read(O/'FINAL_TEST_RESULTS_R6.json');reg=read(O/'R5_REGRESSION_PROOF_R6.json');row=read(O/'ROW_FAMILY_PARITY_R6.json');audit=read(O/'REAL_ROW_AUDIT_R6.json');replay=read(O/'real_replay_r6/REAL_GEOMETRY_REPLAY.json')
assert not replay['totals']['assertion_failures']
items=[
 ('F-1','Choose horizontal basis and cached poses by the query epoch and heading threshold. Decode construction can precede the session context.','test_basis_uses_query_context','PASS'),
 ('F-2','Initialize the live provider and registries inside the backend context; execute and replay under that same context.','test_live_provider_uses_backend_epoch','PASS'),
 ('L-a','Attempt the contracts import at registry construction; fall back to sealed only on ImportError. Standalone imports and construction remain supported.','test_generator_import_order; test_standalone_generator_imports; test_standalone_construction_fallback','PASS'),
 ('L-b','Copy only containers changed by alias merging; share mask payloads and preserve the caller cache.','test_cache_view_shares_mask_payload_without_mutation; test_cache_lookup_preserves_caller','PASS'),
 ('L-c','Return None for a binding dict without phrases so the missing-manifest guard fires.','test_missing_manifest_phrases','PASS'),
 ('L-d','Render pose, move and turn from structured arguments in every heading state.','test_rerender_head_arguments','PASS'),
 ('L-e','Keep runtime batch/cache phrases ahead of row declarations; use a pinned manifest only as fallback.','test_shared_binding_served_or_deferred; test_build_defers_one_row_and_keeps_clean_row','PASS'),
 ('L-f','Reject changed dictionary keys, leaf types and non-string leaves. Validate documented private audit additions and derived offsets separately.','test_strict_row_structure; row_families_r6/validate_evidence.py','PASS'),
 ('L-2c',f"Keep bare-gap deferral under ON: {row['summary']['on_audits']['deferred']} synthetic rows defer; {audit['legacy_bare_gaps']['rows']} real POOL rows use the form. "+link('row evidence','ROW_FAMILY_PARITY_R6.json')+'; '+link('POOL evidence','REAL_ROW_AUDIT_R6.json'),'test_legacy_gap_off_grammar; test_legacy_scalar_gap_audit','PASS'),
]
item_table=['| Item | Current change / decision | Test | Result and source |','|---|---|---|---|']
for key,change,test,status in items:
 evidence=link('row comparison','ROW_FAMILY_PARITY_R6.json') if key=='L-f' else link('suite','FINAL_TEST_RESULTS_R6.json')
 item_table.append(f'| {key} | {change} | {test} | {status}; {evidence} |')
paragraphs=[
 'The r6 packet closes the interdiff findings. Both patched trees pass the full suite, OFF preserves sealed output bytes, and ON changes pass the strict row comparison. '+link('application proof','APPLY_PROOF_R6.json')+'; '+link('parity','ROW_FAMILY_PARITY_R6.json')+'.',
 f"Each patched tree passes {suites['suites']['base']['passed']} tests. All {len(reg['tests'])} new regression cases fail on r5 and pass on r6. "+link('suite evidence','FINAL_TEST_RESULTS_R6.json')+'; '+link('regression evidence','R5_REGRESSION_PROOF_R6.json')+'.',
 f'Mutation tests kill {killed} mutants and verify {equiv} equivalent mutants, including every r5 mutant. Each run uses the full suite with early exit. '+link('mutation evidence','MUTATION_R6.json')+'.',
 f"Each row arm renders {row['summary']['rendered_rows']['base']} rows; OFF equals base byte for byte. ON admits {row['summary']['on_audits']['admitted']} and defers {row['summary']['on_audits']['deferred']} synthetic bare-gap rows. "+link('row evidence','ROW_FAMILY_PARITY_R6.json')+'.',
 f"The POOL audit admits {audit['totals']['admitted']} source records and defers {audit['totals']['deferred']}. It finds {audit['legacy_bare_gaps']['rows']} bare-gap records. "+link('POOL evidence','REAL_ROW_AUDIT_R6.json')+'.',
 f"The real G3T replay covers {replay['totals'].get('captures',len(replay.get('captures',[])))} captures with {len(replay['totals']['assertion_failures'])} failed assertions. "+link('replay evidence','real_replay_r6/REAL_GEOMETRY_REPLAY.json')+'.',
]
# Use the independent capture inventory as the count authority.
inv=read(O/'real_replay_r6/CAPTURE_INVENTORY.json')
paragraphs[-1]=f"The real G3T replay covers {inv['npz_count']} captures with {len(replay['totals']['assertion_failures'])} failed assertions. "+link('capture inventory','real_replay_r6/CAPTURE_INVENTORY.json')+'; '+link('replay evidence','real_replay_r6/REAL_GEOMETRY_REPLAY.json')+'.'
notes=[
 'The mask cache defines the runtime competition universe. Batch cache phrases and persisted batch cache phrases win; row candidate phrases precede row cache phrases and row manifests. A separately pinned manifest supplies a missing binding. '+f'[resolver]({W}/src_r6/student_pilot/phrases.py).',
 'OwnGeometry selects its basis and pose cache at use. Ground lifting also chooses its metric basis at use. The decode response context follows the live session; the live session pins provider construction and execution to its backend. Generator registry construction checks import availability explicitly. Existing class API, mixed-point, provider and replay regressions remain covered. '+link('heading inventory','HEADING_DEPENDENCE_R6.md')+'; '+link('reviewer probes','REVIEW_C5_PROBES_R6.json')+'.',
 'The vertical-reference test checks ON adapter parity separately from the sealed OFF error. It does not use an ON basis as an OFF oracle. '+link('test adjustment','FINAL_TEST_RESULTS_R6.json')+'.',
 'Bare-gap rows still defer under ON. The legacy sealed session can emit bare scalar gaps; the POOL count does not imply that every runtime forbids them. '+f'[legacy emitter]({W}/base/work/base/tree_b01ce449/trace_format/ground_v312.py); '+link('audit','REAL_ROW_AUDIT_R6.json')+'.',
 'RGB inputs and printed numerical observations keep their existing paths. The gravity guard and threshold contract are unchanged. CPU fixtures and synthetic replay masks verify software contracts; they do not measure model quality or establish metric calibration for raw tower units. '+link('guard integrity','PACKET_INTEGRITY_R6.json')+'; '+link('replay scope','real_replay_r6/REAL_GEOMETRY_REPLAY.json')+'.',
 'No project-history statements are retained. The r5/r6 labels identify the requested controlled regression comparison.',
]
write('CONTRACTS_REPORT_R6.md','\n\n'.join(paragraphs)+'\n\n'+'\n'.join(item_table)+'\n\n'+'\n\n'.join(notes)+'\n')
# Include the harness changes separately; the requested source/test interdiff stays exact.
p=subprocess.run(['diff','-u',str(W/'row_families_r5/heading_compare.py'),str(W/'row_families_r6/heading_compare.py')],capture_output=True,text=True);assert p.returncode==1
q=subprocess.run(['diff','-u',str(W/'row_families_r5/compare.py'),str(W/'row_families_r6/compare.py')],capture_output=True,text=True);assert q.returncode==1
write('INTERDIFF_ROW_COMPARE_R6.diff',p.stdout+q.stdout)
checks={}
def check(name,ok,source):
 checks[name]=dict(passed=bool(ok),source=str(source));assert ok,(name,source)
manifest=read(O/'PATCH_MANIFEST_R6.json');proof=read(O/'APPLY_PROOF_R6.json')
for name,digest in manifest['patch_sha256'].items():check('patch '+name,sha(O/name)==digest,O/name)
for rel,m in manifest['files'].items():
 check('source '+rel,sha(W/'src_r6'/rel)==m['patched_sha256'],O/'PATCH_MANIFEST_R6.json')
 for arm,t in [('base',W/'trees/r6_applied'),('tree_r1',W/'trees/r6_snapshot')]:
  expected=m.get('accepted_integration_bases',[m])[0]['patched_sha256'] if arm=='tree_r1' else m['patched_sha256']
  check(arm+' '+rel,sha(t/rel)==expected,O/'PATCH_MANIFEST_R6.json')
for arm,p in proof.items():
 check(arm+' applies and refuses repeat',p['dry']['returncode']==p['apply']['returncode']==0 and p['repeat']['returncode']!=0,O/'APPLY_PROOF_R6.json')
for arm,s in suites['suites'].items():check(arm+' complete suite',s['returncode']==0 and s['failed']==0,Path(s['results']))
check('all new regressions',reg['all_fail_r5_pass_r6'],O/'R5_REGRESSION_PROOF_R6.json')
check('all r5 mutants included',set(old)<=set(mut),O/'MUTATION_R6.json')
check('all mutants killed or equivalent',all(v['killed'] or v['equivalence_verified'] for v in mut.values()),O/'MUTATION_R6.json')
check('row parity',row['summary']['off_parity'] and not row['defects'] and row['validation']['all_evidence_checks_pass'],O/'ROW_FAMILY_PARITY_R6.json')
check('real audit completed',audit['totals']['rows']==sum(v['rows'] for v in audit['by_type'].values()),O/'REAL_ROW_AUDIT_R6.json')
check('real replay',not replay['totals']['assertion_failures'],O/'real_replay_r6/REAL_GEOMETRY_REPLAY.json')
check('changed executable lines covered',not read(O/'COVERAGE_DETAIL_R6.json')['uncovered'],O/'COVERAGE_DETAIL_R6.json')
parts=[]
for a,b in [('src_r5','src_r6'),('tests_r5','tests_r6')]:
 p=subprocess.run(['diff','-ruN',str(W/a),str(W/b)],capture_output=True);assert p.returncode==1;parts.append(p.stdout)
check('source test interdiff exact',b''.join(parts)==(O/'INTERDIFF_R5_TO_R6.diff').read_bytes(),O/'INTERDIFF_R5_TO_R6.diff')
parts=[]
for group in ('geometry','candidates','box','geometry_on_tree_r1'):
 p=subprocess.run(['diff','-u',str(O/f'PATCH_{group}_r5.diff'),str(O/f'PATCH_{group}_r6.diff')],capture_output=True);assert p.returncode in (0,1);parts.append(p.stdout)
check('patch interdiff exact',b''.join(parts)==(O/'INTERDIFF_R5_TO_R6_PATCHES.diff').read_bytes(),O/'INTERDIFF_R5_TO_R6_PATCHES.diff')
allocated=int(subprocess.run(['du','-sk',str(L)],capture_output=True,text=True,check=True).stdout.split()[0])*1024
check('lane storage',allocated<3_900_000_000,L)
names=sorted([p for p in O.iterdir() if p.is_file() and ('_r6' in p.name or '_R6' in p.name)]+[p for p in (O/'real_replay_r6').iterdir() if p.is_file()])
for p in names:check('deliverable '+p.name,p.stat().st_size>0,p)
payload=dict(passed=True,checks=checks,lane_allocated_bytes=allocated,limit_bytes=3_900_000_000,storage_source=str(L),
 df=subprocess.run(['df','-BG','/scratch'],capture_output=True,text=True,check=True).stdout,
 deliverable_sha256={str(p):sha(p) for p in names})
write('DELIVERABLE_CHECKS_R6.json',payload);names.append(O/'DELIVERABLE_CHECKS_R6.json')
mut_table=['| Mutant | Change | Test / probe | Result and source |','|---|---|---|---|']
for mid,r in mut.items():
 change=(r['old']+' → '+r['new']).replace('\n',' ').replace('|','&#124;') if r['old'] else r['equivalent']
 tests='; '.join(r['failing_tests']) if r['killed'] else 'Full suite; '+r['equivalent']
 mut_table.append(f"| {mid} | {change} | {tests.replace('|','&#124;')} | {'KILLED' if r['killed'] else 'EQUIVALENT'}; [log]({r['log']}) |")
text='\n\n'.join(paragraphs)+'\n\n'+'\n'.join(item_table)+'\n\n'+'\n'.join(mut_table)+'\n\n'
text+=f'Every deliverable check passes. The lane uses {allocated} bytes under the {payload["limit_bytes"]}-byte ceiling. Source: '+link('final checks','DELIVERABLE_CHECKS_R6.json')+'.\n\n'
text+='Apply with `bash out/apply_contract_patches_r6.sh TARGET --dry-run`; omit `--dry-run` to install. The helper checks ordered patch hashes and refuses reapplication.\n\n'
text+='| Deliverable path | SHA256 |\n|---|---|\n'
for p in names:text+=f'| [{p}]({p}) | `{sha(p)}` |\n'
text+='\nThe summary hash is recorded in '+link('BUILD9_SUMMARY_R6.sha256','BUILD9_SUMMARY_R6.sha256')+' to avoid a self-referential digest.\n'
write('BUILD9_SUMMARY.md',text)
write('BUILD9_SUMMARY_R6.sha256',sha(O/'BUILD9_SUMMARY.md')+'  '+str(O/'BUILD9_SUMMARY.md')+'\n')
for p,digest in payload['deliverable_sha256'].items():assert sha(Path(p))==digest
print(json.dumps(dict(passed=True,summary=str(O/'BUILD9_SUMMARY.md'),sha256=sha(O/'BUILD9_SUMMARY.md'),mutants=len(mut),killed=killed,equivalent=equiv,lane_allocated_bytes=allocated)))
