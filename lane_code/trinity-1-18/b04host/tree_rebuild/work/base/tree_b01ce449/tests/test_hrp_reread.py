"""CPU re-read state, parsing, native-image and routed-loop integration checks."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import hrp_reread as hrp
from student_pilot import verify_pass as V
from transformers import GenerationConfig
from student_pilot import carrier_c1_decode as decode


class Tokenizer:
    eos_token_id = 1
    def decode(self, ids, **kw):
        return '{"point_2d": [500, 500]}'


class Processor:
    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer or Tokenizer()
        self.calls = []

    def apply_chat_template(self, messages, **kw):
        assert [c['type'] for c in messages[0]['content']] == ['image', 'text']
        assert kw['enable_thinking'] is False
        self.messages = messages
        return 'image prompt'

    def __call__(self, **kw):
        self.calls.append(kw)
        # A native tiny-model image, four unmerged patches -> one image token.
        ids = torch.tensor([[2, 62, 60, 63, 10]])
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids),
                    pixel_values=torch.zeros(4, 24), image_grid_thw=torch.tensor([[1, 2, 2]]),
                    mm_token_type_ids=torch.where(ids == 60, 1, 0))


class Model:
    def __init__(self):
        self.model = SimpleNamespace(rope_deltas=torch.tensor([[17]]))
        self.config = SimpleNamespace(text_config=SimpleNamespace(max_position_embeddings=10000))
        self.embedding = torch.nn.Embedding(64, 4)
        self.calls = []
        self.fail = False

    def get_input_embeddings(self):
        return self.embedding

    def forward(self,input_ids=None,**kwargs):raise AssertionError("unused fake forward")

    def generate(self, input_ids, **kw):
        batch=dict(input_ids=input_ids)
        assert self.model.rope_deltas is None
        self.calls.append((batch, kw))
        self.model.rope_deltas = torch.tensor([[-99]])
        if self.fail:
            raise RuntimeError('synthetic image failure')
        return torch.cat((batch['input_ids'], torch.tensor([[42, 1]])), dim=1)


def config():
    return hrp.Config({1: np.zeros((32, 48, 3), np.uint8), 3: np.ones((32, 48, 3), np.uint8)}, tuple(range(32)))


class RereadTests(unittest.TestCase):
    def test_native_json_null_multiple_bounds(self):
        self.assertEqual(hrp.parse_point('[{"point_2d":[100,200]}]'), ([100, 200], 'point'))
        for raw, status in [('[]', 'null'), ('{"point_2d":null}', 'null'), ('garbage', 'invalid'),
                            ('[{"point_2d":[1,2]}, {"point_2d":[3,4]}]', 'multiple'),
                            ('{"point_2d":[1001,2]}', 'invalid'), ('{"point_2d":[true,2]}', 'invalid')]:
            self.assertEqual(hrp.parse_point(raw)[1], status)

    def test_source_identity_validation_before_inference(self):
        cfg = config()
        cfg.validate(dict(hrp_frame_indices=list(range(32))))
        with self.assertRaisesRegex(ValueError, 'exact 32'):
            cfg.validate(dict(hrp_frame_indices=list(range(1,33))))
        with self.assertRaisesRegex(ValueError, 'exact 32'):
            cfg.validate({})
        with self.assertRaisesRegex(ValueError, 'uint8 RGB'):
            hrp.Config({1: np.zeros((3,3))}, tuple(range(32))).validate(dict(hrp_frame_indices=list(range(32))))

    def test_image_batch_is_separate_and_rope_restored_on_success_and_failure(self):
        model, processor = Model(), Processor()
        old = model.model.rope_deltas
        result = hrp.read_image(model, processor, config().frames[1], 'chair', config())
        self.assertEqual(result['point_2d'], [500,500])
        self.assertIs(model.model.rope_deltas, old)
        batch, kwargs = model.calls[0]
        self.assertNotIn('video_grid_thw', batch)
        self.assertNotIn('past_key_values', kwargs)
        self.assertEqual(processor.calls[0]['size']['longest_edge'],602112)
        model.fail = True
        with self.assertRaisesRegex(RuntimeError,'synthetic'):
            hrp.read_image(model, processor, config().frames[1], 'chair', config())
        self.assertIs(model.model.rope_deltas, old)

    def test_budget_refuses_before_partial_object_read(self):
        cfg = hrp.Config(config().frames, tuple(range(32)), max_queries=1)
        backend = hrp.Backend(Model(), Processor(), None, cfg)
        with self.assertRaisesRegex(hrp.RenderError,'hrp_query_budget'):
            backend.ground('chair', None)
        self.assertEqual(backend.query_count,0)

    def test_truncated_json_is_not_an_accepted_point(self):
        model = Model()
        cfg = hrp.Config(config().frames, tuple(range(32)), max_new_tokens=2)
        def capped(input_ids, **kw):
            return torch.cat((input_ids, torch.tensor([[42,42]])),1)
        model.generate = capped
        result=hrp.read_image(model, Processor(), cfg.frames[1], 'chair', cfg)
        self.assertEqual(result['parse_status'],'capped')
        self.assertIsNone(result['point_2d'])

    def test_routed_generate_reuses_image_queries_and_replays(self):
        from tests.test_grounding_decode import fixture
        model, original, batch = fixture()
        model.generation_config=GenerationConfig.from_model_config(model.config)
        native=V.native_view(model)
        processor = Processor(original.tokenizer)
        processor._routing_tokens = original._routing_tokens
        batch['hrp_frame_indices'] = list(range(32))
        calls, outer_offsets = [], []
        def image_generate(input_ids, **kwargs):
            encoded=dict(input_ids=input_ids,**kwargs)
            calls.append(encoded)
            model.model.rope_deltas = torch.tensor([[777]])
            return torch.cat((encoded['input_ids'], torch.tensor([[42,1]])),1)
        tokenizer_decode = processor.tokenizer.decode
        def decode_ids(ids, skip_special_tokens=False):
            if skip_special_tokens:
                return '{"point_2d":[500,500]}'
            return tokenizer_decode(ids, skip_special_tokens=False)
        script = iter([40,40,1])
        def force(ids, logits):
            outer_offsets.append(model.model.rope_deltas.clone())
            logits = torch.full_like(logits, -1e9)
            logits[:, next(script)] = 0
            return logits
        with patch.object(V,'native_view',return_value=native), patch.object(native, 'generate', image_generate), patch.object(processor.tokenizer, 'decode', decode_ids):
            result = decode.generate(model, processor, batch, logits_processor=force, reread=config())
        self.assertEqual(len(calls),2)  # Two frames, once per unique object.
        self.assertEqual(len(result['calls']),2)
        self.assertEqual(result['heads']['ground_queries'][0]['backend'],'hrp_reread')
        self.assertEqual(len(result['heads']['ground_queries']),1)
        self.assertTrue(all(torch.equal(outer_offsets[0], x) for x in outer_offsets))
        self.assertEqual(result['finish'],'eos')
        self.assertIn('size unavailable', result['calls'][0]['response'])
        self.assertIn('P1', result['calls'][0]['response'])
        self.assertTrue(decode.replay(result)['byte_equal'])

    def test_no_ground_call_performs_no_reread(self):
        from tests.test_grounding_decode import fixture
        model, processor, batch = fixture()
        batch['hrp_frame_indices'] = list(range(32))
        def eos(ids, logits):
            logits = torch.full_like(logits,-1e9);logits[:,1]=0;return logits
        with patch.object(model,'generate',side_effect=AssertionError('unexpected image read')):
            result=decode.generate(model,processor,batch,logits_processor=eos,reread=config())
        self.assertEqual(result['heads']['ground_queries'],[])

    def test_real_native_tiny_image_generation(self):
        from tests.test_grounding_decode import fixture
        model, original, _ = fixture()
        processor = Processor()
        model.generation_config=GenerationConfig.from_model_config(model.config)
        native=V.native_view(model)
        actual = native.generate
        def scripted_native(input_ids, **kw):
            from transformers import LogitsProcessorList
            class Force:
                def __call__(self, ids, logits):
                    logits = torch.full_like(logits, -1e9)
                    logits[:,42 if ids.shape[1] == input_ids.shape[1] else 1] = 0
                    return logits
            return actual(input_ids=input_ids, **kw, logits_processor=LogitsProcessorList([Force()]))
        model.model.rope_deltas = torch.tensor([[23]])
        old = model.model.rope_deltas
        with patch.object(V,'native_view',return_value=native), patch.object(native,'generate',scripted_native):
            result = hrp.read_image(model,processor,config().frames[1],'chair',config())
        self.assertEqual(result['point_2d'],[500,500])
        self.assertIs(model.model.rope_deltas,old)


if __name__ == '__main__':
    unittest.main()
