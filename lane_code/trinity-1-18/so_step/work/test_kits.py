import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from contextlib import ExitStack

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
                  OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'),
                  TMPDIR=str(ROOT/'work/test_runs'),C1_CPU_PREFETCH='0',C1_DECODED_CACHE_MIB='0',C1_BATCH_METRICS='0')
if hasattr(os,'sched_getaffinity'):
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:8])
sys.path.insert(0,os.environ.get('SO_TEST_TREE',str(ROOT/'work/tree')))
sys.path.insert(0,str(ROOT/'out/kit_profile'))
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from tests.test_carrier_c1 import fixture
from tests.test_so_joint import exact
from instrument import Phases,hooks,instrument_step,profiler_table
from disposable import measurement_train


def train_fixture(cfg, smoke_steps=None, resume_pin=None):
    if smoke_steps is not None and (type(smoke_steps)!=int or not 1<=smoke_steps<=10 or resume_pin):
        raise ValueError('invalid smoke')
    output=Path(cfg['output'])
    if smoke_steps:
        output=output/'smoke'
    return output, resume_pin, cfg


class TinyRows:
    def __init__(self,batch,target):
        self.batch,self.target=batch,target
    def get(self,stream,index):
        return copy.deepcopy(self.batch),copy.deepcopy(self.target) if stream=='pose' else None,{}


class KitTests(unittest.TestCase):
    def test_real_native_setup_restores_checkpoint_and_redirects_receipts(self):
        from tests.so_helpers import root
        import torch.distributed as dist
        directory=root()
        original_output=directory/'original_run'
        disposable_output=directory/'measurement'
        model,batch,target=fixture(4)
        cfg=dict(output=str(original_output),preparation={'fixture':True},trace_program_version='3.13')
        auth=directory/'authorization.json'
        auth.write_text(json.dumps(dict(config_sha256=run.identity(cfg),new_gpus=8,job_id='kit_fixture',verdict='GO')))
        cfg['authorization']=run.file_pin(auth)
        pin={'path':str(directory/'checkpoint.json'),'sha256':'fixture'}
        receipt={'streams':{s:{'count':9} for s in ('pose','vqa','pointing')}}
        observed=[]
        def loop(*args,**kwargs):
            observed.append((args,kwargs))
            self.assertEqual(args[5],disposable_output/'smoke/kit_fixture')
            self.assertEqual(args[10],2)
            self.assertEqual(args[11],10)
        with ExitStack() as stack:
            from student_pilot import c1_switches
            stack.enter_context(patch.object(c1_switches, '_frozen', None))
            stack.enter_context(patch.dict(os.environ,WORLD_SIZE='8',RANK='0',LOCAL_RANK='0'))
            stack.enter_context(patch.object(run.rehearsal,'enabled',return_value=False))
            stack.enter_context(patch.object(run.rehearsal,'attempt_id',return_value='kit_fixture'))
            for name in ('set_device','reset_peak_memory_stats'):
                stack.enter_context(patch.object(torch.cuda,name))
            stack.enter_context(patch.object(torch.cuda,'is_available',return_value=True))
            for name in ('init_process_group','destroy_process_group','new_group','barrier','broadcast_object_list'):
                stack.enter_context(patch.object(dist,name))
            stack.enter_context(patch.object(dist,'get_world_size',return_value=8))
            stack.enter_context(patch.object(dist,'all_gather_object',side_effect=lambda out,value,**kw:out.__setitem__(slice(None),[value]*len(out))))
            checks={}
            for name,value in [('validate',None),('prepared',(receipt,{})),('authenticate','fixture'),
                               ('processor_for_receipt',None),('load_model',model),('wrap_model',model),('restore',2)]:
                checks[name]=stack.enter_context(patch.object(run,name,return_value=value))
            stack.enter_context(patch.object(run,'Rows',return_value=SimpleNamespace(close=lambda:None)))
            stack.enter_context(patch.object(run,'run_steps',side_effect=loop))
            restored_binding = {'fixture': 'original production binding'}
            def early_resume_check(config, commit, resume):
                checks['load_model'].assert_not_called()
                self.assertIs(resume,pin)
                return restored_binding
            operation=measurement_train(run,disposable_output,resume_check=early_resume_check)
            operation(cfg,smoke_steps=10,resume_pin=pin)
            for name in ('validate','prepared','authenticate','load_model','wrap_model','restore'):
                checks[name].assert_called_once()
            self.assertIs(checks['restore'].call_args.args[0],pin)
            self.assertIs(checks['restore'].call_args.args[3],restored_binding)
        self.assertEqual(len(observed),1)
        self.assertFalse(original_output.exists())
        self.assertTrue((disposable_output/'smoke/kit_fixture/attempt_kit_fixture.json').is_file())

    def test_disposable_native_train_preserves_config_resume_and_step_guard(self):
        original=SimpleNamespace(train=train_fixture,Path=Path)
        cfg={'output':'/production/read-only','unchanged':True}
        pin={'path':'/checkpoint/read-only','sha256':'same'}
        with self.assertRaises(ValueError):
            original.train(cfg,smoke_steps=10,resume_pin=pin)
        operation=measurement_train(original,ROOT/'work/kit_native_probe')
        output,resumed,configuration=operation(cfg,smoke_steps=10,resume_pin=pin)
        self.assertEqual(output,ROOT/'work/kit_native_probe/smoke')
        self.assertIs(resumed,pin)
        self.assertIs(configuration,cfg)
        self.assertEqual(cfg['output'],'/production/read-only')
        for bad in (0,11,True):
            with self.assertRaises(ValueError):
                operation(cfg,smoke_steps=bad,resume_pin=pin)
        # Also require exact guards in the supplied native trainer, not just the fixture.
        self.assertTrue(callable(measurement_train(run,ROOT/'work/kit_native_probe')))

    def test_instrumented_native_step_and_unmodified_input_default_are_exact(self):
        spec=importlib.util.spec_from_file_location('student_pilot._so_input',ROOT/'in/tree/work/tree_r1/student_pilot/carrier_c1_run.py')
        baseline=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        outcomes=[]
        for kind in ('input','off','instrumented'):
            model,batch,target=fixture(4)
            optimizer=torch.optim.AdamW(parameter_groups(model),weight_decay=.01)
            rows=TinyRows(batch,target)
            plan=[(s,[0]) for s in ('pose','vqa','pointing')]
            phases=Phases(torch.device('cpu'))
            from contextlib import nullcontext
            with hooks(run,model,phases) if kind=='instrumented' else nullcontext():
                fn=instrument_step(run,phases) if kind=='instrumented' else baseline.optimize_step if kind=='input' else run.optimize_step
                if kind=='instrumented':
                    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                        info,_=fn(model,optimizer,rows,plan,0,torch.device('cpu'),1)
                    profiler_table(prof,ROOT/'out/evidence/cpu_profiler_table.json')
                    prof.export_chrome_trace(str(ROOT/'out/evidence/cpu_trace.json'))
                else:
                    info,_=fn(model,optimizer,rows,plan,0,torch.device('cpu'),1)
            outcomes.append((info,{n:(p.detach().clone(),None if p.grad is None else p.grad.detach().clone()) for n,p in model.named_parameters()}))
            if kind=='instrumented':
                names={r[0] for r in phases.records}
                self.assertTrue({'data_wait_including_admission','forward_total','backward_including_recompute_and_fsdp',
                    'lm_layer_forward','lm_layer_recompute','base_vision','gradient_reduce_norm_clip_and_lr','optimizer'} <= names,names)
                phases.table(ROOT/'out/evidence/cpu_phase_table.json')
        reference=outcomes[0]
        for info,params in outcomes[1:]:
            for key in ('components','stream_means','gradient_norms','trained_group_gradients','head_gradients','shapes'):
                self.assertEqual(info[key],reference[0][key])
            self.assertEqual(params.keys(),reference[1].keys())
            for name,(p,g) in params.items():
                exact(p,reference[1][name][0],name)
                expected=reference[1][name][1]
                self.assertEqual(g is None,expected is None,name)
                if g is not None:
                    exact(g,expected,name+'/gradient')
        print('SO_DEFAULT_AND_PROFILE: input/default/instrumented losses, gradients, updates and metadata bitwise equal',flush=True)

    def test_interval_union(self):
        from trace_summary import duration
        self.assertEqual(duration([(0,100),(50,200),(300,400)]),.0003)


if __name__=='__main__':
    unittest.main(verbosity=2)
