"""Reviewer's refute tests (review_rl). Each asserts the claimed property; each FAILS on rlkit-v1."""
import sys
import unittest

import torch

from rltests.test_reward import rec, direct, program, REL, FT, FT_BODY, REL_SHORT, CFG
from rlkit import baselines as BL, floor as F, gate as G, grpo as GR, headuse as H, prompts as P, sampler as S, select as SEL
from rlkit.reward import score_group

CONV = 'Converting to feet: 3.22 x 3.28084 = 10.56.\n'
FAILCALL = '<ground obj="zebra">\n<tool_response>\nzebra: not seen\n</tool_response>\n'
SZ = dict(prompt_id='p', type='object_size_estimation', options=None, gt_answer='120',
          question='What is the length of the longest dimension (length, width, or height) of the table, measured in centimeters?')
LOCATE = 'Step 1: find the table, first seen in frame 3.\n'


class Refute(unittest.TestCase):
    def test_f1_fabricated_response_fails_gate(self):
        r = rec(program(FT_BODY.format(conv=CONV), '10.56'), 120)  # calls=[]: no decoder-forced response
        self.assertEqual(score_group(FT, [r], CFG)[0]['g'], 0)

    def test_f1_fabricated_response_not_admitted_as_own_row(self):
        r = rec(program(FT_BODY.format(conv=CONV), '10.56'), 120)
        r.update(seed=1, tokens=[5] * 120, kinds='s' * 120, prompt_ids_sha256='x',
                 response_sources=S.response_sources(dict(heads={}, calls=[]), {}))
        out, _ = SEL.select([dict(FT, row={})], {'p': [r]}, reward_cfg=CFG)
        self.assertEqual(out['own_rows'], [])

    def test_f2_grpo_row_refuses_outside_responses(self):
        r = rec(program(FT_BODY.format(conv=CONV), '10.56'), 3)
        r.update(seed=1, tokens=[5] * 3, kinds='sss', prompt_ids_sha256='x', logp_tempered=[-1.] * 3,
                 response_sources=dict(S.response_sources(dict(heads={}, calls=[]), {}), donor=True))
        with self.assertRaises(ValueError):
            GR.to_row(dict(FT, row={}), r, 1.0, [-1.] * 3, [1, 2, 3])

    def test_f3_default_loss_temperature_matches_sampler(self):
        sys.path.insert(0, 'grpo_tree')
        from student_pilot import grpo_loss as L
        self.assertEqual(L.SETTINGS['temperature'], S.SAMPLING_DEFAULTS['temperature'])

    def test_f4_recovery_trace_not_rewarded_as_head(self):
        tab = dict(CFG, n_min={'object_rel_distance': {'direct': 20, 'head': 60}})
        d, rcv = score_group(REL, [rec(direct(REL_SHORT, 'D'), 50, 0), rec(program(FAILCALL + REL_SHORT, 'D'), 50, 1)], tab)
        self.assertLessEqual(rcv['r'], d['r'])

    def test_f4_failed_call_is_not_head_use(self):
        self.assertEqual(H.openers(dict(calls=[dict(call='<ground obj="zebra">', kind='ground', response='zebra: not seen')])), [])

    def test_f5_external_geometry_barred(self):
        GroundV3 = type('GroundV3', (), dict(geometry_source='configured_predicted'))
        rr = dict(heads={}, calls=[dict(kind='ground')])
        rr['response_sources'] = S.response_sources(rr, dict(ground_backend=GroundV3(), mask_source='mdg'))
        self.assertIsNotNone(SEL.artifact_policy(rr))

    def test_f5_gt_provenance_query_barred(self):
        rr = dict(heads=dict(ground_queries=[dict(name='cup', backend='ground_v3', source_provenance='gt_masks')]),
                  calls=[dict(kind='ground')])
        rr['response_sources'] = S.response_sources(rr, {})
        self.assertIsNotNone(SEL.artifact_policy(rr))

    def test_f6_benchmark_row_refused_by_pool(self):
        row = dict(qid='q1', scene='s1', question_type='object_counting', answer='3', source='vsibench',
                   student_input=dict(question='How many chairs?', frame_indices=list(range(32))))
        pool, refused = P.build([row], ['s1'], 32)
        self.assertEqual(pool, [])

    def test_f6_source_variants_refused(self):
        base = dict(schema='rlkit-prompt-v1', type='t', question='q', gt_answer='1', row={}, scene_key='s')
        for src in ('VSI_Bench', 'dev-S1', 'devS1'):
            with self.assertRaises(S.PromptError):
                S.check_prompts([dict(base, prompt_id=src, source=src)], {})

    def test_f7_floor_requires_pool(self):
        with self.assertRaises(F.FloorError):
            F.check_heldout([dict(prompt_id='x', scene_key='s')], [])

    def test_f8_numeric_option_detached_answer_fails(self):
        nopt = dict(FT, question='What is the distance between the cup and the trash can (in meters)?', options=['A. 0.1 m', 'B. 3.0 m', 'C. 9.0 m', 'D. 20.0 m'])
        errs, _ = G.program_option(FT_BODY.format(conv=''), nopt, 'A')  # printed gap 3.22 m -> B
        self.assertTrue(errs)

    def test_f9_constant_baseline_r_is_measured(self):
        r = score_group(SZ, [rec(direct(LOCATE, '120'), 20)], CFG)[0]
        rep = BL.constant_report({'object_size_estimation': dict(kind='numeric', answer=120.0)}, [dict(SZ, gt_answer='120')])
        self.assertEqual(rep['object_size_estimation']['r'], r['r'])  # one Locate line + constant earns r = 1.0


if __name__ == '__main__':
    unittest.main()
