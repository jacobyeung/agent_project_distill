from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
s=(L/'work/build24g/copier_tests.py').read_text().split("old=load(")[0]
s=s.replace("D=L/'work/build24g'","D=L/'work/build24k'")
s=s.replace("root/'live_target';target.mkdir()","project")
s=s.replace("alternate=root/'alternate';alternate.mkdir(mode=0o700)","alternate=project/'n_s'")
s=s.replace("from live_tests import WRITER","from live_tests import WRITER")
exec(compile(s,str(D/'session_tests.py'),'exec'))
C=load(L/'work/build24/kits/n/b/pc.py','sessions24h')
records=[]
for label,mutation in [('default',None),('mode','file mode'),('symlink','file symlink'),('missing','file missing'),('object','not an object'),('dir_mode','directory mode'),('dir_owner','directory owner'),('regular','file not regular'),('json','invalid JSON'),('mapping','invalid mapping'),('url','invalid URL')]:
 records.append(case(C,'sessions',label,mutation))
records.append(case(C,'sessions','explicit',override=True))
records.append(case(C,'sessions','env_ignored',envhome=True))
assert all(v['expected_pass'] for v in records)
(D/'SESSION_TESTS.json').write_text(json.dumps(dict(status='PASS',records=records),indent=2)+'\n')
print('13 session tests PASS; no value leaks')
