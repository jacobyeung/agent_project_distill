"""Third-review regressions: real startup, provenance and synchronous budget fallback."""
import copy
from contextlib import ExitStack, nullcontext
import os
import json
from pathlib import Path
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import patch

import torch
from student_pilot import carrier_c1_run as run, c1_switches as switches, c1_cpu_prefetch as prefetch
from tests.so_helpers import root, inputs, native, compact_processor, plan, reset_switches
from tests.test_so_joint import exact


def fallback_worker(rank, directory):
    import torch.distributed as dist
    from tests.so_helpers import assert_nested
    torch.set_num_threads(8)
    directory = Path(directory)
    dist.init_process_group('gloo',init_method='file://'+str(directory/'fallback_rendezvous'),rank=rank,world_size=2)
    try:
        receipt=json.loads((directory/'receipt.json').read_text())
        model=SimpleNamespace(recipe={'world_size':2,'reference_world_size':4},
                              training_mode='final',r1_training=True,frame_count=32)
        original_get, original_reduce = run.Rows.get, dist.all_reduce
        for failure in (False, True):
            results=[]
            for enabled in ('0','1'):
                collectives=[]; values=[]; error=None
                def get(rows, stream, index):
                    if failure and rank == 1 and stream == 'vqa' and index == 3:
                        raise ValueError('planted fallback admission failure')
                    return original_get(rows,stream,index)
                def reduce(flag,*args,**kwargs):
                    assert threading.current_thread() is threading.main_thread()
                    collectives.append((str(kwargs.get('op')),flag.tolist()))
                    return original_reduce(flag,*args,**kwargs)
                with patch.dict(os.environ,C1_CPU_PREFETCH=enabled,C1_CPU_PREFETCH_FALLBACK=enabled), \
                        patch.object(prefetch,'MAX_GROUP_TENSOR_BYTES',1 if rank == 1 else 1<<30), \
                        patch.object(run.Rows,'get',get),patch.object(dist,'all_reduce',reduce):
                    rows=run.Rows(receipt,compact_processor())
                    iterator=run.fetch_plan(rows,model,plan(2),rank,distributed=True)
                    try:
                        values.extend(iterator)
                    except ValueError as exc:
                        error=str(exc)
                    finally:
                        iterator.close();rows.close()
                if enabled == '1':
                    assert getattr(rows,'_c1_budget_fallback_groups',0) == ((2 if failure else 4) if rank == 1 else 0)
                results.append((values,collectives,error))
            assert_nested(unittest.TestCase(),*results)
            assert (results[0][2] is not None) == failure
        (directory/f'fallback_rank{rank}.json').write_text(json.dumps({'rank':rank,'status':'PASS'}))
    finally:
        dist.destroy_process_group()


class Round3(unittest.TestCase):
    def setUp(self):
        reset_switches(self)
        self.env = patch.dict(os.environ, C1_CPU_PREFETCH='0', C1_DECODED_CACHE_MIB='0',
                              C1_BATCH_METRICS='0', C1_CPU_PREFETCH_FALLBACK='0')
        self.env.start()
        self.addCleanup(self.env.stop)

    def step(self, receipt, fallback, cap):
        model = native()
        run.SKIPPED.update(skipped=0, total=0)
        optimizer = torch.optim.AdamW(run.parameter_groups(model))
        seen = []
        original = run.Rows.get
        def get(rows, stream, index):
            seen.append(threading.current_thread().name)
            return original(rows, stream, index)
        with patch.dict(os.environ, C1_CPU_PREFETCH='1' if fallback else '0',
                        C1_CPU_PREFETCH_FALLBACK='1' if fallback else '0'), \
                patch.object(prefetch, 'MAX_GROUP_TENSOR_BYTES', cap), patch.object(run.Rows, 'get', get):
            rows = run.Rows(receipt, compact_processor())
            try:
                info, _ = run.optimize_step(model, optimizer, rows, plan(), 0, torch.device('cpu'), 1)
            finally:
                rows.close()
        return (info, {n:(p.detach().clone(), None if p.grad is None else p.grad.clone())
                       for n,p in model.named_parameters()}, copy.deepcopy(optimizer.state_dict()), seen)

    def test_budget_fallback_is_bitwise_off_and_logged(self):
        receipt = inputs(root())
        off, weights, optimizer, _ = self.step(receipt, False, 1)
        on, actual, actual_optimizer, threads = self.step(receipt, True, 1)
        exact(weights, actual, 'weights/gradients')
        exact(optimizer, actual_optimizer, 'optimizer')
        ignored = {'wall_seconds','data_seconds','memory','peak_allocated_bytes','peak_reserved_bytes',
                   'performance','cpu_prefetch'}
        exact({k:v for k,v in off.items() if k not in ignored},
              {k:v for k,v in on.items() if k not in ignored}, 'training records')
        self.assertEqual(on['cpu_prefetch']['budget_fallback_groups'], 4)
        self.assertEqual(on['performance']['C1_CPU_PREFETCH_FALLBACK'], '1')
        self.assertIn('MainThread', threads)
        self.assertIn('c1-row-cpu_0', threads)
        self.assertNotIn('performance', off)
        self.assertNotIn('cpu_prefetch', off)

    def test_fallback_defaults_off_and_startup_agrees(self):
        self.assertEqual(switches.get('C1_CPU_PREFETCH_FALLBACK'), '0')
        with patch.dict(os.environ, C1_CPU_PREFETCH='1', C1_CPU_PREFETCH_FALLBACK='1'):
            local = switches.startup({'training_mode':'final'})
            self.assertIn('differ', switches.accept(local, ('1','0','0')))
            self.assertIsNone(switches.accept(local, local[0]))
            with patch.dict(os.environ, C1_CPU_PREFETCH_FALLBACK='0'):
                self.assertEqual(switches.get('C1_CPU_PREFETCH_FALLBACK'), '1')
        switches._frozen = None
        with patch.dict(os.environ, C1_CPU_PREFETCH_FALLBACK='bad'):
            self.assertIsNotNone(switches.startup({})[1])

    def test_performance_record_on_only(self):
        model = native(); receipt = inputs(root())
        with patch.dict(os.environ, C1_BATCH_METRICS='1'):
            rows = run.Rows(receipt, compact_processor())
            try:
                info, _ = run.optimize_step(model, torch.optim.AdamW(run.parameter_groups(model)),
                                            rows, plan(), 0, torch.device('cpu'), 1)
            finally:
                rows.close()
        self.assertEqual(info['performance'], dict(zip(switches.NAMES, ('0','0','1'))))

    def test_real_train_startup_payload_and_worker(self):
        from tests.test_carrier_c1_run import RunnerTests
        directory = root(); receipt = inputs(directory); model = native()
        cfg = dict(output=str(directory/'train'), preparation={'fixture':True},
                   trace_program_version='3.13', training_mode='final')
        run.write(directory/'auth.json', dict(config_sha256=run.identity(cfg), new_gpus=1,
                                              job_id='test', verdict='GO'))
        cfg['authorization'] = run.file_pin(directory/'auth.json')
        seen, records, payloads = [], [], []
        original = run.Rows.get
        def get(rows, stream, index):
            seen.append(threading.current_thread().name)
            return original(rows, stream, index)
        def loop(model, wrapped, optimizer, rows, *args, **kwargs):
            with patch.object(torch.cuda, 'is_available', return_value=False):
                records.append(run.optimize_step(model, optimizer, rows, plan(), 0, torch.device('cpu'), 1)[0])
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, WORLD_SIZE='1', RANK='0', LOCAL_RANK='0',
                SLURM_JOB_ID='test', C1_CPU_PREFETCH='1', C1_BATCH_METRICS='1'))
            stack.enter_context(RunnerTests().local_collectives())
            stack.enter_context(patch.object(run.dist, 'broadcast_object_list',
                                            side_effect=lambda value, **kw: payloads.append(copy.copy(value[0]))))
            for name in ('set_device', 'reset_peak_memory_stats'):
                stack.enter_context(patch.object(torch.cuda, name))
            stack.enter_context(patch.object(torch.cuda, 'is_available', return_value=True))
            for name in ('init_process_group','destroy_process_group','new_group'):
                stack.enter_context(patch.object(run.dist, name))
            for name, value in [('validate',None), ('prepared',(receipt,{})), ('authenticate','fixture'),
                                ('processor_for_receipt',compact_processor()), ('load_model',model),
                                ('wrap_model',model), ('recipe_for',model.recipe), ('run_lock',nullcontext())]:
                stack.enter_context(patch.object(run, name, return_value=value))
            stack.enter_context(patch.object(run.Rows,'get',get))
            stack.enter_context(patch.object(run,'run_steps',side_effect=loop))
            # A regression must fail as a test, not terminate the whole test process.
            stack.enter_context(patch.object(run.os,'_exit',side_effect=AssertionError('train failed')))
            run.train(cfg, smoke_steps=1)
        self.assertEqual(switches._frozen, ('1','0','1'))
        self.assertEqual(payloads[0][2], ('1','0','1'))
        self.assertIn('c1-row-cpu_0', seen)
        self.assertEqual(records[0]['performance']['C1_CPU_PREFETCH'], '1')

    def test_two_rank_budget_fallback_keeps_values_and_admission(self):
        import torch.multiprocessing as mp
        directory=root()
        (directory/'receipt.json').write_text(json.dumps(inputs(directory)))
        mp.spawn(fallback_worker,args=(str(directory),),nprocs=2,join=True)
        self.assertEqual([json.loads((directory/f'fallback_rank{r}.json').read_text())['status'] for r in range(2)],['PASS','PASS'])
        print('SO_FALLBACK_PROOF rank1-only over-budget fallback; exact rows and collective sequence; both ranks raise in the same group',flush=True)

    def test_export_leg_has_docstring(self):
        from tests.test_carrier_c1_t0 import ExportLeg
        self.assertIn('restores', ExportLeg.__doc__ or '')
