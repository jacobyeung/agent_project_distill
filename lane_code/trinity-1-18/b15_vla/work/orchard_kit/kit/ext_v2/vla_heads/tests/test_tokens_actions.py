"""Codec round trips, constrained decoding, normalisation, gripper, chunking, ensembling, proprio."""
import json
import math

import numpy as np
import pytest
import torch

from vla_heads import (CharTokenizer, ChunkExecutor, DCTCodec, DigitsCodec, FastCodec, Normalizer, ProprioEncoder,
                       TemporalEnsembler, UniformBins, gripper_command, gripper_from_unit, gripper_to_unit, make_chunks,
                       nav_text, reserved)
from vla_heads.codecs import dct_matrix
from vla_heads.testing import build, full_batch, small_config, stub_batch


def smooth_chunks(n, k=8, a=7, seed=0):
    g = torch.Generator().manual_seed(seed)
    s = torch.linspace(0, 1, k)[None, :, None]
    return (0.6 * torch.sin(2 * s * (1 + torch.rand(n, 1, a, generator=g)) + torch.rand(n, 1, a, generator=g) * 6)).clamp(-1, 1)


def test_uniform_bins_round_trip_bound():
    codec = UniformBins(chunk=8, action_dim=7, bins=256)
    x = torch.rand(64, 8, 7) * 2 - 1
    x[0, 0, :3] = torch.tensor([-1.0, 1.0, 0.0])
    seqs = codec.encode(x)
    assert len(seqs) == 64 and all(len(s) == 56 and 0 <= min(s) and max(s) <= 255 for s in seqs)
    y, ok = codec.decode(seqs)
    assert ok.all() and (y - x).abs().max() <= codec.error_bound() + 1e-6 and codec.error_bound() == 1 / 256
    _, ok = codec.decode([seqs[0][:10]])
    assert not ok[0]


def test_dct_matrix_orthonormal():
    m = dct_matrix(8, torch.float64)
    torch.testing.assert_close(m @ m.T, torch.eye(8, dtype=torch.float64))


@pytest.mark.parametrize('scale', [10.0, 50.0])
def test_dct_round_trip_bound(scale):
    codec = DCTCodec(chunk=8, action_dim=7, scale=scale)
    x = torch.rand(64, 8, 7) * 2 - 1
    y, ok = codec.decode(codec.encode(x))
    assert ok.all() and (y - x).abs().max() <= codec.error_bound() + 1e-6


def test_fast_bpe_round_trip_and_compression(tmp_path):
    train = smooth_chunks(400)
    codec = FastCodec(chunk=8, action_dim=7, vocab=600, scale=10.0).fit(train)
    assert codec.processor.min_token < 0
    test = smooth_chunks(50, seed=1)
    seqs = codec.encode(test)
    y, ok = codec.decode(seqs)
    assert ok.all() and (y - test).abs().max() <= codec.error_bound() + 1e-6
    assert np.mean([len(s) for s in seqs]) < 0.8 * 56  # BPE shortens the 56-integer stream
    assert max(max(s) for s in seqs) < 600
    path = tmp_path / 'fast.json'
    sha = codec.save(path)
    back = FastCodec(chunk=8, action_dim=7, vocab=600, scale=10.0, path=str(path))
    assert back.sha256 == sha and back.encode(test) == seqs
    with pytest.raises(ValueError):
        FastCodec(chunk=8, action_dim=7, vocab=600, scale=20.0, path=str(path))
    bad, ok = codec.decode([seqs[0][:-2], []])  # a truncated or empty stream decodes to zeros, flagged not ok
    assert not ok.any() and bad.abs().sum() == 0


def test_fast_matches_reference_stream():
    """FastCodec calls physical-intelligence/fast's processor (vendored, sha-pinned): on one fit the
    token stream, the tokenizer and the decoded chunks equal an independently imported copy's."""
    import hashlib
    import importlib.util
    from pathlib import Path
    from vla_heads.codecs import fast as fast_mod
    fix = Path(__file__).parent / 'fixtures' / 'fast_reference' / 'processing_action_tokenizer.py'
    pkg = Path(fast_mod.__file__).with_name('fast_reference.py')
    assert hashlib.sha256(fix.read_bytes()).hexdigest() == hashlib.sha256(pkg.read_bytes()).hexdigest() == fast_mod.REFERENCE_SHA256
    spec = importlib.util.spec_from_file_location('fast_ref_fixture', fix)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    train, test = smooth_chunks(300), smooth_chunks(40, seed=2)
    ref = mod.UniversalActionProcessor.fit([a for a in train.double().numpy()], scale=10, vocab_size=1024)
    ours = FastCodec(chunk=8, action_dim=7, vocab=1024, scale=10.0).fit(train)
    assert ours.processor.bpe_tokenizer.backend_tokenizer.to_str() == ref.bpe_tokenizer.backend_tokenizer.to_str()
    assert ours.processor.min_token == ref.min_token
    seqs = ours.encode(test)
    assert seqs == [list(map(int, t)) for t in ref(test.double().numpy())]
    y, ok = ours.decode(seqs)
    assert ok.all() and np.allclose(y.numpy(), ref.decode(seqs, time_horizon=8, action_dim=7), atol=1e-6)
    from vla_heads.config import FAST_REFERENCE
    assert FAST_REFERENCE.endswith('@ec4d7aa71691cac0b8bed6942be45684db2110f4') and ours.reference == FAST_REFERENCE


def test_digits_codec_round_trip():
    tok = CharTokenizer()
    codec = DigitsCodec(chunk=4, action_dim=7, tokenizer=tok)
    x = torch.rand(5, 4, 7) * 2 - 1
    y, ok = codec.decode(codec.encode(x))
    assert ok.all() and (y - x).abs().max() <= codec.error_bound() + 1e-6
    assert codec.text(torch.full((1, 4, 7), -1.0))[0].startswith('0 0')
    assert not codec.parse('12 13')[1]


def test_nav_grammar_v1():
    """Schema 8.1 and example 4: the nav and click arms accept and reject the stated strings."""
    p = nav_text.parse
    assert nav_text.GRAMMAR == 'nav_grammar_v1'
    acts = p('forward 0.50, turn_left 30', 'nav')
    assert acts == ['forward 0.50', 'turn_left 30'] and nav_text.nav_text(acts) == 'forward 0.50, turn_left 30'
    assert nav_text.primitives(acts) == ['forward', 'forward', 'turn_left', 'turn_left']
    assert nav_text.primitives(p('turn_right 45, forward 0.75, stop', 'nav')) == ['turn_right'] * 3 + ['forward'] * 3 + ['stop']
    assert p('<think>go left?</think>\n forward 0.25 ', 'nav') == ['forward 0.25']
    for bad in ('forward 0.40', 'forward 0.5', 'forward 0.6', 'jump 1', 'stop, forward 0.25', '', 'turn_left 90',
                'forward 0.25,forward 0.25', 'forward 0.25, forward 0.25, forward 0.25, stop', 'Forward 0.25',
                '<goal frame=32 x=0.62 y=0.81>'):
        assert p(bad, 'nav') is None, bad
    click = p('<goal frame=32 x=0.62 y=0.81>', 'click', history_frames=32)
    assert click == nav_text.Click(32, 0.62, 0.81) and click.text() == '<goal frame=32 x=0.62 y=0.81>'
    assert p('<goal frame=32 x=0.50 y=0.99>', 'click', 32) == nav_text.Click(32, 0.5, 0.99)
    assert p('turn_left 90', 'click') == 'turn_left 90' and p('stop', 'click') == 'stop'
    assert nav_text.primitives('turn_left 90') == ['turn_left'] * 6
    assert nav_text.primitives('turn_right 90') == ['turn_right'] * 6
    assert nav_text.primitives('turn_around') == ['turn_left'] * 12 and nav_text.primitives('stop') == ['stop']
    for bad in ('<goal frame=31 x=0.62 y=0.81>', '<goal frame=32 x=1.01 y=0.81>', '<goal frame=32 x=0.6 y=0.81>',
                '<goal frame=32 x=0.62 y=0.81> stop', 'forward 0.25', 'turn_left 45', '<goal frame=32 x=-0.10 y=0.5>'):
        assert p(bad, 'click', history_frames=32) is None, bad
    assert nav_text.FALLBACK == ('turn_left',)
    with pytest.raises(ValueError):
        nav_text.primitives(click)


def test_nav_constrained_decoding_trie():
    """The arm's finite language as a token trie: every accepted string, nothing else, ends with the end id."""
    tok = CharTokenizer(alphabet='abcdefghijklmnopqrstuvwxyz_0123456789 .,<>=/')
    nav = nav_text.allowed_strings('nav')
    clicks = nav_text.allowed_strings('click', history_frames=32)
    assert len(nav) == len(set(nav)) == 910 and len(clicks) == len(set(clicks)) == 10205
    assert all(nav_text.parse(s, 'nav') is not None for s in nav)
    assert all(nav_text.parse(s, 'click', 32) is not None for s in clicks[::97] + clicks[-4:])
    trie = nav_text.constraint(tok, 'nav', end_id=999)
    assert len(nav_text.constraint(tok, 'click', 32, end_id=999).allowed(tok.encode('<goal frame=32 x=0.6'))) == 10
    gen, rng = [], np.random.default_rng(0)
    for _ in range(50):  # random walks through the trie always yield grammatical strings
        ids = []
        while True:
            allowed = trie.allowed(ids)
            nxt = int(rng.choice(allowed))
            if nxt == trie.end_id:
                break
            ids.append(nxt)
        gen.append(tok.decode(ids))
    assert all(nav_text.parse(s, 'nav') is not None for s in gen)
    assert trie.allowed(tok.encode('forward 0.4', add_special_tokens=False)) == []
    fn = nav_text.prefix_allowed_tokens_fn(trie, prompt_len=2)
    assert fn(0, torch.tensor([5, 6] + tok.encode('stop', add_special_tokens=False))) == [trie.end_id]


def test_rare_ids(tmp_path):
    class Tok:
        vocab_size = 40
        all_special_ids = [39]
        added_tokens_decoder = {38: '<x>'}

        def decode(self, ids):
            i = ids[0]
            return str(i) if i % 3 == 0 else ' ' if i == 37 else 'tok' + chr(65 + i % 26)

        def __len__(self):
            return 40
    ids = reserved.rare_ids(Tok(), 5)
    assert ids == [29, 31, 32, 34, 35]  # 39 special, 38 added, 37 blank, 36 / 33 / 30 hold digits
    path = tmp_path / 'ids.json'
    reserved.save_ids(path, ids, 'toy')
    assert reserved.load_ids(path, 5) == ids
    meta = json.loads(path.read_text())
    meta['ids'][0] = 30
    path.write_text(json.dumps(meta))
    with pytest.raises(ValueError):
        reserved.load_ids(path)


def fitted_fast(cfg):
    return FastCodec(cfg.chunk, cfg.action_dim, cfg.tok_vocab, 20.0).fit(smooth_chunks(200, cfg.chunk, cfg.action_dim))


@pytest.mark.parametrize('codec_name', ['bins', 'dct', 'fast'])
def test_teacher_forced_states_equal_decoded_states(codec_name):
    """query_states[:, j] in training equals the decoder's state after symbols < j (no exposure gap)."""
    torch.manual_seed(0)
    cfg = small_config('tokens', cond='both', tok_codec=codec_name, tok_dct_scale=20.0)
    codec = fitted_fast(cfg) if codec_name == 'fast' else None
    pol = build(cfg, codec=codec).eval()
    batch = full_batch(cfg, stub_batch(3), 3)
    with torch.no_grad():
        inputs, (_, (sym, mask)) = pol.inputs(batch, batch['actions'])
        ids = pol.head.token_ids(sym)
        dec = pol.backbone.decoder(batch, pol.prefix(batch)[0])
        states = [dec(None)] + [dec(ids[:, j]) for j in range(ids.shape[1] - 1)]
    torch.testing.assert_close(torch.stack(states, 1), inputs.query_states, atol=1e-5, rtol=1e-5)
    if codec_name == 'fast':
        assert pol.head.variable and (sym == pol.head.end).any() and not mask.all()


def test_constrained_decoding_emits_only_codec_ids():
    torch.manual_seed(0)
    cfg = small_config('tokens', tok_codec='bins')
    pol = build(cfg).eval()
    batch = full_batch(cfg, stub_batch(3), 3)
    seen = []
    step = pol.backbone.decoder

    def spy(*a, **k):
        inner = step(*a, **k)
        return lambda ids: (seen.append(ids) if ids is not None else None) or inner(ids)
    pol.backbone.decoder = spy
    pred = pol.predict(batch)
    allowed = set(pol.head.binding.ids.tolist())
    assert seen and all(set(s.tolist()) <= allowed for s in seen) and pol.head.last_ok.all()
    assert pred.shape == (3, cfg.chunk, cfg.action_dim)


def test_digits_head_through_text_tokenizer():
    """The digits codec writes real text ids (a char tokenizer standing in for the LM's) and ends with eos."""
    class Tok(CharTokenizer):
        eos_token_id = 63
    torch.manual_seed(0)
    cfg = small_config('tokens', tok_codec='digits', chunk=2, action_dim=3, tok_max_tokens=40, proprio_dim=0)
    pol = build(cfg, tokenizer=Tok(offset=40))
    batch = full_batch(cfg, stub_batch(2), 2)
    out = pol.loss(batch)
    assert torch.isfinite(out['loss'])
    assert pol.head.binding.ids.tolist()[-1] == 63 and min(pol.head.binding.ids.tolist()) >= 40
    pred = pol.eval().predict(batch)
    assert pred.shape == (2, 2, 3)


def test_normalizer_round_trip_and_json(tmp_path):
    g = torch.Generator().manual_seed(0)
    data = torch.randn(1000, 7, generator=g) * torch.tensor([0.3, 0.3, 0.3, 0.1, 0.1, 0.1, 1.0])
    data[:, 6] = torch.where(data[:, 6] > 0, 1.0, -1.0)
    norm = Normalizer.fit(data, dims=6, subset_sha='abc')
    path = tmp_path / 'norm.json'
    norm.save(path)
    meta = json.loads(path.read_text())
    assert set(meta) == {'kind', 'min', 'max', 'count', 'subset_sha'}
    assert meta['kind'] == 'minmax_subset_v1' and meta['count'] == 1000 and meta['subset_sha'] == 'abc'
    assert len(meta['min']) == len(meta['max']) == 6
    back = Normalizer.load(path)
    y = back.normalize(data.double())
    assert y[:, :6].abs().max() <= 1 + 1e-12 and torch.equal(y[:, 6], data[:, 6].double())
    assert torch.allclose(back.denormalize(y), data.double(), atol=1e-12)  # exact inside the training range
    flat = Normalizer([0.0, 2.0], [1.0, 2.0])
    np.testing.assert_allclose(flat.normalize(np.array([0.5, 2.0])), [0.0, 0.0])
    np.testing.assert_allclose(flat.denormalize(np.array([0.0, 0.3])), [0.5, 2.0])
    with pytest.raises(ValueError):
        Normalizer.from_dict(dict(meta, kind='percentile_minmax_v1'))


def test_t5_action_normalisation_and_gripper():
    """T-5, schema example 5: the round trip, the evaluation clip and the IPEC gripper map."""
    lo = [-0.9375, -0.9375, -0.9375, -0.1875, -0.1875, -0.375]
    norm = Normalizer(lo, [-v for v in lo])
    raw = np.array([0.30, -0.15, -0.60, 0.0375, 0.0, -0.075])
    g = gripper_to_unit(0.0, 'ipec')
    assert g == 1.0  # a6 = 0 (IPEC close) -> +1 close
    y = norm.normalize(np.concatenate([raw, [g]]))
    np.testing.assert_allclose(y, [0.32, -0.16, -0.64, 0.20, 0.00, -0.20, 1.0], atol=1e-12)
    np.testing.assert_allclose(norm.denormalize(y), np.concatenate([raw, [g]]), atol=1e-12)
    pred = np.array([1.30, -0.16, -0.64, 0.20, 0.00, -0.20, -0.83])
    x = norm.denormalize(pred)
    np.testing.assert_allclose(x[:6], [0.9375, -0.15, -0.60, 0.0375, 0.0, -0.075], atol=1e-12)
    assert gripper_command(x[6]) == -1.0  # -0.83 < 0: open
    assert gripper_command(0.0) == 1.0 and gripper_command(0.40) == 1.0  # the tie g = 0 closes (StarVLA)
    # IPEC a6 = 1 (open) gives g = -1; the map inverts; closed never becomes 0.
    a6 = torch.tensor([0.0, 1.0])
    assert torch.equal(gripper_to_unit(a6, 'ipec'), torch.tensor([1.0, -1.0]))
    assert torch.equal(gripper_from_unit(gripper_to_unit(a6, 'ipec'), 'ipec'), a6)
    assert torch.equal(gripper_to_unit(torch.tensor([-1.0, 1.0]), 'unit_open_neg'), torch.tensor([-1.0, 1.0]))
    gs = torch.tensor([-1.0, 1.0, 0.3, -0.2, 0.0, -1e-7])
    assert torch.equal(gripper_command(gs), torch.tensor([-1.0, 1.0, 1.0, -1.0, 1.0, -1.0]))
    # StarVLA's client: env = 1 - 2 [a6 > 0.5] with a6 = (1 - g) / 2 equals gripper_command for every g, ties included.
    starvla = 1 - 2 * (gripper_from_unit(gs.double(), 'ipec') > 0.5).double()
    assert torch.equal(starvla.float(), gripper_command(gs))
    with pytest.raises(ValueError):
        gripper_to_unit(a6, 'open_value_1')


def test_proprio_normalisation_example1():
    """Schema example 1: synthetic proprio statistics and the t = 40 proprio; evaluation clips."""
    norm = Normalizer([-0.30, -0.40, 0.85, 2.80, -0.60, -0.60, 0.00, -0.04], [0.70, 0.40, 1.45, 3.30, 0.60, 0.60, 0.04, 0.00])
    p = np.array([0.50, 0.00, 1.20, 3.141593, 0.0, 0.0, 0.039, -0.039])
    np.testing.assert_allclose(norm.normalize(p, clip=True), [0.6, 0.0, 0.166667, 0.366372, 0, 0, 0.95, -0.95], atol=1e-6)
    assert norm.normalize(np.array([9.0] * 8), clip=True).max() == 1.0


def test_make_chunks():
    a = torch.arange(10, dtype=torch.float32)[:, None].repeat(1, 7)
    c, m = make_chunks(a, 4)
    assert c.shape == (10, 4, 7) and m.shape == (10, 4)
    assert torch.equal(c[2, :, 0], torch.tensor([2.0, 3, 4, 5]))
    assert torch.equal(c[8, :, 0], torch.tensor([8.0, 9, 9, 9])) and m[8].tolist() == [True, True, False, False]


def test_temporal_ensembler_matches_act_weights():
    k, m = 4, 0.5
    ens = TemporalEnsembler(k, m=m)
    chunks = [torch.full((k, 2), float(i)) + torch.arange(k)[:, None] * 10 for i in range(6)]
    outs = [ens.update(c) for c in chunks]
    preds = torch.tensor([i + 10.0 * (5 - i) for i in range(2, 6)], dtype=torch.float64)
    w = torch.exp(-m * torch.arange(4, dtype=torch.float64))
    assert math.isclose(outs[5][0].item(), ((preds * w).sum() / w.sum()).item(), rel_tol=1e-6)
    assert outs[0][0].item() == 0.0
    ens.reset()
    assert ens.update(chunks[3])[0].item() == 3.0


def test_chunk_executor_replans():
    ex = ChunkExecutor(replan=2)
    played = []
    for step in range(5):
        chunk = torch.arange(4)[:, None].float() + 100 * step if ex.needs_query() else None
        played.append(ex.update(chunk)[0].item())
    assert played == [0.0, 1.0, 200.0, 201.0, 400.0]


def test_proprio_encoder():
    enc = ProprioEncoder(8, 32)
    assert enc(torch.randn(3, 8)).shape == (3, 1, 32)
    assert enc.bfloat16()(torch.randn(3, 8)).dtype == torch.bfloat16


def test_dct_integers_match_official_fast_formula():
    """The fixed-length `dct` codec uses FAST's integer formula: round(scale * scipy.fft.dct(chunk,
    axis=time, norm='ortho')) flattened [K, A] row-major (frequency-major), with a symmetric clip in
    place of FAST's fitted minimum. (`fast` itself calls the reference; see test_fast_matches_reference_stream.)"""
    scipy_fft = pytest.importorskip('scipy.fft')
    x = smooth_chunks(16)
    codec = DCTCodec(chunk=8, action_dim=7, scale=10.0, clip=127)
    ref = np.around(scipy_fft.dct(x.double().numpy(), axis=1, norm='ortho') * 10.0).reshape(16, -1)
    assert np.array_equal(codec.ints(x).numpy(), ref.astype(np.int64))
    back = scipy_fft.idct(ref.reshape(16, 8, 7) / 10.0, axis=1, norm='ortho')
    y, ok = codec.from_ints(ref.astype(int).tolist())
    assert ok.all() and np.allclose(y.numpy(), back, atol=1e-6)


def test_warmup_cosine_ends_inside_the_run():
    from vla_heads import warmup_cosine
    f = warmup_cosine(300)
    assert f.warmup == 9 and f(0) == 1 / 9 and f(8) == 1.0 and abs(f(299)) < 1e-3
    assert warmup_cosine(10000).warmup == 300 and warmup_cosine(1000).warmup == 30
    with pytest.raises(ValueError):
        warmup_cosine(300, 500)
