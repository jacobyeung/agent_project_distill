"""Reviewer refute tests (review_h1kit). Each test asserts the registered behaviour; a failure is a finding."""
import json, unittest
from pathlib import Path
from unittest.mock import patch
import torch
from tests.fixtures import camera_fixtures, tiny, packed, routing_batch, Processor, K
from student_pilot import h1, h1_faithful as F, carrier_c1_routing as R, carrier_c1_run as run

class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.clip, _ = camera_fixtures()

    def test_F1_answer_differs_is_not_wrong_answer(self):
        # A 1% own translation error should not count as "faithful answer differs from GT" for the 35% stop rule.
        raw = next(r for r in self.raw if r['question_type'] == 'camera_displacement')
        row = packed(raw, self.clip); p = torch.tensor(raw['gt_pose9']).numpy(); p[:, :3] *= 1.01
        out, *_ = h1.faithful(row, R.OwnGeometry(p, raw['gt_up'], None))
        differs = str(out['answer']) != str(raw['answer'])  # h1_faithful.py own_values definition
        self.assertFalse(differs, f"own {out['answer']} vs GT {raw['answer']} counted as differing")

    def test_F1_stop_rule_implemented(self):
        src = (K/'tree/student_pilot/carrier_c1_run.py').read_text() + (K/'tree/student_pilot/h1.py').read_text()
        self.assertTrue('.35' in src and 'answer_differs' in (K/'tree/student_pilot/carrier_c1_run.py').read_text(),
                        'registered 35% faithful-answer stop rule (steps 1-50) has no trainer implementation')

    def test_F2_step1_draws_own_camera_rows(self):
        cfg = json.loads((K/'configs/h1_1.json').read_text()); g = R.Gates(cfg['recipe']['scheduled_sampling'], False)
        factor = cfg['recipe']['reference_world_size'] // cfg['recipe']['world_size']
        groups = sorted({i // factor for i, s in enumerate(cfg['recipe']['mix']) if s == 'routing'})
        self.assertTrue(any(g.decide(1, gid)[1] for gid in groups),
                        f'step 1 routing groups {groups} all draw GT pose; real_first_batch.py decide(1, .) never runs S1')

    def test_F3_registered_modes(self):
        from h1eval.cli import modes
        cfg = json.loads((K/'configs/eval.json').read_text())
        rot = [m for m in cfg['modes'] if m['name'] == 'rotate_translation']
        self.assertEqual(rot[0]['deg'], 180.0, 'registered movement-direction perturbation is 180 deg')
        modes('scale_translation:0.5,scale_translation:2,scale_scene:0.5,scale_scene:2')  # both registered directions

    def test_F4_m1_m2_bars(self):
        from h1eval import statistics as S
        row = lambda arm, score: dict(id='a', room_key='r', type='camera_displacement', arm=arm, mode='none',
            measurements=dict(M1=dict(call_rate=1., exact=True, openers=['move']), M2=dict(calls=[]), M4=dict(score=score)))
        agg = S.aggregate([row('own', .5), row('tower', .9)])
        rec = agg['camera_displacement']['own']['none']
        self.assertIn('passes_bars', rec['M1'], 'M1 registered bars (98/95/1/2/5 %) not evaluated')
        self.assertTrue(any('tower' in k for k in json.dumps(agg).split('"')) and 'own_minus_tower' in json.dumps(agg),
                        'M2 bar needs own-minus-tower paired interval; none computed')

    def test_F5_unexpected_error_counts_as_refusal(self):
        model, base, _ = tiny(); row = packed(self.raw[0], self.clip); batch, a = routing_batch(base, row)
        class Rows:
            processor = Processor(); h1 = {'faithful_own_camera_rows': True}
            def row(self, *args): return row, None
        with patch.object(R, 'encode_own', side_effect=ValueError('A token straddles a tool-output span edge')):
            try:
                b, audit = run.own_values(model, Rows(), batch, a, 0, (True, True), torch.device('cpu'))
            except ValueError as e:
                self.fail('per-rank ValueError escapes S1 with no all-reduce (other ranks hang): ' + str(e))

    def test_F6_modes_only_on_target_types(self):
        from h1eval import runner
        calls = []
        def factory(arm, mode, item):
            calls.append(mode['name']); return lambda it: dict(text='<answer>A</answer>', calls=[], tokens=[])
        item = dict(id='d', room_key='r', question='How many chairs?', question_type='object_counting', options=[])
        import tempfile
        with tempfile.TemporaryDirectory(dir=str(K/'tmp')) as d:
            runner.run([item], factory, ['own'], [{'name': 'scale_translation', 'k': 2.}, {'name': 'negate_turn'}], d)
        self.assertEqual(calls, ['none'], f'direct item decoded {len(calls)} times: {calls}')

if __name__ == '__main__': unittest.main()
