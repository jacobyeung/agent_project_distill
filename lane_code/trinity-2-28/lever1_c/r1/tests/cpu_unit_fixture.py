"""Tiny production-architecture doubles for the CPU real-unit path (tests only).

build(): a job-shaped data root with a real artifact manifest (parity_kit
build_manifest over the delivered code roots), prepared settings, and a capture
index into the authenticated local a2.tar, so production stage_capture,
bind_item, Artifact.verify and Audit run unchanged on the served PNGs.

Launcher (python cpu_unit_fixture.py <entry argv>): the operator's prefix seam,
as vnice is on the GPU path. It installs three boundary doubles in the worker
process, then runs the numeric entry (action 3 -> g.w.run):
  - parity.load_native returns a tiny native Qwen3.5 hybrid CarrierC1 (linear-
    and full-attention layers, pose/gravity heads, private depth head with its
    ViT copy; bf16 LM as the production loader) instead of the 21.6 GB export;
  - evalpath.runtime.prompt_batch returns that model's token/pixel batch;
  - FrozenG3TTower._load binds real tiny G3T components (aggregator, both
    camera heads, depth and point DPT heads) at 28 px instead of 5.6 GB weights.
Everything else (worker, monitor, receipts, admission, tower run on 64 or 32
real frames, prefill, heads, geometry, scale, record encoding) is production.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent


def sha(path):
    with open(path, 'rb') as f:return hashlib.file_digest(f, 'sha256').hexdigest()


def build(logical, p, archive, env_roots=''):
    """Create logical/d exactly as preparation would, with tiny artifact files."""
    p, archive = Path(p), Path(archive)
    sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
    import l
    l.install(p)
    from orchard_h10.common import write, sha as stored_sha
    from parity_kit.build_manifest import build as manifest_build
    logical = Path(logical); d = logical/'d'; export = d/'e'; g = d/'g'
    for path, raw in [(export/'full_weights/0.bin', b'0'), (export/'full_weights/0.json', b'{}'),
                      (export/'heads.pt', b'0'), (export/'artifact.json', b'{}'),
                      (export/'base/1.json', b'{}'), (g/'model.safetensors', b'0'), (g/'config.json', b'{}'),
                      (d/'0.json', b'{}')]:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    (export/'full_weights/full_weights.json').write_text(json.dumps(dict(files=[dict(name='0.bin')], index=dict(name='0.json'))))
    (export/'model.json').write_text(json.dumps(dict(files=['1.json'])))
    # Exactly preparation's code roots (orchard_h10/prepare.py).
    code = dict(reader=p/'b'/'e2e_reader', heads=p/'b'/'heads', tree=p/'tree', evaluator=p/'h1eval', runner=p/'b'/'parity_kit')
    manifest = manifest_build(logical, export, g, code_roots=code)
    write(d/'manifest.json', manifest)
    write(d/'binding.json', dict(root=str(logical), name='d/manifest.json', sha256=stored_sha(d/'manifest.json'),
                                 code_roots={k: str(v) for k, v in code.items()}))
    captures = json.loads(l.install(p).Path(p/'g/2.json').read_text())
    wanted = {m['path'] for c in captures['captures'].values() for m in c}
    index = {}
    with tarfile.open(archive) as tar:
        for member in tar:
            if member.name in wanted:index[member.name] = dict(archive=str(archive), offset=member.offset_data, bytes=member.size)
    write(d/'9.json', dict(index=index, **captures))
    settings = dict(export_dir=str(export), artifact_manifest=str(d/'binding.json'), tree=str(p/'tree'),
                    config=str(d/'0.json'), frames_root=str(d/'f'), capture_index=str(d/'9.json'),
                    env_roots=[r for r in env_roots.split(':') if r],
                    arm='own_depth', stage1_select_rule='null_argmax', save_own_depth=False, perception_memo='off',
                    perception_memo_modules=['g3t'], perception_memo_verify_ids=[])
    write(d/'settings.json', settings)
    return d


class Tokenizer:
    def encode(self, text, **kwargs):
        return [5]

    def convert_tokens_to_ids(self, token):
        return 5 if token == '<|fim_middle|>' else 61


class FakeTokenizer:
    words = {40: '<depth_at', 41: ' frame=2 pts=[[500,500],[300,700]]>', 42: ' Next', 43: '<tool_response>',
             44: '</tool_response>', 45: '<move', 46: ' from=2 to=9>', 47: '<turn', 48: ' from=4 to=30>',
             49: ' <dist P1 P2>'}
    eos_token_id = 1

    def convert_tokens_to_ids(self, token):
        return {v: k for k, v in self.words.items()}.get(token, 0)

    def encode(self, text, add_special_tokens=False):
        return [50 + ord(c) % 10 for c in text]

    def decode(self, ids, skip_special_tokens=False):
        return ''.join(self.words.get(i, '?') for i in ids)


def tiny_carrier():
    """The tree's final-mode C1 fixture architecture; LM in bf16 as production loads it."""
    import torch
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    from student_pilot.carrier_c1 import CarrierC1, RECIPE
    from student_pilot.carrier_c1_data import insert_frame_carriers
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
    base = Qwen3_5ForConditionalGeneration(config).to(torch.bfloat16)  # production from_pretrained dtype
    camera = dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
                  weight_gravity=.05, weight_scale=.02, supervision={'path': '/fixture', 'sha256': 'a'*64})
    depth = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3])
    placement = 'append_after_temporal_group_video_tokens_v1'
    model = CarrierC1(base, camera, depth, 5, placement, 'final', True, RECIPE, depth_fov_source='pose_head')
    # carrier_c1_run.load_artifact: base parameters bf16, attached heads as built (fp32).
    from student_pilot import full_ft
    for _, parameter in full_ft.base_parameters(model):
        parameter.data = parameter.data.to(torch.bfloat16)
    groups = 16
    ids = torch.tensor([[2]+[v for _ in range(groups) for v in (62, 61, 63)]+[10, 11]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), mm_token_type_ids=torch.where(ids == 61, 2, 0),
                 video_grid_thw=torch.tensor([[groups, 2, 2]]), pixel_values_videos=torch.randn(groups*4, 24))
    batch = insert_frame_carriers(batch, Tokenizer(), carrier_placement=placement)
    return model, batch


def tiny_g3t():
    """Real G3T components at 28 px (tree test_tower_read fixture)."""
    import torch
    from student_pilot import tower_read as T
    from student_pilot.c1r_ref import source_import
    source_import(T.Path(T.__file__).parent/'g3t_vendor')
    from vggt.models.aggregator import Aggregator
    from vggt.heads.camera_head import CameraHead
    from vggt.heads.dpt_head import DPTHead
    torch.manual_seed(13)
    model = torch.nn.Module()
    model.aggregator = Aggregator(img_size=28, embed_dim=8, depth=24, num_heads=2, mlp_ratio=1, patch_embed='conv')
    for name, encoding, bias in (('local_camera_head', 'noT_quaR_FoV', [0, 0, 0, 1, .3, .3]),
                                 ('global_camera_head', 'absT_quaRy_noFoV', [0, 0, 0, 0, 1])):
        head = CameraHead(dim_in=16, trunk_depth=1, num_heads=2, pose_encoding_type=encoding)
        with torch.no_grad():
            head.pose_branch.fc2.weight.mul_(.001)
            head.pose_branch.fc2.bias.copy_(torch.tensor(bias))
        setattr(model, name, head)
    model.depth_head = DPTHead(dim_in=16, features=8, out_channels=[8]*4, output_dim=2, activation='exp')
    model.point_head = DPTHead(dim_in=16, features=8, out_channels=[8]*4, output_dim=4, activation='inv_log')
    return model.float().eval().requires_grad_(False)


def install():
    import torch
    from types import SimpleNamespace
    from unittest import mock
    from e2e_reader import parity
    from evalpath import runtime
    from student_pilot import tower_read as T
    from student_pilot.c1r_ref import source_import
    source_import(T.Path(T.__file__).parent/'g3t_vendor')
    import vggt.utils.load_fn as load_fn
    model, batch = tiny_carrier()
    processor = SimpleNamespace(tokenizer=FakeTokenizer(), _routing_tokens=dict(
        ids={'<depth_at': 40, '<move': 45, '<pose': 39, '<turn': 47, '<box_3d': 38}))

    def load_native(export_dir, *, device='cpu', settings, artifact=None):
        model.to(device).eval().requires_grad_(False)
        return model, processor, dict(config=dict(), receipt=dict(), restore=dict(),
                                      export=dict(step=544, frame_layout='spread'))

    def prompt_batch(p, row, cfg, kind):
        value = {k: v.clone() if hasattr(v, 'clone') else v for k, v in batch.items()}
        inputs = row.get('student_input') or {}
        value.setdefault('frame_indices', inputs.get('frame_indices'))
        value.setdefault('video_sha256', '0'*64)
        return value
    tiny = tiny_g3t()

    def bind(self):
        self.module = tiny.to(self.device)
    preprocess = load_fn.load_and_preprocess_images_square

    def small(images, size):
        value, coords = preprocess(images, 28)
        coords[:, :4] *= 1024/28
        return value, coords
    resize = T.F.interpolate

    def interpolate(*args, **kwargs):
        if kwargs.get('size') == (518, 518):kwargs['size'] = (28, 28)
        return resize(*args, **kwargs)
    for patcher in (mock.patch.object(parity, 'load_native', side_effect=load_native),
                    mock.patch.object(runtime, 'prompt_batch', side_effect=prompt_batch),
                    mock.patch.object(T.FrozenG3TTower, '_load', bind),
                    mock.patch.object(load_fn, 'load_and_preprocess_images_square', side_effect=small),
                    mock.patch.object(T.F, 'interpolate', side_effect=interpolate)):
        patcher.start()
    if os.environ.get('A_UNIT_FIXTURE_SLEEP'):
        # Deadline and memory scenarios: hold the worker inside its first stage.
        import time
        from g import w
        original = w.start_tower
        def slow(*args, **kwargs):
            if os.environ.get('A_UNIT_FIXTURE_ALLOCATE'):
                hold = bytearray(int(os.environ['A_UNIT_FIXTURE_ALLOCATE']))  # noqa: F841
            time.sleep(float(os.environ['A_UNIT_FIXTURE_SLEEP']))
            return original(*args, **kwargs)
        w.start_tower = slow


if __name__ == '__main__' and sys.argv[1] == 'build':
    build(*sys.argv[2:])
elif __name__ == '__main__':
    # argv: <python> -B -I 5.py 30.json (the production worker command)
    entry, config = sys.argv[-2:]
    cfg = json.loads(Path(config).read_text()) if not Path(config).read_text().startswith('{"a0"') else None
    if cfg is None:
        raw = json.loads(Path(config).read_text())['a0']; cfg = json.loads(bytes.fromhex(raw))
    p = Path(cfg['package'])
    sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
    import l
    l.install(p)
    install()
    sys.argv = [entry, config]
    import runpy
    runpy.run_path(entry, run_name='__main__')
