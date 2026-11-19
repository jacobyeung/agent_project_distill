"""Collect test outcomes, document limits, and seal the small review bundle."""
from pathlib import Path
import collections,hashlib,json,re,tarfile,datetime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
prefix='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B '
command=prefix+'code/finalize.py'
setup=json.loads((OUT/'SETUP.json').read_text());touched=json.loads((OUT/'FILES_TOUCHED.json').read_text())
for kind in ('base','new'):
    inventory=dict(setup['base_plus_patchA_files'])
    if kind=='new':inventory.update({f['path']:f['new_sha256'] for f in touched['files']})
    tree=ROOT/'work'/kind
    for name,h in inventory.items():assert sha(tree/name)==h,name
    for group in ('suite','headcall'):
        p=OUT/(group+'_'+kind)/'TEST_RESULTS.json';v=json.loads(p.read_text())
        v['input_sha256'].update({str(tree/name):h for name,h in inventory.items()})
        v['provenance_finalized_by']={'command':command,'script_sha256':sha(Path(__file__))}
        p.write_text(json.dumps(v,indent=2)+'\n')
# Bind each focused/composition result to the complete unchanged source tree.
new_inventory=dict(setup['base_plus_patchA_files'])
new_inventory.update({f['path']:f['new_sha256'] for f in touched['files']})
for name in ('UNIT.json','REGRESSIONS_after.json','SOURCE_TESTS.json','COMPOSITION_A.json'):
    p=OUT/name;v=json.loads(p.read_text())
    v['input_sha256'].update({str(ROOT/'work/new'/rel):h for rel,h in new_inventory.items()})
    v['provenance_finalized_by']={'command':command,'script_sha256':sha(Path(__file__))}
    p.write_text(json.dumps(v,indent=2)+'\n')
p=OUT/'REGRESSIONS_before.json';v=json.loads(p.read_text());original=ROOT.parent/'camform/work/new'
for name in new_inventory:
    q=original/name
    if q.is_file():
        h=sha(q)
        if str(q) in v['input_sha256']:assert v['input_sha256'][str(q)]==h,str(q)
        v['input_sha256'][str(q)]=h
v['provenance_finalized_by']={'command':command,'script_sha256':sha(Path(__file__))}
p.write_text(json.dumps(v,indent=2)+'\n')
inputs={str(Path(__file__)):sha(Path(__file__))};failures={};summaries={}
for label in ('suite_base','suite_new','headcall_base','headcall_new'):
    p=OUT/label/'TEST_RESULTS.json';v=json.loads(p.read_text());inputs[str(p)]=sha(p)
    log=OUT/(label+'.log');inputs[str(log)]=sha(log);text=log.read_text();entries=[]
    for match in re.finditer(r'^(FAIL|ERROR): ([^\n]+)\n(.*?)(?=\n={10}|\n-{10}\nRan |\Z)',text,re.M|re.S):
        m=re.search(r'\((tests\.[^ )]+|unittest\.loader\.[^ )]+)\)',match[2])
        entries.append(dict(kind=match[1],test_id=m[1] if m else match[2].split(' (',1)[0],label=match[2],traceback=match[3]))
    assert len(entries)==v['failures']+v['errors'],(label,len(entries),v['failures'],v['errors'])
    failures[label]=entries;summaries[label]={k:v[k] for k in ('tests_run','tests_executed','failures','errors','source_unchanged')};summaries[label]['skips']=len(v['skipped'])
comparisons={}
for group in ('suite','headcall'):
    a=collections.Counter((x['kind'],x['test_id']) for x in failures[group+'_base']);b=collections.Counter((x['kind'],x['test_id']) for x in failures[group+'_new']);extra=b-a
    comparisons[group]=dict(base=summaries[group+'_base'],new=summaries[group+'_new'],no_new_failure=not extra,new_failing_outcomes=[dict(kind=k[0],test_id=k[1],count=v) for k,v in extra.items()],commands={k:prefix+'code/'+('suite.py' if group=='suite' else 'headcall_suite.py')+' '+k for k in ('base','new')})
required=['SETUP.json','FILES_TOUCHED.json','UNIT.json','REGRESSIONS_before.json','REGRESSIONS_after.json','SOURCE_TESTS.json','COMPOSITION_A.json','A2_PACKAGING.json']
values={}
for name in required:
    p=OUT/name;values[name]=json.loads(p.read_text());inputs[str(p)]=sha(p)
a2=values['A2_PACKAGING.json']
if a2['status']=='PASS':
    for name in ('COMPOSITION_A2.json','UNIT_A2.json'):
        p=OUT/name;values[name]=json.loads(p.read_text());inputs[str(p)]=sha(p)
    for name in ('COMPOSITION_A2.json','UNIT_A2.json'):
        p=OUT/name;v=values[name]
        v['input_sha256'].update({path:h for path,h in a2['input_sha256'].items() if Path(path).is_relative_to(ROOT/'work/newA2')})
        v['input_sha256'][str(OUT/'A2_PACKAGING.json')]=sha(OUT/'A2_PACKAGING.json')
        v['provenance_finalized_by']={'command':command,'script_sha256':sha(Path(__file__))}
        p.write_text(json.dumps(v,indent=2)+'\n');inputs[str(p)]=sha(p)
    assert values['COMPOSITION_A2.json']['absent_byte_identical'] and values['UNIT_A2.json']['success']
    for name,h in a2['input_sha256'].items():
        p=Path(name)
        if p.is_relative_to(ROOT/'work/baseA2') or p.is_relative_to(ROOT/'work/newA2'):
            assert sha(p)==h,name
assert values['UNIT.json']['success'] and values['REGRESSIONS_after.json']['success']
assert not values['REGRESSIONS_before.json']['success']
assert values['COMPOSITION_A.json']['absent_byte_identical']
assert all(v['no_new_failure'] for v in comparisons.values()),comparisons
result=dict(input_sha256=inputs,command=command,comparisons=comparisons,full_suite_baseline='seal 57a1f14d + PATCH_A b95c1c61',focused_tests=values['UNIT.json']['tests'],focused_pass=True,regression_tests=values['REGRESSIONS_after.json']['tests'],fail_before_pass_after=True,declaration_mode_composition=values['COMPOSITION_A.json'],A2_status=a2['status'],A2_focused_tests=values.get('UNIT_A2.json',{}).get('tests','MISSING'),A2_absent_byte_identical=values.get('COMPOSITION_A2.json',{}).get('absent_byte_identical','MISSING'),all_requested_available_checks_pass=True,full_suite_green=False)
(OUT/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'SUITE_FAILURES.json').write_text(json.dumps(dict(input_sha256=inputs,command=command,comparisons=comparisons,failures=failures),indent=2)+'\n')
a=comparisons['suite']['base'];b=comparisons['suite']['new'];h=comparisons['headcall'];composition=values['COMPOSITION_A.json']
a2line=(f"PATCH_CAMFORM2_ON_A2.patch applies with zero fuzz; declaration-mode absent bytes match base+PATCH_A2; {values['UNIT_A2.json']['tests']} focused A2 tests pass."
        if a2['status']=='PASS' else f"PATCH_CAMFORM2_ON_A2.patch: MISSING; required SHA256 companion is {a2['expected_sha256_companion']}.")
report=f'''PATCH_CAMFORM2 fixes M1, S1 and S2. The full CPU comparison has no new failing outcome.

M1: A present camera_trace_form field in deferred mode raises R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION during config validation, before other validation or policy reads.
The shared deferred gate also refuses this combination in admission and launch paths.
S1: The policy pin must equal 169c439a1ac1bf11d66ee7b725277ef8ee07a706807324bed2696b9d99efaace; reformatted and reordered copies refuse.
S2: Receipts retain rewritten-row counts and add changed_base_lines, changed_base_lines_by_type and changed_base_lines_by_rule.
Two matching events in one admitted row count as one rewritten row and two changed lines; repeated matches on one physical line count once.

PATCH_CAMFORM2.patch targets seal 57a1f14d + PATCH_A b95c1c61, includes the complete camera overlay, touches {touched['file_count']} files, and applies with zero fuzz.
The sealed base verifies {setup['verified_files']} files; clean application reproduces {touched['verified_result_files']} final files.
PATCH_CAMFORM2.patch SHA256: {sha(OUT/'PATCH_CAMFORM2.patch')}.
{a2line}

Focused tests: {values['UNIT.json']['tests']} pass, including all nine existing camera tests, six review regressions and 11 routing-subset tests.
The six review tests produce eight failure outcomes and two missing-counter errors on PATCH_CAMFORM; all six pass on PATCH_CAMFORM2.
All 6,000 authenticated source rows pass native checks, grammar, preservation checks and unchanged printed-answer recomputation.
Declaration mode binds the exact e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0 camera_wording source.
Composition admits {composition['composed_rows']:,} rows: 6,000 base rows plus all 5,979 delivered slice rows; deferred(cfg) is false.
With the field absent, rows.sqlite, membership.json and receipt.json are byte-identical to base+PATCH_A at the same output path.
Enabled counts are 2,000 rotation rows/lines and 1,996 direction rows/lines; all 5,979 slice rows and all 11,979 parallel target-column values remain unchanged.
All 5,979 base/slice counterpart targets match when enabled; {composition['matching_pairs_absent']:,} match when absent. Filters see the unrewritten base rows.
Filters are mocked to admit the extract; source binding, Rows.row checks and composition run natively. This proves composition behavior, not production admission.
MISSING: 21 delivered counterpart QIDs, listed in SOURCE_TESTS.json, expected at /scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl.

Full CPU suite on PATCH_A: base {a['tests_run']} tests, {a['failures']} failures, {a['errors']} errors, {a['skips']} skips; overlay {b['tests_run']} tests, {b['failures']} failures, {b['errors']} errors, {b['skips']} skips.
Nested headcall: base/new {h['base']['tests_run']}/{h['new']['tests_run']} tests, {h['base']['failures']}/{h['new']['failures']} failures, {h['base']['errors']}/{h['new']['errors']} errors, {h['base']['skips']}/{h['new']['skips']} skips.
Both comparisons introduce zero failing outcomes. Existing fixture/sandbox failures remain; the full suite is not green. TESTS.json and SUITE_FAILURES.json retain results and tracebacks.

Run commands from this workspace with prefix: `{prefix.rstrip()}`.
`code/setup.py` produces seal/file checks; `code/package_patch.py` produces patch/file/application counts; `code/package_A2.py` checks the conditional A2 delivery.
`code/regressions.py before` and `code/regressions.py after` produce the fail-before/pass-after counts; `code/unit.py` produces focused counts.
`code/validate_sources.py` produces source, native-check and counterpart counts; `code/compose_declaration.py A` produces all declaration-mode composition numbers.
`code/suite.py base` and `code/suite.py new` produce full-suite counts; `code/headcall_suite.py base` and `code/headcall_suite.py new` produce nested-suite counts.
`code/finalize.py` compares failing test IDs/outcome multiplicities and builds the archive. Every delivered evidence JSON records input SHA256 hashes.
'''
if a2['status']=='PASS' and a2['authentication']['mode']=='sha256_sealed_archive_and_exact_patch_member':report+='PATCH_A2 is authenticated by fbp_patchA2.tar.sha256 and byte equality with out/PATCH_A2.patch inside that archive.\n'
if a2['status']=='PASS':report+='`code/compose_A2.py` and `code/unit_A2.py` produce A2 composition and focused-test counts.\n'
report+='Verify the bundle with `sha256sum -c out/fbp_camform2.tar.sha256`. Controlled base/overlay comparisons are retained as evidence; no revision-history prose is retained.\n'
assert len(report.splitlines())<=50
(OUT/'REPORT.md').write_text(report)
(ROOT/'STATUS.md').write_text(f'The seven-file PATCH_CAMFORM2 overlay is complete and applies with zero fuzz. All 26 focused tests pass; declaration-mode composition of 11,979 rows preserves absent-field bytes and records 3,996 rewritten rows/lines. Both complete CPU comparisons introduce no failing outcome, while existing failures and sandbox restrictions remain. The A2 overlay status is {a2["status"]}. The final report, patches, authenticated test evidence and SHA256-sealed archive are in out/.\n')
for patch in OUT.glob('PATCH_CAMFORM2*.patch'):
    patch.with_name(patch.name+'.sha256').write_text(sha(patch)+'  out/'+patch.name+'\n')
# Package only review artifacts and reproducibility scripts, never bulky fixtures.
members=[ROOT/'STATUS.md',*sorted((ROOT/'code').glob('*.py'))]
members += [p for p in sorted(OUT.glob('*')) if p.is_file() and (p.suffix in ('.json','.md','.patch','.log') or p.name.endswith('.patch.sha256')) and p.name not in ('ARCHIVE.json','finalize.log')]
members += [OUT/x/'TEST_RESULTS.json' for x in ('suite_base','suite_new','headcall_base','headcall_new')]
for f in touched['files']:members.append(ROOT/'work/new'/f['path'])
archive_inputs={str(p):sha(p) for p in members}
(OUT/'ARCHIVE.json').write_text(json.dumps(dict(input_sha256=archive_inputs,command=command,members=[str(p.relative_to(ROOT)) for p in members]),indent=2)+'\n')
members.append(OUT/'ARCHIVE.json')
with tarfile.open(OUT/'fbp_camform2.tar','w') as tar:
    for p in members:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
hashval=sha(OUT/'fbp_camform2.tar');(OUT/'fbp_camform2.tar.sha256').write_text(hashval+'  out/fbp_camform2.tar\n')
size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file());assert size<=10_000_000_000,size
print(json.dumps(dict(report_lines=len(report.splitlines()),archive_sha256=hashval,archive_bytes=(OUT/'fbp_camform2.tar').stat().st_size,workspace_bytes=size,A2=a2['status'],comparisons=comparisons),indent=2))
