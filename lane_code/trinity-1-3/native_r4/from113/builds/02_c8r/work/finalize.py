import ast,hashlib,io,json,tarfile
from pathlib import Path
from datetime import datetime,timezone
B=Path(__file__).resolve().parents[1]
def load(p):return json.loads((B/p).read_text())
def dump(p,v):(B/p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def sha(p):return hashlib.sha256((B/p).read_bytes()).hexdigest()
package=load('out/PACKAGE_STATUS.json');tests=load('out/tests/RESULT.json')
audit=load('out/PIN_AUDIT.json');cov=load('out/coverage/UNEXECUTED.json')
assert tests['passed'] and tests['failures']==tests['errors']==0
assert sha('out/c8r/code_c8r.tar')==package['code_sha256']
assert sha('out/c8r/FAMILY_C8R.json')==package['family_sha256']
for label,digest in package['diffs'].items():assert sha('out/C8R_DIFF_vs_'+label+'.patch')==digest
family=load('out/c8r/FAMILY_C8R.json');part=next(x for x in family['assets']['small_objects'] if x['role']=='code')
assert part['sha256']==package['code_sha256']
S=B/'out/c8r/sources';rebuilt=io.BytesIO()
with tarfile.open(fileobj=rebuilt,mode='w',format=tarfile.USTAR_FORMAT) as tf:
 for p in sorted(S.rglob('*')):
  if not p.is_file():continue
  name=str(p.relative_to(S));data=p.read_bytes()
  assert hashlib.sha256(data).hexdigest()==part['members'][name]['sha256']
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
  info.mode=0o755 if name.endswith(('/vnice/vnice.sh','/vnice/terminator.sh')) else 0o644
  tf.addfile(info,io.BytesIO(data))
assert hashlib.sha256(rebuilt.getvalue()).hexdigest()==package['code_sha256']
changed=load('out/CHANGED_LINES.json');c8r_missing={}
for name,missed in cov['uncovered_changed_lines'].items():
 rel=str(Path(name).relative_to(S))
 missing=set(changed.get(rel,{}).get('C8',[])) & set(missed)
 if missing:c8r_missing[rel]=sorted(missing)
assert not c8r_missing,c8r_missing
assert len(audit['rows'])==46 and set(r['status'] for r in audit['rows'])<={'PASS','PASS-REHEARSAL','ORCHARD-ONLY'}
assert load('out/OBJECT_AUDIT.json')['objects']['code']['sha256']==package['code_sha256']
for p in (B/'out/rehearsal').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
tests['tested_code_sha256']=package['code_sha256'];dump('out/tests/RESULT.json',tests)
verification=dict(archive_reproduced_byte_exact=True,source_members_match=True,all_c8r_changed_executable_lines_covered=True,
 code_sha256=package['code_sha256'],family_sha256=package['family_sha256'],coverage_gate_passed=False,
 unexecuted_c8_changed_lines=cov['missed_changed_count'],unexecuted_full_statements=cov['missed_full_count'])
dump('out/PACKAGE_VERIFICATION.json',verification)
listing=(B/'out/DIFF_FILES.md').read_text()
listing=listing.replace('- `camera/vnice/vnice.sh` and `camera/vnice/terminator.sh`: C8 packaging preserves executable archive modes.',
 '- `camera/vnice/vnice.sh`: C8 packaging preserves its executable archive mode.\n- `camera/vnice/terminator.sh`: C8 packaging preserves its executable archive mode.')
(B/'out/DIFF_FILES.md').write_text(listing)
owned=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not p.is_symlink())
assert owned<4_000_000_000
storage=dict(owned_bytes=owned,cap_bytes=4_000_000_000,inputs_read_only=True,
 no_shared_input_expansion=True,measurement='sum of regular non-symlink files under this build')
dump('out/STORAGE.json',storage)
now=datetime.now(timezone.utc)
result=dict(status='PACKAGED_FULL_VALIDATION_PENDING',utc=now.isoformat(),package=package,
 tests=tests,pin_counts=audit['counts'],coverage=verification,storage=storage,
 namespace=load('work/rh_pilot_01/RESULT.json'),sharding='REFUSED: production run/merge has no shard protocol; retained single-process path',
 runbook='out/rehearsal/RUNBOOK.md',decisions='out/DECISIONS.md',
 not_checked=['C8r whole-worker pilot','completed full serving/merge/admission/report/terminal rehearsal',
 'live Orchard pool quota and write probe','real GCS credentials/upload/generation readback',
 'GPU execution and runtime/base/export tensor authentication','new production REVIEW/ORDER/CONFIG/BATCH authority'])
dump('out/FINAL_RESULT.json',result)
(B/'STATUS.md').write_text(
 'C8r is packaged; full validation remains pending.\n\n'
 'Artifacts and hashes: `out/c8r/`, `out/PACKAGE_STATUS.json`. The archive reproduces byte-exactly (`out/PACKAGE_VERIFICATION.json`).\n\n'
 f"All {tests['tests']} tests pass (`out/tests/RESULT.json`). Every C8r changed executable line is covered; {cov['missed_changed_count']} C8 changed lines and {cov['missed_full_count']} full-worker statements remain unexecuted (`out/coverage/UNEXECUTED.json`). The coverage gate fails as required.\n\n"
 f"Pins: {audit['counts']['PASS']} PASS, {audit['counts']['PASS-REHEARSAL']} PASS-REHEARSAL, {audit['counts']['ORCHARD-ONLY']} ORCHARD-ONLY (`out/PIN_AUDIT.json`, `out/PIN_TABLE.md`).\n\n"
 'The sandbox blocked bwrap before staging (`work/rh_pilot_01/RESULT.json`). The harness retains single-process serving and refuses unsupported sharding (`out/SHARDING.md`). Operator commands are in `out/rehearsal/RUNBOOK.md`.\n\n'
 'Code generation and MD5 await upload; production authority, the new live return path, GPU execution, and completed full-mode evidence remain unchecked (`out/FINAL_RESULT.json`).\n')
lines=[
 'C8r is PACKAGED_FULL_VALIDATION_PENDING (`out/FINAL_RESULT.json`).',
 'Code: `out/c8r/code_c8r.tar`, SHA256 `'+package['code_sha256']+'`.',
 'Family: `out/c8r/FAMILY_C8R.json`, SHA256 `'+package['family_sha256']+'`.',
 'Diff against C8: `out/C8R_DIFF_vs_C8.patch`, SHA256 `'+package['diffs']['C8']+'`.',
 'Diff against pilot9: `out/C8R_DIFF_vs_pilot9.patch`, SHA256 `'+package['diffs']['pilot9']+'`.',
 'Exact receipt: `out/c8r/sources/sj/orch_cd/evalx/work/milestone/orchard_native/MASK_CACHE_C8_BOUND.json`, SHA256 `'+package['receipt_sha256']+'`.',
 f"Tests: {tests['tests']} passed, no failures or errors (`out/tests/RESULT.json`, `out/tests/results.log`).",
 f"Pins: {audit['counts']['PASS']} PASS; {audit['counts']['PASS-REHEARSAL']} PASS-REHEARSAL; {audit['counts']['ORCHARD-ONLY']} ORCHARD-ONLY (`out/PIN_TABLE.md`, `out/PIN_AUDIT.json`).",
 'The deterministic archive and all source/member pins match (`out/PACKAGE_VERIFICATION.json`).',
 'All C8r changed executable lines are covered by tests (`out/PACKAGE_VERIFICATION.json`).',
 f"Coverage gate FAIL: {cov['missed_changed_count']} C8 changed lines and {cov['missed_full_count']} full-worker statements remain unexecuted (`out/coverage/UNEXECUTED.json`).",
 'The pilot review maps only identical C8 source lines; no C8r whole-worker pass is claimed (`out/coverage/UNEXECUTED.json`).',
 'Namespace blocked before staging: bwrap could not create its route socket (`work/rh_pilot_01/RESULT.json`).',
 'Pilot command: run the exact operator command in `out/rehearsal/RUNBOOK.md` with `--mode pilot --shards 1 --dest "$PWD/work/rh_pilot_operator"`.',
 'Full command: run the exact operator command in `out/rehearsal/RUNBOOK.md` with `--mode full --shards 1 --dest "$PWD/work/rh_full_operator"`.',
 'Sharded command: `--mode full --shards "$N" --dest "$PWD/work/rh_full_sharded"`; unsupported counts refuse before staging (`out/rehearsal/RUNBOOK.md`, `out/SHARDING.md`).',
 'Coverage uses parallel filenames and combine with input preservation; no sharded serving merge occurred (`out/rehearsal/RUNBOOK.md`, `out/tests/RESULT.json`).',
 'Defaults: independent verified return channels, bounded anonymous pool probe, exact mask bytes, read-only shared inputs, single-process serving (`out/DECISIONS.md`).',
 'Durable return-proof sidecars carry generation and SHA256 evidence; cloud tests used an offline CLI (`out/tests/results.log`).',
 f'Owned bytes: {owned}; build cap: 4000000000 (`out/STORAGE.json`).',
 'Code generation and MD5 remain PENDING_UPLOAD (`out/PACKAGE_STATUS.json`).',
 'Not checked: live Orchard quota/write probe, real GCS credentials, GPU/runtime/base/export tensor checks, new production authority, and completed full rehearsal (`out/FINAL_RESULT.json`).',
 'No network, remote session, GPU job, Git operation, other agent, or write outside this build was used.',
]
assert len(lines)<=40
existing=list((B/'events').glob('*_RESULT_final.md'))
assert len(existing)<=1
event=existing[0] if existing else B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_final.md')
event.write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status=result['status'],tests=tests['tests'],pins=audit['counts'],event=str(event),owned_bytes=owned)))
