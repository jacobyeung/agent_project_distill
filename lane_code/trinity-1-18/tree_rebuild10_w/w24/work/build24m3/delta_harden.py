from common import *
p=L/'out/bind_protected.py';s=p.read_text()
s=s.replace("  control=load(k/'k/a.json')","""  expected={n:h for h,n in (line.split('  ',1) for line in (k/'SHA256SUMS.txt').read_text().splitlines())}
  actual={str(p.relative_to(k)):sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
  if expected!=actual or load(k/'BUILD.json')['kit_sha256']!=sha(k/'SHA256SUMS.txt'):raise ValueError('R1_KIT_CONTENT_DIFFERS')
  control=load(k/'k/a.json')""")
s=s.replace("target=delivery/name/rel;target.parent.mkdir(parents=True,exist_ok=True);os.link(p,target)","target=(delivery.with_name(delivery.name+'_go')/'n'/rel) if name=='n_go' else (delivery/name/rel);target.parent.mkdir(parents=True,exist_ok=True);os.link(p,target)")
replace(p,s,0o755)
# Use the existing fixture as the next baseline, adding a distinct fixture key.
s=(D/'delta_tests.py').read_text()
a=s.index("F=D/'delta_fixture'")
b=s.index("tree_before=",a)
s=s[:a]+"""F=D/'delta_fixture'
role=F/'pose_second.jsonl';role.write_text('{"row_key":"pose-second-fixture"}\\\\n'.replace('\\\\\\\\n','\\\\n'))
"""+s[b:]
s=s.replace("pose-protected-fixture","pose-second-fixture")
# Supply the first fixture role list too; the native validator authenticates both.
s=s.replace("paths[J.sha(role)]=str(role)","paths[J.sha(role)]=str(role);paths[J.sha(F/'pose.jsonl')]=str(F/'pose.jsonl')")
s=s.replace("D/'DELTA_TESTS.json'","D/'DELTA_FINAL_TESTS.json'")
(D/'delta_final_tests.py').write_text(s)
