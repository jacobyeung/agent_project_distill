"""Shapes, masks, dtype and device for every head and every cond value; step-0 parity of cond arms;
the flow convention; config mapping from the design-record spec."""
import pytest
import torch

from vla_heads import HeadInputs, VLAConfig, make_head
from vla_heads.config import CONDS, HEADS
from vla_heads.heads import cosine_alpha_bar, euler, sample_tau
from vla_heads.testing import build, full_batch, small_config, stub_batch

B = 4


def policy(head, cond, seed=0, **kw):
    torch.manual_seed(seed)
    cfg = small_config(head, cond=cond, **kw)
    return cfg, build(cfg)


@pytest.mark.parametrize('cond', CONDS)
@pytest.mark.parametrize('head', HEADS)
def test_loss_predict_shapes(head, cond):
    cfg, pol = policy(head, cond)
    batch = full_batch(cfg, stub_batch(B), B)
    out = pol.loss(batch)
    assert out['loss'].ndim == 0 and out['loss'].dtype == torch.float32 and torch.isfinite(out['loss'])
    assert all(not v.requires_grad for v in out['parts'].values())
    out['loss'].backward()
    trained = pol.module_groups()['head'] + pol.module_groups()['codec_rows']
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in trained)
    pred = pol.eval().predict(batch)
    assert pred.shape == (B, cfg.chunk, cfg.action_dim) and pred.abs().max() <= 1


@pytest.mark.parametrize('head', ['regression', 'tokens'])
def test_masked_action_steps_do_not_count(head):
    """Changing masked targets leaves the loss unchanged. (Tokens with bins: teacher forcing feeds a
    masked token only to later positions, which are masked too.)"""
    cfg, pol = policy(head, 'none')
    batch = full_batch(cfg, stub_batch(B), B)
    other = dict(batch, actions=batch['actions'].clone())
    other['actions'][0, -2:] = -batch['actions'][0, -2:]  # row 0's last two steps are masked
    torch.testing.assert_close(pol.loss(batch)['loss'], pol.loss(other)['loss'])


def test_flow_masked_steps_get_no_gradient():
    """The expert sees padded steps (as at inference, where every step is predicted), but their
    errors carry zero weight."""
    cfg, pol = policy('flow', 'none')
    batch = full_batch(cfg, stub_batch(B), B)
    seen = []
    original = pol.head.denoise

    def capture(*a, **k):
        out = original(*a, **k)
        out.retain_grad()
        seen.append(out)
        return out
    pol.head.denoise = capture
    pol.loss(batch)['loss'].backward()
    g = seen[0].grad
    assert g[0, -2:].abs().max() == 0 and g[0, :-2].abs().max() > 0


@pytest.mark.parametrize('head', ['regression', 'flow'])
def test_lm_and_cond_masks_hide_padding(head):
    """Head level: values at masked LM, cond or where positions cannot change the prediction."""
    torch.manual_seed(0)
    cfg = small_config(head, cond='both', taps=[-1])
    h = make_head(cfg).eval()
    for p in h.parameters():  # leave zero init so every path is live
        p.data.normal_(0, 0.2)
    lm = torch.randn(2, 6, 32)
    mask = torch.ones(2, 6, dtype=torch.bool)
    mask[:, :2] = False
    q = torch.randn(2, cfg.chunk, 32)
    cond = torch.randn(2, 5, 16)
    cmask = torch.tensor([[1, 1, 1, 0, 0], [1, 0, 0, 0, 0]], dtype=torch.bool)
    where = torch.randn(2, 2, 18)
    wmask = torch.tensor([[True, False], [True, True]])
    prop = torch.randn(2, cfg.proprio_dim)
    kw = {'noise': torch.randn(2, cfg.chunk, cfg.action_dim)} if head == 'flow' else {}
    base = HeadInputs(lm, mask, q, cond, cmask, prop, where=where, where_mask=wmask)
    lm2, cond2, where2 = lm.clone(), cond.clone(), where.clone()
    lm2[:, :2] = 100.0
    cond2[~cmask] = -50.0
    where2[~wmask] = 7.0
    alt = HeadInputs(lm2, mask, q, cond2, cmask, prop, where=where2, where_mask=wmask)
    torch.testing.assert_close(h.predict(base, **kw), h.predict(alt, **kw))


@pytest.mark.parametrize('cond', ['spatial_readouts', 'g3t_tokens', 'both'])
@pytest.mark.parametrize('head', ['regression', 'flow'])
def test_t9_gated_cond_leaves_step0_unchanged(head, cond):
    """T-9: with identical tokens and gated (flow: tanh gate at 0) or zero-initialised (regression)
    cond branches, a cond arm's step-0 output equals the no-cond arm's, bit for bit, and the shared
    parameters start equal under one seed."""
    _, plain = policy(head, 'none', seed=3)
    cfg, arm = policy(head, cond, seed=3)
    batch = full_batch(cfg, stub_batch(B), B)
    kw = {'noise': torch.randn(B, cfg.chunk, cfg.action_dim)} if head == 'flow' else {}
    torch.testing.assert_close(arm.eval().predict(batch, **kw),
                               plain.eval().predict({k: v for k, v in batch.items() if k != 'cond'}, **kw), atol=0, rtol=0)
    shared = dict(plain.head.named_parameters())
    for name, p in arm.head.named_parameters():
        if name in shared:
            assert torch.equal(p, shared[name]), name
    if head == 'flow':
        assert all(float(b.cond_gate.detach()) == 0 for b in arm.head.blocks)


@pytest.mark.parametrize('head', ['regression', 'flow'])
def test_cond_gets_gradient_after_the_gates_open(head):
    """Zero-initialised maps and closed gates pass no gradient into cond at step 0 (the gate itself
    gets one); after a few steps every cond module trains."""
    cfg, pol = policy(head, 'both')
    opt = torch.optim.SGD(pol.parameters(), lr=0.5)
    batch = full_batch(cfg, stub_batch(B), B)
    for step in range(3):
        opt.zero_grad()
        pol.loss(batch)['loss'].backward()
        if head == 'flow' and step == 0:
            assert pol.head.cond_proj.weight.grad.abs().sum() == 0
            assert all(b.cond_gate.grad.abs().sum() > 0 for b in pol.head.blocks)
        opt.step()
    assert all(p.grad is not None and p.grad.abs().sum() > 0 for p in pol.cond.g3t.cam[1].parameters())
    assert pol.head.where[0].weight.grad.abs().sum() > 0 if head == 'flow' else pol.head.where.weight.grad.abs().sum() > 0
    gates = pol.gate_norms()
    assert (gates['head.where'] > 0) if head == 'regression' else all(v > 0 for k, v in gates.items() if 'cond_gate' in k)


@pytest.mark.parametrize('cond', ['none', 'both'])
@pytest.mark.parametrize('head', HEADS)
def test_bf16(head, cond):
    cfg, pol = policy(head, cond)
    pol = pol.to(torch.bfloat16)
    batch = full_batch(cfg, stub_batch(B), B)
    batch['proprio'] = batch['proprio'].bfloat16()
    out = pol.loss(batch)
    assert out['loss'].dtype == torch.float32 and torch.isfinite(out['loss'])
    out['loss'].backward()
    pred = pol.eval().predict(batch)
    assert pred.dtype == torch.float32 and torch.isfinite(pred).all()


@pytest.mark.parametrize('head', ['regression', 'flow'])
def test_meta_device_at_9b_width(head):
    """No hard-coded device: the heads run shape inference on the meta device at D = 4096."""
    cfg = VLAConfig(head=head, cond='both')
    n = len(cfg.taps)
    with torch.device('meta'):
        h = make_head(cfg)
        inp = HeadInputs(torch.empty(2, 9, 4096), torch.ones(2, 9, dtype=torch.bool), torch.empty(2, cfg.chunk, 4096),
                         torch.empty(2, 3, 1024), torch.ones(2, 3, dtype=torch.bool), torch.empty(2, 8),
                         tap_states=torch.empty(n, 2, 9, 4096), where=torch.empty(2, 2, 18))
        out = h.loss(inp, torch.empty(2, cfg.chunk, cfg.action_dim))
    assert out['loss'].device.type == 'meta' and out['loss'].shape == ()


def test_flow_convention():
    """openpi: x_tau = tau eps + (1 - tau) a, tau = 1 noise, target eps - a; Euler from tau = 1."""
    # A constant velocity field integrates exactly: x(0) = x(1) - v.
    x1, v = torch.randn(3, 4, 7), torch.randn(3, 4, 7)
    torch.testing.assert_close(euler(lambda x, tau: v, x1.clone(), 7), x1 - v)
    # The exact field of one data point a carries noise to a: v = eps - a = (x - a) / tau.
    a = torch.rand(3, 4, 7) * 2 - 1
    out = euler(lambda x, tau: (x - a) / tau[:, None, None], torch.randn(3, 4, 7), 10)
    torch.testing.assert_close(out, a, atol=1e-5, rtol=1e-5)
    # Beta(1.5, 1): mean 0.6, variance 0.0686, then 0.001 + 0.999 tau.
    torch.manual_seed(0)
    tau = (sample_tau('beta', 400_000, 'cpu') - 0.001) / 0.999
    assert abs(tau.mean() - 0.6) < 2e-3 and abs(tau.var() - 1.5 / (2.5 ** 2 * 3.5)) < 2e-3
    assert tau.min() >= 0 and tau.max() <= 1
    # The training pair the head builds follows the same convention.
    cfg = small_config('flow', taps=[-1])
    h = make_head(cfg)
    seen = {}
    h.denoise = lambda xt, t, *a: seen.update(xt=xt, t=t) or torch.zeros_like(xt)
    acts = torch.rand(2, cfg.chunk, cfg.action_dim) * 2 - 1
    inputs = HeadInputs(torch.randn(2, 3, 32), torch.ones(2, 3, dtype=torch.bool), proprio=torch.zeros(2, 8))
    torch.manual_seed(1)
    loss = h.loss(inputs, acts)
    torch.manual_seed(1)
    eps = torch.randn_like(acts)
    tau = sample_tau('beta', 2, 'cpu')
    torch.testing.assert_close(seen['xt'], tau[:, None, None] * eps + (1 - tau[:, None, None]) * acts)
    torch.testing.assert_close(loss['loss'], ((eps - acts) ** 2).mean())


def test_cosine_schedule():
    ab = cosine_alpha_bar(100)
    assert ab[0] == 1 and (ab[1:] < ab[:-1]).all() and ab[-1] < 1e-3


SCHEMA10 = {'vla': {
    'schema': 'vla_schema_v2', 'control_only': False,
    'backbone': {'kind': 'student', 'path': '<milestone>/full_weights', 'sha256': '<sha>', 'train': 'full', 'vision': 'frozen'},
    'input': {'cameras': ['agentview', 'wrist'], 'image_px': 224, 'orientation': 'dataset', 'proprio': True, 'history_frames': 0},
    'prompt': {'template': 'starvla_qwenoft_985c2238_v1'},
    'head': {'type': 'regression', 'chunk': 8, 'action_dim': 7, 'taps': [-1],
             'regression': {'arch': 'starvla_oft_985c2238', 'hidden': 8192, 'blocks': 2, 'loss': 'l1'},
             'flow': {'layers': 8, 'width': 1024, 'heads': 16, 'objective': 'flow', 'time_dist': 'beta_1.5_1', 'steps': 10,
                      'cond_gate': 'zero_init'},
             'tokens': {'codec': 'fast', 'vocab': 1024, 'bins': 256, 'scale': 10, 'max_tokens': 64,
                        'reserved_ids': 'vla_heads/out/qwen35_9b_c2022362_rare_ids_1025.json',
                        'reserved_sha256': '87a74b676da1fae8b6f94bbe77079ba0216bb7800b31f8f1d7566cab4e4c2860',
                        'fast_reference': 'physical-intelligence/fast processing_action_tokenizer.py@ec4d7aa71691cac0b8bed6942be45684db2110f4',
                        'fast_reference_sha256': '6f021ca1f4c1b194ab6fa399d80baf3d642eadb17efb8f73301e4ac401522c20'}},
    'cond': 'none',
    'where': {'text_line': True, 'vector': True, 'dropout': 0.2, 'dropout_draw': 'sha256_seed_episode_t', 'entities': 2},
    'detach_backbone': False, 'lm_token_loss': 'none',
    'optim': {'lm_lr': 3.0e-5, 'head_lr': 3.0e-4, 'betas': [0.9, 0.95], 'clip': 1.0, 'warmup_frac': 0.03},
    'train': {'batch': 64, 'steps': 10000, 'seed': 17},
    'data': {'suite': 'libero_spatial', 'subset': 'd5_s0', 'action_norm': 'minmax_subset_v1', 'gripper': 'unit_open_neg'},
    'eval': {'init_states': 50}, 'provider': {'history_offsets': [8, 16, 32]},
    'nav': {'action_format': 'nav_text', 'train': {'batch': 32, 'steps': 1000, 'lm_lr': 1.0e-5, 'seed': 17},
            'eval': {'primary_list': 'val_unseen_600_s0', 'max_steps': 500}}}}
NAV_ARM = {'head.type': 'tokens', 'head.tokens.codec': 'nav_text', 'head.taps': [-1], 'prompt.template': 'navrun_prompts_v1',
           'input': {'cameras': ['nav_rgb'], 'image_px': 512, 'orientation': 'dataset', 'proprio': False, 'history_frames': 32},
           'nav.action_format': 'nav_text', 'where': {'text_line': False, 'vector': False}, 'cond': 'none'}
BASE = {'kind': 'base', 'path': 'Qwen/Qwen3.5-9B', 'revision': 'c2022362', 'sha256': None, 'train': 'full', 'vision': 'frozen'}


def _arm(**over):
    import copy
    spec = copy.deepcopy(SCHEMA10)
    for path, value in over.items():
        node = spec['vla']
        keys = path.split('.')
        for k in keys[:-1]:
            node = node[k]
        node[keys[-1]] = value
    return VLAConfig.from_spec(spec)


def test_config_loads_schema10_tree_and_arms():
    """Schema 10: the defaults (B1), the per-arm overrides, exact keys, and no bare tokens.codec."""
    b1, rest = _arm()
    assert (b1.head, b1.taps, b1.reg_arch, b1.reg_hidden, b1.reg_blocks) == ('regression', [-1], 'starvla_oft_985c2238', 8192, 2)
    assert (b1.reg_block, b1.reg_act, b1.reg_input_act, b1.reg_final_norm) == ('oft', 'relu', True, True)
    assert b1.where_dropout == 0.2 and b1.where_seed == 17 and b1.proprio_dim == 8 and not b1.train_vision
    assert b1.tok_ids_sha256.startswith('87a74b67') and rest['optim']['head_lr'] == 3.0e-4 and 'schema' not in rest
    assert (b1.tok_dct_scale, b1.tok_max_tokens) == (10.0, 64) and rest['control_only'] is False
    assert rest['train_effective']['head_lr'] == 3.0e-4 and rest['eval_effective'] == {'init_states': 50}
    b0, rest = _arm(control_only=True, backbone=BASE)
    assert rest['control_only'] is True and rest['backbone']['kind'] == 'base' and b0.head == 'regression'
    assert VLAConfig().to_dict() == VLAConfig.from_spec({'vla': {}})[0].replace(where_seed=17).to_dict()
    u1, _ = _arm(cond='spatial_readouts')
    assert u1.cond == 'spatial_readouts' and u1.where_vector
    f1, _ = _arm(**{'head.type': 'flow', 'head.taps': [16, -1], 'detach_backbone': True, 'lm_token_loss': 'fast'})
    assert (f1.head, f1.taps, f1.flow_time_dist, f1.flow_cond_gate, f1.detach_backbone, f1.lm_token_loss) == (
        'flow', [16, -1], 'beta_1.5_1', 'zero_init', True, 'fast')
    n1, rest = _arm(**NAV_ARM)
    assert n1.tok_codec == 'nav_text' and n1.proprio_dim == 0 and rest['input']['history_frames'] == 32
    # navigation precedence: nav.train overlays optim and train key by key; nav.eval alone sets evaluation
    te = rest['train_effective']
    assert (te['lm_lr'], te['batch'], te['steps'], te['warmup_frac'], te['seed']) == (1.0e-5, 32, 1000, 0.03, 17)
    assert rest['eval_effective'] == {'primary_list': 'val_unseen_600_s0', 'max_steps': 500}
    n0, rest = _arm(**NAV_ARM, control_only=True, backbone=BASE)
    assert rest['control_only'] and n0.tok_codec == 'nav_text'
    nu, _ = _arm(**{**NAV_ARM, 'head.tokens.codec': 'nav_click', 'nav.action_format': 'click'})
    assert nu.tok_codec == 'nav_click'
    with pytest.raises(ValueError, match='vla.cond'):
        _arm(**{**NAV_ARM, 'cond': 'spatial_readouts'})
    with pytest.raises(ValueError, match='nav_grammar_v1'):
        make_head(nu)
    # exact keys: unknown or misplaced keys raise, and so does a bare tokens.codec
    for bad in ({'vla': {'tokens': {'codec': 'fast'}}}, {'tokens': {'codec': 'fast'}}, {'vla': {}, 'tokens': {}},
                {'vla': {'head': {'flow': {'taps': [16, -1]}}}}, {'vla': {'where': {'cross_view_cm': 5}}},
                {'vla': {'schema': 'vla_schema_v1'}}, {'vla': {'not_a_section': 1}}, {'vla': {'control_only': 'yes'}},
                {'vla': {'head': {'tokens': {'fast_reference': 'someone/else@abc'}}}},
                {'vla': {'head': {'tokens': {'fast_reference_sha256': '0' * 64}}}}):
        with pytest.raises(ValueError):
            VLAConfig.from_spec(bad)
    with pytest.raises(ValueError):
        VLAConfig.from_spec({'vla': {}}, **{'tokens.codec': 'fast'})
    with pytest.raises(ValueError):
        VLAConfig.from_dict({'head': 'regression', 'not_a_key': 1})
    with pytest.raises(ValueError):
        VLAConfig(head='regression', detach_backbone=True)
    with pytest.raises(ValueError):  # the OFT arch fixes its block layout
        VLAConfig(reg_block='mlp2')
    assert VLAConfig(reg_arch='custom', reg_block='mlp2', reg_hidden=1024).reg_hidden == 1024
    assert VLAConfig(head='generative').head == 'flow' and VLAConfig(head='discrete').head == 'tokens'
    a = VLAConfig()
    assert a.sha256() == VLAConfig.from_dict(a.to_dict()).sha256() != a.replace(chunk=4).sha256()


@pytest.mark.parametrize('taps', [[0, -1], [32], [16, 32], [33], [-2], [16, 16]])
def test_t8_invalid_taps_raise(taps):
    """T-8: taps are 1..31 or -1; 0 and 32 raise and nothing remaps 32 to -1."""
    with pytest.raises(ValueError):
        VLAConfig(head='flow', taps=taps)
    with pytest.raises(ValueError):
        _arm(**{'head.type': 'flow', 'head.taps': taps})


@pytest.mark.parametrize('head,inject', [('regression', 'head'), ('flow', 'head'), ('flow', 'lm')])
def test_cond_and_proprio_injection_routes(head, inject):
    cfg, pol = policy(head, 'both', cond_inject=inject, proprio_inject=inject)
    batch = full_batch(cfg, stub_batch(B), B)
    pol.loss(batch)['loss'].backward()
    assert (pol.cond_to_lm is not None) == (inject == 'lm') == (pol.where_to_lm is not None)
    assert torch.isfinite(pol.eval().predict(batch)).all()


def test_regression_refuses_lm_injection():
    """The regression head reads the prompt's query tokens; LM-injected tokens would follow them."""
    for kw in ({'cond_inject': 'lm'}, {'proprio_inject': 'lm'}):
        with pytest.raises(ValueError):
            small_config('regression', cond='both', **kw)


def test_where_dropout_sha256_draw():
    """Schema 5.5: training withholds chunk (episode, t) by the sha256 draw over the whole chunk;
    evaluation keeps every chunk unless cond['withheld'] says otherwise."""
    from vla_heads import withheld_draw
    assert not withheld_draw('libero_spatial/task03/demo_007', 40, 17, 0.2)  # 0x9c6b2b8d / 16^8 = 0.6110
    cfg, pol = policy('regression', 'spatial_readouts', where_dropout=0.2)
    n = 400
    raw = full_batch(cfg, stub_batch(B), B)['cond']
    raw = dict(raw, where=raw['where'][:1].expand(n, -1, -1).clone())
    raw['where'][:, 1] = raw['where'][0, 0]
    episodes, ts = [f'libero_spatial/task{i % 10:02d}/demo_{i // 10:03d}' for i in range(n)], list(range(n))
    with pytest.raises(ValueError):
        pol.cond(raw, training=True)
    train = pol.cond(dict(raw, episode=episodes, t=ts), training=True)
    expect = torch.tensor([withheld_draw(e, t, 17, 0.2) for e, t in zip(episodes, ts)])
    assert torch.equal(train['where_mask'], ~expect[:, None].expand(-1, 2))
    assert torch.equal(train['where'][expect], torch.zeros_like(train['where'][expect]))
    assert 0.12 < expect.float().mean() < 0.28
    test = pol.cond(dict(raw, episode=episodes, t=ts), training=False)
    assert test['where_mask'].all()
    held = pol.cond(dict(raw, withheld=torch.ones(n, dtype=torch.bool)), training=False)
    assert not held['where_mask'].any() and held['where'].abs().sum() == 0


def test_lm_injection_keeps_context_but_not_predictions():
    """Review finding 13: parity holds only for fully gated, identical-token inputs. cond_inject = lm
    appends (zero-valued) tokens the LM attends to, so the context states stay equal (causal attention)
    while the appended positions, and hence the flow predictions, differ from the plain arm."""
    _, plain = policy('flow', 'none', seed=3)
    cfg, arm = policy('flow', 'both', seed=3, cond_inject='lm', proprio_inject='head')
    batch = full_batch(cfg, stub_batch(B), B)
    noise = torch.randn(B, cfg.chunk, cfg.action_dim)
    with torch.no_grad():
        a = arm.eval().inputs(batch)[0]
        p = plain.eval().inputs({k: v for k, v in batch.items() if k != 'cond'})[0]
        pa = arm.predict(batch, noise=noise)
        pp = plain.predict({k: v for k, v in batch.items() if k != 'cond'}, noise=noise)
    t = p.lm_states.shape[1]
    torch.testing.assert_close(a.lm_states[:, :t], p.lm_states, atol=1e-5, rtol=1e-4)  # kernel rounding only
    assert a.lm_states.shape[1] > t and not torch.equal(pa, pp)


@pytest.mark.parametrize('prediction', ['epsilon', 'sample'])
def test_ddim_all_steps_finite(prediction):
    """DDIM with as many steps as training steps (consecutive k) stays finite; more steps refuse."""
    cfg, pol = policy('flow', 'none', flow_objective='ddpm', ddpm_prediction=prediction)
    batch = full_batch(cfg, stub_batch(B), B)
    pred = pol.eval().predict(batch, steps=cfg.ddpm_train_steps)
    assert torch.isfinite(pred).all()
    with pytest.raises(ValueError):
        pol.predict(batch, steps=cfg.ddpm_train_steps + 1)
    with pytest.raises(ValueError):
        small_config('flow', flow_objective='ddpm', flow_steps=21, ddpm_train_steps=20)
