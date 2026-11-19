"""Two real FSDP1/gloo ranks: exact losses, all gradients, updates, draws and collectives."""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from tests.so_helpers import root, inputs, native, plan, compact_processor


ARMS = {
    'off': ('0','0','0'),
    'prefetch': ('1','0','0'),
    'cache': ('0','1','0'),
    'metrics': ('0','0','1'),
    'all': ('1','1','1'),
}


def exact(a,b, label):
    if isinstance(a,torch.Tensor):
        assert a.dtype == b.dtype and a.shape == b.shape,label
        assert torch.equal(a.detach().reshape(-1).contiguous().view(torch.uint8),
                           b.detach().reshape(-1).contiguous().view(torch.uint8)),label
    elif isinstance(a,dict):
        assert a.keys() == b.keys(),label
        for key in a:
            exact(a[key],b[key],label+'/'+str(key))
    elif isinstance(a,(tuple,list)):
        assert len(a) == len(b),label
        for i,(x,y) in enumerate(zip(a,b)):
            exact(x,y,label+'/'+str(i))
    else:
        assert a == b,(label,a,b)


def worker(rank, directory):
    torch.set_num_threads(8)
    directory = Path(directory)
    dist.init_process_group('gloo',init_method='file://'+str(directory/'rendezvous'),rank=rank,world_size=2,
                            timeout=datetime.timedelta(seconds=180))
    receipt = json.loads((directory/'receipt.json').read_text())
    reference = {}
    summaries = []
    try:
        for failure in (False,True):
            for arm,switches in ARMS.items():
                env = dict(zip(('C1_CPU_PREFETCH','C1_DECODED_CACHE_MIB','C1_BATCH_METRICS'),switches))
                with patch.dict(os.environ,**env):
                    model = native(world=2)
                    wrapped = run.wrap_model(model,torch.device('cpu'),mixed_precision=False)
                    optimizer = torch.optim.AdamW(parameter_groups(wrapped),weight_decay=.01)
                    rows = run.Rows(receipt,compact_processor())
                    draws, collectives, losses, grads = [], [], [], {}
                    main_thread = threading.get_ident()
                    original_get = run.Rows.get
                    def get(source,stream,index):
                        draws.append((stream,index,index))
                        if failure and rank == 1 and stream == 'vqa' and index == 3:
                            raise ValueError('planted rank-1 row failure')
                        return original_get(source,stream,index)
                    hook = model.register_forward_hook(lambda m,a,o: losses.append(o['loss'].detach().clone()))
                    clip = run.full_ft.clip_sharded
                    def capture(*a,**kw):
                        grads.update({n:None if p.grad is None else p.grad.detach().clone()
                                      for n,p in run.full_ft.named_trainable(wrapped)})
                        return clip(*a,**kw)
                    def traced(name, original):
                        def call(*a,**kw):
                            assert threading.get_ident() == main_thread, 'collective on CPU worker'
                            tensors = [x for x in a if isinstance(x,torch.Tensor)]
                            source = a[1] if name in ('all_gather','all_gather_into_tensor','reduce_scatter_tensor') else a[0]
                            digest = hashlib.sha256(source.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
                            collectives.append((name,[(tuple(t.shape),str(t.dtype)) for t in tensors],
                                                str(kw.get('op','default')),digest))
                            return original(*a,**kw)
                        return call
                    from contextlib import ExitStack
                    info = error = None
                    with ExitStack() as stack:
                        stack.enter_context(patch.object(run.Rows,'get',get))
                        stack.enter_context(patch.object(run.full_ft,'clip_sharded',capture))
                        for name in ('all_reduce','all_gather','all_gather_into_tensor','reduce_scatter_tensor','broadcast'):
                            stack.enter_context(patch.object(dist,name,traced(name,getattr(dist,name))))
                        try:
                            info,_ = run.optimize_step(wrapped,optimizer,rows,plan(2),rank,torch.device('cpu'),1,True)
                        except ValueError as exc:
                            error = str(exc)
                        finally:
                            rows.close()
                    hook.remove()
                    names = [(n,p.numel()) for n,p in run.full_ft.named_trainable(wrapped)]
                    after = {n:p.detach().clone() for n,p in run.full_ft.named_trainable(wrapped)}
                    state = dict(losses=losses,grads=grads,after=after,names=names,draws=draws,collectives=collectives,
                                 error=error,components=None if info is None else info['components'],
                                 stream_means=None if info is None else info['stream_means'])
                    if failure:
                        assert error and 'Final-mode row failure' in error,error
                        assert len(losses) == 2,('wrong failure microstep',len(losses))
                        assert draws == [('pose',rank,rank),('pose',2+rank,2+rank),
                                         ('vqa',rank,rank),('vqa',2+rank,2+rank)],draws
                    else:
                        assert error is None,error
                        assert grads and len(losses) == 8
                    if arm == 'off':
                        reference[failure] = state
                    else:
                        exact(reference[failure],state,f'rank{rank}/{arm}/failure={failure}')
                    summaries.append(dict(arm=arm,failure=failure,rank=rank,losses=len(losses),
                        gradients=len(grads),trainable_tensors=len(names),local_trainable_elements=sum(n for _,n in names),
                        draws=draws,collective_count=len(collectives),status='BITWISE_EQUAL',
                        failure_microstep=2 if failure else None))
                    (directory/f'rank{rank}_progress.json').write_text(json.dumps(summaries,indent=2)+'\n')
                    del optimizer,wrapped,model,rows
        (directory/f'rank{rank}.json').write_text(json.dumps(summaries,indent=2)+'\n')
    finally:
        dist.destroy_process_group()


class JointTests(unittest.TestCase):
    def test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives(self):
        torch.set_num_threads(8)
        directory = root()
        (directory/'receipt.json').write_text(json.dumps(inputs(directory)))
        mp.spawn(worker,args=(str(directory),),nprocs=2,join=True)
        reports = [json.loads((directory/f'rank{rank}.json').read_text()) for rank in range(2)]
        self.assertEqual(sum(len(r) for r in reports),20)
        print('SO_GLOO_PROOF '+json.dumps(dict(directory=str(directory),ranks=2,comparisons=16,
              losses_and_every_gradient='bitwise',trainables='identical',row_draws='identical',
              collectives='identical; main thread only',failure_microstep=2)),flush=True)


if __name__ == '__main__':
    unittest.main()
