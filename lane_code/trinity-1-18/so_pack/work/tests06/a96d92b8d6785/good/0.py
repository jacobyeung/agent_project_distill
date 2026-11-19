import json,subprocess,sys,time
from pathlib import Path
src=Path('/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/a');sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
from orchard_h10 import runner
from orchard_h10.common import ORDER
config=dict(package=str(src),output='/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/r',python=sys.executable,plan_sha256='3d6ddc47f1968c24b5b997448084910d4d8962942fa7a1347942f7cb1b0b0248',
            inputs_sha256='0'*64,device='cpu',types=[],
            arms=['tower'],modes=['none'],stop_margin=0,return_margin=0,
            perception_memo='on',perception_memo_modules=['g3t'],
            perception_memo_verify_ids=[],stage1_select_rule='candidates_argmax')
config.update(export=str(src/'e'),binding=str(src/'b.json'),export_pin=str(src/'p.json'))
op=__import__('runpy').run_path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/package/a/6.py',run_name='pack_probe')
spec=op['descriptors'](str(src))[0]
config['types']=[ORDER[t] for t in spec['types']]
# prepare() identifies the real item input without loading any weights.
settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
              perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
Path('/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/settings.json').write_text(json.dumps(settings));config.update(settings='/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/settings.json',operator_sha256='247f8cdfd507c2655adb5e68169c1cb198800c7bb24ef3ac4f9d7352404b34af')
prepared=op['prepare'](config)[0];config=prepared
config.update(stop_margin=0,return_margin=0)
def launcher(argv,**kw):
    cfg=json.loads((Path(kw['cwd'])/argv[-1]).read_text())
    actual=runner.worker_args(cfg);marker=actual[actual.index('--stop-file')+1]
    return subprocess.Popen([sys.executable,'-I','-s','-B','/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/1.py',marker,'/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/0.ready','/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/0.end'],**kw)
summary=runner.run(config,[''],time.time()+60,launcher=launcher)
Path('/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/summary.json').write_text(json.dumps(summary))
if summary.get('failure') or not summary.get('stopped') or not Path('/scratch/jjyeung/orch_n30/so_pack/work/tests06/a96d92b8d6785/good/0.end').exists():
    raise ValueError('Native runner stop/end proof failed')
print('NATIVE_STOP_PASS')
