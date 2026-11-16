"""Toy overfit, the bimodal task, detach_backbone, save/load/resume and determinism."""
import pytest
import torch

from vla_heads import EpochSampler, FastCodec, load_checkpoint, save_checkpoint
from vla_heads.testing import build, full_batch, small_config, stub_batch, student_batch
from vla_heads.toy import bimodal, mode_stats, pairs, train

TOY = dict(hidden_size=64, reg_hidden=64, flow_width=64, flow_layers=2)

# (head, config overrides, steps, lr, mean-abs bound, max-abs bound) on 64 pairs within 120 s.
# DDPM with epsilon prediction bounds the 99th percentile instead of the max: recovering
# x0 = (x - sqrt(1 - ab) eps) / sqrt(ab) multiplies the eps error by up to 1 / sqrt(ab) ~ 2000 at the
# high-noise steps, which leaves a few elements in 1,792 wrong (notes/dbg_ddpm_*.txt: max 1.10 at
# 1,500 steps, 0.87 at 3,000; x0 prediction on the same model gives max 0.02). With the prompt's
# query tokens in the toy states, q99 measured 0.444 (mean 0.066) at 1,500 steps, so the q99 bound is 0.5.
OVERFIT = [
    ('regression', {}, 400, 3e-3, 0.03, 0.15),
    ('flow', {'flow_steps': 10}, 1500, 2e-3, 0.08, 0.40),
    ('flow', {'flow_objective': 'ddpm', 'flow_steps': 10}, 1500, 2e-3, 0.08, ('q99', 0.50)),
    ('flow', {'flow_objective': 'ddpm', 'ddpm_prediction': 'sample', 'flow_steps': 10}, 1500, 2e-3, 0.02, 0.10),
    ('tokens', {'tok_codec': 'bins'}, 400, 3e-3, 0.03, 1 / 32 + 1e-4),
    ('tokens', {'tok_codec': 'dct', 'tok_dct_scale': 20.0}, 400, 3e-3, 0.03, 0.08),
    ('tokens', {'tok_codec': 'fast', 'tok_dct_scale': 20.0}, 500, 3e-3, 0.03, 0.08),
]


@pytest.mark.parametrize('head,kw,steps,lr,mean_bound,max_bound', OVERFIT,
                         ids=['regression', 'flow', 'ddpm', 'ddpm_x0', 'bins', 'dct', 'fast'])
def test_overfit_64_pairs(head, kw, steps, lr, mean_bound, max_bound):
    cfg = small_config(head, **TOY, **kw)
    batch = pairs(64, chunk=cfg.chunk)
    codec = None
    if kw.get('tok_codec') == 'fast':  # fit the BPE on the training chunks only
        codec = FastCodec(cfg.chunk, cfg.action_dim, cfg.tok_vocab, cfg.tok_dct_scale).fit(batch['actions'])
    pol, losses, seconds = train(cfg, batch, steps, lr, max_seconds=120, codec=codec)
    assert len(losses) == steps, f'ran out of the 120 s budget after {len(losses)} steps'
    torch.manual_seed(0)
    err = (pol.predict(batch) - batch['actions']).abs()
    print(f'{head} {kw}: loss {losses[0]:.3f} -> {losses[-1]:.4f}, |err| mean {err.mean():.4f} '
          f'max {err.max():.4f}, {seconds:.1f} s')
    if isinstance(max_bound, tuple):
        q99 = err.flatten().quantile(0.99)
        print(f'  |err| q99 {q99:.4f}')
        assert err.mean() < mean_bound and q99 < max_bound[1]
    else:
        assert err.mean() < mean_bound and err.max() < max_bound


def test_bimodal_flow_fits_regression_cannot():
    """Each state's chunk is +m or -m with equal odds. The flow expert samples both modes (most samples
    within 0.15 of a mode, each mode drawn for a quarter or more of each state's samples); the L1
    regression head is deterministic, so it covers at most one mode and in practice sits between them."""
    stats = {}
    for head, steps in (('regression', 600), ('flow', 1500)):
        cfg = small_config(head, **TOY, action_dim=2, proprio_dim=0, flow_steps=10, flow_time_dist='uniform')
        base, mode, sample = bimodal(32, chunk=cfg.chunk)
        pol, losses, seconds = train(cfg, base, steps, 2e-3, sample_batch=sample, max_seconds=120)
        torch.manual_seed(0)
        pred = torch.stack([pol.predict(base) for _ in range(32)])
        stats[head] = mode_stats(pred, mode)
        print(head, 'near-mode share %.3f, minority share %.3f, distance to nearest mode %.3f' % stats[head],
              f'{seconds:.1f} s')
    near, minority, dist = stats['flow']
    assert near > 0.8 and minority > 0.25
    r_near, r_minority, r_dist = stats['regression']
    assert r_minority == 0.0 and r_dist > 3 * dist


def _lm_grads(pol):
    return {n: p.grad.clone() for n, p in pol.backbone.named_parameters() if p.grad is not None and p.grad.abs().sum() > 0}


def _policy(kind, model, **kw):
    torch.manual_seed(0)
    cfg = small_config('flow', **kw)
    pol = build(cfg) if kind == 'stub' else build(cfg, 'student', model)
    base = stub_batch(4) if kind == 'stub' else student_batch(model, b=2)
    return cfg, pol, full_batch(cfg, base, base['input_ids'].shape[0])


@pytest.mark.parametrize('cond', ['none', 'both'])
@pytest.mark.parametrize('kind', ['stub', 'student'])
def test_detach_backbone(kind, cond, tiny_student):
    """detach_backbone: exactly zero LM gradient from the expert; the default sends a non-zero one."""
    grads = {}
    for detach in (False, True):
        _, pol, batch = _policy(kind, tiny_student, cond=cond, detach_backbone=detach)
        pol.zero_grad(set_to_none=True)
        tiny_student.zero_grad(set_to_none=True)
        pol.loss(batch)['loss'].backward()
        grads[detach] = sum(float(g.abs().sum()) for g in _lm_grads(pol).values())
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in pol.head.parameters())
    assert grads[True] == 0.0 and grads[False] > 0.0


@pytest.mark.parametrize('codec', ['bins', 'fast'])
@pytest.mark.parametrize('kind', ['stub', 'student'])
def test_detach_with_lm_token_loss(kind, codec, tiny_student):
    """T-9 and knowledge insulation: with detach_backbone and lm_token_loss the LM's gradient is
    exactly the token loss's gradient (the flow loss alone gives exactly zero, the FAST or bins loss
    alone a non-zero one), and the expert's inputs equal those of a run without the token block."""
    kw = dict(detach_backbone=True, lm_token_loss=codec, tok_dct_scale=20.0, cond='both')
    cfg, pol, batch = _policy(kind, tiny_student, **kw)
    if codec == 'fast':
        fast = FastCodec(cfg.chunk, cfg.action_dim, cfg.tok_vocab, 20.0).fit(batch['actions'])
        cfg, pol, batch = _policy(kind, tiny_student, **kw)
        pol.aux_tokens.codec = fast
    pol.zero_grad(set_to_none=True)
    tiny_student.zero_grad(set_to_none=True)
    torch.manual_seed(5)
    out = pol.loss(batch)
    out['loss'].backward()
    total = _lm_grads(pol)
    assert total and 'tok_ce' in out['parts'] and 'mse_flow' in out['parts']
    pol.zero_grad(set_to_none=True)
    tiny_student.zero_grad(set_to_none=True)
    inputs, (tok_inputs, targets) = pol.inputs(batch, batch['actions'], batch['action_mask'])
    pol.aux_tokens.loss(tok_inputs, batch['actions'], batch['action_mask'], targets=targets)['loss'].backward()
    only_tokens = _lm_grads(pol)
    assert total.keys() == only_tokens.keys()
    for n in total:
        torch.testing.assert_close(total[n], only_tokens[n], atol=1e-6, rtol=1e-5)
    # Review finding 12: the flow loss alone sends exactly zero gradient into the LM; the token loss
    # alone sends a non-zero one, so knowledge insulation leaves the LM trainable, not unchanged.
    pol.zero_grad(set_to_none=True)
    tiny_student.zero_grad(set_to_none=True)
    inputs, _ = pol.inputs(batch, batch['actions'], batch['action_mask'])
    pol.head.loss(inputs, batch['actions'], batch['action_mask'])['loss'].backward()
    assert not _lm_grads(pol) and any(p.grad is not None and p.grad.abs().sum() > 0 for p in pol.head.parameters())
    assert only_tokens
    with torch.no_grad():
        plain = pol.inputs(batch)[0]
    torch.testing.assert_close(inputs.lm_states, plain.lm_states, atol=1e-5, rtol=1e-5)


def _run(head, steps, seed=0, resume=None, save_at=None, path=None):
    """AdamW + warm-up schedule + epoch sampler on the stub; returns per-step losses and the policy.
    The checkpoint carries weights, optimizer moments, scheduler, RNG streams and the sampler position."""
    torch.manual_seed(seed)
    cfg = small_config(head, cond='both')
    pol = build(cfg)
    opt = torch.optim.AdamW([p for p in pol.parameters() if p.requires_grad], lr=1e-3)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / 10)
    sampler = EpochSampler(3, seed=0)  # 3 items: step 3 starts a new epoch
    start = 0
    if resume is not None:
        payload = load_checkpoint(resume, pol, opt, sched)
        start = payload['step']
        sampler.load_state_dict(payload['extra']['sampler'])
    losses = []
    for step in range(start, steps):
        item = sampler.next_indices(1)[0]
        batch = full_batch(cfg, stub_batch(4, seed=item), 4, seed=item)
        loss = pol.loss(batch)['loss']
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
        losses.append(loss.detach())
        if save_at == step + 1:
            save_checkpoint(path, pol, opt, sched, step=step + 1, extra={'sampler': sampler.state_dict()})
    return losses, pol


@pytest.mark.parametrize('head', ['regression', 'flow', 'tokens'])
def test_resume_equals_uninterrupted(head, tmp_path):
    path = tmp_path / 'ckpt.pt'
    full, pol_a = _run(head, 5)
    _run(head, 2, save_at=2, path=path)
    resumed, pol_b = _run(head, 5, seed=123, resume=path)  # a different init seed: the checkpoint wins
    assert len(resumed) == 3 and all(torch.equal(a, b) for a, b in zip(resumed, full[2:]))
    for (n, a), (_, b) in zip(pol_a.state_dict().items(), pol_b.state_dict().items()):
        assert torch.equal(a, b), n


def test_checkpoint_refuses_other_config(tmp_path):
    path = tmp_path / 'ckpt.pt'
    _run('regression', 1, save_at=1, path=path)
    pol = build(small_config('regression', cond='none'))
    with pytest.raises(ValueError, match='config differs'):
        load_checkpoint(path, pol)


@pytest.mark.parametrize('head', ['regression', 'flow', 'tokens'])
def test_determinism(head):
    a, pa = _run(head, 3, seed=7)
    b, pb = _run(head, 3, seed=7)
    assert all(torch.equal(x, y) for x, y in zip(a, b))
    batch = full_batch(pa.cfg, stub_batch(4), 4)
    torch.manual_seed(5)
    ya = pa.eval().predict(batch)
    torch.manual_seed(5)
    yb = pb.eval().predict(batch)
    assert torch.equal(ya, yb)


def test_epoch_sampler_resumes_and_reshuffles():
    a = EpochSampler(10, seed=3)
    first = a.next_indices(10)
    second = a.next_indices(10)
    assert sorted(first) == sorted(second) == list(range(10)) and first != second
    b = EpochSampler(10, seed=3)
    b.next_indices(7)
    c = EpochSampler(10, seed=3)
    c.load_state_dict(b.state_dict())
    assert c.next_indices(13) == (first + second)[7:20]
    ranks = [EpochSampler(10, seed=3, rank=r, world_size=2).next_indices(5) for r in range(2)]
    assert not set(ranks[0]) & set(ranks[1])
