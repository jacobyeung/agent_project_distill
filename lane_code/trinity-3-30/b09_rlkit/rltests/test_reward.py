"""Planted reward cases: correct long, correct short, wrong short, detached answer, empty think,
program chains, replay, budget, MRA parity."""
import unittest

from rlkit.reward import score_group
from rlkit.score import mra

EOS = '<|im_end|>'
REL_Q = 'Using closest-point distance, which of these objects is the closest to the couch?'
REL_OPTS = ['A. metronome', 'B. tv', 'C. door', 'D. piano bench']
REL_BODY = ('Step 1: find the couch, first seen in frame 1.\n'
            'Step 2: the candidates ordered nearest to farthest from the couch are: piano bench, then tv, then door and metronome (tied).\n'
            'The question asks for the closest object, the piano bench.\n')
REL_SHORT = 'Step 1: the piano bench is nearest to the couch.\n'
WRONG_SHORT = 'Step 1: the tv is nearest to the couch.\n'
FT_Q = 'Measuring from the closest point of each object, what is the distance between the cup and the trash can (in feet)?'
FT_BODY = ('I will ground the boxes and ask the tool to measure their box distance.\n'
           '<ground obj="cup" mode="box">\n<tool_response>\ncup: frames 9,15,16,22,23,31 (best 23)\n'
           'B1: f1 centre (-2.09, -0.51, -1.07) m\nsize 0.05 x 0.04 x 0.09 m\n'
           'yaw -153 deg (0 = +x; positive +x toward -z about +y)\n</tool_response>\n'
           '<ground obj="trash can" mode="box">\n<tool_response>\ntrash can: frames 1,29 (best 1)\n'
           'B2: f1 centre (0.15, -1.15, 1.33) m\nsize 0.16 x 0.15 x 0.18 m\n'
           'yaw 12 deg (0 = +x; positive +x toward -z about +y)\n</tool_response>\n'
           '<gap a="cup" b="trash can" rule="box_grid_5cm">\n<tool_response>\ndistance 3.22 m\n</tool_response>\n'
           "The box gap is the smallest distance between points on a grid over both objects' full boxes, taken over every pair of instances.\n"
           '{conv}')


def rec(text, n, draw=0, finish='eos', budget=False, path='free'):
    return dict(prompt_id='p', draw=draw, path=path, text=text + EOS, own_tokens=n, finish=finish,
                budget_hit=budget, calls=[])


def served(r):
    """Give a planted program trace the calls a decoder would have forced (one per printed response)."""
    import re as _re
    r['calls'] = [dict(call='<served>', response=m.strip('\n'), kind='head')
                  for m in _re.findall(r'<tool_response>(.*?)</tool_response>', r['text'], _re.S)]
    r['kinds'] = 'sr'
    return r


def prec(text, n, draw=0, **kw):
    return served(rec(text, n, draw, **kw))


def direct(body, answer):
    return body + '</think>\n\n' + answer


def program(body, answer):
    return body + '</think>\n<answer>' + answer + '</answer>'


REL = dict(prompt_id='p', type='object_rel_distance', question=REL_Q, options=REL_OPTS, gt_answer='D')
FT = dict(prompt_id='p', type='object_abs_distance', question=FT_Q, options=None, gt_answer='10.5')
CFG = dict(lam=0.2, n_ref={'object_rel_distance': 100, 'object_abs_distance': 300})


class Planted(unittest.TestCase):
    def test_mra_parity_with_benchmark_scorer(self):
        self.assertEqual(mra(0, 0), 0.0)
        self.assertLess(mra(8, 10), 1.0)
        self.assertEqual(mra(10, 10), 1.0)
        # |e| = 0.2 passes 1 - t for t = 0.50..0.75; at t = 0.80, 1 - 0.8 = 0.19999999999999996 < 0.2
        self.assertAlmostEqual(mra(8, 10), 0.6)
    def test_correct_long_short_wrong_detached_empty(self):
        rows = score_group(REL, [rec(direct(REL_BODY, 'D'), 60, 0), rec(direct(REL_SHORT, 'D'), 20, 1),
                                 rec(direct(WRONG_SHORT, 'B'), 18, 2), rec(direct(REL_BODY, 'B'), 60, 3),
                                 rec(direct('', 'D'), 3, 4)], CFG)
        long_, short, wrong, detached, empty = rows
        self.assertEqual((long_['c'], long_['g']), (1.0, 1), long_['reasons'])
        self.assertEqual((short['c'], short['g']), (1.0, 1), short['reasons'])
        self.assertEqual(wrong['c'], 0.0)
        self.assertEqual(detached['g'], 0)
        self.assertIn('answer_detached_from_trace', detached['reasons'])
        self.assertEqual(empty['g'], 0)
        self.assertIn('grammar_empty_think', empty['reasons'])
        self.assertGreater(short['r'], long_['r'])
        self.assertGreater(long_['r'], wrong['r'])
        self.assertEqual(wrong['r'], 0.0)
        self.assertEqual(detached['r'], 0.0)
        self.assertGreater(long_['r'], 0.5 * long_['base'])
        # n_min from the group: shortest valid direct trace
        self.assertEqual(long_['n_min'], 20)
        self.assertEqual(short['length_term'], 0.0)

    def test_length_term_cap_keeps_right_above_wrong(self):
        rows = score_group(REL, [rec(direct(REL_BODY, 'D'), 5000, 0), rec(direct(REL_SHORT, 'D'), 20, 1)], CFG)
        self.assertAlmostEqual(rows[0]['r'], 0.5)
        self.assertGreater(rows[0]['r'], 0)

    def test_budget_and_bad_finish_fail_the_gate(self):
        rows = score_group(REL, [rec(direct(REL_SHORT, 'D'), 20, 0, budget=True),
                                 rec(direct(REL_SHORT, 'D'), 20, 1, finish='call_limit')], CFG)
        self.assertEqual([r['g'] for r in rows], [0, 0])
        self.assertEqual([r['r'] for r in rows], [0.0, 0.0])

    def test_program_chain_conversion_and_replay(self):
        good = prec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56'), 120, 0)
        detached = prec(program(FT_BODY.format(conv='The distance is about ten feet.\n'), '10.56'), 110, 1)
        wrong_arith = prec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 11.56.\n'), '11.56'), 120, 2)
        untraced = prec(program(FT_BODY.format(conv='Converting to feet: 3.25 x 3.28084 = 10.66.\n'), '10.66'), 120, 3)
        rows = score_group(FT, [good, detached, wrong_arith, untraced], CFG)
        self.assertEqual(rows[0]['g'], 1, rows[0]['reasons'])
        self.assertEqual(rows[0]['path'], 'head')
        self.assertEqual(rows[0]['provenance']['kind'], 'numeric_chain')
        self.assertGreater(rows[0]['c'], 0.9)
        self.assertEqual(rows[1]['g'], 0)
        self.assertEqual(rows[2]['g'], 0)
        self.assertIn('grammar_number_not_allowed', rows[2]['reasons'])  # the validator checks written arithmetic
        self.assertEqual(rows[3]['g'], 0)  # the validator refuses the untraced 3.25 first
        from rlkit.gate import program_numeric  # second layer, called directly
        errs, _ = program_numeric(FT_BODY.format(conv='Converting to feet: 3.25 x 3.28084 = 10.66.\n'), FT, '10.66')
        self.assertTrue(any(e.startswith('untraced_operand') for e in errs), errs)
        errs, prov = program_numeric(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), FT, '10.56')
        self.assertEqual((errs, prov['kind']), ([], 'numeric_chain'))

    def test_constant_only_computation_fails(self):
        body = FT_BODY.format(conv='Converting: 100 x 0.1 = 10.\n')
        rows = score_group(dict(FT, question=FT_Q + ' Use 0.1 as the factor.'), [prec(program(body, '10'), 100)], CFG)
        self.assertEqual(rows[0]['g'], 0)
        self.assertIn('constant_only_computation', rows[0]['reasons'])

    def test_gap_closest_projection_and_swap_replay(self):
        body = ('I will measure each candidate against the couch.\n'
                '<gap a="couch" b="tv" rule="box_grid_5cm">\n<tool_response>\ndistance 2.10 m\n</tool_response>\n'
                '<gap a="couch" b="piano bench" rule="box_grid_5cm">\n<tool_response>\ndistance 0.40 m\n</tool_response>\n'
                '<gap a="couch" b="door" rule="box_grid_5cm">\n<tool_response>\ndistance 3.00 m\n</tool_response>\n'
                'Step 1: the piano bench is nearest, with the smallest printed distance.\n')
        rows = score_group(REL, [prec(program(body, 'D'), 80, 0), prec(program(body, 'B'), 80, 1)], CFG)
        self.assertEqual(rows[0]['g'], 1, rows[0]['reasons'])
        self.assertEqual(rows[0]['provenance']['kind'], 'gap_extreme')
        self.assertEqual(rows[1]['g'], 0)


if __name__ == '__main__':
    unittest.main()


class Served(unittest.TestCase):
    def test_recovery_trace_is_charged_against_the_direct_floor(self):
        fail = '<ground obj="zebra">\n<tool_response>\nzebra: not seen\n</tool_response>\n'
        tab = dict(CFG, n_min={'object_rel_distance': {'direct': 20, 'head': 60}})
        d, rcv = score_group(REL, [rec(direct(REL_SHORT, 'D'), 50, 0), prec(program(fail + REL_SHORT, 'D'), 50, 1)], tab)
        self.assertEqual((rcv['g'], rcv['path'], rcv['n_min']), (1, 'recovery', 20), rcv['reasons'])
        self.assertLessEqual(rcv['r'], d['r'])

    def test_response_must_equal_the_forced_one(self):
        r = prec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56'), 120)
        self.assertEqual(score_group(FT, [r], CFG)[0]['g'], 1)
        r['calls'][2]['response'] = 'distance 9.99 m'
        self.assertIn('response_not_forced', score_group(FT, [r], CFG)[0]['reasons'])
