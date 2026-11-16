"""review_rl2 adversarial cases on the fixed kit. Each asserts the property the fix claims."""
import sys
import types
import unittest

from rltests.test_reward import rec, prec, direct, program, served, REL, REL_SHORT, FT, FT_BODY, CFG
from rlkit import gate as G, headuse as H, sampler as S, select as SEL
from rlkit.reward import score_group

CONV = 'Converting to feet: 3.22 x 3.28084 = 10.56.\n'
GAP_FAIL = '<gap a="couch" b="tv" rule="box_grid_5cm">\n<tool_response>\nnot seen\n</tool_response>\n'
OWN = dict(pose_source='own', mask_source='mdg', ground_backend='GroundV3', geometry_source='same_checkpoint_own',
           geometry_identity='same_checkpoint_own:abc', source_identity='native_mdg:abc', ground_query_backends=['ground_v3'],
           query_provenance=['None'], presence_sources=['None'], tower_state=False, verify=False, reread=False, donor=False,
           call_kinds=['ground'])
NOPT = dict(FT, question='What is the distance between the cup and the trash can (in meters)?')


class Fix1(unittest.TestCase):
    def test_served_calls_plus_one_fabricated_span_fail(self):
        r = prec(program(FT_BODY.format(conv=CONV), '10.56'), 120)
        self.assertEqual(score_group(FT, [r], CFG)[0]['g'], 1)  # honest control
        r['text'] = r['text'].replace('{conv}', '').replace(
            CONV, '<gap a="cup" b="trash can">\n<tool_response>\ndistance 9.99 m\n</tool_response>\n' + CONV)
        self.assertEqual(score_group(FT, [r], CFG)[0]['g'], 0)

    def test_fabricated_span_replacing_a_served_one_fails(self):
        r = prec(program(FT_BODY.format(conv=CONV), '10.56'), 120)
        r['text'] = r['text'].replace('distance 3.22 m', 'distance 3.21 m')
        self.assertEqual(score_group(FT, [r], CFG)[0]['g'], 0)

    @unittest.skip('vacuous: the fixture FakeTokenizer decodes responses as ???, so split() refuses every draw')
    def test_honest_fixture_decode_passes_forced_check(self):
        import tempfile
        from rltests.fixture import FixtureBackend, prompt, sampler_config
        from rlkit import store as storemod
        with tempfile.TemporaryDirectory() as tmp:
            raw = sampler_config(draws=4, temperature=0.7)
            ps = [prompt('p1')]
            S.run(raw, ps, tmp, backend=FixtureBackend())
            recs = storemod.DrawStore(tmp, S.SamplerConfig(raw).identity).groups(ps, 4)['p1']
        called = [r for r in recs if r['calls']]
        self.assertTrue(called)
        for r in called:
            try:
                _, body, _, _ = G.split(r['text'])
            except ValueError:
                continue
            self.assertIsNone(G.forced_mismatch(body, r), r['text'])


class Fix2(unittest.TestCase):
    def test_trainer_recheck_refuses_foreign_grounding(self):
        sys.path.insert(0, 'grpo_tree')
        from student_pilot import grpo_rows
        bad = dict(OWN, ground_backend='SAM3Ground', geometry_identity='predicted:x', source_identity='sam3:x',
                   ground_query_backends=['hrp_reread'], query_provenance=['gt_masks'])
        self.assertIsNotNone(SEL.artifact_policy(dict(response_sources=bad)))
        with self.assertRaises(ValueError):
            grpo_rows.check_sources(dict(response_policy='artifact', response_sources=bad))


class Fix4(unittest.TestCase):
    def test_bare_not_seen_gap_is_not_head_use(self):
        self.assertFalse(H.head_call(dict(call='<gap a="couch" b="tv">', kind='gap', response='not seen')))

    def test_bare_not_seen_gap_trace_is_recovery(self):
        r = prec(program(GAP_FAIL + REL_SHORT, 'D'), 50)
        self.assertEqual(score_group(REL, [r], CFG)[0]['path'], 'recovery')

    def test_one_success_plus_junk_failure_stays_head(self):
        body = '<ground obj="zebra">\n<tool_response>\nzebra: not seen\n</tool_response>\n' + FT_BODY.format(conv=CONV)
        row = score_group(FT, [prec(program(body, '10.56'), 120)], CFG)[0]
        self.assertEqual((row['g'], row['path']), (1, 'head'))


class Fix5(unittest.TestCase):
    def test_foreign_presence_prior_on_real_query_records_barred(self):
        # GroundV3._emit records queries as dict(name, backend, state, result, mask...): no top-level
        # source_provenance / presence_source; those live on gb.source.provenance and gb.stages.presence.
        gb = types.SimpleNamespace(geometry_source='same_checkpoint_own',
                                   scene=types.SimpleNamespace(geometry_identity='same_checkpoint_own:abc'),
                                   source=types.SimpleNamespace(identity='native_mdg:abc'),
                                   stages=types.SimpleNamespace(presence=types.SimpleNamespace(identity='sam3_presence:gt')))
        GroundV3 = type('GroundV3', (), {})
        g = GroundV3()
        g.__dict__.update(vars(gb))
        rr = dict(heads=dict(ground_queries=[dict(name='cup', backend='ground_v3', state='resolved', result={})]),
                  calls=[dict(kind='ground')])
        rr['response_sources'] = S.response_sources(rr, dict(ground_backend=g, mask_source='mdg'))
        self.assertIsNotNone(SEL.artifact_policy(rr))


class Fix6(unittest.TestCase):
    def test_punctuation_variants_refused(self):
        base = dict(schema='rlkit-prompt-v1', type='t', question='q', gt_answer='1', row={}, scene_key='s')
        for src in ('VSI\u2013Bench', 'VSI:Bench', 'dev+S1'):
            with self.assertRaises(S.PromptError, msg=src):
                S.check_prompts([dict(base, prompt_id=src, source=src)], {})

    def test_row_source_variant_refused(self):
        base = dict(schema='rlkit-prompt-v1', prompt_id='x', type='t', question='q', gt_answer='1', scene_key='s',
                    source='reserve_r0_rl')
        with self.assertRaises(S.PromptError):
            S.check_prompts([dict(base, row=dict(source='VSI_Bench'))], {})


class Fix8(unittest.TestCase):
    def test_honest_largest_option_passes(self):
        opts = dict(NOPT, options=['A. 1.0 m', 'B. 2.0 m', 'C. 3.0 m', 'D. 4.0 m'])
        body = FT_BODY.format(conv='').replace('distance 3.22 m', 'distance 3.98 m')
        errs, _ = G.program_option(body, opts, 'D')
        self.assertEqual(errs, [])

    def test_honest_well_separated_options_pass(self):
        opts = dict(NOPT, options=['A. 0.5 m', 'B. 3.0 m', 'C. 9.0 m', 'D. 20.0 m'])
        errs, _ = G.program_option(FT_BODY.format(conv=''), opts, 'B')  # printed 3.22 m -> B; x1.37 = 4.41 -> B
        self.assertEqual(errs, [])

    def test_constant_dominated_node_fails(self):
        opts = dict(NOPT, options=['A. 0.5 m', 'B. 2.5 m', 'C. 9.0 m', 'D. 20.0 m'],
                    question=NOPT['question'] + ' Offset 2.54.')
        body = FT_BODY.format(conv='3.22 x 0.001 = 0.00322\n0.00322 + 2.54 = 2.54322\n')
        errs, _ = G.program_option(body, opts, 'B')
        self.assertTrue(errs)


if __name__ == '__main__':
    unittest.main()
