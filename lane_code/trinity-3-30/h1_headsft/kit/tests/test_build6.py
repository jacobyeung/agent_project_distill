"""Native fixture-batch proof with a tiny pixel processor and real native model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest
import torch

from first_batch import real_fixture_batch as B
from tests.fixtures import CharacterTokenizer, Processor, tiny


class PixelTokenizer(CharacterTokenizer):
    def convert_tokens_to_ids(self, token):
        return {'<|fim_middle|>': 5, '<|video_pad|>': 61,
                '<|vision_start|>': 62, '<|vision_end|>': 63}[token]

    def encode(self, text, **kw):
        if text in ('<|fim_middle|>', '<|video_pad|>'):
            return [self.convert_tokens_to_ids(text)]
        return super().encode(text, **kw)


class PixelProcessor(Processor):
    """Extend the fixture processor with pixels; never reuse tiny()'s batch."""
    video_token_id = 61
    video_processor = SimpleNamespace(merge_size=2, temporal_patch_size=2)

    def __init__(self):
        self.tokenizer = PixelTokenizer()
        self.tokenizer._c1_frame_markers = True
        self.calls = 0

    def __call__(self, *, text, videos, video_metadata, **kw):
        self.calls += 1
        arrays = videos[0]
        assert arrays.shape[1:] == (4, 4, 3)
        metadata = video_metadata[0]
        groups = len(arrays)//2
        ids = []
        pixels = []
        for g in range(groups):
            timestamp = sum(metadata.frames_indices[2*g:2*g+2])/2/metadata.fps
            ids += self.tokenizer.encode(f'<{timestamp:.1f} seconds>') + [62, 61, 63]
            # Native 2x2 spatial and 2-frame temporal patches, merge size 2.
            pair = arrays[2*g:2*g+2].astype(np.float32)/255
            for y, x in ((0, 0), (0, 2), (2, 0), (2, 2)):
                pixels.append(pair[:, y:y+2, x:x+2].transpose(3, 0, 1, 2).reshape(-1))
        ids += self.tokenizer.encode(text[0])
        ids = torch.tensor([ids])
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids),
                    mm_token_type_ids=torch.where(ids == 61, 2, 0),
                    pixel_values_videos=torch.tensor(np.stack(pixels)),
                    video_grid_thw=torch.tensor([[groups, 2, 2]]), video_metadata=video_metadata)


def arguments(tmp_path, force=False):
    cfg = json.loads((B.K/'configs/h1_1.json').read_text())
    artifact = tmp_path/'artifact.json'
    artifact.write_text(json.dumps(dict(step=544)))
    cfg['init_artifact']['artifact']['sha256'] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (tmp_path/'config.json').write_text(json.dumps(cfg))
    (tmp_path/'model.json').write_text(json.dumps(dict(schema='p3-model-input-v1', root=str(tmp_path), files={})))
    (tmp_path/'receipt.json').write_text('{}')
    frames = []
    for i in range(32):
        path = tmp_path/f'f{i}.png'
        Image.fromarray(np.full((4, 4, 3), i*7, dtype=np.uint8)).save(path)
        frames.append(dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_index=10+i*3))
    (tmp_path/'clip.json').write_text(json.dumps(dict(frames=frames, fps=30., total_num_frames=110)))
    args = B.parser().parse_args([
        '--config', str(tmp_path/'config.json'), '--model-manifest', str(tmp_path/'model.json'),
        '--receipt', str(tmp_path/'receipt.json'), '--artifact', str(artifact),
        '--frames', str(tmp_path/'clip.json'), '--frames-root', str(tmp_path),
        '--threads', '2', '--output', str(tmp_path/'out'),
    ] + (['--force-pose-own'] if force else []))
    return args


def tiny_loader(manifest, receipt, pin):
    model, _, _ = tiny()
    model.frame_layout = 'duplicate'
    model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    return model, PixelProcessor()


@pytest.mark.parametrize('force', [False, True])
def test_native_end_to_end(tmp_path, monkeypatch, force):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    args = arguments(tmp_path, force)
    loaded = []
    before = []
    trained_text = []
    def loader(*values):
        model, processor = tiny_loader(*values)
        loaded.append((model, processor))
        before.append({k: v.detach().clone() for k, v in model.named_parameters()})
        def capture(module, inputs, kwargs, output):
            if kwargs.get('stream') == 'routing':
                trained_text.append(processor.tokenizer.decode(inputs[0]['input_ids'][0].tolist()))
        model.register_forward_hook(capture, with_kwargs=True)
        return model, processor
    summary = B.run(args, loader=loader)
    assert summary['pass'], summary['errors'] or summary['ranks']
    records = [json.loads(s) for s in (Path(args.output)/'real_fixture_batch.jsonl').read_text().splitlines()]
    assert len(records) == 12
    assert summary == json.loads((Path(args.output)/'SUMMARY.json').read_text())
    model, processor = loaded[0]
    assert processor.calls == 12
    assert all(torch.equal(p, before[0][name]) for name, p in model.named_parameters())
    for r, text in zip((r for r in records if r['stream'] == 'routing'), trained_text):
        if r['h1']['values'] == 'own':
            assert text.endswith('\n</think>\n\n'+str(r['h1']['answer'])+processor.tokenizer.eos_token)
    assert summary['fixtures']['camera'] == 12
    assert summary['fixtures']['ground'] + len(summary['fixtures']['ground_skipped']) == 2
    from student_pilot import carrier_c1_routing as routing
    gates = routing.Gates(model.recipe['scheduled_sampling'], False)
    factor = model.recipe.get('reference_world_size', 4)//4
    for rank in range(4):
        own = 0
        for r in [r for r in records if r['rank'] == rank]:
            assert r['finite_loss'] and r['finite_gradients'] and r['gradient_tensors'] > 0
            assert all(v >= 0 for v in r['seconds'].values())
            assert r['peak_rss_kib'] > 0 and r['components']
            assert set(('values', 'refused', 'answer_differs', 'type')) <= r['h1'].keys()
            if r['stream'] == 'routing':
                expected = gates.decide(2, r['microstep']//factor)
                assert r['decision'] == list((expected[0], True) if force else expected)
                assert r['trained_tokens'] > 0
                assert r['fixture_index'] == r['planned_index'] % summary['plan_counts']['routing']
                own += r['h1']['values'] == 'own'
            else:
                assert r['decision'] is None and r['trained_tokens'] == 0
        assert summary['ranks'][str(rank)]['own'] == own
        if force:
            assert own > 0


def test_all_rows_use_native_get(tmp_path):
    args = arguments(tmp_path)
    cfg, manifest, receipt, pin = B.read_inputs(args)
    model, processor = tiny_loader(manifest, receipt, pin)
    rows, metadata = B.fixture_rows(cfg, processor, args.frames, args.frames_root)
    from student_pilot import carrier_c1_run as R
    assert type(rows).get is R.Rows.get
    for i in range(rows.count('routing')):
        batch, targets, audit = rows.get('routing', i)
        R.check_row(batch, targets, 'routing', model)
        assert (batch['aux_camera_positions'] >= 0).all()
        assert audit['h1_pose']['supervised'] == (i < 12)
    assert processor.calls == rows.count('routing')
    assert metadata['ground_skipped']
    assert all(r['reason'] == 'Absolute label mismatch' for r in metadata['ground_skipped'])
    rows.close()


def test_nonfinite_gradient_fails(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    args = arguments(tmp_path)
    args.ranks = '0'
    def loader(*values):
        model, processor = tiny_loader(*values)
        model.lm_head.weight.register_hook(lambda grad: grad*float('nan'))
        return model, processor
    summary = B.run(args, loader=loader)
    assert not summary['pass'] and summary['non_finite']


def test_artifact_pin_and_missing_asset(tmp_path):
    args = arguments(tmp_path)
    cfg, manifest, receipt, pin = B.read_inputs(args)
    manifest['files'] = {'absent.safetensors': '0'*64}
    with pytest.raises(FileNotFoundError, match='Missing node-local.*absent.safetensors'):
        B.real_loader(manifest, receipt, pin)
    Path(args.artifact).write_text('{"step": 543}')
    with pytest.raises(ValueError, match='artifact digest'):
        B.read_inputs(args)


def test_real_json_loading_until_missing_weights(tmp_path):
    root = Path(os.environ.get('B6_REAL_JSON_DIR', '/dev/shm/jjyeung/h1tmp/from118'))
    needed = [root/n for n in ('model.json', 'receipt.json', 'artifact.json', 'RESTORE.json')]
    absent = [str(p) for p in needed if not p.is_file()]
    if absent:
        pytest.skip('Real loading proof unavailable; missing staged JSON: '+', '.join(absent))
    assert isinstance(json.loads(needed[-1].read_text()), dict)
    base = ['--model-manifest', str(needed[0]), '--receipt', str(needed[1]),
            '--artifact', str(needed[2]), '--frames', str(tmp_path/'unused.json'), '--output', str(tmp_path/'real')]
    restore = json.loads(needed[-1].read_text())
    original = Path(restore['original']['artifact']['path'])
    with B.local_io(tmp_path):
        # The restored artifact carries local paths, so its file digest differs from the D0 pin.
        with pytest.raises(ValueError, match='differs from the D0 initialization pin'):
            B.read_inputs(B.parser().parse_args(base))
        args = B.parser().parse_args(base+['--restore', str(needed[-1])])
        if not original.is_file():
            with pytest.raises(FileNotFoundError):
                B.read_inputs(args)
            return
        cfg, manifest, receipt, pin = B.read_inputs(args)
        assert restore['original']['artifact']['sha256'].startswith('1d6eeb28')
        with pytest.raises(FileNotFoundError, match='Missing node-local model/processor/artifact file'):
            B.real_loader(manifest, receipt, pin)


def test_io_guard(tmp_path):
    link = tmp_path/'forbidden'
    link.symlink_to('/data3/nonexistent-frame')
    with B.local_io(tmp_path):
        for path in ('/home/no-file', '/data/no-file', '/data9/no-file', '/lustre/no-file', link):
            with pytest.raises(PermissionError, match='node-local'):
                open(path)
        with pytest.raises(PermissionError, match='under --output'):
            (B.K/'must-not-write.txt').open('w')


def test_wrapper_portable():
    source = (B.K/'first_batch/real_fixture_batch.sh').read_text()
    assert str(B.K) not in source and 'ulimit' not in source
    assert 'PY_OVERLAY' in source and 'CUDA_VISIBLE_DEVICES' in source


def test_wrapper_failure_exit_and_summary(tmp_path):
    args = arguments(tmp_path)
    Path(args.model_manifest).write_text(json.dumps(dict(schema='p3-model-input-v1',
        root=str(tmp_path/'absent-model'), files={'config.json': '0'*64})))
    result = subprocess.run(['bash', str(B.K/'first_batch/real_fixture_batch.sh'),
                             '--config', args.config, '--model-manifest', args.model_manifest,
                             '--receipt', args.receipt, '--artifact', args.artifact,
                             '--frames', args.frames, '--output', args.output, '--threads', '2'],
                            env={**os.environ, 'PY': sys.executable, 'PY_OVERLAY': str(B.K/'tree')},
                            text=True, capture_output=True)
    assert result.returncode == 1, result.stderr
    summary = json.loads((Path(args.output)/'SUMMARY.json').read_text())
    assert not summary['pass'] and 'Missing node-local' in summary['errors'][0]
    assert (Path(args.output)/'tmp').is_dir()


def test_native_loader_wiring(tmp_path, monkeypatch):
    from student_pilot import carrier_c1_run as R
    (tmp_path/'asset.json').write_text('{}')
    manifest = dict(root=str(tmp_path), files={'asset.json': 'unused by opening probe'})
    receipt = dict(init_artifact='unused warm start', depth_init='unused depth init', recipe={})
    pin = dict(path='explicit-step544', sha256='pinned')
    processor, model = object(), object()
    calls = []
    def proc(m, r):
        assert m == manifest and r == receipt
        calls.append('processor')
        return processor
    def load(m, r, p, evaluation):
        assert m == manifest and r == {'recipe': {}} and p is processor and evaluation
        calls.append('model')
        return model
    def artifact(m, p):
        assert m is model and p == pin
        calls.append('artifact')
    monkeypatch.setattr(R, 'processor_for_receipt', proc)
    monkeypatch.setattr(R, 'load_model', load)
    monkeypatch.setattr(R, 'load_artifact', artifact)
    assert B.real_loader(manifest, receipt, pin) == (model, processor)
    assert calls == ['processor', 'model', 'artifact']
