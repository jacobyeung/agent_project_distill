"""Final-mode C1 on the native tiny Qwen: routing LM loss, own-head readout, one FoV, scheduled sampling."""
import json
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import torch

from student_pilot import carrier_c1_routing as routing
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import CarrierC1, RECIPE
from student_pilot.carrier_c1_data import insert_frame_carriers, mixed_indices
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.decoupled_v import target_tensors
from tests.test_carrier_c1 import Tokenizer

POOL = Path('/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl')


def final_fixture(placement='append_after_temporal_group_video_tokens_v1'):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    torch.manual_seed(31)
    text = dict(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                num_attention_heads=4, num_key_value_heads=2, head_dim=8, use_cache=False,
                layer_types=['linear_attention', 'full_attention'], linear_key_head_dim=4,
                linear_value_head_dim=4, linear_num_key_heads=4, linear_num_value_heads=4,
                pad_token_id=0, rope_parameters=dict(rope_type='default', rope_theta=10000.,
                                                    mrope_section=[1, 1, 2], partial_rotary_factor=1.))
    vision = dict(depth=3, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=32,
                  num_position_embeddings=16, patch_size=2, temporal_patch_size=2, spatial_merge_size=2)
    config = Qwen3_5Config(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                           vision_start_token_id=62, vision_end_token_id=63)
    for item in (config, config.text_config, config.vision_config):
        item._attn_implementation = 'sdpa'
    base = Qwen3_5ForConditionalGeneration(config).float()
    camera = dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
                  weight_gravity=.05, weight_scale=.02, supervision={'path': '/fixture', 'sha256': 'a'*64})
    depth = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3])
    recipe = {**RECIPE, 'scheduled_sampling': dict(seed=17, max_own_probability=1., pose_open_deg=45., pose_full_deg=25., fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=0, exposure_from_step=None, exposure_probability=0.)}
    model = CarrierC1(base, camera, depth, 5, placement, 'final', True, recipe, depth_fov_source='pose_head')
    groups = 16
    ids = torch.tensor([[2]+[v for _ in range(groups) for v in (62, 61, 63)]+[10, 11, 12, 13]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                 mm_token_type_ids=torch.where(ids == 61, 2, 0),
                 video_grid_thw=torch.tensor([[groups, 2, 2]]), pixel_values_videos=torch.randn(groups*4, 24))
    batch['labels'][0, -2:] = ids[0, -2:]
    batch = insert_frame_carriers(batch, Tokenizer(), carrier_placement=placement)
    record = dict(camera=[[0., 0., 0., 0., 0., 0., 1., 1., 1.]]*32, camera_mask=[True]*32,
                  trajectory_scale=1., gravity=[0., -1., 0.], gravity_mask=True,
                  point_depth=dict(uv=[[[500., 500.], [200., 300.]]]*32, depth=[[2., 3.]]*32, mask=[[True, True]]*32))
    return model, batch, target_tensors(record, all_frames=True)


class FinalModel(unittest.TestCase):
    def test_pose_rows_condition_depth_on_the_pose_head_fov(self):
        model, batch, targets = final_fixture()
        seen = []
        original = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.forward
        def spy(llm, vits, fov, uv):
            seen.append(fov.detach().clone())
            return original(llm, vits, fov, uv)
        with mock.patch.object(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth, 'forward', spy):
            result = model(batch, targets)
        result['loss'].backward()
        self.assertLessEqual({'pose', 'trans', 'rot', 'fov', 'gravity', 'scale'}, set(result['metrics']['pose_parts']))
        head = model.auxiliary_heads.pose
        parts = result['metrics']['pose_parts']
        weighted = (head.settings['weight_trans'] * parts['trans'] + head.settings['weight_rot'] * parts['rot']
                    + head.settings['weight_focal'] * parts['fov'])
        self.assertTrue(np.isfinite(weighted) and weighted >= 0)
        self.assertTrue(all(np.isfinite(v) for v in result['metrics']['pose_parts'].values()))
        self.assertEqual(float(result['components']['depth_fov']), 0.)
        self.assertGreater(float(result['components']['depth']), 0.)
        expected = model.pose_fov(model.hidden(batch), batch)[0]
        torch.testing.assert_close(seen[0], expected)
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0
                            for n, p in model.named_parameters() if n.startswith('auxiliary_heads.depth.model.visual.')))

    def test_routing_stream_is_lm_loss_and_readout_reads_the_prefix_only(self):
        model, batch, _ = final_fixture()
        result = model(batch, stream='routing')
        result['loss'].backward()
        self.assertGreater(float(result['components']['routing']), 0.)
        model.zero_grad(set_to_none=True)
        uv = torch.full((32, 50, 2), 500.)
        with torch.no_grad():
            full = model(batch, {'uv': uv}, stream='readout')
            prefix = model(routing.prefix_batch({**batch, 'aux_suffix_start': torch.tensor([60])}), {'uv': uv},
                           stream='readout')
        self.assertEqual(tuple(full['pose'].shape), (1, 32, 9))
        self.assertEqual(tuple(full['gravity'].shape), (1, 3))
        self.assertEqual(tuple(full['depth'].shape), (32, 50))
        for key in ('pose', 'gravity', 'depth'):
            torch.testing.assert_close(full[key], prefix[key])
        self.assertTrue(all(p.grad is None for p in model.parameters()))

    def test_milestone_readout_conditions_depth_on_the_pose_head_fov(self):
        model, batch, _ = final_fixture()
        uv = [[[200., 300.], [500., 500.]]] * 32
        values = model.eval().readout(batch, uv)
        with torch.no_grad():
            direct = model(batch, {'uv': torch.tensor(uv)}, stream='readout')
        np.testing.assert_allclose(values['point_depth'], direct['depth'].double().numpy(), rtol=1e-5)

    def test_stage1_depth_init_loads_head_and_freezes_the_encoder_copy(self):
        import tempfile
        from safetensors.torch import save_file
        from student_pilot.carrier_c1 import load_depth_stage1, parameter_groups
        from student_pilot.decoupled_v import tensor_identity
        from student_pilot.p3_provenance import file_pin
        source, _, _ = final_fixture()
        model, batch, targets = final_fixture()
        torch.manual_seed(5)
        depth = source.auxiliary_heads.depth
        for parameter in depth.parameters():
            parameter.data.normal_()
        root = Path(tempfile.mkdtemp())
        encoder = {k: v.detach().clone().contiguous() for k, v in depth.model.visual.state_dict().items()}
        heads = {'camera.point_depth.' + k: v.detach().clone().contiguous()
                 for k, v in depth.auxiliary_heads.camera.point_depth.state_dict().items()}
        heads['camera.point_depth.group_embed'] = heads['camera.point_depth.group_embed'][::2].clone()
        heads['camera.pose_branch.extra'] = torch.zeros(3)
        save_file(encoder, str(root / 'encoder.safetensors'))
        save_file(heads, str(root / 'heads.safetensors'))
        artifact = dict(schema='p3-head-artifact-v1', feature_backing='decoupled_vc',
                        weights=file_pin(root / 'heads.safetensors'),
                        encoder_copy=dict(weights=file_pin(root / 'encoder.safetensors')))
        (root / 'artifact.json').write_text(json.dumps(artifact))
        report = load_depth_stage1(model, file_pin(root / 'artifact.json'))
        self.assertTrue(report['encoder_frozen'] and model.depth_stage1)
        loaded = model.auxiliary_heads.depth
        torch.testing.assert_close(loaded.auxiliary_heads.camera.point_depth.point_mlp[0].weight,
                                   depth.auxiliary_heads.camera.point_depth.point_mlp[0].weight)
        torch.testing.assert_close(loaded.auxiliary_heads.camera.point_depth.group_embed,
                                   heads['camera.point_depth.group_embed'].repeat_interleave(2, 0))
        self.assertFalse(any(p.requires_grad for p in loaded.model.visual.parameters()))
        self.assertNotIn('encoder_copy', [g['name'] for g in parameter_groups(model)])
        model(batch, targets)['loss'].backward()
        self.assertTrue(any(p.grad is not None for p in loaded.auxiliary_heads.camera.point_depth.parameters()))

    def test_carrier_embeddings_clip_in_their_own_group(self):
        from student_pilot.carrier_c1_data import PLACEMENTS
        for placement in (PLACEMENTS[0], PLACEMENTS[1]):
            model, batch, targets = final_fixture(placement)
            attached = [p for p in model.auxiliary_heads.parameters() if p.requires_grad]
            carriers, heads = run.clip_groups(model, attached)
            self.assertEqual(len(carriers) + len(heads), len(attached))
            self.assertFalse({id(p) for p in carriers} & {id(p) for p in heads})
            self.assertEqual(len(carriers), 2 if placement == PLACEMENTS[1] else 1)
            model(batch, targets)['loss'].backward()
            for p in carriers:
                p.grad = torch.full_like(p, 100.)
            before = [p.grad.clone() for p in heads if p.grad is not None]
            torch.nn.utils.clip_grad_norm_(carriers, 1.)
            self.assertLessEqual(float(torch.sqrt(sum(p.grad.square().sum() for p in carriers))), 1.0001)
            after = [p.grad for p in heads if p.grad is not None]
            self.assertTrue(all(torch.equal(a, b) for a, b in zip(before, after)))

    def test_failed_row_encodes_are_refused_without_substitution(self):
        model, _, _ = final_fixture()
        good = dict(input_ids=torch.zeros(1, 8, dtype=torch.long), labels=torch.tensor([[-100]*4 + [1]*4]),
                    aux_camera_positions=torch.tensor([list(range(32))]))
        seen = []
        class Rows:
            def count(self, stream):
                return 10
            def get(self, stream, index):
                seen.append(index)
                if index < 2:
                    raise ValueError('Complete routing row exceeds 16384 tokens')
                return good, None, {'qid': index}
        for tries in (2, 8):
            seen.clear()
            with self.assertRaisesRegex(ValueError, 'no substitution'):
                run.fetch(Rows(), 'routing', 0, model, tries=tries)
            self.assertEqual(seen, [0])
        _, _, audit = run.fetch(Rows(), 'routing', 2, model)
        self.assertEqual(audit['qid'], 2)
        self.assertNotIn('substituted_from', audit)

    def test_prefix_readout_is_exact_for_every_placement(self):
        from student_pilot.carrier_c1_data import PLACEMENTS
        for placement in PLACEMENTS:
            model, batch, _ = final_fixture(placement)
            uv = torch.full((32, 25, 2), 500.)
            with torch.no_grad():
                full = model(batch, {'uv': uv}, stream='readout')
                prefix = model(routing.prefix_batch(batch), {'uv': uv}, stream='readout')
            for key in ('pose', 'gravity', 'depth'):
                torch.testing.assert_close(full[key], prefix[key], msg=placement)

    def test_final_mix_and_recipe_are_world_general(self):
        counts = dict(pose=9, routing=5, vqa=4, pointing=3)
        mix = ['pose', 'pose', 'routing', 'routing', 'vqa', 'pointing']
        plans = list(mixed_indices(counts, 3, training_mode='final', mix=mix, world=16))
        self.assertEqual([s for s, _ in plans[0]], mix)
        self.assertTrue(all(len(i) == 16 for plan in plans for _, i in plan))
        cfg = dict(training_mode='final', mix=mix, world_size=16, steps=800, milestones=[100, 200, 400, 800],
                   weights=dict(routing=1.), scheduled_sampling=dict(seed=17, max_own_probability=1., pose_open_deg=45., pose_full_deg=25., fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=0, exposure_from_step=None, exposure_probability=0.))
        recipe = recipe_for(cfg)
        self.assertEqual(recipe['global_batch'], 96)
        with self.assertRaises(ValueError):
            recipe_for({**cfg, 'mix': ['pose', 'vqa', 'pointing']})


@unittest.skipUnless(POOL.exists(), 'derivgen review pool not on this host')
class ScheduledSampling(unittest.TestCase):
    def test_own_values_run_the_readout_and_re_render_tool_outputs(self):
        model, batch, _ = final_fixture()
        raw = json.loads(next(line for line in POOL.open() if '"absolute_count"' in line))

        class Rows:
            processor = None
            def row(self, stream, index):
                return {'routing': raw, 'student_input': {}}, {}

        captured = {}
        def encode_own(processor, row, gt_batch, target, spans, segments, source):
            captured.update(target=target, spans=spans, source=source)
            return gt_batch, {'values': source}
        with mock.patch.object(routing, 'encode_own', encode_own):
            out, audit = run.own_values(model, Rows(), batch, {'values': 'gt'}, 0, (True, True), torch.device('cpu'))
        self.assertEqual(audit['values'], 'own')
        _, closed = run.own_values(model, Rows(), batch, {'values': 'gt'}, 0, (False, False), torch.device('cpu'))
        self.assertEqual(closed, {'values': 'gt'})
        gt, gt_spans = routing.render(raw['events'], raw['answer'])
        self.assertNotEqual(captured['target'], gt)
        self.assertEqual(len(captured['spans']), len(gt_spans))
        self.assertIn('<depth_at frame=2 pts=[[767,848],[767,977],[783,719]]>', captured['target'])


@unittest.skipUnless(POOL.exists(), 'derivgen review pool not on this host')
class TrainDecodeParity(unittest.TestCase):
    """Training-time injected responses == decode-loop responses for the same calls (kept check)."""
    def test_injected_values_match_decode_responses(self):
        from student_pilot import carrier_c1_decode as decode
        from student_pilot import p3_printed_calculator as calculator
        rows = []
        for line in POOL.open():
            row = {**json.loads(line), 'trace_revision': '3.11'}
            pts = [p for e in row['events'] if e['kind'] == 'tool_response' and e['name'] == 'depth_at' for p in e['points']]
            names = {e['name'] for e in row['events'] if e['kind'] == 'tool_response'}
            if pts and all(p['requested_frame'] == p['actual_frame'] for p in pts) and len(names) >= 2:
                rows.append(row)
            if len(rows) == 4:
                break
        self.assertTrue(rows)
        compared = 0
        for placement in ('append_after_temporal_group_video_tokens_v1', 'append_all_after_video_frame_embeddings_v1'):
            model, batch, _ = final_fixture(placement)
            model.eval()
            for row in rows:
                queries = routing.depth_queries(row)
                uv, slots = routing.query_tensor(queries)
                with torch.no_grad():
                    readout = model(routing.prefix_batch(batch), {'uv': uv}, stream='readout')
                    heads = decode.HeadState(model, batch, model.hidden(batch))
                try:
                    geometry, _ = routing.row_geometry(row, readout, queries, slots, True, True)
                    target, spans, _ = routing.rerender(row, geometry)
                except routing.RenderError:
                    continue
                trained = [target[s['start'] + len('<tool_response>'):s['end'] - len('</tool_response>')] for s in spans]
                registry, decoded = calculator.PrintedPointRegistry(), []
                for e in row['events']:
                    if e['kind'] in ('tool_call', 'calculator_call'):
                        with torch.no_grad():
                            decoded.append(decode.respond(e.get('token') or e['command'], registry, heads.geometry())[0])
                self.assertEqual(trained, decoded, (placement, row['qid']))
                compared += 1
        self.assertGreater(compared, 0)


class FakeTokenizer:
    """Tiny-vocabulary stand-in: scripted call tokens, special response delimiters, char ids."""
    words = {40: '<depth_at', 41: ' frame=2 pts=[[500,500],[300,700]]>', 42: ' Next', 43: '<tool_response>',
             44: '</tool_response>', 45: '<move', 46: ' from=2 to=9>', 47: '<turn', 48: ' from=4 to=30>',
             49: ' <dist P1 P2>'}
    eos_token_id = 1

    def convert_tokens_to_ids(self, token):
        return {v: k for k, v in self.words.items()}.get(token, 0)

    def encode(self, text, add_special_tokens=False):
        out = []
        while text:
            for key, word in ((43, '<tool_response>'), (44, '</tool_response>')):
                if text.startswith(word):
                    out.append(key); text = text[len(word):]; break
            else:
                out.append(50 + ord(text[0]) % 10); text = text[1:]
        return out

    def decode(self, ids, skip_special_tokens=False):
        return ''.join(self.words.get(i, '?') for i in ids)


class RoutedDecode(unittest.TestCase):
    def test_decode_injects_responses_from_the_shared_layer_and_replays_byte_equal(self):
        from types import SimpleNamespace
        from student_pilot import carrier_c1_decode as decode
        model, batch, _ = final_fixture()
        model.eval()
        processor = SimpleNamespace(tokenizer=FakeTokenizer(),
                                    _routing_tokens=dict(ids={'<depth_at': 40, '<move': 45, '<pose': 39,
                                                              '<turn': 47, '<box_3d': 38}))
        script = [40, 41, 49, 45, 46, 47, 48, 42, 1]
        def force(ids, logits):
            generated = [i for i in ids if i in script]
            out = torch.full_like(logits, -1e9)
            out[:, script[len(generated)]] = 0.
            return out
        prompt = {k: v[:, :-2] if k in ('input_ids', 'attention_mask', 'labels', 'mm_token_type_ids') else v
                  for k, v in batch.items()}
        record = decode.generate(model, processor, prompt, logits_processor=force)
        self.assertEqual(record['finish'], 'eos')
        self.assertEqual([c['kind'] for c in record['calls']], ['head', 'calculator', 'head', 'head'])
        self.assertTrue(record['calls'][0]['response'].startswith('P1: cam2 ('))
        self.assertIn('P2: cam2 (', record['calls'][0]['response'])
        self.assertTrue(record['calls'][1]['response'].endswith(' m'))
        self.assertTrue(record['calls'][2]['response'].startswith('dx = '))
        self.assertTrue(record['calls'][3]['response'].startswith('turn = '))
        self.assertEqual(decode.replay(record), dict(calls=4, mismatches=0, byte_equal=True))
        with torch.no_grad():
            readout = model(prompt, {'uv': torch.full((32, 25, 2), 500.)}, stream='readout')
        np.testing.assert_allclose(record['heads']['pose9'], readout['pose'][0].double().numpy(), atol=1e-4)

    def test_invalid_calls_get_typed_errors(self):
        from student_pilot import carrier_c1_decode as decode
        from student_pilot import p3_printed_calculator as calculator
        registry = calculator.PrintedPointRegistry()
        self.assertEqual(decode.respond('<depth_at frame=40 pts=[[500,500]]>', registry, object())[1]['code'], 'bad_frame')
        self.assertEqual(decode.respond('<depth_at frame=4 pts=[[5,500]]>', registry, object())[1]['code'],
                         'point_outside_20_980')
        self.assertEqual(decode.respond('<dist P1 P2>', registry, None)[1]['code'], 'unknown_point_label')
        self.assertEqual(decode.respond('<depth_at frame=4 image_frame=4 pts=[[50,500]]>', registry, object())[1]['code'],
                         'malformed_call')


class CanarySummary(unittest.TestCase):
    def test_answers_and_summary(self):
        from student_pilot import carrier_c1_canary as canary
        self.assertEqual(canary.answer_of('<think>\nx\n</think>\n\n0.30<|im_end|>'), '0.30')
        self.assertTrue(canary.agree('0.31', '0.30') and canary.agree('b', 'B') and not canary.agree(None, '1'))
        own = dict(calls=[dict(kind='head'), dict(kind='error')], finish='eos', errors=1)
        records = [dict(category='route', gt_calls=True, own=own, replay=dict(byte_equal=True), readout_diff=1e-5,
                        answer='2', agree=True, shuffle_changed=True),
                   dict(category='direct', gt_calls=False, own=dict(calls=[], finish='eos', errors=0),
                        replay=dict(byte_equal=True), readout_diff=0., answer=None, agree=False)]
        summary = canary.summarize(records)
        self.assertEqual(summary['c1_parse_valid_calls'], .5)
        self.assertEqual(summary['c1_policy_agreement'], 1.)
        self.assertEqual(summary['c7_bad_termination'], .5)
        self.assertEqual(summary['c3_answer_change_under_shuffle'], 1.)


if __name__ == '__main__':
    unittest.main()
