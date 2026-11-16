import hashlib
import unittest
from pathlib import Path
from navrun.actions import Decoder
from navrun.config import Config, load_arm
from navrun.controller_v2 import ControllerV2, BLOCKED_EPS_M, controller_v1
from navrun.episodes import load_split
from navrun.io import read_json, ordered_id_sha256
from navrun.paths import ROOT
from navrun.policies import OracleClickPolicy, ScriptPolicy
from navrun.runner import Runner
from navrun.sim import Environment
from vla_where.nav import ClickTranslator
import vla_where.nav


class ControllerUnitTests(unittest.TestCase):
    def setUp(self):
        self.c = ControllerV2()

    def decide(self, bearing=1):
        return self.c.decide(controller_v1(bearing, .75), None, {'bearing_deg':bearing})[0]

    def test_normal_parity(self):
        for beta in (-180, -7.5, -1, 0, 1, 7.5, 180):
            self.assertEqual(self.decide(beta), controller_v1(beta, .75))

    def test_blocked_probe_and_latched_direction(self):
        for beta, direction in ((1,'turn_left'),(-1,'turn_right'),(0,'turn_left')):
            self.c.reset(); self.decide(beta)
            self.assertTrue(self.c.executed('forward', 0))
            self.assertEqual(self.decide(-beta), [direction, 'forward'])
            self.assertFalse(self.c.executed(direction, 0))
            self.assertTrue(self.c.executed('forward', 0))
            self.assertEqual(self.decide(-beta), [direction, 'forward'])

    def test_motion_resets_recovery(self):
        self.decide(); self.c.executed('forward', 0)
        self.assertFalse(self.c.executed('forward', .25))
        self.assertEqual(self.decide(), ['forward']*3)

    def test_numeric_block_boundary(self):
        self.assertTrue(self.c.executed('forward', BLOCKED_EPS_M/2))
        self.assertFalse(self.c.executed('forward', BLOCKED_EPS_M))

    def test_stop_and_reset(self):
        self.decide(); self.c.executed('forward', 0)
        self.assertEqual(self.c.decide(['stop'], None, {})[0], ['stop'])
        self.c.reset(); self.assertEqual(self.decide(), ['forward']*3)

    def test_config_default_and_validation(self):
        self.assertEqual(Config().controller_version, 'v2')
        self.assertEqual(load_arm(ROOT/'configs/NU.json')[1].controller_version, 'v2')
        with self.assertRaises(ValueError): Config(controller_version='v3')

    def test_external_translator_uses_selected_version(self):
        obs = dict(frames=[None]*32, instruction='', executed=(), decision_index=0, constants={})
        for version in ('v1','v2'):
            backend=ClickTranslator()
            decoder=Decoder(Config(output_format='click',controller_version=version),backend)
            text='<goal frame=32 x=0.49 y=0.99>'
            original=backend.decide(text,obs)[0]
            self.assertEqual(decoder.decode(text,obs)[0],original)
            self.assertEqual(decoder.executed('forward',0), version=='v2')
            self.assertEqual(decoder.decode(text,obs)[0],
                             ['turn_left','forward'] if version=='v2' else original)
            decoder.reset(); self.assertEqual(decoder.decode(text,obs)[0],original)

    def test_runner_cancels_blocked_leg_and_accounts_issued_steps(self):
        class BlockedEnvironment(Environment):
            def step(self, action):
                if action != 'forward':
                    return super().step(action)
                self.steps += 1
                self.positions.append(self.position)
                return None
        episode=load_split('val_unseen')[0]
        for version in ('v1','v2'):
            env=BlockedEnvironment(Config(output_format='click',controller_version=version,step_cap=3))
            backend=ClickTranslator()
            try:
                r=Runner(env,click_backend=backend).episode(episode,ScriptPolicy(['<goal frame=32 x=0.49 y=0.75>']))
                self.assertEqual(r['termination'],'step_cap')
                self.assertEqual(r['actions'], ['forward']*3 if version=='v1' else ['forward','turn_left','forward'])
                self.assertEqual(backend.commanded_m,[.75] if version=='v1' else [.25,.25])
            finally:
                env.close()


class StallReplayTests(unittest.TestCase):
    def test_replay_all_102_stalled_episodes(self):
        fixture=read_json(ROOT/'tests/fixtures/controller_v1_stalls.json')
        rows=fixture['episodes']; self.assertEqual(len(rows),102)
        self.assertEqual(ordered_id_sha256([r['episode_id'] for r in rows]),fixture['ordered_id_sha256'])
        self.assertEqual(hashlib.sha256(Path(vla_where.nav.__file__).read_bytes()).hexdigest(),
                         fixture['controller_v1_sha256'])
        episodes={e.episode_id:e for e in load_split('val_unseen')}
        for version in ('v1','v2'):
            env=Environment(Config(output_format='click',controller_version=version))
            try:
                runner=Runner(env); policy=OracleClickPolicy(env)
                for row in rows:
                    with self.subTest(version=version,episode_id=row['episode_id']):
                        trace=[]; result=runner.episode(episodes[row['episode_id']],policy,trace=trace)
                        if version=='v1':
                            self.assertEqual(result['actions'],row['actions'])
                            self.assertEqual(result['decisions'],row['decisions'])
                            self.assertEqual(result['termination'],'step_cap')
                            self.assertTrue(result['stationary_tail'])
                            for actual,expected in zip(trace[-20:],row['tail']):
                                for key in ('step','position','heading','answer','primitives'):
                                    self.assertEqual(actual[key],expected[key])
                        else:
                            self.assertFalse(result['stationary_tail'])
            finally:
                env.close()
