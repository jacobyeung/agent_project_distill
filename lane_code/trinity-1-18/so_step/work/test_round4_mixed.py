"""Mix synchronous fallback and prefetched groups without changing trainer bytes."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',
    LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'),TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path.insert(0,str(ROOT/'work/b21_final/work/tree_r1'))
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run, c1_cpu_prefetch as prefetch
from tests.so_helpers import root, inputs, compact_processor, reset_switches
from tests import test_so_round3 as prior
from tests.test_so_joint import exact


class MixedFallback(unittest.TestCase):
    def test_small_large_small_large_groups_preserve_training(self):
        reset_switches(self)
        receipt=inputs(root()); rows=run.Rows(receipt,compact_processor())
        try:
            sizes={s:sum(prefetch.tensor_bytes(rows.get(s,i)) for i in (0,1))
                   for s in receipt['streams']}
        finally:
            rows.close()
        small=min(sizes,key=sizes.get); large=max(sizes,key=sizes.get)
        cap=(sizes[small]+sizes[large])//2
        self.assertLess(sizes[small],cap); self.assertLess(cap,sizes[large])
        draw_plan=[(s,[i]) for s in (small,large,small,large) for i in (0,1)]
        decisions=[]; draws=[]; original=run.Rows.get; prepare=prefetch.Producer.prepare
        def get(rows,stream,index):
            import threading
            draws.append((stream,index,threading.current_thread().name))
            return original(rows,stream,index)
        def observe(producer,*args):
            value=prepare(producer,*args); decisions.append(value is None); return value
        with patch.dict(os.environ,C1_CPU_PREFETCH='0',C1_CPU_PREFETCH_FALLBACK='0',
                        C1_BATCH_METRICS='0',C1_DECODED_CACHE_MIB='0'), \
                patch.object(prior,'plan',return_value=draw_plan),patch.object(run.Rows,'get',get):
            off,weights,optimizer,_=prior.Round3().step(receipt,False,cap)
            draws.clear()
            with patch.object(prefetch.Producer,'prepare',observe):
                on,actual,actual_optimizer,threads=prior.Round3().step(
                    receipt,True,1 if os.environ.get('SO_MIXED_MUTATION') else cap)
        self.assertEqual(decisions,[False,True,False,True])
        self.assertEqual(on['cpu_prefetch']['budget_fallback_groups'],2)
        self.assertEqual([(s,i) for s,i,n in draws if n=='MainThread'],[(large,0),(large,1)]*2)
        self.assertEqual([(s,i) for s,i,n in draws if n.startswith('c1-row-cpu') and s==small],
                         [(small,0),(small,1)]*2)
        exact(weights,actual,'weights/gradients'); exact(optimizer,actual_optimizer,'optimizer')
        ignored={'wall_seconds','data_seconds','memory','peak_allocated_bytes','peak_reserved_bytes',
                 'performance','cpu_prefetch'}
        exact({k:v for k,v in off.items() if k not in ignored},
              {k:v for k,v in on.items() if k not in ignored},'training records')
        print('SO_MIXED_FALLBACK_PROOF sizes='+str(sizes)+' cap='+str(cap)+
              ' decisions='+str(decisions)+' fallback_groups=2; bitwise records, gradients, weights, optimizer')


if __name__=='__main__':
    unittest.main(verbosity=2)
