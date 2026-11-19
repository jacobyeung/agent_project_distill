import os
import tempfile
import unittest

from rltests.fixture import FixtureBackend, prompt, sampler_config
from rltests.test_reward import EOS, FT, FT_BODY, program
from rlkit import headuse, sampler, store as storemod

GOOD = program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56')
import re as _re
_RESP = [m.strip('\n') for m in _re.findall(r'<tool_response>(.*?)</tool_response>', GOOD, _re.S)]
CALLS = [dict(call='<ground obj="cup" mode="box">', kind='ground', response=_RESP[0]),
         dict(call='<ground obj="trash can" mode="box">', kind='ground', response=_RESP[1]),
         dict(call='<gap a="cup" b="trash can" rule="box_grid_5cm">', kind='gap', response=_RESP[2])]


def rec(draw, text, calls, path='free', n=80):
    return dict(prompt_id='p', draw=draw, path=path, text=text + EOS, own_tokens=n, finish='eos', budget_hit=False,
                calls=calls)


class HeadUse(unittest.TestCase):
    def test_summary_placement_and_split(self):
        p = dict(FT, scene_key='s', source='reserve_r0_rl')
        recs = [rec(0, GOOD, CALLS), rec(1, GOOD, CALLS[2:]), rec(2, 'The gap is about 3 m.\n</think>\n<answer>9</answer>', []),
                rec(3, 'It is 3.2 m. ' + GOOD, CALLS, path='head')]
        usage = {'p|0': dict(moved=True), 'p|1': dict(moved=False)}
        out = headuse.summarize([p], {'p': recs}, dict(n_ref={'object_abs_distance': 300}), usage=usage)
        t = out['types']['object_abs_distance']
        self.assertEqual(t['call_rate'], 0.75)
        self.assertAlmostEqual(t['free_call_rate'], 2 / 3)
        self.assertEqual(t['placement'], {'exact': 2, 'missing': 1, 'none': 1})
        self.assertEqual(t['heads'], {'ground': 4, 'gap': 3})
        self.assertAlmostEqual(t['estimate_first_rate'], 1 / 3)
        self.assertEqual((t['usage_rate'], t['usage_n']), (0.5, 2))
        self.assertEqual(t['reward_split']['called']['rollouts'], 3)
        self.assertEqual(t['reward_split']['not_called']['r'], 0.0)
        self.assertGreater(t['reward_split']['called']['r'], 0.0)
        text = headuse.curve([dict(out, label='r0')])
        self.assertIn('| r0 |', text)

    def test_perturb_scales_measures_only(self):
        self.assertEqual(headuse.perturb_text('frames 2,3 (best 3)\ndistance 3.22 m'), 'frames 2,3 (best 3)\ndistance 4.41 m')
        self.assertEqual(headuse.perturb_text('size 1.25 x 0.64 x 0.74 m'), 'size 1.71 x 0.88 x 1.01 m')
        self.assertEqual(headuse.perturb_text('B1: f1 centre (-0.23, 0.00, -2.28) m'), 'B1: f1 centre (-0.32, 0.00, -3.12) m')
        self.assertEqual(headuse.perturb_text('yaw -88 deg; 3 instances'), 'yaw -120.56 deg; 3 instances')

    def test_usage_redecodes_the_same_draw_with_perturbed_responses(self):
        be = FixtureBackend()
        prompts = [prompt('p1')]
        raw = sampler_config(draws=4, temperature=1.0)
        with tempfile.TemporaryDirectory() as tmp:
            sampler.run(raw, prompts, tmp, backend=be)
            groups = storemod.DrawStore(tmp, sampler.SamplerConfig(raw).identity).groups(prompts, 4)
        head = groups['p1'][2]
        self.assertTrue(head['calls'])
        res = headuse.usage_for(raw, be, prompts, groups)
        self.assertIn('p1|2', res)
        u = res['p1|2']
        self.assertEqual(u['responses'][0], headuse.perturb_text(u['base_responses'][0]))
        self.assertNotEqual(u['responses'][0], u['base_responses'][0])
        self.assertEqual(u['base_responses'][0], head['calls'][0]['response'])  # same forced call, same served value
        again = headuse.usage_for(raw, be, prompts, groups)
        self.assertEqual(again, res)  # greedy: no sampling noise


if __name__ == '__main__':
    unittest.main()
