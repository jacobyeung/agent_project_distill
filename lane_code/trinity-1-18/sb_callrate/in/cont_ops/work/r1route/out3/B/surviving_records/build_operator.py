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
                    '7.py':(O/'tower_sequence.py').read_bytes()})
(P/'BATCH.sh').write_text(build.batch(bundle,public['token']))
(P/'a').mkdir(exist_ok=True)
for src,dst in [('tower_sequence.py','6.py'),('node_check.py','5.py')]:
 (P/'a'/dst).write_bytes((O/src).read_bytes())
manifest=json.loads((P/'PACKAGE.json').read_text());manifest['files']['BATCH.sh']=sha(P/'BATCH.sh');
for n in ('a/5.py','a/6.py'):manifest['files'][n]=sha(P/n)
write(P/'PACKAGE.json',manifest)
sys.path.insert(0,str(O));import tower_sequence as sequence
plan=json.loads((O/'original/READ_PLAN.json').read_text())
plan.update(token=public['token'],plan_sha256=public['plan_sha256'],
            operator_sha256=sha(O/'tower_sequence.py'),operator_path='7.py')
plan['cpu_check']={**plan.get('cpu_check',{}), 'partition':'preempt', 'cpus':8,
    'memory':'200G','walltime':'04:00:00','gpus':0,'exclude':'orchard-flame-[0-31]',
    'results':'a/c/CPU.json','required_flags':['passed','bundle_guard_passed','entry_sequence_passed']+
        (['full_reader_passed','full_reader.passed'] if 'full_reader_passed' in (O/'node_check.py').read_text() else []),
    'helper_sha256':sha(O/'node_check.py'),'bootstrap_sha256':sha(O/'tower_bootstrap.py')}
write(O/'READ_PLAN.json',plan)
(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())

print(json.dumps(dict(batch=sha(P/'BATCH.sh'),package=sha(P/'PACKAGE.json'),operator=sha(O/'tower_sequence.py'))))

(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())
