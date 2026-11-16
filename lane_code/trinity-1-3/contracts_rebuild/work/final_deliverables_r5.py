"""Check the completed packet and write its final digest inventory."""
from pathlib import Path
import hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[1];O=L/'out'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
checks={}
def check(name,condition,source):
    checks[name]={'passed':bool(condition),'source':str(source)}
    assert condition,(name,source)
manifest=read(O/'PATCH_MANIFEST_R5.json');proof=read(O/'APPLY_PROOF_R5.json')
for name,digest in manifest['patch_sha256'].items():check('hash '+name,sha(O/name)==digest,O/name)
for rel,meta in manifest['files'].items():
    check('base '+rel,sha(L/'work/base/work/base/tree_b01ce449'/rel)==meta['base_sha256'],O/'PATCH_MANIFEST_R5.json')
    check('overlay '+rel,sha(L/'work/src_r5'/rel)==meta['patched_sha256'],O/'PATCH_MANIFEST_R5.json')
    for label,tree in [('base',proof['tree']),('integration',proof['integration']['tree'])]:
        expected=meta['patched_sha256']
        if label=='integration' and meta.get('accepted_integration_bases'):expected=meta['accepted_integration_bases'][0]['patched_sha256']
        check(label+' patched '+rel,sha(Path(tree)/rel)==expected,O/'APPLY_PROOF_R5.json')
check('ordered application and dry-run',all(proof['ordered'][k] for k in ('all_patched_hashes_match','untouched_files_equal','dry_run_target_unchanged')),O/'APPLY_PROOF_R5.json')
for name,data in proof['refusals'].items():check('refusal '+name,data['returncode']!=0 and data['unchanged'],O/'APPLY_PROOF_R5.json')
def commands(obj):
    if isinstance(obj,dict):
        if 'command' in obj:yield obj
        for value in obj.values():yield from commands(value)
    elif isinstance(obj,list):
        for value in obj:yield from commands(value)
for i,command in enumerate(commands(proof)):
    if command['command'][0]=='patch':check('clean patch '+str(i),command['returncode']==0 and not any(s in command.get('output','').lower() for s in ('offset','fuzz')),O/'APPLY_PROOF_R5.json')
results=read(O/'FINAL_TEST_RESULTS_R5.json')
for key in ('tests','integration_tests'):check(key,all(v['outcome']=='passed' for v in results[key].values()) and len(results[key])==187,O/'FINAL_TEST_RESULTS_R5.json')
mutations=read(O/'MUTATION_R5.json')
check('mutation coverage',len(mutations['mutations'])==82 and mutations['killed']==78 and mutations['equivalent']==4,O/'MUTATION_R5.json')
for name,m in mutations['mutations'].items():
    check('mutation '+name,m['final_source_hashes_verified'] and m['full_suite'] and (m['killed'] or bool(m['equivalent'])) and Path(m['log']).is_file(),O/'MUTATION_R5.json')
regressions=read(O/'R4_REGRESSION_PROOF_R5.json');check('regressions reject r4',all(v['rejects_r4'] for v in regressions.values()),O/'R4_REGRESSION_PROOF_R5.json')
parity=read(O/'ROW_FAMILY_PARITY_R5.json');check('OFF bytes and strict ON parity',parity['summary']['off_parity'] and not parity['defects'],O/'ROW_FAMILY_PARITY_R5.json')
strict=read(O/'STRICT_COMPARISON_R5.json');check('strict negative control',strict['r4_verdict']=='FAIL' and len(strict['r4_error_rows'])==3 and strict['r5_verdict']=='PASS' and strict['numeric_error_and_offset_negative_controls'],O/'STRICT_COMPARISON_R5.json')
audit=read(O/'REAL_ROW_AUDIT_R5.json');check('real audit',audit['totals']['deferred']==0 and audit['legacy_bare_gaps']['rows']==0 and all(audit['ablations'][k]['admitted_only']>0 for k in ('vocabulary','templates','aliases')),O/'REAL_ROW_AUDIT_R5.json')
replay=read(O/'real_replay_r5/REAL_GEOMETRY_REPLAY.json');check('G3T replay',not replay['totals']['assertion_failures'],O/'real_replay_r5/REAL_GEOMETRY_REPLAY.json')
attacks=read(O/'REVIEW_ATTACK_RESULTS_R5.json');check('sensor replay and rotated angle',attacks['sensor_replay']['mismatches']==0 and attacks['rotated_calculator']['passed'],O/'REVIEW_ATTACK_RESULTS_R5.json')
coverage=read(O/'COVERAGE_DETAIL_R5.json');check('changed-line coverage',not coverage['uncovered_executable'],O/'COVERAGE_DETAIL_R5.json')
integrity=read(O/'PACKET_INTEGRITY_R5.json');check('guard and base seal',integrity['guard_ast_equal'] and integrity['base_seal']==manifest['base_seal'],O/'PACKET_INTEGRITY_R5.json')
parts=[]
for old,new in [('src_r4','src_r5'),('tests_r4','tests_r5')]:
    result=subprocess.run(['diff','-ruN',str(L/'work'/old),str(L/'work'/new)],capture_output=True);assert result.returncode==1;parts.append(result.stdout)
check('source and test interdiff',b''.join(parts)==(O/'INTERDIFF_R4_TO_R5.diff').read_bytes(),O/'INTERDIFF_R4_TO_R5.diff')
parts=[]
for stem in ('geometry','candidates','box','geometry_on_tree_r1'):
    result=subprocess.run(['diff','-u',str(O/f'PATCH_{stem}_r4.diff'),str(O/f'PATCH_{stem}_r5.diff')],capture_output=True);assert result.returncode in (0,1);parts.append(result.stdout)
check('patch interdiff',b''.join(parts)==(O/'INTERDIFF_R4_TO_R5_PATCHES.diff').read_bytes(),O/'INTERDIFF_R4_TO_R5_PATCHES.diff')
allocated=int(subprocess.run(['du','-sk',str(L)],capture_output=True,text=True,check=True).stdout.split()[0])*1024
check('lane cap',allocated<4_000_000_000,L)
names=['PATCH_geometry_r5.diff','PATCH_candidates_r5.diff','PATCH_box_r5.diff','PATCH_geometry_on_tree_r1_r5.diff','PATCH_MANIFEST_R5.json','apply_contract_patches_r5.sh','contract_hash_checks_r5.py','APPLY_PROOF_R5.json','INTERDIFF_R4_TO_R5.diff','INTERDIFF_R4_TO_R5_PATCHES.diff','FINAL_TEST_RESULTS_R5.json','MUTATION_R5.json','ROW_FAMILY_PARITY_R5.json','ROW_FAMILY_PARITY_R5.md','REAL_ROW_AUDIT_R5.json','HEADING_DEPENDENCE_R5.md','CHANGED_LINE_COVERAGE_R5.md','CONTRACTS_REPORT_R5.md','COVERAGE_DETAIL_R5.json','OUTPUT_INVENTORY_R5.json','PACKET_INTEGRITY_R5.json','PACKET_HELPER_PARITY_R5.json','R4_REGRESSION_PROOF_R5.json','REVIEW_ATTACK_RESULTS_R5.json','STRICT_COMPARISON_R5.json']
names += ['real_replay_r5/'+p.name for p in sorted((O/'real_replay_r5').iterdir()) if p.is_file()]
for name in names:check('deliverable '+name,(O/name).is_file() and (O/name).stat().st_size>0,O/name)
payload={'passed':True,'checks':checks,'lane_allocated_bytes':allocated,'storage_source':str(L),'df':subprocess.run(['df','-BG','/scratch'],capture_output=True,text=True,check=True).stdout,'deliverable_sha256':{str(O/n):sha(O/n) for n in names}}
(O/'DELIVERABLE_CHECKS_R5.json').write_text(json.dumps(payload,indent=2)+'\n')
names.append('DELIVERABLE_CHECKS_R5.json')
content=read(L/'work/summary_content_r5.json')
text='\n\n'.join(content['paragraphs'])+'\n\n'+'\n'.join(content['item_table'])+'\n\n'+'\n'.join(content['mutant_table'])+'\n\n'
text+=f'Every deliverable check passes: [checks]({O}/DELIVERABLE_CHECKS_R5.json). The strict comparator rejects the r4 malformed-depth rows and accepts r5: [negative control]({O}/STRICT_COMPARISON_R5.json). Final real replay evidence uses `closed_r5_*`; the other replay files are retained intermediate outputs.\n\n'
text+='| Deliverable path | SHA256 |\n|---|---|\n'
for name in names:text+=f'| [{O/name}]({O/name}) | `{sha(O/name)}` |\n'
text+=f'\nThe summary digest is stored externally to avoid a self-referential hash: [BUILD8_SUMMARY_R5.sha256]({O}/BUILD8_SUMMARY_R5.sha256).\n'
(O/'BUILD8_SUMMARY.md').write_text(text)
(O/'BUILD8_SUMMARY_R5.sha256').write_text(sha(O/'BUILD8_SUMMARY.md')+'  '+str(O/'BUILD8_SUMMARY.md')+'\n')
for path,digest in payload['deliverable_sha256'].items():assert sha(Path(path))==digest
assert (O/'BUILD8_SUMMARY_R5.sha256').read_text().split()[0]==sha(O/'BUILD8_SUMMARY.md')
print(json.dumps({'all_checks_passed':True,'checks':len(checks),'summary':str(O/'BUILD8_SUMMARY.md'),'summary_sha256':sha(O/'BUILD8_SUMMARY.md'),'lane_allocated_bytes':allocated}))
