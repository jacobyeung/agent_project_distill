from common import *
# Keep exact first-run outputs and all fixture artifacts.
a=L/'attic/build24m4j/suites_first';a.mkdir()
for name in ('arming_final','review_negatives','resolver','proofs','guard_q','guard_n','native_arm'):
 p=D/name
 if p.exists():p.rename(a/name)
for p in list(D.glob('*.log')):
 if p.name not in ('inputs_audit.log','scan_fix.log'):p.rename(a/p.name)
p=D/'TEST_RUNS.json';p.rename(a/p.name)
for n in ('guard_q','guard_n'):(D/n).mkdir()
H=L/'work/build24m4h'
for name in ('integration.py','offline.py','namespace_test.py'):
 s=(H/name).read_text().replace('work/build24m4h','work/build24m4k')
 if name=='offline.py':
  s=s.replace("J.sha(D/'p.tar')","J.sha(L/'work/build24m4h/p.tar')")
 (D/name).write_text(s)
(D/'CONFIG_INPUTS.json').write_bytes((H/'CONFIG_INPUTS.json').read_bytes())
# This function reads data only, never imports a superseded workspace.
p=D/'common.py';s=p.read_text().replace('L/"work/build24m4d/upload/u"):', 'L/"work/build24m4d/upload/u",W/"w24g/work/build24m4g/inputs",W/"w24/work/build24m4/hidden/inputs",W/"w24/work/build24m3/hidden/inputs",W/"w24/work/build24m3/hidden/payload"):');replace(p,s)
