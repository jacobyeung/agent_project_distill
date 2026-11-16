"""Loss parity of head (a) against StarVLA's QwenOFT head on one batch (design record 5.8.5).

StarVLA's `L1RegressionActionHead` (commit 985c2238, copied verbatim under fixtures/) is
LayerNorm -> Linear(D, 2D) -> ReLU -> 2 x [x + ReLU(Linear(LN(x)))] -> LayerNorm -> Linear(2D, A) per
action query, and QwenOFT's loss is `masked_l1_loss`. With the default reg_arch starvla_oft_985c2238,
reg_hidden 2D, no proprio and no cond, and with StarVLA's
weights copied in, our head gives the same predictions and the same masked L1 on the same query states.
"""
import importlib.util
from pathlib import Path

import torch

from vla_heads import HeadInputs, RegressionHead
from vla_heads.testing import small_config

FIX = Path(__file__).parent / 'fixtures' / 'starvla_985c2238'


def load(name):
    spec = importlib.util.spec_from_file_location(name, FIX / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def oft_mapping(ours, theirs):
    m = theirs.model
    pairs = [(ours.norm, m.layer_norm1), (ours.inp, m.fc1), (ours.final_norm, m.layer_norm2), (ours.out, m.fc2)]
    for blk, ref in zip(ours.blocks, m.mlp_resnet_blocks):
        pairs += [(blk.norm, ref.ffn[0]), (blk.fc1, ref.ffn[1])]
    return pairs


def test_regression_head_matches_starvla_qwenoft():
    heads = load('MLP_ActionHeader')
    masked_l1_loss = load('masked_l1_loss').masked_l1_loss
    d, k, a = 64, 8, 7
    torch.manual_seed(0)
    theirs = heads.L1RegressionActionHead(input_dim=d, hidden_dim=2 * d, action_dim=a, NUM_ACTIONS_CHUNK=k)
    cfg = small_config('regression', hidden_size=d, chunk=k, action_dim=a, proprio_dim=0, reg_hidden=2 * d,
                       reg_cond_heads=4)
    assert cfg.reg_arch == 'starvla_oft_985c2238'  # the default head is StarVLA's layout
    ours = RegressionHead(cfg)
    assert sum(p.numel() for p in ours.parameters()) == sum(p.numel() for p in theirs.parameters())
    with torch.no_grad():
        for mine, ref in oft_mapping(ours, theirs):
            mine.weight.copy_(ref.weight)
            mine.bias.copy_(ref.bias)
    queries = torch.randn(4, k, d)
    actions = torch.rand(4, k, a) * 2 - 1
    mask = torch.ones(4, k, a, dtype=torch.bool)
    mask[0, -3:] = False
    inputs = HeadInputs(torch.randn(4, 5, d), torch.ones(4, 5, dtype=torch.bool), query_states=queries)
    pred_theirs = theirs.predict_action(queries)
    torch.testing.assert_close(ours(inputs), pred_theirs, atol=0, rtol=0)
    ref = masked_l1_loss(pred_theirs, actions, mask)
    got = ours.loss(inputs, actions, mask)['loss']
    torch.testing.assert_close(got, ref, atol=1e-7, rtol=1e-6)
    # QwenOFT without a mask is the plain mean.
    torch.testing.assert_close(ours.loss(inputs, actions)['loss'], masked_l1_loss(pred_theirs, actions), atol=1e-7, rtol=1e-6)
    # gradients agree too
    ours.zero_grad(); theirs.zero_grad()
    ours.loss(inputs, actions, mask)['loss'].backward()
    masked_l1_loss(theirs.predict_action(queries), actions, mask).backward()
    for mine, ref in oft_mapping(ours, theirs):
        torch.testing.assert_close(mine.weight.grad, ref.weight.grad, atol=1e-6, rtol=1e-5)
