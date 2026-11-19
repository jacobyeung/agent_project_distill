import json,subprocess,sys,time
from pathlib import Path
src=Path('/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/a');sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
from orchard_h10 import runner
from orchard_h10.common import ORDER
config=dict(package=str(src),output='/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/r',python=sys.executable,plan_sha256='9ec160bae333260cdeff58816f72781b4ca4403d2406fcb9618c2948002730d5',
            inputs_sha256='0'*64,device='cpu',types=[],
            arms=['tower'],modes=['none'],stop_margin=0,return_margin=0,
            perception_memo='on',perception_memo_modules=['g3t'],
            perception_memo_verify_ids=[],stage1_select_rule='candidates_argmax')
config.update(export=str(src/'e'),binding=str(src/'b.json'),export_pin=str(src/'p.json'))
op=__import__('runpy').run_path('/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/a15_cot_apd45befa4edc73/a/6.py',run_name='pack_probe')
spec=op['descriptors'](str(src))[0]
config['types']=[ORDER[t] for t in spec['types']]
# prepare() identifies the real item input without loading any weights.
settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
              perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
Path('/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/settings.json').write_text(json.dumps(settings));config.update(settings='/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/settings.json',operator_sha256='f56faeee50825d76a652078a93cfef952b83dcb7613175a821ecca3d0bf59994')
prepared=op['prepare'](config)[0];config=prepared
config.update(stop_margin=0,return_margin=0)
def launcher(argv,**kw):
    cfg=json.loads((Path(kw['cwd'])/argv[-1]).read_text())
    actual=runner.worker_args(cfg);marker=actual[actual.index('--stop-file')+1]
    return subprocess.Popen([sys.executable,'-I','-s','-B','/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/1.py',marker,'/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/0.ready','/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/0.end'],**kw)
summary=runner.run(config,[''],time.time()+60,launcher=launcher)
Path('/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/summary.json').write_text(json.dumps(summary))
if summary.get('failure') or not summary.get('stopped') or not Path('/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a5/0.end').exists():
    raise ValueError('Native runner stop/end proof failed')
print('NATIVE_STOP_PASS')
