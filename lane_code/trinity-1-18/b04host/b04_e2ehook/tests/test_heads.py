"""CPU tests of the two trained heads: forward on real K1 inputs, retrain determinism, sha256 refusal."""
import json, shutil, sys
from pathlib import Path
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'heads/scale'), str(ROOT / 'heads/selector')]
TOWER = '/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2/01949c4249271126/tower.npz'
SCALE = ROOT / 'heads/scale/work/run1'
SCALE_RETRAIN = ROOT / 'heads/scale/work/det_a'
SEL = ROOT / 'heads/selector/work/run_iso'
SEL_RETRAIN = ROOT / 'heads/selector/work/run_iso_retrain'


def test_scale_forward_real_tower():
    from scale_head import load_head, prepare_inputs
    head = load_head(SCALE)
    with torch.no_grad():
        s = torch.exp(head(**prepare_inputs(TOWER)))
    assert s.shape == (1,) and torch.isfinite(s).all() and 0.1 < float(s) < 20


def test_scale_retrain_identical():
    a = json.loads((SCALE / 'scale_head.json').read_text())['weights_sha256']
    b = json.loads((SCALE_RETRAIN / 'scale_head.json').read_text())['weights_sha256']
    assert a == b


def test_scale_refuses_mismatch(tmp_path):
    from scale_head import load_head
    d = tmp_path / 'h'; shutil.copytree(SCALE, d)
    with pytest.raises(ValueError, match='sha256 mismatch'):
        load_head(d, expected_sha256='0' * 64)
    p = d / 'scale_head.safetensors'; b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
    with pytest.raises(ValueError, match='sha256 mismatch'):
        load_head(d)


def test_selector_forward_real_capture():
    import common as C, train_selector as T
    from selector_head import load_head
    head, _ = load_head(SEL)
    rows = [r for r in C.load() if r['capture'] == 'scannetpp/dfa70fb232']
    g = T.groups(rows, T.names_table())[0]
    with torch.no_grad():
        slots = head.with_null(g['x'], g['e'], g['name'])
        zero = head.with_null(g['x'], g['e'], g['name'], mask_tokens=torch.zeros(len(g['y']), 256),
                              vit_feats=torch.zeros(len(g['y']), 1024))
    assert slots.shape == (len(g['y']) + 1,) and torch.isfinite(slots).all()
    assert torch.equal(slots, zero), 'zero sockets must not change the answer'


def test_selector_retrain_identical():
    a = json.loads((SEL / 'selector_head.json').read_text())['weights_sha256']
    b = json.loads((SEL_RETRAIN / 'selector_head.json').read_text())['weights_sha256']
    assert a == b


def test_selector_refuses_mismatch(tmp_path):
    from selector_head import load_head
    d = tmp_path / 's'; shutil.copytree(SEL, d)
    p = d / 'selector_head.safetensors'; b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
    with pytest.raises(ValueError, match='sha256 mismatch'):
        load_head(d)
