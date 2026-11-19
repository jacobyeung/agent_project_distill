import ast
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import torch
from PIL import Image

from student_pilot.sam3_tower import Sam3Tower, attach_sam3_tower, normalize_phrase, postprocess


class StubModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(1))
        self.backbone = SimpleNamespace(forward_text=self.text)
        self.phrases = []
        self.grad_modes = []

    def text(self, phrases, device):
        self.phrases.extend(phrases)
        return {'language_features': torch.tensor([len(phrases[0])], device=device)}

    def _get_dummy_prompt(self):
        return object()

    def forward_grounding(self, *, backbone_out, **kwargs):
        self.grad_modes.append(torch.is_grad_enabled())
        seed = backbone_out['backbone_fpn'][0][0, 0, 0, 0]
        return {
            'pred_logits': torch.logit(torch.linspace(.99, .1, 12)).view(1, 12, 1),
            'presence_logit_dec': torch.logit(torch.tensor([.8])),
            'pred_boxes': torch.tensor([.5, .5, .5, .5]).expand(1, 12, 4),
            'pred_masks': (torch.tensor([[-1., 1.], [1., -1.]]) + seed).expand(1, 12, 2, 2),
        }


class StubBackend:
    def __init__(self):
        self.model = StubModel()
        self.find_stage = object()
        self.batch_sizes = []

    def set_image_batch(self, images):
        self.batch_sizes.append(len(images))
        pixels = torch.tensor([im.getpixel((0, 0))[0] / 255 for im in images])[:, None, None, None]
        return {'backbone_out': {'backbone_fpn': [pixels], 'vision_pos_enc': [pixels*0]}}

    def set_image(self, image):
        return self.set_image_batch([image])


class TowerTests(unittest.TestCase):
    def make(self):
        backend = StubBackend()
        return Sam3Tower({'device': 'cpu'}, backend=backend), backend

    def test_import_is_lazy_and_flag_is_off(self):
        self.assertNotIn('sam3', sys.modules)
        parent = torch.nn.Linear(2, 2)
        with patch('student_pilot.sam3_tower.Sam3Tower', side_effect=AssertionError('loaded')):
            self.assertIsNone(attach_sam3_tower(parent))
        self.assertFalse(hasattr(parent, 'sam3_tower'))
        with self.assertRaises(ValueError):
            attach_sam3_tower(parent, enabled='false')

    def test_attachment_excludes_weights_and_train_recursion(self):
        parent = torch.nn.Linear(2, 2)
        before = {k: v.clone() for k, v in parent.state_dict().items()}
        params = tuple(parent.parameters())
        modules = tuple(parent.modules())
        backend = StubBackend()
        tower = attach_sam3_tower(parent, {'device': 'cpu'}, enabled=True, backend=backend)
        parent.train()
        self.assertFalse(tower._backend.model.training)
        self.assertFalse(backend.model.weight.requires_grad)
        self.assertEqual(tuple(parent.parameters()), params)
        self.assertEqual(tuple(parent.modules()), modules)
        self.assertEqual(set(parent.state_dict()), set(before))
        for name, tensor in parent.state_dict().items():
            torch.testing.assert_close(tensor, before[name], rtol=0, atol=0)
        optimizer = torch.optim.SGD(parent.parameters(), lr=.1)
        self.assertTrue(all(p is not backend.model.weight for group in optimizer.param_groups for p in group['params']))
        with self.assertRaises(ValueError):
            attach_sam3_tower(parent, {'device': 'cpu'}, enabled=True, backend=backend)

    def test_shapes_batches_phrase_reuse_and_ownership(self):
        tower, backend = self.make()
        frames = [Image.new('RGB', (17+i, 11+i), (i, 0, 0)) for i in range(17)]
        features = tower.encode(frames)
        self.assertEqual(backend.batch_sizes, [1]*17)
        first = tower.detect(features, ' Kitchen_Cabinets ')
        second = tower.detect(features, 'TABLES')
        self.assertEqual(backend.batch_sizes, [1]*17)
        self.assertEqual(backend.model.phrases, ['kitchen cabinet', 'table'])
        self.assertEqual(len(first), 17)
        for i, result in enumerate(first):
            count = len(result.scores)
            self.assertEqual(result.masks.shape, (count, 11+i, 17+i))
            self.assertEqual(result.boxes.shape, (count, 4))
            self.assertEqual(result.masks.dtype, torch.bool)
            self.assertTrue((result.joint_scores >= .2).all())
            self.assertTrue(count <= 10)
            self.assertFalse(result.scores.requires_grad)
            torch.testing.assert_close(result.masks, second[i].masks)
            self.assertNotIn('language_features', features.frames[i])
        self.assertFalse(any(backend.model.grad_modes))
        with self.assertRaises(ValueError):
            self.make()[0].detect(features, 'chair')

    def test_batch_equals_singles_even_with_batch_dependent_backend(self):
        class BatchDependent(StubBackend):
            def set_image_batch(self, images):
                state = super().set_image_batch(images)
                state['backbone_out']['backbone_fpn'][0] += len(images)-1
                return state
        images = [Image.new('RGB', (11+i, 9+i), (50*i, 0, 0)) for i in range(4)]
        for precision in ('bf16', 'float32'):
            backend = BatchDependent()
            tower = Sam3Tower({'device': 'cpu', 'precision': precision, 'image_batch_size': 4}, backend=backend)
            batch = tower.encode(images)
            singles = [tower.encode([im]) for im in images]
            self.assertEqual(backend.batch_sizes, [1]*8)
            for i, single in enumerate(singles):
                for key in batch.frames[i]:
                    for a, b in zip(batch.frames[i][key], single.frames[0][key]):
                        torch.testing.assert_close(a, b, rtol=0, atol=0)
            for legacy in (False, True):
                outputs = tower._detect(batch, 'chair', legacy=legacy)
                for a, single in zip(outputs, singles):
                    b = tower._detect(single, 'chair', legacy=legacy)[0]
                    self.assertEqual(a.presence, b.presence)
                    for key in ('scores', 'all_scores', 'joint_scores', 'query_ids', 'boxes', 'masks'):
                        torch.testing.assert_close(getattr(a, key), getattr(b, key), rtol=0, atol=0)
            native = Sam3Tower({'device': 'cpu', 'image_batch_size': 4, 'native_image_batch': True},
                               backend=BatchDependent())
            self.assertFalse(torch.equal(native.encode(images).frames[0]['backbone_fpn'][0],
                                         batch.frames[0]['backbone_fpn'][0]))

    def test_native_batches_require_explicit_override(self):
        backend = StubBackend()
        tower = Sam3Tower({'device': 'cpu', 'image_batch_size': 8, 'native_image_batch': True}, backend=backend)
        tower.encode([Image.new('RGB', (4, 4)) for _ in range(17)])
        self.assertEqual(backend.batch_sizes, [8, 8, 1])
        for settings in ({'image_batch_size': 0}, {'image_batch_size': 9}, {'image_batch_size': True},
                         {'native_image_batch': 'true'}, {'precision': 'fp16'}):
            with self.assertRaises(ValueError):
                Sam3Tower(dict(device='cpu', **settings), backend=StubBackend())

    def test_float32_control_does_not_force_bf16_and_is_scoped(self):
        linear = torch.nn.Linear(7, 11).eval()
        x = torch.randn(2, 3, 7)
        def forced(activation, linear, value):
            return torch.relu(torch.nn.functional.linear(value.bfloat16(), linear.weight.bfloat16(),
                                                         linear.bias.bfloat16()))
        fake = SimpleNamespace(addmm_act=forced)
        tower, _ = self.make()
        with patch.dict(sys.modules, {'sam3.model.vitdet': fake}), torch.inference_mode():
            with tower._autocast():
                actual = fake.addmm_act(torch.nn.ReLU, linear, x)
                self.assertEqual(actual.dtype, torch.float32)
                torch.testing.assert_close(actual, torch.relu(linear(x)))
            self.assertIs(fake.addmm_act, forced)
            tower.precision = 'bf16'
            with tower._autocast():
                self.assertIs(fake.addmm_act, forced)

    def test_dual_contract_comparison_reuses_grounding_forward(self):
        tower, backend = self.make()
        features = tower.encode([Image.new('RGB', (11, 9))])
        production, legacy = tower._detect(features, 'chair', legacy=None)[0]
        self.assertEqual(len(backend.model.grad_modes), 1)
        for a, b in ((production, tower.detect(features, 'chair')[0]),
                     (legacy, tower.detect_cache_reference(features, 'chair')[0])):
            for key in ('all_scores', 'scores', 'query_ids', 'masks'):
                torch.testing.assert_close(getattr(a, key), getattr(b, key), rtol=0, atol=0)

    def test_joint_floor_cap_ties_and_legacy(self):
        raw = StubModel().forward_grounding(backbone_out={'backbone_fpn': [torch.zeros(1, 1, 1, 1)]})
        raw['pred_logits'] = torch.zeros(1, 12, 1)  # sigmoid = .5
        raw['presence_logit_dec'] = torch.tensor([0.])
        result = postprocess(raw, (9, 13))
        self.assertEqual(result.query_ids.tolist(), list(range(10)))
        torch.testing.assert_close(result.boxes[0], torch.tensor([3.25, 2.25, 9.75, 6.75]))
        raw['presence_logit_dec'] = torch.logit(torch.tensor([.2]))
        self.assertEqual(postprocess(raw, (9, 13)).masks.shape, (0, 9, 13))
        self.assertEqual(len(postprocess(raw, (9, 13), legacy=True).scores), 5)
        raw['pred_logits'][:] = torch.inf  # sigmoid exactly 1; inclusive joint boundary
        self.assertEqual(len(postprocess(raw, (9, 13)).scores), 10)

    def test_mixed_score_ties_sort_by_query_id_across_cap(self):
        raw = StubModel().forward_grounding(backbone_out={'backbone_fpn': [torch.zeros(1, 1, 1, 1)]})
        for dtype in (torch.float32, torch.bfloat16):
            raw['pred_logits'] = torch.tensor([0., 2., 0., 2., 0., 2., 0., 2., 0., 2., 0., 2.],
                                              dtype=dtype).view(1, 12, 1)
            self.assertEqual(postprocess(raw, (9, 13), legacy=True).query_ids.tolist(), [1, 3, 5, 7, 9])
            self.assertEqual(postprocess(raw, (9, 13)).query_ids.tolist(), [1, 3, 5, 7, 9, 11, 0, 2, 4, 6])

    def test_invalid_input(self):
        tower, _ = self.make()
        for images in ([], [Image.new('L', (4, 4))], [torch.zeros(3, 4, 4)]):
            with self.assertRaises(ValueError):
                tower.encode(images)
        features = tower.encode([Image.new('RGB', (4, 4))])
        with self.assertRaises(ValueError):
            tower.detect(features, ' _ ')
        with self.assertRaises(ValueError):
            Sam3Tower({'unknown': 1})

    def test_normalization_matches_reference(self):
        reference = Path('/scratch/jjyeung/orch_cd/ttower/work/sam3/common.py')
        tree = ast.parse(reference.read_text())
        nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'phrase') or
                 (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SINGULAR' for t in n.targets))]
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(reference), 'exec'), namespace)
        for label in list(namespace['SINGULAR']) + ['  Kitchen_Cabinets ', 'TV', 'trash  bin', 'office chairs']:
            from trace_format.contracts import contract_epoch
            with contract_epoch(False):
                self.assertEqual(normalize_phrase(label), namespace['phrase'](label))


if __name__ == '__main__':
    unittest.main()
