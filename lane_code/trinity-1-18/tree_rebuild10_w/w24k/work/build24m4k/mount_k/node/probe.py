import sys,json,errno,os
from pathlib import Path
root=Path(sys.argv[-2]);target=Path('/project/community/jjyeung/okh7/x_22c714e1/o/123')
assert Path('/dev/null').exists() and Path('/proc/self/maps').is_file()
assert Path('/tmp/q_22c714e1').is_dir()
for p in (target/'x',root/'f/x',Path('/project/community/jjyeung/c7d31ddd/x')):
 try:p.write_text('bad')
 except OSError as e:assert e.errno==errno.EROFS,(p,e)
 else:raise AssertionError('read-only mount lost: '+str(p))
(root/'ok.json').write_text(json.dumps(dict(status='PASS',devices=True,proc=True,target_readonly=True,sites_readonly=True,root_writable=True)))
print('ACTUAL_LAUNCH_MOUNTS_PASS')
