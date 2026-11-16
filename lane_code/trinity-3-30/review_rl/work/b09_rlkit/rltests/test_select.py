"""Mode (a) selector on planted rollouts, admitted by the tree's own direct grammar."""
import json
import unittest

from rltests.fixture import TREE
from rltests.test_reward import EOS, FT, FT_BODY, REL, REL_BODY, REL_SHORT, WRONG_SHORT, direct, program
from rlkit.select import select, think_target, tree_validator

ROW = dict(qid='q1', dataset='d2', scene='v1', question_type='object_rel_distance', answer='D', target='',
           student_input=dict(question=REL['question'], options=REL['options'], fps=24.,
                              frame_indices=list(range(0, 320, 10)), total_num_frames=320))


def rec(pid, draw, text, n, path='free', calls=()):
    return dict(prompt_id=pid, draw=draw, path=path, seed=draw, text=text + EOS, own_tokens=n, finish='eos',
                budget_hit=False, calls=list(calls), tokens=[1] * n, kinds='s' * n)


def prompt(base, pid, **kw):
    return dict(base, prompt_id=pid, scene_key='s_' + pid, source='reserve_r0_rl', row=dict(ROW, qid=pid), **kw)


class Select(unittest.TestCase):
    def setUp(self):
        self.validator, self.program_types = tree_validator(TREE)

    def run_select(self, prompts, groups, **kw):
        return select(prompts, groups, reward_cfg=dict(lam=0.2, n_ref={'object_rel_distance': 100}),
                      program_types=self.program_types, validator=self.validator, round_tag='r1', **kw)

    def test_shortest_right_direct_wins_and_is_admitted(self):
        p = prompt(REL, 'a')
        groups = {'a': [rec('a', 0, direct(REL_BODY, 'D'), 60), rec('a', 1, direct(REL_SHORT, 'D'), 20),
                        rec('a', 2, direct(WRONG_SHORT, 'B'), 18)]}
        out, report = self.run_select([p], groups)
        self.assertEqual(report['counts']['vqa_rows'], 1, out)
        row = out['vqa_rows'][0]
        self.assertEqual(row['rl_selection']['draw'], 1)
        self.assertEqual(row['target'], '<think>\n' + REL_SHORT + '</think>\n\nD')
        self.assertEqual(row['answer'], 'D')
        self.assertTrue(row['rl_selection']['admission'].startswith('r2_grammar.validate_direct'))
        self.assertEqual(row['student_input'], ROW['student_input'])
        self.assertEqual(report['kept_by_type_path'], {'object_rel_distance': {'direct': 1}})

    def test_no_winner_when_nothing_right(self):
        p = prompt(REL, 'b')
        out, report = self.run_select([p], {'b': [rec('b', 0, direct(WRONG_SHORT, 'B'), 18)]})
        self.assertEqual(report['counts']['no_winner'], 1)
        self.assertEqual(out['vqa_rows'], [])

    def program_case(self, sources):
        p = prompt(FT, 'c')
        p['row'] = dict(ROW, qid='c', question_type='object_abs_distance')
        text = program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56')
        calls = [dict(call='<gap a="cup" b="trash can" rule="box_grid_5cm">', response='distance 3.22 m', kind='head')]
        r = rec('c', 0, text, 80, 'head', calls)
        r.update(kinds='ff' + 'r' * 10 + 's' * 68, prompt_ids_sha256='a' * 64, response_sources=sources)
        return self.run_select([p], {'c': [r]})

    def test_artifact_head_winner_trains_as_own_row(self):
        src = dict(pose_source='own', mask_source='mdg', ground_backend='GroundV3', ground_query_backends=['ground_v3'],
                   tower_state=False, donor=False, call_kinds=['head'])
        out, report = self.program_case(src)
        self.assertEqual(report['counts']['own_rows'], 1, out)
        row = out['own_rows'][0]
        self.assertEqual((row['schema'], row['stream'], row['response_policy']), ('rlkit-own-row-v1', 'routing', 'artifact'))
        self.assertEqual(row['rl_selection']['answer'], '10.56')
        self.assertEqual(report['kept_by_type_path'], {'object_abs_distance': {'head': 1}})

    def test_outside_responses_are_barred(self):
        base = dict(pose_source='own', mask_source='mdg', ground_backend='GroundV3', ground_query_backends=['ground_v3'],
                    tower_state=False, donor=False, call_kinds=['head'])
        for change, word in ((dict(donor=True), 'donor'), (dict(mask_source='gt'), 'mask source'),
                             (dict(ground_query_backends=['hrp_reread']), 'backends'), (dict(pose_source='override'), 'pose')):
            out, report = self.program_case({**base, **change})
            self.assertEqual(report['counts']['barred'], 1, change)
            self.assertIn(word, out['barred'][0]['reason'])
        out, _ = self.program_case(None)
        self.assertIn('no response_sources', out['barred'][0]['reason'])

    def test_refusal_is_recorded_not_dropped(self):
        p = prompt(REL, 'd')
        def refuse(row):
            raise ValueError('planted refusal')
        out, report = select([p], {'d': [rec('d', 0, direct(REL_SHORT, 'D'), 20)]}, validator=refuse)
        self.assertEqual(report['counts']['refused'], 1)
        self.assertEqual(out['refused'][0]['reason'], 'planted refusal')

    def test_think_target_strips_special_tail(self):
        self.assertEqual(think_target('x\n</think>\n\nD<|im_end|>'), '<think>\nx\n</think>\n\nD')


if __name__ == '__main__':
    unittest.main()
