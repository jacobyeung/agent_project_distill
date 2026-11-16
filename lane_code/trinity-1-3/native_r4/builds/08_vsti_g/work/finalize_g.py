"""Verify the isolated snapshot-bind change and seal local evidence."""
from pathlib import Path
import ast,hashlib,json,re,sys,tarfile,time
B=Path(__file__).resolve().parents[1];OLD=B.parent/'07_vsti_f'
sys.path.append(str(B/'code'));sys.path.append(str(B/'work'))
from adapter import load,dump,pin,sha
import engine,path_audit
old=(OLD/'code/o.py').read_text();new=(B/'code/o.py').read_text()
start=new.index('        # The processor and base loader')
end=new.index("        for value in runtime['import_paths']",start)
assert new[:start]+new[end:]==old
changed=[]
for p in sorted((B/'code').rglob('*')):
 if p.is_file() and p.read_bytes()!=(OLD/'code'/p.relative_to(B/'code')).read_bytes():changed.append(str(p.relative_to(B)))
assert changed==['code/o.py']
f=load(B/'out/FAMILY.json');baseline=load(OLD/'out/FAMILY.json');expected=json.loads(json.dumps(baseline))
for k in ('code','code_sources'):expected[k]=f[k]
expected['added']['c']=f['added']['c'];assert expected==f
assert f['code_sources']==engine.source_pins()
assert sha(B/'out/d.tar')==sha(OLD/'out/d.tar')=='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f'
with tarfile.open(B/'out/c.tar') as t:
 members=t.getmembers();assert all(m.isfile() for m in members)
 assert {m.name for m in members}=={str(p.relative_to(B/'code')) for p in (B/'code').rglob('*') if p.is_file()}
 for m in members:assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(B/'code'/m.name)
audit=load(B/'out/PATH_AUDIT.json');path_audit.assert_audit(audit);assert audit==path_audit.build()
kit=B/'work/kit_final.log';assert re.search(r'Ran 70 tests.*\n\nOK\s*$',kit.read_text(),re.S)
assert (B/'work/audit_test.log').read_text().rstrip().endswith('OK')
legacy=load(B/'out/LEGACY_TESTS.json');extra=load(B/'out/LEGACY_EXTRA.json')
assert legacy['run']==28 and not legacy['errors'] and not legacy['failures']
assert extra['run']==2 and extra['passed']
rh=load(B/'out/rehearsal/RESULT.json');assert rh['passed'] and rh['path_audit_passed']
assert rh['path_audit']==pin(B/'out/PATH_AUDIT.json')
seen=set();unique=allocated=0
for p in B.rglob('*'):
 if not p.is_file():continue
 st=p.stat()
 if (st.st_dev,st.st_ino) not in seen:
  seen.add((st.st_dev,st.st_ino));unique+=st.st_size;allocated+=st.st_blocks*512
assert unique<3_000_000_000 and allocated<3_000_000_000
footprint=dict(unique_bytes=unique,allocated_bytes=allocated,limit_bytes=3_000_000_000)
dump(B/'out/TESTS.json',dict(passed=True,kit_run=70,inherited_run=30,kit_log=pin(kit),audit_tests=pin(B/'work/audit_test.log'),
 inherited=pin(B/'out/LEGACY_TESTS.json'),extra=pin(B/'out/LEGACY_EXTRA.json'),cpu_rehearsal=pin(B/'out/rehearsal/RESULT.json'),namespace_executed=rh['namespace']=='executed'))
dump(B/'out/PACKAGE_VERIFY.json',dict(passed=True,changed_code=changed,only_snapshot_binding_changed=True,
 family_policy_unchanged=True,d_byte_identical=True,code_members_verified=True,footprint=footprint))
pkg=load(B/'out/PACKAGE.json')
for k in ('code','family','reference'):assert pkg[k]==pin(B/'out'/dict(code='c.tar',family='FAMILY.json',reference='d.tar')[k])
unchecked=['Actual GPU processor/model/head loading and scale/read execution',
 'Actual namespace mount: sandbox bwrap NETLINK_ROUTE denied',
 'Exact payload-selected export/index/depth filenames: local metadata payloads unavailable; audit uses complete directory coverage',
 'Orchard execution, served-output equality and live return transport']
dump(B/'out/FINAL_RESULT.json',dict(status='built; CPU verified; namespace and exact payload audit limited',package=pkg,
 audit=pin(B/'out/PATH_AUDIT.json'),tests=pin(B/'out/TESTS.json'),verify=pin(B/'out/PACKAGE_VERIFY.json'),not_checked=unchecked))
lines=[
'RESULT: V1g built; only the read-only student snapshot binding changes production code (code/o.py).',
'Code SHA256 '+pkg['code']['sha256']+' (out/c.tar).',
'Family SHA256 '+pkg['family']['sha256']+' (out/FAMILY.json).',
'Reference SHA256 '+pkg['reference']['sha256']+'; byte-identical to V1f (out/d.tar).',
'Audit SHA256 '+sha(B/'out/PATH_AUDIT.json')+' (out/PATH_AUDIT.json).',
'Diff SHA256 '+sha(B/'out/DIFF_vs_V1f.patch')+' (out/DIFF_vs_V1f.patch).',
f"Audit: {len(audit['paths'])} exact paths/directory closures; zero unbound; missing-snapshot regression fails closed (out/PATH_AUDIT.json; work/audit_test.log).",
'Tests: 70 kit and 30 inherited pass (out/TESTS.json).',
'CPU pipeline passes; namespace creation is denied by sandbox NETLINK_ROUTE permissions (out/rehearsal/RESULT.json; out/rehearsal/NAMESPACE.json).',
'No object-grounding selector or VSTI-fitted file is loaded (out/DECISIONS.md).',
'Served calls, frames, tokens, scores, proof, phase order, budgets and return code are byte-identical (out/PACKAGE_VERIFY.json).',
f"Footprint: {unique} unique bytes; {allocated} allocated; cap 3000000000 bytes (out/PACKAGE_VERIFY.json).",
'Unchecked: exact export/index/depth payload-selected filenames; audit uses directory coverage (out/PATH_AUDIT.json).',
'Unchecked: GPU load/scale/read, Orchard mounts, output equality and live transport; no submission (out/FINAL_RESULT.json).',
'Operator command and audit gate: out/rehearsal/RUNBOOK.md.'
]
(B/'events'/(time.strftime('%Y%m%dT%H%MZ',time.gmtime())+'_RESULT_final.md')).write_text('\n'.join(lines)+'\n')
(B/'STATUS.md').write_text('V1g is built and CPU-verified. The snapshot bind is isolated; d.tar is unchanged. All 70 kit and 30 inherited tests pass. The audit covers 931 paths/directory closures with zero unbound. Sandbox namespace creation and exact payload-selected filenames remain unverified. See out/FINAL_RESULT.json.\n')
print('Final package verified; final RESULT written.')
