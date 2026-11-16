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
        # ORCH RULING 1535Z: own-value rows train on the model's own answer; the stop metric is tolerance-based, never "answer != GT".
        raw = next(r for r in self.raw if r['question_type'] == 'camera_displacement')
        row = packed(raw, self.clip); p = torch.tensor(raw['gt_pose9']).numpy().copy(); p[:, :3] *= 1.01
        out, target, *_ = h1.faithful(row, R.OwnGeometry(p, raw['gt_up'], None))
        self.assertIn(str(out['answer']), target, 'faithful target must carry the own answer')
        self.assertFalse(F.answer_differs(raw['question_type'], out['answer'], raw['answer']),
                         f"1% own error {out['answer']} vs GT {raw['answer']} counted as differing")
        far = p.copy(); far[:, :3] *= 1.2
        out2, *_ = h1.faithful(row, R.OwnGeometry(far, raw['gt_up'], None))
        self.assertTrue(F.answer_differs(raw['question_type'], out2['answer'], raw['answer']), '>10% displacement must differ')

    def test_F1_perturbation_moves_answer_vs_unperturbed(self):
        # ORCH RULING 1535Z: M3 compares the perturbed answer with the SAME model's unperturbed answer, never with GT.
        import numpy as np
        from h1eval.perception import Heads, perturb
        from h1eval.scorers import usage
        flip = {'left': 'right', 'right': 'left', 'forward': 'backward', 'backward': 'forward'}
        modes = {'camera_displacement': [{'name': 'scale_translation', 'k': .5}, {'name': 'scale_translation', 'k': 2.}],
                 'camera_movement_direction': [{'name': 'rotate_translation', 'deg': 180.}],
                 'camera_rotation': [{'name': 'negate_turn'}]}
        seen = set()
        for raw in self.raw:
            kind = raw['question_type']; row = packed(raw, self.clip)
            p = torch.tensor(raw['gt_pose9']).numpy().copy(); p[:, :3] *= 1.01
            own = Heads(p, np.asarray(raw['gt_up']), None, 'own')
            base, *_ = h1.faithful(row, R.OwnGeometry(own.pose9, own.gravity, None))
            for mode in modes[kind]:
                h, _ = perturb(own, mode); g = h.turn_pose9 if h.turn_pose9 is not None else h.pose9
                out, *_ = h1.faithful(row, R.OwnGeometry(g, h.gravity, None))
                if kind == 'camera_displacement':
                    self.assertAlmostEqual(float(out['answer']), mode['k'] * float(base['answer']), delta=.02 * mode['k'] * float(base['answer']) + .01)
                elif kind == 'camera_rotation':
                    self.assertAlmostEqual(float(out['answer']), -float(base['answer']), delta=1.)
                else:
                    label = {o.split('. ', 1)[0]: o.split('. ', 1)[1] for o in raw['options']}
                    self.assertEqual(label[out['answer']], flip[label[base['answer']]])
                seen.add(kind)
        self.assertEqual(seen, set(modes))
        item = dict(question_type='camera_displacement', question='How far in centimeters?')
        def o(n, a): return dict(calls=[dict(call='<move from=1 to=2>', response=f'dx = 0 m, dy = 0 m, dz = {n} m, distance = {n} m')], text=f'<answer>{a}</answer>')
        a = usage(o(1, 100), o(2, 200), item); b = usage(o(1, 100), o(2, 200), {**item, 'answer': '7', 'gt': 7.})
        self.assertEqual(a, b, 'usage must not read GT'); self.assertEqual(a['follow'], 1.)

    def test_F1_stop_rule_implemented(self):
        src = (K/'tree/student_pilot/carrier_c1_run.py').read_text() + (K/'tree/student_pilot/h1.py').read_text()
        self.assertTrue('.35' in src and 'answer_differs' in (K/'tree/student_pilot/carrier_c1_run.py').read_text(),
                        'registered 35% faithful-answer stop rule (steps 1-50) has no trainer implementation')

    def test_F2_step2_and_forced_pose_own_cover_every_rank(self):
        # ORCH RULING 1535Z: the first-batch tools run step 2; one run forces pose-own so S1 runs on every rank.
        import copy
        cfg = json.loads((K/'configs/h1_1.json').read_text()); g = R.Gates(cfg['recipe']['scheduled_sampling'], False)
        factor = cfg['recipe']['reference_world_size'] // cfg['recipe']['world_size']
        groups = sorted({i // factor for i, s in enumerate(cfg['recipe']['mix']) if s == 'routing'})
        self.assertTrue(any(g.decide(2, gid)[1] for gid in groups), f'step 2 routing groups {groups} all draw GT pose')
        for name in ('real_first_batch.py', 'run_first_batch.py'):
            self.assertIn('force-pose-own', (K/'first_batch'/name).read_text(), name + ' lacks the forced pose-own run')
        forced = copy.deepcopy(cfg['recipe']['scheduled_sampling']); forced['max_own_probability'] = 1.
        f = R.Gates(forced, False)
        self.assertTrue(all(f.decide(step, gid)[1] for step in (1, 2) for gid in groups), 'forced schedule leaves a GT pose draw')

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
