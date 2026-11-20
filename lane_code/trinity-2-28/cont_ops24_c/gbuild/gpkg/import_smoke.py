"""Import the delivered payload in fresh CPU processes, without model loads."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import build

CHILD = r'''
import importlib, importlib.util, json, sys
from pathlib import Path
p, package, mode = map(Path, sys.argv[1:4])
sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
import torch
from orchard_h10.common import install_process_guard
import g.w as w
if str(mode) == 'fixed':
    w.bind_reader_root()
from h1eval.h10.parity_adapter import settings_for, artifact_spec, prepare_runtime, make_capped_real
settings_path=package/'smoke_settings.json'
settings_path.write_text(json.dumps(dict(tree=str(p/'tree'),perception_memo='verify',
                                       perception_memo_modules=['g3t'],perception_memo_verify_ids=[])))
prepare_runtime(settings_for(settings_path,'devs1_routed'))
from e2e_reader import parity
from student_pilot.carrier_c1_decode import _prepare_decode
from student_pilot.ground_context import closed_adapters
from e2e_reader.artifact import Audit
from e2e_reader.generate import EntryCounter
from e2e_reader import stage1, grounding
from h1eval.items import digest
from h1eval.h10.parity_adapter import MaxCalls, PER_READ_CALL_CAP
for name in ('orchard_h10.common', 'orchard_h10.runner', 'orchard_h10.prepare',
             'orchard_h10.job', 'orchard_h10.operator'):
    importlib.import_module(name)
spec = importlib.util.spec_from_file_location('delivered_dispatch', package/'a/6.py')
dispatch = importlib.util.module_from_spec(spec); spec.loader.exec_module(dispatch)
dispatch.prepare(dict(package=str(p),output=str(package/'smoke_output'),settings=str(settings_path),
                      plan_sha256='0'*64,inputs_sha256='1'*64,operator_sha256='2'*64))
from e2e_reader.perception_memo import settings
if (p/'g/pw.py').exists():
    for name in ('g.pw', 'g.geometric', 'g.point_socket', 'g.restricted'):
        importlib.import_module(name)
w.assert_reader_root(p/'b')
files = {k:v.__file__ for k,v in sys.modules.items()
         if k == 'e2e_reader' or k.startswith('e2e_reader.')}
print(json.dumps(dict(passed=True, python=sys.executable, torch=torch.__version__, reader_files=files)))
'''

OPERATOR = r'''
import json, runpy, sys
from pathlib import Path
p, package = map(Path,sys.argv[1:3])
operator=runpy.run_path(str(p/'8.py'))
config=operator['load_helpers'](package)
from orchard_h10.job import check_inputs
check_inputs(json.loads((package/'a/1.json').read_text()),config,package=package)
print(json.dumps(dict(passed=True,stdlib_only=True,token=config['token'])))
'''


def smoke(delivery, mode='fixed', python=sys.executable):
    root = Path(tempfile.mkdtemp(prefix='imports_', dir=build.ROOT/'work'))
    build.extract(Path(delivery).read_bytes(), root/'package')
    build.extract((root/'package/0.tgz').read_bytes(), root/'p')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
               MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    child = subprocess.run([str(python), '-B', '-I', '-c', CHILD, str(root/'p'),
                            str(root/'package'), mode], env=env, text=True,
                           capture_output=True, timeout=120)
    operator = subprocess.run([str(python),'-B','-I','-S','-c',OPERATOR,str(root/'p'),str(root/'package')],
                              env=env,text=True,capture_output=True,timeout=30)
    return dict(delivery=str(delivery), delivery_sha256=build.sha(Path(delivery).read_bytes()),
                mode=mode, python=str(python), extraction=str(root),
                returncode=child.returncode or operator.returncode, stdout=child.stdout, stderr=child.stderr,
                operator=dict(returncode=operator.returncode,stdout=operator.stdout,stderr=operator.stderr))


def main():
    p=argparse.ArgumentParser(); p.add_argument('delivery',type=Path)
    p.add_argument('--mode',choices=['fixed','legacy'],default='fixed')
    p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    result=smoke(a.delivery,a.mode); a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result['returncode']


if __name__=='__main__':raise SystemExit(main())
