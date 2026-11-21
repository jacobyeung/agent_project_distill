"""Tiny authenticated export for the delivered CPU real-batch path.

The production runtime, restore, loader, artifact binder, prompt adapter,
prefill, cache merge, batched decode, row selection, first-call stop and
serial agreement check all run. Only external boundaries are doubled: the
checkpoint is a tiny native Qwen3.5 hybrid (linear- and full-attention
layers), processor assets use a tiny tokenizer, and RGB decoding returns
zeros. Prompt lengths vary with the question so rows stop at different steps.
"""
import contextlib
import hashlib
import sys
import types
from unittest.mock import patch

PLACEMENT = 'append_after_temporal_group_video_tokens_v1'
OPENER = 36  # decodes to a call opener, so rows also stop at the first opening


@contextlib.contextmanager
def tiny_export(t, p, cfg, dtype='float32'):
    """Populate package `p` with a tiny export; yield while boundary doubles are active."""
    import numpy as np
    import torch
    ROOT, B, C, FILES = t.ROOT, t.B, t.C, t.FILES
    tests = types.ModuleType('tests'); tests.__path__ = [str(ROOT/'in/D400/src/tree/tests')]
    sys.modules['tests'] = tests
    from tests.test_carrier_c1_final import final_fixture, FakeTokenizer
    from student_pilot import carrier_c1_run as trainer, pose_samples
    from parity_kit import stage_restore
    from e2e_reader import parity
    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
    tiny, _, _ = final_fixture()
    recipe = getattr(trainer, 'RECIPE', None) or __import__('student_pilot.carrier_c1', fromlist=['RECIPE']).RECIPE
    model_receipt = dict(camera=dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
        weight_gravity=.05, weight_scale=.02, supervision={'path': '/fixture', 'sha256': 'a'*64}),
        depth=dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3]),
        carrier_placement=PLACEMENT, training_mode='final', depth_enabled=True, recipe=recipe,
        depth_fov_source='pose_head', trace_program_version='3.14')
    d = p/'d'; d.mkdir(); cfg['logical'] = str(p)
    cfg['inputs']['frames_root'] = str(d/'f'); (d/'f').mkdir()
    (d/'f/0').write_bytes(b'0')
    data = C.loads(FILES['1.json'])
    for cap in data['captures'].values():
        for f in cap['frames']: f.update(path='0', sha256=hashlib.sha256(b'0').hexdigest())
    C.store(p/'1.json', data); C.store(p/'2.json', cfg)
    base = d/'b'; base.mkdir(); weights = d/'m400/full_weights'; weights.mkdir(parents=True)
    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = B.jd(value); path.write_bytes(C.pack(raw)); return dict(bytes=len(raw), sha256=B.digest(raw))
    assets = {}
    for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json', 'preprocessor_config.json'):
        raw = B.jd(tiny.config.to_dict()) if name == 'config.json' else b'{}'
        (base/name).write_bytes(raw); assets[name] = B.digest(raw)
    original = B.jd(dict(schema='p3-model-input-v1', base_identity='a', files=assets))
    archive = d/'o/0.tgz'; archive.parent.mkdir(); archive.write_bytes(B.archive({'model.json': original}))
    from safetensors.torch import save_file
    from student_pilot import full_ft
    state = {k: v.detach().to(torch.bfloat16).clone().contiguous() for k, v in full_ft.base_parameters(tiny)}
    save_file(state, str(weights/'0.bin'))
    ix = put(weights/'0.json', dict(weight_map={k: '0.bin' for k in state}))
    full = dict(schema='full-ft-export-v1', dtype='bfloat16', files=[dict(name='0.bin', **B.pin((weights/'0.bin').read_bytes()))],
                index=dict(name='0.json', **ix), tensor_count=len(state))
    fp = put(weights/'full_weights.json', full)
    torch.save(tiny.auxiliary_heads.state_dict(), d/'m400/heads.pt')
    artifact_value = dict(config_sha256='a'*64, base_identity='a', frame_layout='duplicate',
                          full_weights=dict(sha256=fp['sha256']), heads=dict(sha256=B.digest((d/'m400/heads.pt').read_bytes())))
    ap = put(d/'m400/artifact.json', artifact_value)
    receipt = dict(config_sha256='a'*64, frame_layout='duplicate', **model_receipt,
                   model=dict(path='/a', sha256=B.digest(original)))
    rp = put(d/'p0/receipt.json', receipt)
    config = dict(base_identity='a', frame_layout='duplicate', carrier_placement=PLACEMENT, training_mode='final',
                  preparation=dict(path='/a', sha256=rp['sha256']))
    cp = put(d/'p0/config.json', config)
    data_receipt = dict(status='PREPARED', schema='s1-in-job-data-v1', config=dict(path='/b', sha256=cp['sha256']),
                        preparation=config['preparation'], real_frames_verified=True, rehearsal=False)
    dp = put(d/'p0/data_receipt.json', data_receipt)
    pins = dict(artifact=ap, preparation={name: dict(path='p0/'+filename, source_path=source, **pin) for name, filename, source, pin in
        [('config', 'config.json', '/b', cp), ('receipt', 'receipt.json', '/a', rp), ('data_receipt', 'data_receipt.json', '/c', dp)]})
    for name, path in [('full_weights', weights/'full_weights.json'), ('artifact', d/'m400/artifact.json'),
                       ('base_config', base/'config.json'), ('original_model', archive)]:
        cfg['inputs']['files'][name]['path'] = str(path)
    C.store(p/'2.json', cfg)
    real_stage = stage_restore.stage
    def preparation(*args, **kw):
        kw['export_pins'] = pins
        return real_stage(*args, **kw)
    class Tokenizer(FakeTokenizer):
        pad_token_id = 0
        def __init__(self): self.vocab = {'<|fim_middle|>': 5, '<|video_pad|>': 61, '<|vision_start|>': 62, '<|vision_end|>': 63}
        def encode(self, text, **kw):
            return [self.vocab[text]] if text in self.vocab else super().encode(text, **kw)
        def get_vocab(self): return self.vocab
        def add_tokens(self, tokens):
            for token in tokens: self.vocab[str(token)] = 32+len(self.vocab)
        def convert_tokens_to_ids(self, token):
            return self.vocab.get(token, super().convert_tokens_to_ids(token))
        def decode(self, ids, skip_special_tokens=False):
            return ''.join('<pose' if i == OPENER else 'x'+str(i)+' ' for i in ids)
    def processor(*a, **kw):
        from transformers import Qwen3VLProcessor, Qwen3VLVideoProcessor, Qwen2VLImageProcessor, Qwen2Tokenizer
        native = Qwen3VLProcessor(tokenizer=Qwen2Tokenizer(), image_processor=Qwen2VLImageProcessor(),
                                  video_processor=Qwen3VLVideoProcessor())
        native.tokenizer = Tokenizer()
        return native
    def encode_frames(processor, question, *a, **kw):
        extra = [10+(len(question)+j) % 20 for j in range(len(question) % 7)]
        ids = torch.tensor([[2]+[v for _ in range(32) for v in (62, 61, 63)]+[10, 11, 12, 13]+extra])
        result = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                      mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[32, 2, 2]]),
                      pixel_values_videos=torch.zeros((128, 24)))
        result['labels'][0, -2:] = ids[0, -2:]
        return result, {}
    native_dir = p/'tiny_native'; native_dir.mkdir()
    Qwen3_5ForConditionalGeneration(tiny.config).float().save_pretrained(native_dir)
    real_pretrained = Qwen3_5ForConditionalGeneration.from_pretrained
    real_artifact, real_read = trainer.load_artifact, trainer.load
    def pretrained(*a, **kw):
        kw['dtype'] = torch.float32
        return real_pretrained(native_dir, **kw)
    def bind_artifact(model, artifact_pin):
        from student_pilot import trained_groups
        heads = tiny.auxiliary_heads.state_dict()
        groups = {name: dict(names=sorted(values), initial_sha256='0'*64,
            final_sha256=trained_groups.fingerprint({k: heads[k] for k in values})[0],
            changed=True, gradient_steps=1) for name, values in trained_groups.parameters(model).items()}
        def metadata(path):
            value = real_read(path)
            if str(path) == artifact_pin['path']:
                value.update(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm',
                    placement=model.carrier_placement, training_mode=model.training_mode,
                    frame_layout=model.frame_layout, depth_backing='tiny',
                    config_sha256=trainer.identity(config), trace_program_version='3.14', step=400,
                    trained_groups=dict(schema=trained_groups.SCHEMA, step=400, groups=groups))
            return value
        with patch.object(trainer, 'load', side_effect=metadata):
            value = real_artifact(model, artifact_pin)
        # float32 for exact serial/batched comparison; bfloat16 checks CPU kernel coverage as in production.
        model.to(getattr(torch, dtype))
        return value
    with patch.object(stage_restore, 'stage', side_effect=preparation), \
         patch.object(AutoProcessor, 'from_pretrained', side_effect=processor), \
         patch.object(Qwen3_5ForConditionalGeneration, 'from_pretrained', side_effect=pretrained), \
         patch.object(trainer, 'load_artifact', side_effect=bind_artifact), \
         patch.object(pose_samples, 'load_frames', return_value=np.zeros((32, 4, 4, 3), dtype=np.uint8)), \
         patch.object(pose_samples, 'encode_frames', side_effect=encode_frames):
        yield dict(parity=parity, stage_restore=stage_restore)


def torchvision_fixture(ROOT):
    """Local p1cpu lacks torchvision; the pinned environment ships it."""
    try:
        import torchvision  # noqa: F401
        return False
    except ImportError:
        pass
    import importlib.util
    spec = importlib.util.spec_from_file_location('native_fixture', ROOT/'tests/native_fixture.py')
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    sys.path.insert(0, str(value.prepare(ROOT)))
    import torch
    library = torch.library.Library('torchvision', 'DEF')
    library.define('nms(Tensor dets, Tensor scores, float iou_threshold) -> Tensor')
    torchvision_fixture.library = library
    return True
