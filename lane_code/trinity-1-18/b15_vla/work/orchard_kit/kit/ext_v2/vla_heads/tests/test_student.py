"""The first batch through the tiny real-architecture student (native Qwen3.5 hybrid DeltaNet + full
attention LM and vision tower, fp32 on CPU) for every head and cond value: forward, loss, backward,
one optimizer step; adapter parity, padding, taps, caching and train modes."""
import pytest
import torch

from vla_heads import StudentAdapter
from vla_heads.config import CONDS, HEADS
from vla_heads.testing import build, full_batch, small_config, student_batch


def make(model, head, cond='none', **kw):
    torch.manual_seed(0)
    cfg = small_config(head, cond=cond, **kw)
    return cfg, build(cfg, 'student', model)


@pytest.mark.parametrize('cond', CONDS)
@pytest.mark.parametrize('head', HEADS)
def test_first_batch_step(tiny_student, head, cond):
    cfg, pol = make(tiny_student, head, cond)
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    opt = torch.optim.AdamW([p for p in pol.parameters() if p.requires_grad], lr=1e-3)
    out = pol.loss(batch)
    assert torch.isfinite(out['loss'])
    out['loss'].backward()
    groups = pol.module_groups()
    assert sum(float(p.grad.norm()) for p in groups['lm'] if p.grad is not None) > 0
    trained = groups['head'] + groups['codec_rows']
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in trained)
    before = {n: p.detach().clone() for n, p in pol.named_parameters() if p.requires_grad}
    opt.step()
    assert sum(not torch.equal(before[n], p) for n, p in pol.named_parameters() if p.requires_grad) > 0
    pred = pol.eval().predict(batch)
    assert pred.shape == (2, cfg.chunk, cfg.action_dim) and torch.isfinite(pred).all()


def test_adapter_states_equal_plain_model_bitwise(tiny_student):
    """Design 5.4 step-0 parity: with cond none the adapter's states equal the plain model's (fp32, bitwise)."""
    batch = student_batch(tiny_student, b=2, pad='left')
    with torch.no_grad():
        ref = tiny_student.model(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                                 pixel_values=batch['pixel_values'], image_grid_thw=batch['image_grid_thw'],
                                 mm_token_type_ids=(batch['input_ids'] == tiny_student.config.image_token_id).long(),
                                 output_hidden_states=True)
        adapter = StudentAdapter(tiny_student, taps=(1, -1)).eval()
        taps, mask = adapter.encode(batch)
    assert torch.equal(taps[-1], ref.last_hidden_state) and torch.equal(taps[0], ref.hidden_states[1])
    assert torch.equal(mask, batch['attention_mask'].bool())


def test_padding_invariance(tiny_student):
    """A right-padded row gives the same states as the row alone (the adapter left-pads)."""
    adapter = StudentAdapter(tiny_student).eval()
    batch = student_batch(tiny_student, b=2, lengths=(6, 2))
    ext = torch.randn(2, 3, adapter.hidden_size)
    with torch.no_grad():
        taps, mask = adapter.encode(batch, ext)
        n = int(batch['attention_mask'][1].sum())
        alone = dict(input_ids=batch['input_ids'][1:, :n], attention_mask=batch['attention_mask'][1:, :n],
                     pixel_values=batch['pixel_values'][batch['pixel_values'].shape[0] // 2:],
                     image_grid_thw=batch['image_grid_thw'][2:])
        single, _ = adapter.encode(alone, ext[1:])
    s = single.shape[2]
    assert mask[1, -s:].all() and not mask[1, :-s].any()
    torch.testing.assert_close(taps[-1, 1, -s:], single[-1, 0], atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize('codec', ['bins', 'dct'])
def test_cached_decoder_matches_reencoding(tiny_student, codec):
    cfg, pol = make(tiny_student, 'tokens', 'both', tok_codec=codec, tok_dct_scale=20.0)
    pol.eval()
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    ext = pol.prefix(batch)[0]
    cached, plain = pol.backbone.decoder(batch, ext), pol.backbone.decoder(batch, ext, use_cache=False)
    ids = pol.head.binding.ids
    with torch.no_grad():
        torch.testing.assert_close(cached(None), plain(None), atol=1e-5, rtol=1e-5)
        for _ in range(4):
            tok = ids[torch.randint(0, len(ids), (2,))]
            torch.testing.assert_close(cached(tok), plain(tok), atol=1e-5, rtol=1e-5)
        inputs, (_, (sym, _)) = pol.inputs(batch, batch['actions'])
        tf = pol.head.token_ids(sym)
        dec = pol.backbone.decoder(batch, ext)
        states = [dec(None)] + [dec(tf[:, j]) for j in range(tf.shape[1] - 1)]
        torch.testing.assert_close(torch.stack(states, 1), inputs.query_states, atol=1e-4, rtol=1e-4)
        torch.testing.assert_close(pol.predict(batch), pol.predict(batch, use_cache=False))


def test_codec_rows_follow_vocabulary(tiny_student):
    cfg, pol = make(tiny_student, 'tokens', tok_codec='bins')
    v = tiny_student.config.text_config.vocab_size
    assert pol.head.binding.ids.tolist() == list(range(v, v + cfg.tok_bins))
    assert pol.backbone.extra_embed.weight.shape == (cfg.tok_bins, 32)
    assert tiny_student.lm_head.weight.shape[0] == v  # the student's own tables are not resized


@pytest.mark.parametrize('mode', ['full', 'lora', 'frozen'])
def test_train_modes(tiny_student, mode):
    cfg, pol = make(tiny_student, 'regression', train_mode=mode, lora_rank=4, lora_alpha=8)
    lm = list(pol.backbone.named_parameters())
    lora = [n for n, p in lm if 'lora_' in n]
    trainable = [n for n, p in lm if p.requires_grad]
    assert not any(p.requires_grad for n, p in lm if '.visual.' in n)
    if mode == 'full':
        assert not lora and len(trainable) > 10
    elif mode == 'lora':
        assert lora and set(trainable) == set(lora) and all('language_model.layers' in n for n in lora)
    else:
        assert not trainable
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    pol.loss(batch)['loss'].backward()
    assert all(p.grad is None for n, p in lm if not p.requires_grad)
    assert all(p.grad is not None for p in pol.head.parameters() if p.requires_grad)


def test_train_vision_flag(tiny_student):
    cfg, pol = make(tiny_student, 'regression', train_mode='frozen', train_vision=True)
    assert all(p.requires_grad for p in pol.backbone.inner.visual.parameters())


@pytest.mark.parametrize('taps,norm', [((1, -1), False), ((1, -1), True), ((-1,), False)])
def test_taps(tiny_student, taps, norm):
    """Tap i is transformers' hidden_states[i] (the last one post-norm); tap_norm normalises lower taps."""
    cfg, pol = make(tiny_student, 'flow', taps=list(taps), tap_norm=norm)
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    with torch.no_grad():
        inputs = pol.inputs(batch)[0]
        ids, mask, tt, kw, _ = pol.backbone._inputs(batch, None)
        out = pol.backbone.inner(input_ids=ids, attention_mask=mask.long(), mm_token_type_ids=tt,
                                 output_hidden_states=True, **kw)
    ref = [out.hidden_states[2 if t == -1 else t] for t in taps]
    if norm:
        ref = [pol.backbone.language_model.norm(r) if t == 1 else r for t, r in zip(taps, ref)]
    got = inputs.tap_states if len(taps) > 1 else inputs.lm_states[None]
    torch.testing.assert_close(got, torch.stack(ref).float())


def test_bf16_student(tiny_student):
    cfg, pol = make(tiny_student.bfloat16(), 'flow', 'both')
    pol = pol.bfloat16()
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    batch['pixel_values'] = batch['pixel_values'].bfloat16()
    out = pol.loss(batch)
    assert torch.isfinite(out['loss'])
    out['loss'].backward()
    assert pol.eval().predict(batch).dtype == torch.float32  # heads return fp32 (schema 1)


def test_t8_taps_on_the_student(tiny_student):
    """T-8 on the real architecture (2 layers here, 32 in the 9B): 0 and L raise; tap l equals the
    forward-hook output of language_model.layers[l - 1]; -1 equals last_hidden_state."""
    for bad in ((0,), (2,), (3,), (-2,)):
        with pytest.raises(ValueError):
            StudentAdapter(tiny_student, taps=bad)
    seen = {}
    lm = tiny_student.model.language_model
    lm.layers[0].register_forward_hook(lambda m, a, out: seen.update(h=out[0] if isinstance(out, tuple) else out))
    adapter = StudentAdapter(tiny_student, taps=(1, -1)).eval()
    batch = student_batch(tiny_student, b=2, pad='left')
    with torch.no_grad():
        taps, _ = adapter.encode(batch)
        ref = tiny_student.model(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                                 pixel_values=batch['pixel_values'], image_grid_thw=batch['image_grid_thw'],
                                 mm_token_type_ids=(batch['input_ids'] == tiny_student.config.image_token_id).long())
    assert torch.equal(taps[0], seen['h']) and torch.equal(taps[1], ref.last_hidden_state)


def test_query_states_are_the_prompt_query_tokens(tiny_student):
    """Schema 1: the regression head reads tap -1 at the last K query-token positions of the prompt,
    whatever the padding side."""
    from vla_heads.testing import TINY_QUERY_ID
    cfg, pol = make(tiny_student, 'regression')
    for pad in ('right', 'left'):
        batch = full_batch(cfg, student_batch(tiny_student, b=2, pad=pad, chunk=cfg.chunk), 2)
        with torch.no_grad():
            inputs = pol.eval().inputs(batch)[0]
            taps, mask = pol.backbone.encode(batch)
        ids = pol.backbone.padded_ids(batch)
        for b in range(2):
            pos = (ids[b] == TINY_QUERY_ID).nonzero().flatten()[-cfg.chunk:]
            assert torch.equal(inputs.query_states[b], taps[-1][b, pos])
    batch = student_batch(tiny_student, b=2, chunk=cfg.chunk - 1)
    with pytest.raises(ValueError, match='query tokens'):
        pol.inputs(full_batch(cfg, batch, 2))


def test_lower_tap_is_differentiable(tiny_student):
    """Unlike the tree's grounding capture (grounding_features.py, detached), the adapter's lower tap
    carries gradient: a loss on tap 1 alone reaches layer 1's weights (layers[0]) and the embedding."""
    cfg, pol = make(tiny_student, 'flow', taps=[1, -1])
    tiny_student.zero_grad(set_to_none=True)
    batch = full_batch(cfg, student_batch(tiny_student, b=2), 2)
    inputs = pol.inputs(batch)[0]
    assert inputs.tap_states.requires_grad
    inputs.tap_states[0].float().pow(2).mean().backward()
    layer1 = pol.backbone.language_model.layers[0]
    assert sum(float(p.grad.abs().sum()) for p in layer1.parameters() if p.grad is not None) > 0
    later = pol.backbone.language_model.layers[1]
    assert all(p.grad is None or p.grad.abs().sum() == 0 for p in later.parameters())


def test_from_export_loads_the_student_weights(tmp_path):
    """B1 loader: the tree's own save_export writes a perturbed bf16 copy; from_export loads it exactly
    into a fresh base through full_ft.load_export (manifest-verified)."""
    from student_pilot import full_ft
    from vla_heads.testing import tiny_qwen35
    trained = tiny_qwen35(seed=31).bfloat16()
    with torch.no_grad():
        trained.model.language_model.layers[0].mlp.up_proj.weight.add_(1.0)
    names = [n for n, _ in full_ft.base_parameters(trained)]
    full_ft.save_export(full_ft.export_tensors(dict(trained.named_parameters()), names), tmp_path / 'full_weights',
                        {'name': 'tiny'}, {})
    base = tiny_qwen35(seed=31).bfloat16()
    cfg = small_config('flow')
    adapter = StudentAdapter.from_export(base, tmp_path / 'full_weights', cfg)
    for (n, p), (_, q) in zip(adapter.student.named_parameters(), trained.named_parameters()):
        assert torch.equal(p, q), n
