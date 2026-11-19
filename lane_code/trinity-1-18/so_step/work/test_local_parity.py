"""Native CPU parity when the execution sandbox cannot create gloo sockets."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'), TMPDIR=str(ROOT/'work/test_runs'))
if hasattr(os, 'sched_getaffinity'):
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path.insert(0, os.environ.get('SO_TEST_TREE',str(ROOT/'work/tree')))
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from tests.so_helpers import root, inputs, native, compact_processor, plan
from tests.test_so_joint import ARMS, exact


class LocalParity(unittest.TestCase):
    def test_exact_comparator_rejects_signed_zero(self):
        with self.assertRaises(AssertionError):
            exact(torch.tensor(0.),torch.tensor(-0.),'signed zero')

    def test_all_switches_native_loss_every_gradient_update_trainables_and_rows(self):
        directory = root()
        receipt = inputs(directory)
        reference = {}
        summaries = []
        for failure in (False, True):
            for arm, switches in ARMS.items():
                with patch.dict(os.environ, **dict(zip(
                        ('C1_CPU_PREFETCH', 'C1_DECODED_CACHE_MIB', 'C1_BATCH_METRICS'), switches))):
                    model = native()
                    optimizer = torch.optim.AdamW(parameter_groups(model), weight_decay=.01)
                    rows = run.Rows(receipt, compact_processor())
                    draws, losses = [], []
                    original_get = run.Rows.get
                    def get(source, stream, index):
                        draws.append((stream, index, index))
                        if failure and stream == 'vqa' and index == 1:
                            raise ValueError('planted local row failure')
                        return original_get(source, stream, index)
                    hook = model.register_forward_hook(lambda m, a, o: losses.append(o['loss'].detach().clone()))
                    info = error = None
                    try:
                        with patch.object(run.Rows, 'get', get):
                            info, _ = run.optimize_step(model, optimizer, rows, plan(), 0, torch.device('cpu'), 1)
                    except ValueError as exc:
                        error = str(exc)
                    finally:
                        rows.close()
                        hook.remove()
                    state = dict(losses=losses, draws=draws, error=error,
                        trainables=[(n, p.numel()) for n, p in model.named_parameters() if p.requires_grad],
                        tensors={n: (p.detach().clone(), None if p.grad is None else p.grad.detach().clone())
                                 for n, p in model.named_parameters()},
                        optimizer=copy.deepcopy(optimizer.state_dict()),
                        components=None if info is None else info['components'],
                        streams=None if info is None else info['stream_means'])
                    self.assertEqual(len(losses), 2 if failure else 8)
                    self.assertEqual(error is not None, failure)
                    if arm == 'off':
                        reference[failure] = state
                    else:
                        exact(reference[failure], state, f'{arm}/failure={failure}')
                    summaries.append(dict(arm=arm, failure=failure, losses=len(losses), draws=draws,
                                          trainable_tensors=len(state['trainables']), status='BITWISE_EQUAL'))
                    del model, optimizer, rows
        (directory/'local_parity.json').write_text(json.dumps(summaries, indent=2)+'\n')
        print('SO_LOCAL_PROOF '+json.dumps(dict(directory=str(directory), arms=5, comparisons=8,
            loss_gradients_updates_optimizer='bitwise', trainables='identical', row_draws='identical',
            failure_microstep=2, distributed=False, full_fsdp_proof=False)), flush=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
