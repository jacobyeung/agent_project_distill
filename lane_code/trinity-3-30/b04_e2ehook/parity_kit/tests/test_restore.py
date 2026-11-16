import copy
from pathlib import Path

import pytest
import torch

from parity_kit import stage_restore as S
from parity_kit.common import PREP, pin, read, sha, write


@pytest.fixture
def staged_inputs(tmp_path):
    from transformers import Qwen3_5Config
    source, heads, meta = [tmp_path / n for n in ('source', 'heads', 'meta')]
    source.mkdir(); heads.mkdir(); meta.mkdir()
    cfg = Qwen3_5Config(text_config=dict(vocab_size=16, hidden_size=32, intermediate_size=64,
                            num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
                            head_dim=16, linear_key_head_dim=16, linear_value_head_dim=16,
                            linear_num_key_heads=1, linear_num_value_heads=2),
                       vision_config=dict(depth=3, hidden_size=32, intermediate_size=64, num_heads=2,
                                          out_hidden_size=32, num_position_embeddings=16))
    write(source / 'config.json', cfg.to_dict())
    for n in ('tokenizer.json', 'tokenizer_config.json', 'preprocessor_config.json'):
        write(source / n, {})
    depth = dict(d_proj=16, mlp_hidden=16, num_heads=2, context_depth=1, vit_layers=[1, 2, 3])
    receipt = dict(schema='c1-preparation-v1', depth=depth, model=dict(path='/AWS/base', sha256='old'),
                   depth_init=dict(path='/AWS/depth', sha256='old'), frame_layout='duplicate', config_sha256='identity')
    expected = S.depth_shapes(source / 'config.json', receipt)
    torch.save({k: torch.zeros(shape) for k, shape in expected.items()}, heads / 'heads.pt')
    shard = source / 'model-00001-of-00001.safetensors'
    shard.write_bytes(b'fake-shard')
    write(source / 'model.safetensors.index.json', dict(weight_map={'x': shard.name}))
    full = dict(schema='full-ft-export-v1', dtype='bfloat16', tensor_count=1,
                files=[dict(name=shard.name, sha256=sha(shard), bytes=shard.stat().st_size)],
                index=dict(name='model.safetensors.index.json', sha256=sha(source/'model.safetensors.index.json')))
    write(heads / 'full_weights/full_weights.json', full)
    artifact = dict(frame_layout='duplicate', config_sha256='identity', base_identity='base',
                    heads=dict(path='/AWS/heads', sha256=sha(heads/'heads.pt')),
                    full_weights=dict(path='/AWS/full', sha256=sha(heads/'full_weights/full_weights.json')))
    write(heads / 'artifact.json', artifact)
    write(meta / PREP / 'prepared/s1_receipt.json', receipt)
    cfg = dict(base_identity='base', frame_layout='duplicate',
               preparation=pin(meta/PREP/'prepared/s1_receipt.json'))
    write(meta/PREP/'config.json', cfg)
    data = dict(schema='s1-in-job-data-v1', status='PREPARED', real_frames_verified=True,
                rehearsal=False, config=pin(meta/PREP/'config.json'), preparation=cfg['preparation'])
    data_path = meta/'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json'
    write(data_path, data)
    req = dict(config=pin(meta/PREP/'config.json'), data_receipt=pin(data_path), artifact=pin(heads/'artifact.json'))
    request = tmp_path / 'request.json'; write(request, req)
    return source, heads, meta, request, expected


def test_restore_paths_and_depth_proof(staged_inputs, tmp_path):
    source, heads, meta, request, expected = staged_inputs
    out = tmp_path/'out'
    report = S.stage(source, heads, meta, out, request=request)
    original, new = read(heads/'artifact.json'), read(out/'artifact.json')
    assert sha(heads/'artifact.json') != sha(out/'artifact.json')
    for k in ('full_weights', 'heads'):
        assert new[k]['sha256'] == original[k]['sha256']
        original[k]['path'] = new[k]['path']
    assert original == new
    assert 'depth_init' not in read(out/'receipt.json')
    assert set(report['depth_overwrite']['depth_keys']) == set(expected)
    assert (out/'full_weights/model-00001-of-00001.safetensors').is_symlink()
    assert (out/'base/model.safetensors.index.json').is_symlink()
    assert read(out/'model.json')['schema'] == 'p3-model-input-v1'


@pytest.mark.parametrize('name', ['model-00001-of-00001.safetensors', 'model.safetensors.index.json'])
def test_restore_refuses_corruption(staged_inputs, tmp_path, name):
    source, heads, meta, request, _ = staged_inputs
    (source/name).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='sha256 mismatch'):
        S.stage(source, heads, meta, tmp_path/'out', request=request)
    assert not (tmp_path/'out').exists()


def test_depth_proof_rejects_missing_key(staged_inputs, tmp_path):
    source, heads, meta, request, _ = staged_inputs
    state = torch.load(heads/'heads.pt', weights_only=True)
    state.pop(next(iter(state)))
    torch.save(state, tmp_path/'incomplete.pt')
    with pytest.raises(ValueError, match='depth overwrite unproven'):
        S.prove_depth(tmp_path/'incomplete.pt', source/'config.json', read(meta/PREP/'prepared/s1_receipt.json'))


def test_manifest_resolves_links_and_refuses_escape(staged_inputs, tmp_path):
    from parity_kit.build_manifest import build
    from e2e_reader.artifact import Artifact
    source, heads, meta, request, _ = staged_inputs
    out = tmp_path/'out'
    S.stage(source, heads, meta, out, request=request)
    g3t = tmp_path/'tower'; g3t.mkdir()
    (g3t/'model.safetensors').write_bytes(b'fixture')
    write(g3t/'config.json', {})
    code = tmp_path/'code'; code.mkdir(); (code/'x.py').write_text('x=1\n')
    manifest = build(tmp_path, out, g3t, code_roots=dict(reader=code))
    write(tmp_path/'manifest.json', manifest)
    artifact = Artifact(tmp_path, 'manifest.json', sha(tmp_path/'manifest.json'),
                        code_roots=dict(reader=code), required_roles=('checkpoint', 'tokenizer', 'g3t')).verify()
    assert source/'model-00001-of-00001.safetensors' in artifact.files('checkpoint')
    assert all(not Path(f['rel']).is_absolute() for c in manifest['components'].values() for f in c['files'])
    # The restore alone cannot serve as root: its shard links leave that root.
    with pytest.raises(ValueError):
        build(out, out, g3t, code_roots=dict(reader=code))
