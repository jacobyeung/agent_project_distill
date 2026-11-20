import sys,json,errno
from pathlib import Path
value=json.loads(Path(sys.argv[1]).read_text())
sys.path[:0]=value['environment']['paths']
import q_overlay
assert q_overlay.value==226
for p in (Path(value['environment']['paths'][0])/'new',Path(sys.argv[2])/'new'):
 try:
  with p.open('w') as f:f.write('bad')
 except OSError as e:assert e.errno==errno.EROFS
 else:raise AssertionError('read-only binding lost')
(Path(value['root'])/'writable').write_text('ok')
print('MOUNTS PASS')
