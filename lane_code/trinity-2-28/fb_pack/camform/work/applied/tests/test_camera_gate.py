"""Camera-loss early-stop gate: decisions on synthetic curves, rank consistency, config pinning and exit status."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student_pilot import camera_config
from student_pilot.camera_gate import GATE_STOPPED_EXIT_CODE, CameraGate, LMGate, exit_status, normalize_gate, normalize_lm_gate

GATE = {'baseline_step': 50, 'check_step': 200, 'min_relative_drop': 0.2, 'window': 10}
PIN = {'path': '/fixture/camera', 'sha256': '0' * 64}
REFERENCE = [0.10481, 0.10921, 0.10986, 0.11402, 0.10856, 0.10866, 0.11407, 0.10695, 0.10667, 0.10374]
LM = {'check_step': 200, 'window': 10, 'max_relative_increase': 0.1,
      'reference': {'run': 'reference_run', 'metrics_sha256': 'a' * 64, 'steps': list(range(191, 201)), 'values': REFERENCE}}


def run(curve, rows=lambda step: 8, gate=GATE):
    """Feed per-step mean losses (times the supervised row count) and return every non-empty decision."""
    camera = CameraGate(gate)
    decisions = {}
    for step in range(1, gate['check_step'] + 1):
        count = rows(step)
        camera.record(step, curve(step) * count, count)
        decision = camera.decide(step)
        if decision is not None:
            decisions[step] = decision
    return decisions


class GateTests(unittest.TestCase):
    def test_a_falling_loss_passes_at_the_check_step_only(self):
        decisions = run(lambda step: 2.0 * 0.995 ** step)
        self.assertEqual(list(decisions), [200])
        record = decisions[200]
        self.assertEqual(record['status'], 'GATE_PASSED')
        self.assertEqual((record['baseline_steps'], record['check_steps']), (list(range(41, 51)), list(range(191, 201))))
        base = sum(2.0 * 0.995 ** s for s in range(41, 51)) / 10
        check = sum(2.0 * 0.995 ** s for s in range(191, 201)) / 10
        self.assertAlmostEqual(record['relative_drop'], (base - check) / base)
        self.assertGreaterEqual(record['relative_drop'], 0.2)

    def test_a_flat_loss_stops_with_a_reason_and_the_exit_status(self):
        record = run(lambda step: 1.0 - 0.0002 * step)[200]
        self.assertEqual(record['status'], 'GATE_STOPPED')
        self.assertLess(record['relative_drop'], 0.2)
        self.assertEqual(record['exit_code'], GATE_STOPPED_EXIT_CODE)
        self.assertIn('under the required 0.2', record['reason'])
        self.assertEqual(exit_status({'status': 'GATE_STOPPED'}), GATE_STOPPED_EXIT_CODE)
        self.assertEqual(exit_status({'status': 'TRAINED'}), 0)

    def test_only_steps_with_pose_rows_count(self):
        # Odd steps carry no pose rows and a misleading loss; they must not enter the windows.
        record = run(lambda step: 1.0 if step % 2 == 0 else 100.0, rows=lambda step: 8 if step % 2 == 0 else 0)[200]
        self.assertEqual(record['baseline_steps'], [42, 44, 46, 48, 50])
        self.assertEqual((record['baseline_mean'], record['check_mean'], record['relative_drop']), (1.0, 1.0, 0.0))
        empty = run(lambda step: 1.0, rows=lambda step: 0 if 41 <= step <= 50 else 8)[200]
        self.assertEqual(empty['status'], 'GATE_STOPPED')
        self.assertIn('no optimizer step', empty['reason'])
        zero = run(lambda step: 0.0)[200]
        self.assertEqual(zero['status'], 'GATE_STOPPED')

    def test_ranks_reach_one_decision_from_all_reduced_sums(self):
        world = 4
        gates = [CameraGate(GATE) for _ in range(world)]
        single = CameraGate(GATE)
        records = []
        for step in range(1, 201):
            # Each rank holds a different share of the rows and of the loss; the all-reduce sums them.
            local = [((rank + 1) * 0.3 * 0.996 ** step * (rank + step % 3), rank + step % 3) for rank in range(world)]
            total = (sum(x for x, _ in local), sum(n for _, n in local))
            for gate in gates:
                gate.record(step, *total)
            single.record(step, *total)
            decisions = [gate.decide(step) for gate in gates]
            self.assertTrue(all(d == decisions[0] for d in decisions))
            if decisions[0] is not None:
                records.append(decisions[0])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], single.decide(200))

    def test_history_restores_from_metrics_lines(self):
        live = CameraGate(GATE)
        lines = []
        for step in range(1, 120):
            loss, rows = 3.0 / step, 4.0
            live.record(step, loss * rows, rows)
            lines.append({'step': step, 'auxiliary': {'camera_gate_sample': {'step': step, 'loss_sum': loss * rows, 'rows': rows}}})
        resumed = CameraGate(GATE)
        resumed.restore(lines)
        self.assertEqual(resumed.samples, live.samples)

    def test_gate_settings_validate_and_are_pinned_outside_the_training_settings(self):
        self.assertIsNone(camera_config.normalize({})['gate'])
        self.assertEqual(normalize_gate(GATE), GATE)
        for bad in [{**GATE, 'window': 0}, {**GATE, 'check_step': 55}, {**GATE, 'window': 60}, {**GATE, 'min_relative_drop': 1.0},
                    {**GATE, 'extra': 1}, {k: v for k, v in GATE.items() if k != 'window'}, {**GATE, 'baseline_step': 1.5}]:
            with self.assertRaises(ValueError, msg=str(bad)):
                normalize_gate(bad)
        from student_pilot import ddp_config
        from student_pilot.common import digest_json
        from student_pilot.provisional_data import training_protocol_fields
        root = Path(tempfile.mkdtemp(prefix='camera-gate-test-'))
        fields = {}
        for name, camera in (('plain', {'weight': 0.2, 'supervision': PIN}), ('gated', {'weight': 0.2, 'supervision': PIN, 'gate': GATE})):
            (root / f'{name}.json').write_text(json.dumps({'world_size': 32, 'camera': camera}))
            fields[name] = training_protocol_fields(root / f'{name}.json', 'qwen35')
        self.assertEqual(fields['gated']['training'], fields['plain']['training'])
        self.assertEqual(fields['gated']['camera']['gate'], GATE)
        self.assertNotEqual(fields['gated']['camera_sha256'], fields['plain']['camera_sha256'])
        self.assertEqual(fields['gated']['camera_sha256'], digest_json(fields['gated']['camera']))
        self.assertEqual(ddp_config.validate_camera_protocol(fields['gated']), fields['gated']['camera'])

    def test_cli_returns_the_documented_status(self):
        from student_pilot import provisional_cli
        argv = ['train-ddp', '--manifest', 'm', '--protocol', 'p', '--lease', 'l', '--output', 'o', '--scratch-root', 's',
                '--provisional-diagnostic', 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW']
        for result, code in (({'status': 'GATE_STOPPED'}, GATE_STOPPED_EXIT_CODE), ({'status': 'TRAINED'}, 0)):
            with patch('student_pilot.ddp_training.train', lambda *args, **kwargs: result), patch('builtins.print'):
                self.assertEqual(provisional_cli.main(argv), code)


class LMGateTests(unittest.TestCase):
    @staticmethod
    def run_lm(curve, rows=lambda step: 240, gate=LM):
        lm = LMGate(gate)
        decisions = {}
        for step in range(1, gate['check_step'] + 1):
            count = rows(step)
            lm.record(step, curve(step) * count, count)
            decision = lm.decide(step)
            if decision is not None:
                decisions[step] = decision
        return decisions

    def test_matching_or_slightly_higher_loss_passes_at_the_check_step_only(self):
        reference = sum(REFERENCE) / 10
        for factor in (1.0, 1.0999):
            decisions = self.run_lm(lambda step: reference * factor)
            self.assertEqual(list(decisions), [200])
            self.assertEqual(decisions[200]['status'], 'GATE_PASSED')
            self.assertAlmostEqual(decisions[200]['relative_increase'], factor - 1)
            self.assertEqual(decisions[200]['check_steps'], list(range(191, 201)))

    def test_loss_over_ten_percent_above_the_reference_stops_with_a_reason(self):
        record = self.run_lm(lambda step: sum(REFERENCE) / 10 * 1.11)[200]
        self.assertEqual((record['status'], record['exit_code'], record['gate']), ('GATE_STOPPED', GATE_STOPPED_EXIT_CODE, 'lm'))
        self.assertIn('above the reference', record['reason'])
        self.assertIn('reference_run', record['reason'])
        empty = self.run_lm(lambda step: 0.1, rows=lambda step: 0 if step > 190 else 240)[200]
        self.assertEqual(empty['status'], 'GATE_STOPPED')
        self.assertIn('no optimizer step', empty['reason'])

    def test_the_mean_is_over_text_rows_only(self):
        # Pose-only rows add neither loss nor rows, so fewer text rows at the same per-row loss give the same mean.
        lm = LMGate(LM)
        for step in range(1, 201):
            rows = 200 if step % 2 else 256
            lm.record(step, 0.105 * rows, rows)
        record = lm.decide(200)
        self.assertAlmostEqual(record['check_mean'], 0.105)
        self.assertEqual(record['status'], 'GATE_PASSED')

    def test_history_restores_and_settings_validate(self):
        live, lines = LMGate(LM), []
        for step in range(1, 150):
            live.record(step, 0.2 * 100, 100)
            lines.append({'step': step, 'auxiliary': {'lm_gate_sample': {'step': step, 'loss_sum': 20.0, 'rows': 100.0}}})
        resumed = LMGate(LM)
        resumed.restore(lines)
        self.assertEqual(resumed.samples, live.samples)
        self.assertIsNone(camera_config.normalize({})['lm_gate'])
        self.assertEqual(normalize_lm_gate(LM), LM)
        ref = LM['reference']
        for bad in [{**LM, 'window': 0}, {**LM, 'window': 201}, {**LM, 'max_relative_increase': 1.0}, {**LM, 'extra': 1},
                    {**LM, 'reference': {**ref, 'steps': list(range(190, 200))}}, {**LM, 'reference': {**ref, 'values': REFERENCE[:9]}},
                    {**LM, 'reference': {**ref, 'values': [0.0] * 10}}, {**LM, 'reference': {**ref, 'metrics_sha256': 'x'}},
                    {**LM, 'reference': {**ref, 'run': ''}}, {k: v for k, v in LM.items() if k != 'reference'}]:
            with self.assertRaises(ValueError, msg=str(bad)):
                normalize_lm_gate(bad)

    def test_lm_gate_is_pinned_in_the_camera_block_only(self):
        from student_pilot.provisional_data import training_protocol_fields
        root = Path(tempfile.mkdtemp(prefix='lm-gate-test-'))
        fields = {}
        for name, camera in (('plain', {'weight': 0.2, 'supervision': PIN, 'gate': GATE}),
                             ('both', {'weight': 0.2, 'supervision': PIN, 'gate': GATE, 'lm_gate': LM})):
            (root / f'{name}.json').write_text(json.dumps({'world_size': 32, 'camera': camera}))
            fields[name] = training_protocol_fields(root / f'{name}.json', 'qwen35')
        self.assertEqual(fields['both']['training'], fields['plain']['training'])
        self.assertEqual(fields['both']['camera']['lm_gate'], LM)
        self.assertNotEqual(fields['both']['camera_sha256'], fields['plain']['camera_sha256'])


if __name__ == '__main__':
    unittest.main()
