import os, sys, json, traceback, importlib, ast, time
from pathlib import Path
base = Path(os.environ['CT_BASE']); S = base/'s'; KIT = Path(os.environ['CT_KIT'])
sys.path.insert(0, str(base/'src'))
import cudatrace as ct
ST = ct.STATE; ST['results'] = {}
def mods_before(): return set(sys.modules)
def imp(names, label):
    before = mods_before(); res = {}
    for n in names:
        try:
            importlib.import_module(n); res[n] = 'ok'
        except BaseException as e:
            res[n] = '%s: %s' % (type(e).__name__, str(e)[:200])
    new = sorted({m.split('.')[0] for m in set(sys.modules) - before})
    ST['results'][label] = dict(imports=res, new_top_packages=new); ct.flush()
sys.path.insert(0, str(S))
# a.py top: kit/b modules and launch_r1 / p3_provenance / r1_persisted
sys.path.insert(1, str(KIT/'b'))
ct.stage('A_apy_imports')
imp(['z', 'pl', 'rb', 'launch_r1.build', 'launch_r1.entry', 'student_pilot.p3_provenance',
     'student_pilot.r1_persisted', 'student_pilot.s1_admission', 'launch_r1.production_proof'], 'A_apy_imports')
# _run's lazy imports before admit, with the variable as the job would have it (here '' by rule)
ct.stage('B_run_pre_admit_imports')
imp(['student_pilot.r1_coverage', 'student_pilot.r1_rooms', 'student_pilot.r1_direction_twins',
     'student_pilot.r1_training', 'launch_r1.p_opener_witness', 'student_pilot.r1_handover',
     'student_pilot.r1_population', 'student_pilot.r1_loader', 'student_pilot.source_seal',
     'student_pilot.carrier_c1_run'], 'B_run_pre_admit_imports')
# Mirror production_proof.py:438-447 around the real admit()
import student_pilot.s1_admission as adm
from student_pilot.p3_provenance import file_pin
out = base/'admit_out'; out.mkdir(exist_ok=True)
cfgfile = None
for c in os.environ.get('CT_FIXTURES', '').split(':'):
    if c and Path(c).is_file(): cfgfile = Path(c); break
if cfgfile is None:
    cfgfile = base/'empty_cfg.json'; cfgfile.write_text('{}')
ST['admit_config'] = str(cfgfile)
frames = base/'frames'; frames.mkdir(exist_ok=True)
ct.stage('C_admit_real_call')
visible = os.environ.get('CUDA_VISIBLE_DEVICES'); os.environ['CUDA_VISIBLE_DEVICES'] = ''
try:
    r = adm.admit(file_pin(cfgfile), out, [str(frames)], threads=8, memory_gib=15, prepare_only=True)
    ST['results']['C_admit_real_call'] = dict(status='returned', keys=sorted(r)[:20])
except BaseException as e:
    tb = traceback.format_exc().splitlines()
    ST['results']['C_admit_real_call'] = dict(status='raised', error='%s: %s' % (type(e).__name__, str(e)[:300]), tb=tb[-12:])
finally:
    if visible is None: os.environ.pop('CUDA_VISIBLE_DEVICES', None)
    else: os.environ['CUDA_VISIBLE_DEVICES'] = visible
ct.flush()
# Every module named by a function-level import in modules on admit's path (over-approximation)
ct.stage('D_admit_function_level_imports')
roots = ['s1_admission', 'carrier_c1_data', 'carrier_c1_run', 'rehearsal', 'first_batch_progress', 's1_exclusions',
         'r1_coverage', 'mdg_parent', 's1_routing', 'r1_routing', 'r1_handover', 'row_removals', 'orchard_paths',
         'grounding_train', 'p3_provenance', 'job_env']
targets = set()
for r in roots:
    p = S/'student_pilot'/(r+'.py')
    if not p.is_file(): continue
    for node in ast.walk(ast.parse(p.read_text())):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.col_offset > 0:
            if isinstance(node, ast.Import):
                targets.update(a.name for a in node.names)
            elif node.level:
                if node.module: targets.add('student_pilot.'+node.module)
                else: targets.update('student_pilot.'+a.name for a in node.names)
            else:
                targets.add(node.module)
ST['D_targets'] = sorted(targets)
os.environ['CUDA_VISIBLE_DEVICES'] = ''
imp(sorted(targets), 'D_admit_function_level_imports')
# Third-party probes named in the brief
ct.stage('E_third_party_probes')
imp(['transformers', 'transformers.models.qwen3_5', 'transformers.models.qwen3_5.modeling_qwen3_5',
     'fla', 'fla.ops', 'triton', 'torch.utils.data'], 'E_third_party_probes')
try:
    from transformers import AutoProcessor  # noqa
    ST['results']['E_autoprocessor_symbol'] = 'ok'
except BaseException as e:
    ST['results']['E_autoprocessor_symbol'] = repr(e)[:200]
ct.stage('F_end')
import torch
ST['final'] = dict(cuda_initialized=torch.cuda.is_initialized.__wrapped__() if hasattr(torch.cuda.is_initialized, '__wrapped__') else None,
                   cached_device_count=getattr(torch.cuda, '_cached_device_count', 'n/a'),
                   libcuda_mapped=any('libcuda.so' in l for l in open('/proc/self/maps')),
                   fla_loaded='fla' in sys.modules, triton_loaded='triton' in sys.modules,
                   transformers_loaded='transformers' in sys.modules)
ct.flush()
print('DONE')
