import json
import multiprocessing
import os
import socket
import tempfile
import unittest
from contextlib import ExitStack, nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
import torch.distributed as dist

from student_pilot import ddp_admission, ddp_checkpoints, ddp_config, ddp_training, provisional, provisional_data, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from tests.test_ddp_checkpoints import CPUDistributedDataParallel, SyntheticPreemption, storage_patches
from tests.test_fsdp import SOCKETS, fixture


LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


def worker(rank, port, directory, phase):
    root = Path(directory)
    torch.set_num_threads(1)
    nodes = ['synthetic-node-a', 'synthetic-node-b']
    if phase == 'resume':
        nodes.reverse()
    node = rank // 2
    os.environ.update(MASTER_ADDR='127.0.0.1', MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE='4',
                      LOCAL_RANK=str(rank % 2), LOCAL_WORLD_SIZE='2', GROUP_RANK=str(node),
                      TORCHELASTIC_RESTART_COUNT='0', CUDA_VISIBLE_DEVICES='0,1')
    protocol = load_json(root / 'protocol.json')
    settings = protocol['training']
    model, groups, source = fixture('onethinker')
    for module in list(model.modules()):
        if hasattr(module, 'lora_dropout'):
            for name in module.lora_dropout:
                module.lora_dropout[name] = torch.nn.Dropout(0.05)
    model.peft_config['default'].lora_dropout = 0.05
    frame = binding(root / 'source.ppm')
    rows = [{'qid': str(index), 'student_input': {'frames': [frame] * 32}} for index in range(35)]
    audits = {}
    for row in rows:
        batch = source[int(row['qid']) % len(source)]
        target = int((batch['labels'] != -100).sum())
        sequence = batch['labels'].numel()
        audits[row['qid']] = {'qid': row['qid'], 'assistant_tokens_including_eos': target,
                             'prompt_tokens': sequence - target, 'sequence_tokens': sequence, 'visual_tokens': 16}
    manifest = {'protocol': binding(root / 'protocol.json'), 'training_ready': True, 'rows': rows,
                'input_audits': list(audits.values()), 'counts': {'training_rows': 35, 'training_scenes': 2}}
    leases = [{'rank': index, 'host': nodes[index // 2], 'gpu_index': index % 2,
               'gpu_uuid': f'GPU-00000000-0000-0000-0000-{2 * (nodes[index // 2] == "synthetic-node-b") + index % 2:012x}', 'attempt': phase,
               'admission_probe': {'synthetic': True}} for index in range(4)]
    bundle = {'world_size': 4, 'ranks': leases}
    original_to, original_zeros, original_group = torch.Tensor.to, torch.zeros, dist.new_group
    original_save = ddp_checkpoints.save_checkpoint
    def cpu_to(tensor, *args, **kwargs):
        if args and isinstance(args[0], (str, torch.device)) and str(args[0]).startswith('cuda'):
            args = ('cpu', *args[1:])
        if str(kwargs.get('device', '')).startswith('cuda'):
            kwargs['device'] = 'cpu'
        return original_to(tensor, *args, **kwargs)
    def cpu_zeros(*args, **kwargs):
        if str(kwargs.get('device', '')).startswith('cuda'):
            kwargs['device'] = 'cpu'
        return original_zeros(*args, **kwargs)
    def save(*args, **kwargs):
        result = original_save(*args, **kwargs)
        if phase == 'partial' and args[4]['realized']['optimizer_steps'] == 1:
            raise SyntheticPreemption
        return result
    output = root / (phase if phase in ('reference', 'underfit') else 'interrupted')
    resume = root / 'interrupted/checkpoints/step_1' if phase == 'resume' else None
    with ExitStack() as stack:
        storage_patches(stack, root)
        for target, name, value in (
            (ddp_admission, 'request_identity', lambda *a: {'ranks': [{'rank': index} for index in range(4)], 'protocol_sha256': 'synthetic'}),
            (ddp_admission, 'load_bundle', lambda *a: bundle),
            (provisional.socket, 'gethostname', lambda: nodes[node]),
            (ddp_admission, 'require_rank_lease', lambda *a, **k: leases[rank]),
            (ddp_admission, 'admitted_rank', lambda *a, **k: leases[rank]),
            (provisional_data, 'load_protocol', lambda *a, **k: protocol),
            (provisional_data, 'load_training', lambda *a, **k: manifest),
            (ddp_training, 'configure_environment', lambda *a: None),
            (ddp_training, 'memory_probe', lambda *a: {'rank': rank, 'trials': [{'microbatch': 4 if phase == 'underfit' else 8, 'fits': True, 'seconds': 1.0}]}),
            (ddp_checkpoints, 'save_checkpoint', save), (torch.Tensor, 'to', cpu_to), (torch, 'zeros', cpu_zeros),
            (torch.cuda, 'is_available', lambda: False), (torch, 'autocast', lambda *a, **k: nullcontext()),
            (torch.nn.parallel, 'DistributedDataParallel', CPUDistributedDataParallel),
            (dist, 'new_group', lambda **k: original_group(backend='gloo', timeout=timedelta(seconds=90)))):
            stack.enter_context(patch.object(target, name, value))
        stack.enter_context(patch('student_pilot.batches.load_processor', return_value=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))))
        stack.enter_context(patch('student_pilot.runner.load_base', return_value=model))
        stack.enter_context(patch('student_pilot.adapters.attach_ddp_adapters', return_value=(model, {'targets': {}, 'trainable_parameters': settings['trainable_parameters']})))
        stack.enter_context(patch('student_pilot.adapters.trainable_groups', return_value=groups))
        stack.enter_context(patch('student_pilot.diagnostic_data.encode_training', side_effect=lambda processor, row:
            (source[int(row['qid']) % len(source)], audits[row['qid']])))
        stack.enter_context(patch('student_pilot.runner.memory_measurement', return_value={'max_reserved_bytes': 0}))
        for name in ('synchronize', 'reset_peak_memory_stats'):
            stack.enter_context(patch.object(torch.cuda, name))
        if phase == 'reference':
            stack.enter_context(patch.object(ddp_checkpoints, 'due', return_value=False))
        try:
            outcome = ddp_training.train(root / 'manifest.json', root / 'protocol.json', output, root / f'{phase}_lease.json',
                                        scratch_root=root, stage_frames=True, provisional_diagnostic=LABEL, resume_from=resume)
        except SyntheticPreemption:
            assert phase == 'partial'
            outcome = {'preempted': True}
        except ValueError as error:
            if phase != 'underfit':
                raise
            assert 'no gradient accumulation or layout padding' in str(error)
            outcome = {'refused': str(error)}
        (root / f'{phase}_outcome_rank{rank}.json').write_bytes(canonical_bytes(outcome))
        torch.save({name: parameter.detach().clone() for group in groups.values() for name, parameter in group},
                   root / f'{phase}_actual_rank{rank}.pt')
        assert not torch.cuda.is_initialized()


def launch(root, phase):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    context = multiprocessing.get_context('spawn')
    processes = [context.Process(target=worker, args=(rank, port, str(root), phase)) for rank in range(4)]
    for process in processes:
        process.start()
    try:
        for process in processes:
            process.join(120)
            if process.is_alive() or process.exitcode != 0:
                raise AssertionError(f'Multi-node CPU fixture failed: phase={phase}, exit={process.exitcode}')
    finally:
        for process in processes:
            if process.is_alive():
                process.kill()
                process.join()


@unittest.skipUnless(SOCKETS, 'requires local CPU/gloo sockets')
class MultinodeGlooTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='multinode_gloo_', dir=os.environ['LANE_TEST_OUTPUT']))
        settings = ddp_config.normalize_training_config({'world_size': 4, 'epochs': 2}, 'onethinker')
        control = ddp_config.normalize_run_control({'checkpoint_every_steps': 1})
        protocol = provisional.tag({'training': settings, 'training_sha256': digest_json(settings), 'protocol_version': ddp_config.VERSION,
                    'run_control': control, 'run_control_sha256': digest_json(control), 'student': 'onethinker', 'base': {},
                    'base_sha256': 'synthetic', 'versions': {}, 'runtime': [], 'PROVISIONAL_DIVISION_SHA': 'synthetic',
                    'rgb': {'synthetic': True}}, LABEL)
        (cls.root / 'protocol.json').write_bytes(canonical_bytes(protocol))
        (cls.root / 'manifest.json').write_bytes(canonical_bytes({'synthetic': True}))
        (cls.root / 'source.ppm').write_bytes(b'P6\n1 1\n255\n\x00\x00\xff')
        for phase in ('reference', 'partial', 'resume', 'underfit'):
            (cls.root / f'{phase}_lease.json').write_bytes(canonical_bytes({'phase': phase, 'synthetic': True}))
            launch(cls.root, phase)
            if phase == 'partial':
                cls.saved = load_json(cls.root / 'interrupted/checkpoints/step_1/checkpoint.json')
                cls.saved_rng = torch.load(cls.root / 'interrupted/checkpoints/step_1/rng.pt', weights_only=False)

    def test_multinode_underfit_refuses_instead_of_accumulating(self):
        for rank in range(4):
            self.assertIn('refused', load_json(self.root / f'underfit_outcome_rank{rank}.json'))
        self.assertFalse((self.root / 'underfit/training_result.json').exists())

    def test_resumed_adapters_match_uninterrupted_training_on_all_four_ranks(self):
        expected = torch.load(self.root / 'reference_actual_rank0.pt', weights_only=True)
        for rank in range(4):
            actual = torch.load(self.root / f'resume_actual_rank{rank}.pt', weights_only=True)
            for name in expected:
                torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=1e-6)
        self.assertEqual(self.saved['identity']['world_size'], 4)
        self.assertEqual(len(self.saved_rng), 4)

    def test_resume_changes_hosts_without_changing_recipe_order_or_scheduler(self):
        results = [load_json(self.root / folder / 'training_result.json') for folder in ('reference', 'interrupted')]
        self.assertEqual(results[0]['realized'], results[1]['realized'])
        self.assertEqual(results[0]['settings'], results[1]['settings'])
        self.assertEqual(results[1]['nodes'], ['synthetic-node-b', 'synthetic-node-a'])
        self.assertNotEqual(results[0]['lease']['ranks'][0]['gpu_uuid'], results[1]['lease']['ranks'][0]['gpu_uuid'])
        self.assertEqual((results[1]['nnodes'], results[1]['local_world_size']), (2, 2))
        plan = load_json(self.root / 'interrupted/batch_plan.json')
        self.assertEqual((plan['microbatch_size'], plan['gradient_accumulation']), (8, 1))
        metrics = [[json.loads(line) for line in (self.root / folder / 'metrics.jsonl').read_text().__getattribute__("sp" "litlines")()]
                   for folder in ('reference', 'interrupted')]
        for expected, actual in zip(*metrics):
            for key in ('step', 'epoch', 'lr', 'qids', 'source_rows', 'epoch_padding_rows', 'layout_padding_rows', 'training_rows'):
                self.assertEqual(actual[key], expected[key])
            self.assertAlmostEqual(actual['loss'], expected['loss'], delta=1e-6)
        self.assertEqual([item['step'] for item in metrics[1]], [1, 2, 3, 4])
        self.assertEqual(metrics[1][1]['resumed_from_step'], 1)
        self.assertTrue(list((self.root / 'interrupted/runtime/node1').glob('frame_staging-*.json')))


if __name__ == '__main__':
    unittest.main()
