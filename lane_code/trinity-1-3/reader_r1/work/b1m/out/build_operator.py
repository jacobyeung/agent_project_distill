"""Seal the operator wrapper into the production batch descriptor."""
from pathlib import Path
import json,sys,hashlib
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O/'src'))
from orchard_h10 import build
from orchard_h10.common import template,sha,write
build.T=O/'src/orchard_h10/vendor';template(build.T)
import orchard_launcher as L
P=O/'package';public=json.loads((P/'0.json').read_text())
bundle=L.tar_bytes({'0.py':(O/'tower_bootstrap.py').read_bytes(),'0.json':(P/'0.json').read_bytes(),
                    '6.py':(O/'tower_sequence.py').read_bytes()})
(P/'BATCH.sh').write_text(build.batch(bundle,public['token']))
(P/'a').mkdir(exist_ok=True)
for src,dst in [('tower_sequence.py','6.py'),('node_check.py','5.py')]:
 (P/'a'/dst).write_bytes((O/src).read_bytes())
manifest=json.loads((P/'PACKAGE.json').read_text());manifest['files']['BATCH.sh']=sha(P/'BATCH.sh');
for n in ('a/5.py','a/6.py'):manifest['files'][n]=sha(P/n)
write(P/'PACKAGE.json',manifest)
write(O/'READ_PLAN.json',dict(token=public['token'],operator_sha256=sha(O/'tower_sequence.py'),
  sequence=[[0,3],[1,3],[0,0],[0,1],[0,2],[0,4]],expected=[636,150],arms=['tower'],modes=['none'],
  rules=['null_argmax','candidates_argmax'],perception_memo='verify first 30 scheduled reads, then on',
  memo_max_bytes=64*1024**3,memo_scope='one worker per segment',
  read_settings=[dict(stage1_select_rule='null_argmax',perception_memo='verify',perception_memo_verify_reads=30,perception_memo_verify_types=['object_abs_distance']),
                 dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_verify_reads=None,perception_memo_verify_types=None)],save_own_depth=False,walltime='05:00:00',stop_margin=1800,return_margin=1200))
print(json.dumps(dict(batch=sha(P/'BATCH.sh'),package=sha(P/'PACKAGE.json'),operator=sha(O/'tower_sequence.py'))))
