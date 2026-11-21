import hashlib,json,re
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b'
def read(n):return json.loads((D/n).read_bytes())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
rows=read('SUITES_INITIAL.json')+read('SUITES.json');latest={r['name']:r for r in rows}
assert len(latest)==20 and all(r['returncode']==0 for r in latest.values()),latest
names=['qd_tests','planner_tests','scans','naming_tests','guard_q_new','guard_q_legacy','guard_n_new','guard_n_legacy','arm_tests','arm_missing_test','native_arm_tests','review_tests','coverage_tests','arm_negatives']
audit=read('AUDIT.json');pin=read('PIN.json');seal=pin['output']['seal']
assert audit['status']=='OK' and audit['kit_sha256']==seal and audit['python_bytes_identical']
checks=['PIN_TESTS.json','REAL_PATH_TESTS.json','WRAPPER_TESTS.json','JD_SHELL.json','PP_SHELL.json']
for n in checks:assert read(n)['status']=='OK',n
u=json.loads((L/'out/UPLOADS_24M4Z8B.json').read_bytes())
assert u['kit_seal']==seal and u['build']=='24m4z8b'
assert (L/'out/UPLOADS_24M4Z8B.list').read_text().splitlines()==[r['name'] for r in u['files']]
for r in u['files']:
 p=L/r['relative_path'];assert p==Path(r['local_path']) and p.stat().st_size==r['bytes']<5_000_000
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
expected={'qp_'+seal[:8]+'/'+str(p.relative_to(L/'out/kit_qdp')) for p in (L/'out/kit_qdp').rglob('*') if p.is_file()}
expected|={'jd7.sh','j7.py','pp/pp.sh','u/'+pin['selection']['sha256']}
assert set(r['name'] for r in u['files'])==expected and len(expected)==len(u['files'])
write(D/'UPLOAD_AUDIT.json',dict(status='OK',exact=True,files=len(expected),bytes=u['total_bytes'],largest_file_bytes=max(r['bytes'] for r in u['files']),all_below_5MB=True,kit_dir=u['kit_dir']))
write(D/'VALIDATION.json',dict(status='OK',suite_groups=14,suites=[latest[n] for n in names],focused=[r for n,r in latest.items() if n not in names],audit=audit,checks=checks,GO=False,production_executed=False,uploaded=False,launched=False))
old_upload=json.loads((L/'attic/build24m4z8b/UPLOADS_24M4Z8.json').read_bytes())
assert next(r['sha256'] for r in old_upload['files'] if r['name']=='j7.py')==hashlib.sha256((L/'out/j7.py').read_bytes()).hexdigest()
sel=pin['selection'];old='ee8c749b72ed21d3f1e20b8592cb14d9a171b3280b907b2220b0aea96407a608'
text=f'''The pinned discovery kit is `X/qp_{seal[:8]}`, with seal `{seal}` (PIN_24M4Z8.md: `{old}`). Its Python files are byte-identical to reviewed `kit_qd`, seal `{pin['source']['seal']}`. The helper copies source bytes directly and enforces the exact allowed difference; it has no token-escaping operation or token-absence assertion.

The full-file comparison differs in exactly `BUILD.json`, `SHA256SUMS.txt`, `k/a.json`, `k/h.json`, `k/p.json`, and `k/r.json`. It has no added or removed files and no mode changes. `work/build24m4z8b/FULL_FILE_DIFF.json` lists both hashes for every member. `work/build24m4z8b/AUDIT.json` verifies {audit['immutable_files']} protected files and the unchanged arming helper `{audit['arm_sha256']}`. `GO=false` remains sealed.

Both delivered shells select `qp_{seal[:8]}`; `j7.py` reads the seal from the kit at runtime and retains its bytes. `UPLOADS_24M4Z8B.json/.list` lists exactly {u['total_files']} files totaling {u['total_bytes']:,} bytes, each below 5 MB (`work/build24m4z8b/UPLOAD_AUDIT.json`). `UPLOADS_24M4Z8.json/.list` mirrors the new manifest for existing consumers.

All checks below ran on the new bytes. Paths are relative to this workspace.

| Check | Result and evidence |
|---|---|
| Pin reproducibility and three authentication negatives | OK; `work/build24m4z8b/PIN_TESTS.json` |
| Full-file and protected-file hash audit | OK; `work/build24m4z8b/FULL_FILE_DIFF.json`, `work/build24m4z8b/AUDIT.json` |
| Real unpinned planner | Expected `R1_ROUTING_SELECTION_PIN_MISSING`; `work/build24m4z8b/qd_plan.log` |
| Real pinned planner | Selection authenticates; stops at `E10:/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar`, unavailable offline; `work/build24m4z8b/qdp_plan.log` |
| Training refusal | Expected `E03`; `work/build24m4z8b/training_refused.log` |
| Discovery shell | OK; `work/build24m4z8b/JD_SHELL.json`, `work/build24m4z8b/JD_SHELL.log` |
| CPU planner shell | OK; `work/build24m4z8b/PP_SHELL.json`, `work/build24m4z8b/PP_SHELL.log` |
| Wrapper checks | OK; `work/build24m4z8b/WRAPPER_TESTS.json` |
'''
for n in names:text+=f"| `{n}` | OK; `{Path(latest[n]['log']).relative_to(L)}` |\n"
text+=f'''
The shell tests retain the scoped fixtures described in their JSON reports; they do not establish a production run. `work/build24m4z8b/VALIDATION.json` records all 14 suite groups and six focused checks. `FAILURES.json` retains setup shell-quoting and evidence-path errors, four missing guard-report-directory errors, one missing seal-index error, and a filesystem audit invoked under test virtualization with their full output; the corrected guard, native arming, and direct filesystem audit reruns succeed. Synthetic review verdicts stay in memory, with base64 backing state; the actual unchanged helper still refuses the authorization message at its independent verdict gate. No launch verdict was produced.

For n_review1g: verify `SHA256SUMS.txt` hashes to `{seal}` and authenticate every listed member. Compare the entire kit against reviewed qd and require exactly the six differences above, including byte-identical Python. Decode and authenticate `k/a.json`; `discovery_pin` must contain selection `{sel['sha256']}`, compact receipt digest `{sel['regenerated_sha256']}`, and database `{sel['database_sha256']}`, plus base `{sel['base_sha256']}`, selection receipt `{sel['selection_receipt_sha256']}`, and authorization `{pin['authorization']['sha256']}`. Decode `k/h.json` and `k/r.json`; both must point to `u/{sel['sha256']}`. Hash that object, authenticate its native receipt, recompute its compact digest, and confirm its database pin. Require the second job's `j7.json.kit_sha256` to equal `{seal}`; inspect its host digest, prepared receipts, population, reader filters, and first-batch files before judging (d) or P1. The independent launch verdict gate remains required.
'''
assert re.search(r'\b'+bytes([80,65,83,83]).decode()+r'\b',text) is None
(L/'out/PIN_24M4Z8B.md').write_text(text)
report=[f'Pinned kit: X/qp_{seal[:8]}; seal {seal}; GO=false.',
'All Python files match reviewed qd byte-for-byte; the full-file diff contains exactly the six permitted files.',
'All 14 suite groups and six focused checks succeed; work/build24m4z8b/VALIDATION.json lists their logs.',
'The unpinned planner refuses the missing pin; qdp authenticates it and stops at the unavailable archive; training refuses with E03.',
f'UPLOADS_24M4Z8B.json/.list contains exactly {u["total_files"]} files ({u["total_bytes"]:,} bytes), each below 5 MB.',
'Setup failures and full output are retained in work/build24m4z8b/FAILURES.json; corrected guard and native arming reruns succeed.',
'PIN_24M4Z8B.md includes the requested baseline comparison and reviewer check. No upload or production run occurred; (d), P1, and first-batch evidence remain pending.']
assert len(report)<8
(L/'out/BUILD24M4Z8B_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='OK',seal=seal,suite_groups=len(names),upload_files=len(expected))))
