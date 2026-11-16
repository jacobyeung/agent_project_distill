"""Portable safetensors head export with strict configuration and provenance checks."""
from dataclasses import asdict
from pathlib import Path

from safetensors.torch import save, load_file

from .common import atomic_write_bytes, atomic_write_json, read_json, sha256_file
from .head import Config, GroundingHead

REQUIRED_HASHES = {'config', 'labels', 'vit', 'name_rows', 'tokenizer', 'gate'}


def save_head(directory, model, hashes, extra=None):
    if not REQUIRED_HASHES <= hashes.keys() or any(not isinstance(hashes[k], str) or not hashes[k] for k in REQUIRED_HASHES):
        raise ValueError('Missing export provenance hashes')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'head.safetensors'
    state = {k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}
    atomic_write_bytes(path, save(state))
    atomic_write_json(directory/'meta.json', dict(schema='owngrd-head-v1', config=asdict(model.cfg),
        head_config_sha256=model.cfg.sha256, hashes=hashes, weights_sha256=sha256_file(path),
        parameter_counts=model.parameter_counts(), extra=extra or {}))


def load_head(directory, expected_hashes=None, device='cpu'):
    directory = Path(directory)
    meta = read_json(directory/'meta.json')
    if meta['schema'] != 'owngrd-head-v1' or not REQUIRED_HASHES <= meta['hashes'].keys():
        raise ValueError('Invalid export metadata')
    if expected_hashes is not None and meta['hashes'] != expected_hashes:
        raise ValueError('Export provenance mismatch')
    if sha256_file(directory/'head.safetensors') != meta['weights_sha256']:
        raise ValueError('Export weights checksum mismatch')
    cfg = Config(**meta['config'])
    if cfg.sha256 != meta['head_config_sha256']:
        raise ValueError('Export configuration checksum mismatch')
    model = GroundingHead(cfg, load_pretrained=False)
    model.load_state_dict(load_file(str(directory/'head.safetensors')), strict=True)
    return model.to(device).eval(), meta
