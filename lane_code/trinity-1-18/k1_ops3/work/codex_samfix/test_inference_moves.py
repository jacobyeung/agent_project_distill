"""CPU regression through GPU boundaries, real lazy SAM load, encode and get_abs_pos.

Only heavyweight model construction/assets and physical device transport are stubbed.
The transport calls Module._apply with Tensor.to(copy=True): it exercises PyTorch's
real parameter .data replacement without CUDA or precision changes.
"""
import argparse
import ast
from contextlib import ExitStack, contextmanager
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
SAM_SOURCE = Path('/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src')
parser = argparse.ArgumentParser()
parser.add_argument('--kit-root', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.kit_root/'native_kit'))
import boundaries
import bindings as B
import sam3_tower as SAM
from stub_backend import Model, StubBackend
from student_pilot import tower_read as G3T

torch.set_num_threads(1)
RUN = ROOT/'receipts'/('regression_'+uuid.uuid4().hex[:8])
RUN.mkdir(parents=True)
EVENTS = []

# Execute the actual failing function without importing the heavyweight SAM package.
source = SAM_SOURCE/'sam3/model/vitdet.py'
tree = ast.parse(source.read_text(), filename=str(source))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'get_abs_pos')
scope = dict(torch=torch, F=F, math=math, Tensor=torch.Tensor, Tuple=tuple)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
get_abs_pos = scope['get_abs_pos']

class CopyModel(Model):
    def __init__(self, **unused):
        super().__init__()
        self.pos_embed = torch.nn.Parameter(torch.arange(15.).reshape(1, 5, 3), requires_grad=False)
        self.moves = []

    def to(self, device):
        before = self.pos_embed.detach().clone()
        identity = id(self.pos_embed)
        # A CPU .to('cpu') is a no-op; copy=True forces the same _apply path as a device change.
        self._apply(lambda t: t.to(device='cpu', copy=True))
        assert id(self.pos_embed) == identity, 'Test must exercise parameter data replacement'
        assert torch.equal(before, self.pos_embed), 'Transport changed values'
        event = dict(requested_device=str(device), inference_mode=torch.is_inference_mode_enabled(),
                     parameter_is_inference=self.pos_embed.is_inference())
        self.moves.append(event)
        EVENTS.append(event)
        return self

class SliceProcessor(StubBackend):
    def __init__(self, model, resolution, device):
        self.model, self.find_stage = model, None
        assert resolution == 1008

    def set_image(self, image):
        # This is vitdet.py's real get_abs_pos, including the failing [:, :1] slice.
        pos = get_abs_pos(self.model.pos_embed, True, (2, 2))
        state = super().set_image(image)
        state['backbone_out']['backbone_fpn'][0] += pos.sum()
        return state

def module(name, **attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    return result

@contextmanager
def sam_environment():
    files = {'sam3/model_builder.py', 'sam3/model/sam3_image_processor.py',
             'sam3/model/sam3_image.py', 'sam3/model/vl_combiner.py',
             'sam3/model/box_ops.py', 'sam3/model/data_misc.py'}
    receipt = RUN/'sam_receipt.json'
    receipt.write_text(json.dumps(dict(checkpoint_sha256=SAM.CHECKPOINT_SHA256,
        sam3_upstream_revision=SAM.UPSTREAM_REVISION, source_files={n:'a'*64 for n in files})))
    checkpoint = RUN/'stub_checkpoint'
    def build(**kwargs):
        assert torch.is_inference_mode_enabled(), 'Real lazy load must run inside encode'
        assert kwargs['load_from_HF'] is False
        assert kwargs['eval_mode'] is True
        assert kwargs['enable_inst_interactivity'] is False
        return CopyModel()
    modules = {'sam3': module('sam3', __file__=str(SAM_SOURCE/'sam3/__init__.py'), __path__=[]),
               'sam3.model': module('sam3.model', __path__=[]),
               'sam3.model_builder': module('sam3.model_builder', build_sam3_image_model=build),
               'sam3.model.sam3_image_processor': module('sam3.model.sam3_image_processor', Sam3Processor=SliceProcessor)}
    with patch.dict(sys.modules, modules), patch.object(SAM, 'sha256', side_effect=lambda p:
            SAM.CHECKPOINT_SHA256 if Path(p) == checkpoint else 'a'*64), \
            patch.object(B, 'checked', side_effect=lambda pin: Path(pin['path'])):
        yield dict(sam_checkpoint=dict(path=str(checkpoint), sha256=B.perception.SAM_SHA),
                   sam_receipt=dict(path=str(receipt)), sam_source=str(SAM_SOURCE),
                   tower_weights=dict(path='unused', sha256=G3T.WEIGHTS_SHA256),
                   tower_config=dict(path='unused', sha256=G3T.CONFIG_SHA256))

def boundary(cls, settings):
    # Bypass only CUDA admission checks. Execute the real GPU methods on CPU.
    obj = cls.__new__(cls)
    obj.settings, obj.device = settings, 'cpu'
    obj.model = obj.sam_model = None
    return obj

def original_boundary():
    spec = importlib.util.spec_from_file_location('original_boundaries', KIT/'native_kit/boundaries.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.GPU

class Regression(unittest.TestCase):
    def test_torch_mechanism_and_inference_copy_control(self):
        with torch.inference_mode():
            broken = torch.nn.Parameter(torch.arange(15.).reshape(1, 5, 3), requires_grad=False)
        broken.data = broken.data.to('cpu', copy=True)
        self.assertFalse(broken.is_inference())
        with torch.inference_mode(), self.assertRaisesRegex(RuntimeError, 'Inference tensors do not track version counter'):
            get_abs_pos(broken, True, (2, 2))
        with torch.inference_mode():
            safe = CopyModel()
            safe.to('cpu')
            self.assertTrue(safe.pos_embed.is_inference())
            self.assertEqual(tuple(get_abs_pos(safe.pos_embed, True, (2, 2)).shape), (1, 2, 2, 3))

    def test_four_capture_round_trips_real_lazy_load_encode_and_slice(self):
        with sam_environment() as settings:
            b = boundary(boundaries.GPU, settings)
            image = Image.new('RGB', (48, 36), (21, 55, 89))
            capture = dict(dense_frames=[dict(index=0)], anchor_slots=[0], anchor_indices=[0])
            first = None
            with patch.object(G3T, 'FrozenG3TTower') as tower:
                for index in range(4):
                    b.tower(capture, [image])
                    sam = b.sam()
                    features = sam.encode([image])
                    tensor = features.frames[0]['backbone_fpn'][0]
                    if first is None:
                        first = tensor.clone()
                    else:
                        self.assertTrue(torch.equal(first, tensor), f'Capture {index+1} differs')
                    self.assertTrue(sam._backend.model.pos_embed.is_inference())
                self.assertEqual(tower.call_count, 4, 'G3T is constructed anew for each capture')
            self.assertTrue(all(m['inference_mode'] for m in sam._backend.model.moves))

    def test_sam_offload_alone_preserves_parameter_state(self):
        with sam_environment() as settings:
            b = boundary(boundaries.GPU, settings)
            sam = b.sam()
            sam.encode([Image.new('RGB', (8, 8))])
            with patch.object(G3T, 'FrozenG3TTower'):
                b.tower(dict(dense_frames=[], anchor_slots=[], anchor_indices=[]), [])
            with torch.inference_mode():
                get_abs_pos(sam._backend.model.pos_embed, True, (2, 2))

    def test_sam_restore_alone_preserves_parameter_state(self):
        with sam_environment() as settings:
            b = boundary(boundaries.GPU, settings)
            b.sam().encode([Image.new('RGB', (8, 8))])
            b.sam().encode([Image.new('RGB', (8, 8))])

    def test_capture_one_features_and_detections_are_exactly_equal(self):
        outputs = []
        with sam_environment() as settings, patch.object(G3T, 'FrozenG3TTower'):
            for cls in (original_boundary(), boundaries.GPU):
                torch.manual_seed(17)
                b = boundary(cls, settings)
                b.tower(dict(dense_frames=[], anchor_slots=[], anchor_indices=[]), [])
                sam = b.sam()
                features = sam.encode([Image.new('RGB', (48, 36), (21, 55, 89))])
                outputs.append((features, sam.detect(features, 'chair')[0], sam._backend.model))
        a, b = outputs
        for key in a[0].frames[0]:
            for x, y in zip(a[0].frames[0][key], b[0].frames[0][key], strict=True):
                self.assertTrue(torch.equal(x, y))
        for key, x in vars(a[1]).items():
            y = getattr(b[1], key)
            self.assertTrue(torch.equal(x, y) if isinstance(x, torch.Tensor) else x == y, key)
        for x, y in zip(a[2].parameters(), b[2].parameters(), strict=True):
            self.assertTrue(torch.equal(x, y))

    def test_g3t_real_load_keeps_initial_move_in_inference_mode(self):
        config = RUN/'tower_config.json'
        config.write_text(json.dumps(dict(embed_dim=1024, img_size=518, patch_size=14,
            enable_depth=True, enable_point=True, enable_gravity_camera_heads=True)))
        normal = CopyModel()
        state = normal.state_dict()
        class Weights:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def keys(self): return state.keys()
            def get_tensor(self, key): return state[key]
        modules = {'student_pilot.c1r_ref': module('student_pilot.c1r_ref', source_import=lambda p: CopyModel),
                   'student_pilot.g3t_online': module('student_pilot.g3t_online', VENDOR=RUN,
                                                     vendor_digest=lambda: G3T.SOURCE_SHA256),
                   'safetensors': module('safetensors', safe_open=lambda *a, **kw: Weights())}
        with patch.dict(sys.modules, modules), patch.object(G3T, '_hash', side_effect=lambda p:
                G3T.CONFIG_SHA256 if str(p) == str(config) else G3T.WEIGHTS_SHA256):
            tower = G3T.FrozenG3TTower(dict(weights_path='stub', config_path=str(config), device='cpu'))
            tower._load()
            self.assertTrue(tower.module.pos_embed.is_inference())
            self.assertTrue(all(m['inference_mode'] for m in tower.module.moves))
            with torch.inference_mode(): get_abs_pos(tower.module.pos_embed, True, (2, 2))

    def test_own_model_moves_keep_normal_parameters_across_four_captures(self):
        model = CopyModel().eval().requires_grad_(False)
        own = NS(depth_map=torch.ones(1), gravity=torch.tensor([0., -1., 0.]),
                 depth_head=NS(query=lambda d, uv: torch.ones((32, 51*51))))
        def decode(*args, **kwargs):
            self.assertFalse(torch.is_grad_enabled())
            self.assertFalse(torch.is_inference_mode_enabled())
            get_abs_pos(model.pos_embed, True, (2, 2))
            return NS(heads=own)
        def load(*args, **kwargs):
            self.assertFalse(torch.is_inference_mode_enabled())
            return model, object(), {}
        runtime = NS(prompt_batch=lambda *a: {})
        modules = {'read_runtime': module('read_runtime', load_model=load),
                   'routed': module('routed', source_pins=lambda: {}),
                   'evalpath': module('evalpath', runtime=runtime),
                   'student_pilot.carrier_c1_decode': module('student_pilot.carrier_c1_decode', _prepare_decode=decode),
                   'student_pilot.ground_context': module('student_pilot.ground_context', closed_adapters=lambda fn: fn)}
        c = dict(anchor_indices=[0], video_sha256='video', anchor_slots=[0], dense_frames=[dict(sha256='frame')],
                 model_row=dict(student_input=dict(frame_indices=[0], video_identity=dict(video_sha256='video'),
                                                   frames=[dict(sha256='frame')])))
        b = boundary(boundaries.GPU, dict(config={}, artifact={}, data_receipt={}))
        with patch.dict(sys.modules, modules), patch.object(B, 'checked', return_value=RUN), \
                patch.object(B, 'load', return_value={}):
            for _ in range(4):
                depth, gravity = b.own(c, [], NS(grid_uv=G3T.GRID_UV))
                self.assertEqual(depth.shape, (32, 51, 51))
                np.testing.assert_array_equal(gravity, [0., -1., 0.])
                self.assertFalse(model.pos_embed.is_inference())
                self.assertIsInstance(model.pos_embed._version, int)
        self.assertFalse(any(m['inference_mode'] for m in model.moves))

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Regression))
    (RUN/'result.json').write_text(json.dumps(dict(kit_root=str(args.kit_root), torch_version=torch.__version__,
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), success=result.wasSuccessful(),
        cuda_initialized=torch.cuda.is_initialized(), events=EVENTS), indent=2)+'\n')
    print('Receipt:', RUN/'result.json')
    raise SystemExit(0 if result.wasSuccessful() else 1)
