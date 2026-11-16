import unittest
from copy import deepcopy
from unittest.mock import patch

from scripts import tracecold_resources as resources
from scripts.tracecold_prepare import check_cold
from scripts.tracecold_train import cold_first_step
from scripts.tracecold_transport import GENERATION, validate_job
from student_pilot.ddp_config import normalize_training_config
from student_pilot.trace_contract import ANSWER_FORMAT_INSTRUCTION


class ResourceTests(unittest.TestCase):
    def test_foreign_leases_are_scoped_to_physical_cards(self):
        lease = {'status': 'running', 'host': 'trinity-0-3', 'command': 'other lane GPU 1', 'work_id': 'foreign'}
        uuids = {'GPU-00000000-0000-0000-0000-000000000004'}
        self.assertFalse(resources.blocks(lease, 'trinity-0-3', (4, 5, 6, 7), uuids))
        self.assertTrue(resources.blocks({**lease, 'command': 'GPU 4'}, 'trinity-0-3', (4, 5, 6, 7), uuids))
        self.assertTrue(resources.blocks({**lease, 'command': 'unknown GPU allocation'}, 'trinity-0-3', (4, 5, 6, 7), uuids))
        self.assertTrue(resources.blocks({**lease, 'command': 'gpu_uuid=' + next(iter(uuids))}, 'trinity-0-3', (4, 5, 6, 7), uuids))
        self.assertFalse(resources.blocks({**lease, 'status': 'failed'}, 'trinity-0-3', (1,), uuids))
        self.assertFalse(resources.blocks(lease, 'trinity-2-28', (1,), uuids))
        self.assertEqual(resources.named_cards({'command': 'GPUs 3-6, 7'}), {3, 4, 5, 6, 7})

    def test_site_refuses_partial_or_foreign_training_placements(self):
        with patch.object(resources.socket, 'gethostname', return_value='trinity-0-3'), patch.object(resources, 'load',
                return_value={'site_id': 'trinity', 'coord_root': str(resources.COORD_ROOT)}):
            self.assertEqual(resources.site((4, 5, 6, 7), 'training'), 'trinity-0-3')
            for cards in ((4,), (0, 1, 2, 3), (4, 5, 6, 6)):
                with self.subTest(cards=cards), self.assertRaises(ValueError):
                    resources.site(cards, 'training')
            with self.assertRaises(ValueError):
                resources.site((4,), 'evaluation')

    def test_dual_device_locks_do_not_admit_a_changed_uuid(self):
        device = {'uuid': 'GPU-first', 'index': 4}
        with patch.object(resources, 'site', return_value='trinity-0-3'), patch.object(resources, 'probe',
                side_effect=[[device], [{**device, 'uuid': 'GPU-changed'}]]), patch.object(resources, 'inspect_leases',
                return_value=[]), patch.object(resources, 'lock') as lock:
            with self.assertRaises(ValueError):
                with resources.locked_devices((4,), 'training'):
                    self.fail('A changed UUID entered the GPU scope')
            self.assertEqual(lock.call_count, 2)

    def test_ambient_warm_start_and_resume_flags_are_removed(self):
        with patch.dict(resources.os.environ, {'INIT_ADAPTER': 'foreign', 'RESUME_FROM': 'foreign', 'CUDA_VISIBLE_DEVICES': '7'}):
            value = resources.environment()
            self.assertNotIn('INIT_ADAPTER', value)
            self.assertNotIn('RESUME_FROM', value)
            self.assertEqual(value['CUDA_VISIBLE_DEVICES'], '')


class ColdIdentityTests(unittest.TestCase):
    def test_cold_first_step_accepts_large_finite_loss_and_refuses_warm_state(self):
        protocol = {'base': {'revision': 'frozen'}, 'base_sha256': 'a' * 64}
        header = {**protocol, 'base_restart': 'fresh_load_of_original_snapshot_no_smoke_adapter'}
        proof = cold_first_step({'step': 1, 'loss': 8.0}, {}, header, protocol)
        self.assertIsNone(proof['init_adapter_identity'])
        self.assertEqual(proof['step_1_loss'], 8.0)
        for changed in ({'initialization': {}}, {'initialization_source': 'parent'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                cold_first_step({'step': 1, 'loss': .1}, changed, header, protocol)
        with self.assertRaises(ValueError):
            cold_first_step({'step': 1, 'loss': float('nan')}, {}, header, protocol)

    def test_only_the_fixed_cold_recipe_is_admitted(self):
        raw = {'world_size': 4, 'epochs': 1, 'seed': 17, 'checkpoint_every_steps': 188,
               'answer_format_instruction': ANSWER_FORMAT_INSTRUCTION}
        protocol = {'training': normalize_training_config(raw, 'qwen35'), 'answer_format_instruction': ANSWER_FORMAT_INSTRUCTION}
        check_cold(protocol, raw, 17)
        with self.assertRaises(ValueError):
            check_cold({**protocol, 'init_adapter_identity': {}}, raw, 17)
        with self.assertRaises(ValueError):
            check_cold(protocol, raw, 18)


class DiagnosticTransportTests(unittest.TestCase):
    def test_input_builder_and_packet_import_without_gpu(self):
        import importlib
        import sys
        for name in ('scripts.tracecold_step0_prepare', 'scripts.tracecold_seal', 'scripts.tracecold_read_native'):
            self.assertTrue(callable(importlib.import_module(name).main))
        if 'torch' in sys.modules:
            self.assertFalse(sys.modules['torch'].cuda.is_initialized())

    def test_native_cohort_guard_reads_the_bound_json_admission_projection(self):
        from uuid import uuid4
        from scripts.tracecold_bare_prepare import guard_projection
        from scripts.tracecold_step0_prepare import reference_modules
        contracts, _ = reference_modules()
        root = resources.OUT / 'fixtures' / ('guard_' + uuid4().hex)
        root.mkdir(parents=True, exist_ok=False)
        values = [{'qid': '1000000', 'student_input': {'question': 'synthetic'}},
                  {'qid': '1000001', 'student_input': {'question': 'synthetic'}}]
        inputs = resources.io.save_rows(root / 'inputs.jsonl', values)
        guard = {'source': resources.pin('/home/jjyeung/agent_project/agent/scripts/cohort_guard.py'),
                 'registry': resources.pin('/home/jjyeung/agent_project/agent/evaluation/RETIRED_COHORTS.json')}
        manifest = {'guard': guard, 'membership': resources.save(root / 'membership.json', {'qids': [1000000, 1000001]})}
        with self.assertRaisesRegex(Exception, 'cannot read JSON|Extra data'):
            contracts.guard_inputs(guard['source'], guard['registry'], [inputs['path']])
        result = guard_projection(contracts, manifest, inputs, root)
        self.assertEqual(result['inputs'], inputs)
        self.assertEqual(resources.load(resources.verify(result['admission_input'])), values)
        self.assertEqual(len(result['results']), 2)

    def test_cell_membership_generation_and_placement_are_fixed(self):
        runtime = [{'path': 'synthetic', 'sha256': '0' * 64}]
        for kind, count in (('bare', 251), ('heldout', 269)):
            cell = kind + '_CS_s17'
            value = {'cell': cell, 'expected_count': count, 'models': {cell: {}}, 'generation': GENERATION,
                     'code': runtime, 'assignments': [['trinity-0-13', 1]], 'status': 'APPROVED_FOR_DIAGNOSTIC_EVALUATION',
                     'supports_decisions': False, 'score_nomination_allowed': False}
            validate_job(value, cell, {'runtime_code': runtime})
            for key, replacement in (('expected_count', 1), ('supports_decisions', True),
                                     ('assignments', [['trinity-0-3', 4]]), ('generation', {**GENERATION, 'max_new_tokens': 16384})):
                with self.subTest(kind=kind, key=key), self.assertRaises(ValueError):
                    validate_job({**value, key: replacement}, cell, {'runtime_code': runtime})


if __name__ == '__main__':
    unittest.main()
