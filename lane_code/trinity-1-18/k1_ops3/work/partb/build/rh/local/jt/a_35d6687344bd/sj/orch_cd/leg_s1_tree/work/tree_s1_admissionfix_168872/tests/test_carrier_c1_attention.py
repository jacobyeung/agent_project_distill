"""C1 prefix isolation must not depend on the loader's attention backend."""
import unittest
from unittest.mock import patch

import torch

from student_pilot.carrier_c1 import CarrierC1
from student_pilot.carrier_c1_data import C1_A, C1_B, C1_C
from tests import test_carrier_c1 as fixtures


def requested_backend(backend, placement=C1_C):
    def wrap(base, *args, **kwargs):
        # Construct on CPU with installed kernels, then emulate the loader's
        # backend choice before C1 takes ownership of the native model.
        base.config.text_config._attn_implementation = backend
        return CarrierC1(base, *args, **kwargs)
    with patch.object(fixtures, 'CarrierC1', side_effect=wrap):
        return fixtures.fixture(4, placement=placement, depth_enabled=False)


class AttentionTests(unittest.TestCase):
    def test_requested_eager_cannot_leak_answer_into_video_prefix(self):
        model, batch, _ = requested_backend('eager')
        model.eval()
        changed = {**batch, 'input_ids': batch['input_ids'].clone()}
        changed['input_ids'][0, -1] = 17
        end = int(batch['aux_video_prefix_end'][0])
        with torch.no_grad():
            before, after = model.hidden(batch), model.hidden(changed)
        torch.testing.assert_close(before[:, :end+1], after[:, :end+1], atol=0, rtol=0)

    def test_c_pins_native_text_backend_and_preserves_outputs_gradients_and_cache(self):
        reference = None
        for backend in ('sdpa', 'eager', 'flash_attention_2', 'flash_attention_3', 'flex_attention'):
            with self.subTest(backend=backend):
                model, batch, target = requested_backend(backend)
                lm = model.model.language_model
                self.assertEqual(lm.config._attn_implementation, 'sdpa')
                self.assertEqual(lm.layers[1].self_attn.config._attn_implementation, 'sdpa')
                self.assertEqual(model.model.visual.config._attn_implementation, 'sdpa')
                masks = []
                hook = lm.layers[0].linear_attn.register_forward_pre_hook(
                    lambda m, a, k: masks.append(k['attention_mask']), with_kwargs=True)
                loss = model(batch, target)['loss']
                loss.backward()
                hook.remove()
                self.assertTrue(all(mask is None or mask.ndim == 2 for mask in masks))
                grad = lm.layers[1].self_attn.q_proj.weight.grad.clone()
                model.eval()
                with torch.no_grad():
                    hidden = model.hidden(batch)
                    changed = {**batch, 'pixel_values_videos': batch['pixel_values_videos'].clone()}
                    changed['pixel_values_videos'][-4:] *= -4
                    future = model.hidden(changed)
                    first = int(batch['aux_camera_positions'][0, 0])
                    self.assertGreater(float((hidden[:, first]-future[:, first]).abs().max()), 1e-6)
                    generated = model.generate(batch, max_new_tokens=2, do_sample=False)
                values = (loss.detach(), grad, hidden, generated)
                if reference is None:
                    reference = values
                else:
                    for value, expected in zip(values, reference):
                        torch.testing.assert_close(value, expected, atol=0, rtol=0)

    def test_other_placements_keep_the_requested_backend(self):
        for placement in (C1_A, C1_B):
            model, _, _ = requested_backend('eager', placement)
            self.assertEqual(model.model.language_model.config._attn_implementation, 'eager')


if __name__ == '__main__':
    unittest.main()
