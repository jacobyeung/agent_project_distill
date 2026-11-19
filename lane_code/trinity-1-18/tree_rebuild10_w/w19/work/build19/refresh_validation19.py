from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build19'
p=B/'mutations19.py';s=p.read_text()
s=s.replace("if banks & set(SCOPE) or not artifact.get('component_evidence'):","if banks & set(SCOPE) or not deferred_export:")
case=('dev_scope','student_pilot/r2_policy.py','if banks & set(SCOPE) or not deferred_export:',
      'if banks & set(SCOPE):','tests.test_r1_build19.Components19.test_official_and_dev_actual_gateway')
s=s.replace('cases=[','cases=['+repr(case)+',',1)
p.write_text(s)
# Fresh final kits retain the earlier owned directory without modifying its files.
p=B/'kits'
if p.exists():p.rename(B/'retained_kits19')
(B/'STATUS.md').write_text('Build 19: GO=false. The dev exception now requires a native N export with a DEFERRED slot. The affected gateway tests and final source qualification are being refreshed. The native population capacity refusal remains unchanged.\n')
