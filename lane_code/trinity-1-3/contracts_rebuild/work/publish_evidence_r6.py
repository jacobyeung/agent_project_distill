from pathlib import Path
import json,subprocess,hashlib,shutil
L=Path(__file__).resolve().parents[1];O=L/'out';W=L/'work'
def write(name,value):
 with (O/name).open('x') as f:
    if isinstance(value,str):f.write(value)
    else:json.dump(value,f,indent=2);f.write('\n')
suites=json.loads((W/'final_suites_r6.json').read_text())
for v in suites.values():
 records=json.loads(Path(v['results']).read_text());v['passed']=sum(r['outcome']=='passed' for r in records.values());v['failed']=sum(r['outcome']=='failed' for r in records.values())
 assert v['returncode']==0 and v['failed']==0
write('FINAL_TEST_RESULTS_R6.json',dict(suites=suites,tests_source=str(W/'tests_r6'),
 semantic_test_adjustment=dict(source=str(W/'tests_r6/test_heading_r2.py'),reason='The vertical-reference OFF oracle must retain the sealed vertical_camera_heading error. ON adapter parity is checked independently; the old oracle depended on the frozen ON basis.')))
a=json.loads((W/'R6_OLD_results.json').read_text());b=json.loads((W/'R6_NEW_results.json').read_text())
assert set(a)==set(b)
records={k:dict(r5=v,r6=b[k],fails_r5_passes_r6=v['outcome']=='failed' and b[k]['outcome']=='passed') for k,v in a.items()}
assert all(r['fails_r5_passes_r6'] for r in records.values())
write('R5_REGRESSION_PROOF_R6.json',dict(tests=records,all_fail_r5_pass_r6=True,
 source_paths=[str(W/'R6_OLD_results.json'),str(W/'R6_NEW_results.json')],strict_compare_r5=str(W/'row_families_r5/heading_compare.py'),
 baseline_parity=str(W/'CONTEXT_PARITY_R6.json')))
write('REAL_ROW_AUDIT_R6.json',json.loads((W/'REAL_ROW_AUDIT_R6.json').read_text()))
row=json.loads((W/'row_families_r6/comparison.json').read_text())
row['validation']=json.loads((W/'row_families_r6/validation.json').read_text())
row['integrity']=json.loads((W/'row_families_r6/integrity.json').read_text())
assert not row['defects'] and row['validation']['all_evidence_checks_pass'] and row['integrity']['all_hashes_match']
row['strict_compare']=dict(source=str(W/'row_families_r6/heading_compare.py'),
 tests=str(W/'R6_NEW_results.json'),normalization='Known private metric audit additions and independently recomputed spans/token counts are validated by compare.mapping, then normalized before the strict key/type/scalar/text walk. All raw differences remain in this artifact.')
row['status']='PASS';write('ROW_FAMILY_PARITY_R6.json',row)
s=row['summary'];source=f'[evidence]({O}/ROW_FAMILY_PARITY_R6.json)'
text=f"OFF equals base byte for byte across {s['rendered_rows']['base']} rows in {s['families']} renderer/family groups. ON admits {s['on_audits']['admitted']} rows and defers {s['on_audits']['deferred']} bare-gap legacy fixtures. All changes pass the strict comparison. Source: {source}.\n\n"
text+='The strict walker rejects added or missing keys, changed leaf types, and changed non-string leaves. The caller separately validates documented private audit fields and derived text offsets. The evidence retains complete returned rows and every difference.\n\n'
text+='| Family | Base / OFF / ON | OFF parity | ON admitted / deferred | Source |\n|---|---|---|---|---|\n'
for r in row['families']:
 text+=f"| {r['family']} | {' / '.join(str(r['rows_per_arm'][a]) for a in ('base','off','on'))} | {r['off_parity']} | {r['audit_counts'].get('admitted',0)} / {r['audit_counts'].get('deferred',0)} | {source} |\n"
write('ROW_FAMILY_PARITY_R6.md',text)
parts=[]
for old,new in [('src_r5','src_r6'),('tests_r5','tests_r6')]:
 p=subprocess.run(['diff','-ruN',str(W/old),str(W/new)],capture_output=True,text=True)
 assert p.returncode in (0,1);parts.append(p.stdout)
write('INTERDIFF_R5_TO_R6.diff',''.join(parts))
parts=[]
for group in ('geometry','candidates','box','geometry_on_tree_r1'):
 p=subprocess.run(['diff','-u',str(O/f'PATCH_{group}_r5.diff'),str(O/f'PATCH_{group}_r6.diff')],capture_output=True,text=True)
 assert p.returncode in (0,1);parts.append(p.stdout)
write('INTERDIFF_R5_TO_R6_PATCHES.diff',''.join(parts))
# Keep only the changed availability rows; all other table rows retain their meaning.
s=(O/'HEADING_DEPENDENCE_R5.md').read_text();rows=[line for line in s.splitlines() if line.startswith('|')]
changed=[]
for i,line in enumerate(rows):
 fields=line.split('|')
 if len(fields)<8:continue
 call,field=fields[1].strip(),fields[2].strip()
 if (call=='depth_at' and field in ('f1 x','f1 z')) or call.startswith(('pose(k)','move(i,j)','turn(i,j)')) or call=='all decode paths':
  fields[5]=fields[5].strip()+' Basis and pose caches use the query epoch and threshold; pose/move/turn rerender reads structured arguments. '
  fields[6]=' test_basis_uses_query_context; test_rerender_head_arguments; '+fields[6].strip()+' '
  rows[i]='|'.join(fields);changed.append(call+' / '+field)
text='Heading-dependent fields use the query context. Stable private operands support heading-independent measurements.\n\n'
text+='Updated rows: '+', '.join(changed)+'. Other field classifications remain unchanged. Evidence: '+f'[regressions]({O}/R5_REGRESSION_PROOF_R6.json).\n\n'
text+='\n'.join(rows).replace('/r5_applied/','/r6_applied/')+'\n\n'
text+=f'Live sessions choose providers and registries inside the backend epoch and threshold, and execute and replay in that context. Ground lifting chooses its private metric basis at each call. The decode construction sites can run before respond_state because OwnGeometry chooses its basis at use. Sources: [routing]({W}/src_r6/student_pilot/carrier_c1_routing.py), [live session]({W}/src_r6/student_pilot/live_trace313.py), [ground lifting]({W}/src_r6/student_pilot/ground_lifting.py), [context parity]({W}/CONTEXT_PARITY_R6.json).\n'
write('HEADING_DEPENDENCE_R6.md',text)
print('Evidence published.')
