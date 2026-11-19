"""Head-call decoding in the orchard evaluator (--headcall decode): the pin and identities, cpu_mock generation with the
per-item call sidecars, scoring re-validation, the summary tool, the wrapper's EVAL_HEADCALL, and a real decode on the
tiny Qwen3.5 asset whose heads answer the trace's call from the carrier prefill."""
import importlib.util
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import torch

from student_pilot.common import load_json
from student_pilot.orchard_eval import contracts, frames, generate
from tests.fullft_eval_toys import (CAMERA, LABEL, CarrierTokenizer, PublicationFixtures, generation_manifest,
                                    scoring_manifest)
from tests.fullft_toys import tiny_base

REPO = Path(__file__).resolve().parents[1]
SCOPE = {'provisional_diagnostic': LABEL}
TINY = os.environ.get('HEADCALL_TINY', '/scratch/jjyeung/phase2_opus/in33/scratch/jjyeung/cursor_lanes/'
                                       'distill_pd_phase2_opus/assets/tiny_qwen35')
CALL = '<tool_call>{"name": "depth", "frame": 4, "point": [500, 500]}</tool_call>'


def synthetic_trace(processor):
    """A cpu_mock generator: one call, its inserted response, and an answer; with the decode loop's record."""
    from headcall.decode import CallRecord, DecodeResult
    from headcall.eval_hook import record
    from headcall.protocol import parse_call

    tokenizer = processor.tokenizer
    before = tokenizer.encode('<think>\nlook ' + CALL)
    response = tokenizer.encode('<tool_response>2.00 m</tool_response>')
    after = tokenizer.encode(' so 2.00 m away\n</think>\n\nA<|im_end|>')
    tokens = before + response + after
    inserted = [False] * len(before) + [True] * len(response) + [False] * len(after)
    body = CALL[len('<tool_call>'):-len('</tool_call>')]
    call = CallRecord(0, len(tokenizer.encode('<think>\nlook ')), len(before) - 1, body, parse_call(body), '2.00 m', None,
                      0.0, len(response))

    def generator(batch, audit, effective):
        assert audit['carriers'] == 'insert'
        raw = tokenizer.decode(tokens)
        return {'tokens': tokens, 'raw': raw, 'display': raw,
                'headcall': record(DecodeResult(tokens, inserted, [call], 'eos', {}, 0))}
    return generator


class HeadcallPinTests(PublicationFixtures, unittest.TestCase):
    """The headcall pin: explicit, only on a full-weights camera-head publication with carriers inserted."""

    def setUp(self):
        self.publication_setup()
        self.adapter, self.receipt = self.full_publication(camera=CAMERA, carrier=5)

    def validate(self, **options):
        return contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG,
                                          allow_synthetic=True, provisional_diagnostic=LABEL, **options)

    def test_pin_identity_and_refusals(self):
        insert = self.validate(carriers='insert')
        self.assertEqual(self.validate(carriers='insert', headcall='none'), insert)
        decode = self.validate(carriers='insert', headcall='decode')
        self.assertEqual({key: value for key, value in decode.items() if key != 'headcall'}, insert)
        pin = decode['headcall']
        self.assertEqual(pin['mode'], 'decode')
        self.assertEqual(pin['auxiliary_heads'], insert['carriers']['auxiliary_heads'])
        self.assertEqual(pin['camera_tokens'], insert['carriers']['camera_tokens'])
        self.assertEqual(pin['decode'], contracts.HEADCALL_DECODE)
        self.assertEqual(pin['decode']['max_calls'], 80)
        self.assertEqual(pin['decode']['max_call_tokens'], 128)
        self.assertEqual([Path(item['path']).name for item in pin['code']], list(contracts.HEADCALL_CODE))
        self.assertNotEqual(contracts.adapter_identity(decode), contracts.adapter_identity(insert))
        self.assertEqual(contracts.adapter_identity(insert),
                         contracts.adapter_identity({key: value for key, value in decode.items() if key != 'headcall'}))
        with self.assertRaisesRegex(ValueError, 'carriers=insert'):
            self.validate(carriers='none', headcall='decode')
        with self.assertRaisesRegex(ValueError, 'none or decode'):
            self.validate(carriers='insert', headcall='always')
        with self.assertRaisesRegex(ValueError, 'labeled full fine-tuning'):
            contracts.validate_adapter('base', 'qwen35', None, None, contracts.DEFAULT_CONFIG, headcall='decode')
        base = {'sha256': 'a' * 64}, {'model': 'fixture'}, None, contracts.DEFAULT_CONFIG
        self.assertEqual(contracts.protocol_identity(*base), contracts.protocol_identity(*base, headcall='none'))
        self.assertNotEqual(contracts.protocol_identity(*base, carriers='insert'),
                            contracts.protocol_identity(*base, carriers='insert', headcall='decode'))
        self.root = self.root / 'plain'  # a second pool under the same Orchard-owned project
        self.root.mkdir()
        plain, plain_receipt = self.full_publication(name='plain')
        with self.assertRaisesRegex(ValueError, 'camera head'):
            contracts.validate_adapter('distilled', 'qwen35', plain, plain_receipt, contracts.DEFAULT_CONFIG, True, LABEL,
                                       carriers='insert', headcall='decode')

    def test_heads_load_exactly_and_tokens_must_match(self):
        pin = self.validate(carriers='insert', headcall='decode')['headcall']
        model = tiny_base('qwen35')
        heads = generate.load_headcall_heads(model, pin, CarrierTokenizer(5))
        saved = torch.load(pin['auxiliary_heads']['path'], weights_only=True)
        self.assertIs(model.auxiliary_heads, heads)
        self.assertTrue(all(torch.equal(value, saved[name]) for name, value in heads.state_dict().items()))
        self.assertFalse(any(parameter.requires_grad for parameter in heads.parameters()))
        wrong = dict(pin, camera_tokens={**pin['camera_tokens'], 'sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'camera tokens'):
            generate.load_headcall_heads(tiny_base('qwen35'), wrong, CarrierTokenizer(5))


class HeadcallRunTests(PublicationFixtures, unittest.TestCase):
    """cpu_mock preflight and generation of a head-call arm: per-item sidecars, scoring, the summary tool."""

    def setUp(self):
        self.publication_setup()
        self.manifest, _ = generation_manifest(self.stack, self.root)
        self.adapter, self.receipt = self.full_publication(camera=CAMERA, carrier=13)

    def run_arm(self, name, generator=None, **options):
        report = frames.cpu_check(self.manifest, 'qwen35', self.root / f'check_{name}', self.root, synthetic=True,
                                  variant='distilled', adapter=self.adapter, training_receipt=self.receipt, **options, **SCOPE)
        completion = generate.generate_run(self.manifest, 'qwen35', 'distilled', self.root / f'run_{name}', self.root,
                                           self.root / f'check_{name}/preflight.json', adapter=self.adapter,
                                           training_receipt=self.receipt, cpu_mock=True, allow_unpaired_adapter=True,
                                           generator=generator, **options, **SCOPE)
        return report, completion

    def test_sidecars_scoring_and_summary(self):
        from student_pilot.orchard_eval import score
        from student_pilot.orchard_eval.frames import SyntheticProcessor
        report, completion = self.run_arm('decode', synthetic_trace(SyntheticProcessor()), carriers='insert',
                                          headcall='decode')
        self.assertEqual(report['headcall'], 'decode')
        self.assertEqual(set(completion['outcomes'].values()), {'ok'})
        core = load_json(self.root / 'run_decode/run.json')['core']
        self.assertEqual(core['adapter']['headcall']['mode'], 'decode')
        self.assertNotIn('headcall', {key for key in core if key != 'adapter'})
        ids = core['ordered_ids']
        records = [load_json(self.root / 'run_decode/headcalls' / f'{contracts.safe_id(qid)}.json') for qid in ids]
        self.assertEqual([item['qid'] for item in records], ids)
        self.assertTrue(all(item['summary']['calls'] == 1 and item['summary']['inserted_tokens'] > 0 for item in records))
        # A preflight without head-call decoding cannot generate the decode arm, and the reverse.
        self.run_arm('insert', carriers='insert')
        for preflight, options in (('check_insert', {'headcall': 'decode'}), ('check_decode', {})):
            with self.subTest(preflight=preflight), self.assertRaisesRegex(ValueError, 'Preflight .*differs'):
                generate.generate_run(self.manifest, 'qwen35', 'distilled', self.root / 'run_mismatch', self.root,
                                      self.root / preflight / 'preflight.json', adapter=self.adapter,
                                      training_receipt=self.receipt, cpu_mock=True, allow_unpaired_adapter=True,
                                      carriers='insert', **options, **SCOPE)
        self.assertFalse((self.root / 'run_insert/headcalls').exists())
        insert_core = load_json(self.root / 'run_insert/run.json')['core']
        self.assertNotEqual(insert_core['protocol_sha256'], core['protocol_sha256'])
        # Scoring re-validates the head-call pin; the summary reports strict, lenient and call metrics.
        scoring = scoring_manifest(self.root, self.manifest)
        result = score.score_run(self.root / 'run_decode', scoring, self.root / 'score_decode', self.root, **SCOPE)
        self.assertEqual(result['run_core']['adapter']['headcall'], core['adapter']['headcall'])
        summary = load_tool('headcall_eval_summary').summarize(self.root / 'score_decode', self.root / 'run_decode')
        self.assertEqual(summary['strict']['primary_score'], result['primary_score'])
        self.assertEqual(summary['lenient']['answer_sources'], {'strict': len(ids)})
        calls = summary['calls']['overall']
        self.assertEqual((calls['items'], calls['calls'], calls['valid_calls'], calls['strict_calls']), (2, 2, 2, 2))
        self.assertEqual(calls['zero_call_items'], 0)
        self.assertEqual(calls['used_exchanges'], 2)  # "2.00 m" is cited after its response
        # Without an injected generator, the mock records a zero-call synthetic account.
        self.root = self.root / 'mock'
        self.root.mkdir()
        self.run_arm('plain_mock', carriers='insert', headcall='decode')
        mock_record = load_json(self.root / 'run_plain_mock/headcalls' / f'{contracts.safe_id(ids[0])}.json')
        self.assertTrue(mock_record['synthetic'])
        self.assertEqual(mock_record['summary']['calls'], 0)

    def test_cli_and_wrapper_forward_the_option(self):
        from student_pilot.orchard_eval.__main__ import main
        shared = ['--manifest', 'manifest.json', '--model', 'qwen35', '--output', 'unused/run', '--variant', 'distilled',
                  '--adapter', 'adapter', '--training-receipt', 'receipt', '--artifact-root', 'unused', '--carriers', 'insert']
        for flag in ([], ['--headcall', 'decode']):
            with mock.patch.object(frames, 'cpu_check', return_value={}) as check, redirect_stdout(io.StringIO()):
                main(['cpu-check', *shared, *flag])
            with mock.patch.object(generate, 'generate_run', return_value={}) as run, redirect_stdout(io.StringIO()):
                main(['generate', *shared, *flag, '--preflight', 'preflight.json'])
            for call in (check, run):
                if flag:
                    self.assertEqual(call.call_args.kwargs['headcall'], 'decode')
                else:
                    self.assertNotIn('headcall', call.call_args.kwargs)
        job = load_script('eval_job', REPO / 'scripts/orchard/eval_job.py')
        self.assertEqual(job.resolve_model_args('distilled', {'EVAL_CARRIERS': 'insert'}), ['--carriers', 'insert'])
        self.assertEqual(job.resolve_model_args('distilled', {'EVAL_CARRIERS': 'insert', 'EVAL_HEADCALL': 'decode'}),
                         ['--carriers', 'insert', '--headcall', 'decode'])
        self.assertEqual(job.resolve_model_args('distilled', {}), [])
        for env in ({'EVAL_HEADCALL': 'decode'}, {'EVAL_CARRIERS': 'none', 'EVAL_HEADCALL': 'decode'},
                    {'EVAL_CARRIERS': 'insert', 'EVAL_HEADCALL': 'yes'}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                job.resolve_model_args('distilled', env)


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tool(name):
    return load_script(name, REPO / 'tools' / f'{name}.py')


class LenientRuleTests(unittest.TestCase):
    def test_strict_first_then_the_documented_rule(self):
        summary = load_tool('headcall_eval_summary')
        options = ['A. red', 'B. blue']
        self.assertEqual(summary.lenient_answer('<think>\nx\n</think>\n\nB<|im_end|>', options), ('B', 'strict'))
        self.assertEqual(summary.lenient_answer('<think>\nx\n</think>\n\nThe answer is (B).<|im_end|>', options),
                         ('B', 'lenient'))
        self.assertEqual(summary.lenient_answer('<think>\nx\n</think>\n\nabout 3.5 m<|im_end|>', []), ('3.5', 'lenient'))
        self.assertEqual(summary.lenient_answer('<think>\nunclosed', []), (None, 'none'))


# ---------------------------------------------------------------------------------------------- real decode (tiny asset)

def camera_model():
    """The tiny Qwen3.5 asset with a 4-block ViT and the trainer's camera, gravity, scale and point-depth heads."""
    from transformers import AutoConfig, AutoModelForImageTextToText
    from student_pilot import auxiliary_losses, camera_config
    from transformers import AutoTokenizer
    config = AutoConfig.from_pretrained(TINY)
    config.vision_config.depth = 4
    torch.manual_seed(0)
    model = AutoModelForImageTextToText.from_config(config).float().eval()
    settings = camera_config.normalize({
        'weight': 1.0, 'weight_gravity': 0.5, 'weight_scale': 0.2, 'embed_dim': 16, 'num_heads': 2, 'trunk_depth': 2,
        'refine_iterations': 2, 'supervision': {'path': '/fixture/bank.npz', 'sha256': '0' * 64},
        'point_depth': {'weight': 0.5, 'd_proj': 16, 'mlp_hidden': 16, 'num_heads': 2, 'context_depth': 1,
                        'vit_layers': [1, 2, 4], 'num_points_per_frame': 8}})
    heads = auxiliary_losses.attach(model, None, AutoTokenizer.from_pretrained(TINY), settings)
    with torch.no_grad():
        heads.camera.tokens.normal_(0.0, 0.5)
        heads.camera.head.pose_branch.fc2.bias[7:9] += 1.0  # a printable field of view when untrained
    heads.requires_grad_(False)
    return model


class Forced(object):
    """A model wrapper whose next token follows a script; attributes (the heads) resolve on the model."""

    def __init__(self, model, script, prompt_length):
        self.model, self.script, self.prompt_length, self.history = model, script, prompt_length, []

    def __getattr__(self, name):
        return getattr(self.__dict__['model'], name)

    def __call__(self, **kwargs):
        out = self.model(**kwargs)
        if kwargs.get('past_key_values') is None:
            self.history = kwargs['input_ids'][0].tolist()
        else:
            self.history.append(int(kwargs['input_ids'][0, 0]))
        generated = self.history[self.prompt_length:]
        boundary = max([i for i, token in enumerate(generated) if token == self.script['close']], default=-1)
        segment = self.script['segments'][min(sum(token == self.script['close'] for token in generated),
                                               len(self.script['segments']) - 1)]
        position = len(generated) - boundary - 1
        forced = torch.full_like(out.logits[:, -1:], -1e4)
        forced[0, 0, segment[position] if position < len(segment) else self.script['filler']] = 0.0
        out.logits = forced
        return out


@unittest.skipUnless(os.path.isdir(TINY), 'needs the tiny Qwen3.5 asset')
class RealDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy
        from transformers import AutoProcessor
        from transformers.video_utils import VideoMetadata
        from student_pilot.camera_targets import insert_carriers
        cls.model = camera_model()
        cls.processor = AutoProcessor.from_pretrained(TINY)
        video = (numpy.random.RandomState(2).rand(32, 64, 64, 3) * 255).astype(numpy.uint8)
        metadata = VideoMetadata(total_num_frames=32, fps=2.0, frames_indices=list(range(32)), width=64, height=64)
        messages = [{'role': 'user', 'content': [{'type': 'video'}, {'type': 'text', 'text': 'How far is the chair?'}]}]
        text = cls.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        batch = dict(cls.processor(text=[text], videos=[video], video_metadata=[metadata], do_sample_frames=False,
                                   return_tensors='pt', return_metadata=True))
        batch.pop('video_metadata', None)
        extended = insert_carriers(batch, cls.processor.tokenizer)
        cls.positions = extended.pop('aux_camera_positions')
        cls.batch = extended  # pack_input's carrier-bearing batch: the audit holds the positions
        cls.audit = {'carriers': 'insert', 'carrier_positions': cls.positions[0].tolist()}
        tok = cls.processor.tokenizer
        cls.eos = [tok.convert_tokens_to_ids('<|im_end|>'), tok.convert_tokens_to_ids('<|endoftext|>')]
        call = '<tool_call>{"name": "depth", "frame": 4, "point": [300, 700]}</tool_call>'
        cls.first = tok.encode('look ' + call, add_special_tokens=False)
        cls.script = {'segments': [cls.first, tok.encode(' so far', add_special_tokens=False) + [cls.eos[0]]],
                      'close': tok.convert_tokens_to_ids('</tool_response>'), 'filler': tok.encode('a')[0]}

    def decode(self, max_new_tokens):
        effective = {'max_new_tokens': max_new_tokens, 'eos_token_id': self.eos, 'do_sample': False, 'num_beams': 1,
                     'num_return_sequences': 1}
        forced = Forced(self.model, self.script, self.batch['input_ids'].shape[1])
        decoder = generate.headcall_decoder(forced, self.processor, effective, {'decode': contracts.HEADCALL_DECODE})
        seen = []
        language = self.model.model.language_model
        handle = language.register_forward_pre_hook(
            lambda module, args, kwargs: seen.append(kwargs['inputs_embeds'].detach().clone()), with_kwargs=True)
        try:
            result, record = generate.headcall_item(decoder, dict(self.batch), self.audit, 'q1')
        finally:
            handle.remove()
        return result, record, seen

    def test_heads_answer_the_call_from_the_carrier_prefill(self):
        from student_pilot.head_api import HeadSession
        from headcall.protocol import format_value
        result, record, seen = self.decode(256)
        self.assertEqual(record['summary']['calls'], 1)
        self.assertEqual(record['summary']['valid_calls'], 1)
        self.assertEqual(record['summary']['finish_reason'], 'eos')
        self.assertEqual(result['tokens'][-1], self.eos[0])
        reference = HeadSession.from_forward(self.model, {**self.batch, 'aux_camera_positions': self.positions})
        expected = format_value('depth', float(reference.depth(4, [300, 700])))
        self.assertEqual(record['calls'][0]['response'], expected)
        self.assertIn('<tool_response>' + expected + '</tool_response>', result['raw'])
        self.assertEqual(record['summary']['inserted_tokens'],
                         len(self.processor.tokenizer.encode('<tool_response>' + expected + '</tool_response>',
                                                             add_special_tokens=False)))
        # The prefill (the first, multi-token forward) carries c_first / c_rest at the 16 carrier positions.
        tokens = self.model.auxiliary_heads.camera.tokens.detach()[[0] + [1] * 15]
        self.assertGreater(seen[0].shape[1], 1)
        self.assertTrue(torch.equal(seen[0][0, self.positions[0]], tokens.to(seen[0].dtype)))
        self.assertTrue(all(step.shape[1] == 1 for step in seen[1:]))

    def test_the_cap_counts_inserted_tokens(self):
        cap = len(self.first) + 3
        result, record, _ = self.decode(cap)
        self.assertEqual(len(result['tokens']), cap)
        self.assertEqual(record['summary']['finish_reason'], 'max_new_tokens')
        self.assertEqual(record['summary']['inserted_tokens'], 3)
        # The evaluator's finish rule holds: not an EOS, exactly the cap.
        self.assertNotIn(result['tokens'][-1], self.eos)

    def test_an_audit_without_carriers_refuses(self):
        decoder = generate.headcall_decoder(self.model, self.processor, {'max_new_tokens': 4, 'eos_token_id': self.eos},
                                            {'decode': contracts.HEADCALL_DECODE})
        with self.assertRaisesRegex(ValueError, '16 carriers'):
            generate.headcall_item(decoder, dict(self.batch), {'carriers': 'none'}, 'q1')


if __name__ == '__main__':
    unittest.main()
