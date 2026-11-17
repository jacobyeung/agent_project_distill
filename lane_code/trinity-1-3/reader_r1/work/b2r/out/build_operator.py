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
sys.path.insert(0,str(O));import tower_sequence as sequence
write(O/'READ_PLAN.json',dict(token=public['token'],operator_sha256=sha(O/'tower_sequence.py'),
  plan_sha256=public['plan_sha256'],item_set_sha256=json.loads((O/'src/items/room134.json').read_text())['item_set_sha256'],
  item_keys=(O/'ITEM_KEYS.txt').read_text().splitlines(),sequence=sequence.SCHEDULE,expected=[134],arms=['tower'],modes=['none'],
  rules=sequence.RULES,read_settings=sequence.descriptors(O/'src'),memo_scope='one worker per read',
  cpu_check=dict(partition='general',cpus=8,memory='200G',walltime='04:00:00',gpus=0,
    sets=['dev-S1','R0-dev'],scope='First item of each set through full reader with CPU model stubs after staging and export restore',
    results='a/c/CPU.json',pass_flag='full_reader_passed',records='full_reader.records',
    helper_sha256=sha(O/'node_check.py'),bootstrap_sha256=sha(O/'tower_bootstrap.py')),
  item_file='items/room134.json',types=['room_size_estimation'],settings=dict(arm='tower',mode='none',stage1_select_rule='null_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['room_size_estimation']),save_own_depth=False,walltime='02:30:00',stop_margin=1800,return_margin=1200))

print(json.dumps(dict(batch=sha(P/'BATCH.sh'),package=sha(P/'PACKAGE.json'),operator=sha(O/'tower_sequence.py'))))

(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())
