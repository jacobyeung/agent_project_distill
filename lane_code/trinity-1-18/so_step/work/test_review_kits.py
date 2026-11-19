"""CPU and mocked-stream checks for kit review fixes; no CUDA work is launched."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'),TMPDIR=str(ROOT/'work/test_runs'))
if hasattr(os,'sched_getaffinity'):
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path[:0]=[str(ROOT/'out/kit_profile'),str(ROOT/'out/kit_timing'),os.environ.get('SO_TEST_TREE',str(ROOT/'work/tree'))]
import torch
torch.set_num_threads(8)
from instrument import Phases, hooks
from resume import preflight
from privacy import opaque, scrub, write_json, WORDS
from launch import save_interrupted
from row_hash import encoded_hash, compare_rows
from tests.so_helpers import root


class ReviewKits(unittest.TestCase):
    def test_autograd_worker_events_and_recompute_and_producer_exclusion(self):
        from torch.distributed.fsdp import _runtime_utils as runtime
        recorded=[]
        class Event:
            def __init__(self, **kw): pass
            def record(self, stream): recorded.append((threading.current_thread().name,stream))
            def query(self): return True
            def elapsed_time(self, end): return 2.
        decoder=type('Qwen3_5DecoderLayer',(),{'forward':lambda self:None})()
        model=SimpleNamespace(named_modules=lambda:[('block',decoder)])
        run=SimpleNamespace(**{name:lambda *a:None for name in ('check_row','move','memory_stats','own_values')})
        phases=Phases(torch.device('cuda:0'))
        errors=[]
        with patch.object(torch.cuda,'Event',Event), patch.object(torch.cuda,'current_stream',
                side_effect=lambda device:'stream-'+threading.current_thread().name), \
                patch.object(runtime,'_unshard',lambda *a:None), patch.object(runtime,'_reduce_grad',lambda *a:None):
            with hooks(run,model,phases), phases.scope('backward_including_recompute_and_fsdp'):
                def backward():
                    try:
                        decoder.forward()
                        runtime._reduce_grad(None)
                        runtime._unshard(None,None,'all-gather-stream',None)
                    except Exception as exc:
                        errors.append(exc)
                worker=threading.Thread(target=backward,name='autograd-device')
                worker.start();worker.join()
                before=len(recorded)
                def producer():
                    with phases.scope('check_row'): pass
                worker=threading.Thread(target=producer,name='c1-row-cpu_0')
                worker.start();worker.join()
                self.assertEqual(len(recorded),before)
        self.assertFalse(errors,errors)
        self.assertIn('lm_layer_recompute',[row[0] for row in phases.records])
        self.assertIn(('autograd-device','all-gather-stream'),recorded)
        self.assertEqual(recorded.count(('autograd-device','stream-autograd-device')),4)
        self.assertFalse(any(name.startswith('c1-row-cpu') for name,stream in recorded))

    def test_partial_signal_output_without_cuda_synchronize(self):
        directory=root()
        phases=Phases(torch.device('cpu'))
        with phases.scope('forward_total'): pass
        with patch.object(torch.cuda,'synchronize',side_effect=AssertionError('must not block')):
            save_interrupted(directory,dict(completed_steps=0,completed_microsteps=1),phases,15)
        self.assertEqual(json.loads((directory/'progress.json').read_text())['stage'],'incomplete_signal_15')
        self.assertIn('forward_total',json.loads((directory/'phase_partial.json').read_text()))

    def test_real_term_writes_incomplete_status(self):
        import signal
        import subprocess
        directory=root()
        program = """
import signal, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from launch import save_interrupted
def stop(number, frame):
    save_interrupted(Path(sys.argv[2]), {'completed_steps':0}, None, number)
    raise SystemExit(128+number)
signal.signal(signal.SIGTERM, stop)
print('ready', flush=True)
while True: time.sleep(.05)
"""
        process=subprocess.Popen([sys.executable,'-I','-s','-B','-c',program,
            str(ROOT/'out/kit_profile'),str(directory)],stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,text=True)
        self.assertEqual(process.stdout.readline().strip(),'ready')
        process.send_signal(signal.SIGTERM)
        output,_=process.communicate(timeout=10)
        self.assertEqual(process.returncode,143)
        self.assertIn('SO_INCOMPLETE signal=15',output)
        self.assertEqual(json.loads((directory/'progress.json').read_text())['stage'],'incomplete_signal_15')

    def test_source_only_production_resume_bridge_and_early_refusals(self):
        old=dict(code={'path':'old_code'},preparation={'path':'old_data'},output='/original',training_mode='final',recipe={'world_size':4})
        new=dict(old,code={'path':'new_code'},preparation={'path':'new_data'})
        def identity(cfg): return opaque(json.dumps({k:v for k,v in cfg.items() if k!='preparation'},sort_keys=True))
        bound=dict(config_sha256=identity(old),preparation=old['preparation'],trainer_commit='old',world_size=4)
        files={'source':old,'old_code':{'commit':'old'},'new_code':{'commit':'new'},
               'old_data':{'rows':'same','trainer_commit':'old'},'new_data':{'rows':'same','trainer_commit':'new'},
               'checkpoint':dict(schema='c1-checkpoint-v1',binding=bound)}
        run=SimpleNamespace(identity=identity,load=lambda path:files[path],pinned=lambda pin:pin['path'],recipe_for=lambda cfg:cfg['recipe'])
        pin={'path':'checkpoint'}
        self.assertEqual(preflight(run,new,'new',pin,'source'),bound)
        self.assertEqual(preflight(run,old,'old',pin),bound)
        self.assertEqual(preflight(run,new,'new',None)['trainer_commit'],'new')
        with self.assertRaisesRegex(ValueError,'RESUME_CONFIG'):
            preflight(run,new,'new',pin)
        with self.assertRaisesRegex(ValueError,'configuration changes'):
            preflight(run,dict(new,learning_rate=5),'new',pin,'source')
        files['new_data']['rows']='different'
        with self.assertRaisesRegex(ValueError,'prepared data changes'):
            preflight(run,new,'new',pin,'source')
        files['new_data']['rows']='same'
        with self.assertRaisesRegex(ValueError,'world binding differs'):
            preflight(run,dict(new,recipe={'world_size':2}),'new',pin,'source')

    def test_hash_signed_zero_scalar_structure_and_cross_arm_failure(self):
        self.assertNotEqual(encoded_hash(torch.tensor(0.)),encoded_hash(torch.tensor(-0.)))
        self.assertNotEqual(encoded_hash(torch.tensor([1.])),encoded_hash(torch.tensor(1.)))
        row={'pixels':torch.arange(12).reshape(3,4),'mask':torch.tensor(True)}
        a=[dict(encoded_row_sha256=[encoded_hash(row)])]
        compare_rows(a,a)
        row['pixels'][0,0]=1
        with self.assertRaisesRegex(ValueError,'differs from OFF'):
            compare_rows(a,[dict(encoded_row_sha256=[encoded_hash(row)])])

    def test_output_scrubber_and_opaque_identifiers(self):
        directory=root()
        payload={'name':'qwen3_5.DecoderLayer','path':'/pkg/qwen3_next/file.py',
                 'args':{'function':'torch_chunk_gated_delta_rule','norm':'Qwen3_5RMSNormGated'}}
        write_json(directory/'trace.json',payload)
        self.assertIsNone(WORDS.search((directory/'trace.json').read_text()))
        self.assertEqual(opaque('same'),opaque('same'))
        self.assertNotEqual(opaque('same'),opaque('other'))

    def test_bounded_cache_snapshot_and_shell_limits(self):
        import cache_state
        directory=root()
        (directory/'entry').write_text('cache')
        with patch.dict(os.environ,{key:str(directory) for key in ('CUDA_CACHE_PATH','TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR')}):
            state=cache_state.snapshot()
        self.assertTrue(all(len(value['entries'])==1 and not value['recursive'] for value in state.values()))
        import subprocess
        for folder in ('kit_profile','kit_timing'):
            for path in (ROOT/'out'/folder).glob('*.sh'):
                subprocess.run(['bash','-n',str(path)],check=True)
        timing=(ROOT/'out/kit_timing/run.sh').read_text()
        self.assertIn('timeout --signal=TERM',timing)
        self.assertIn('off prefetch off cache off metrics off',timing)
        self.assertNotIn('OMP_NUM_THREADS=8',timing)


if __name__=='__main__':
    unittest.main(verbosity=2)
