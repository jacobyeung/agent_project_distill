from common import *
import runpy
for name in ('rd_mount','RDIFF_MOUNT_TEST.log'):
 p=D/name
 if p.exists():
  q=L/'attic/build24m4m/fixture_attempt2'/name;q.parent.mkdir(parents=True,exist_ok=True);p.rename(q)
runpy.run_path(str(D/'rdiff_mount_test.py'),run_name='__main__')
