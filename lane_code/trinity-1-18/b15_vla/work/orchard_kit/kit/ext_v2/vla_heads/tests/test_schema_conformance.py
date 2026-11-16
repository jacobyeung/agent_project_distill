"""VLA_SCHEMA.md (vla_schema_v2) conformance tests owned by vla_heads: T-2 (the where encoder reads
examples 1-3), the head side of T-1 (the 36 numbers the regression head's where map receives) and
T-12 (example 7: action tokens). T-5 lives in test_tokens_actions.py, T-8 in test_heads.py and
test_student.py, T-9 in test_heads.py and test_training.py. Expected values come from the schema's
own generators (tests/fixtures/schema_v2/schema_examples.py, vendored by sha256)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from vla_heads import HeadInputs, where_features
from vla_heads.testing import build, full_batch, small_config, stub_batch

FIX = Path(__file__).parent / 'fixtures'
_spec = importlib.util.spec_from_file_location('schema_examples_v2', FIX / 'schema_v2' / 'schema_examples.py')
se = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(se)
assert se.SCHEMA == 'vla_schema_v2'

EX1_TARGET, EX1_PLACE = se.EX1_WHERE
EX3_TARGET, EX3_PLACE = se.EX3_WHERE
EXAMPLES = {  # example -> (where [2, 18] as the provider writes it, expected where_mask)
    1: ([EX1_TARGET, EX1_PLACE], [True, True]),
    2: ([[0] * 18, EX1_PLACE], [False, True]),   # cross_view: an invalid row is 18 zeros
    3: ([EX3_TARGET, EX3_PLACE], [True, True]),  # t = 0: valid, metric scale unknown (uv-only rows)
}


def batch_of_examples():
    where = torch.tensor([EXAMPLES[k][0] for k in (1, 2, 3)], dtype=torch.float32)
    mask = torch.tensor([EXAMPLES[k][1] for k in (1, 2, 3)])
    return where, mask


def test_t2_where_encoder_reads_examples_1_to_3():
    where, expect = batch_of_examples()
    feats, mask = where_features(where)
    assert torch.equal(mask, expect) and torch.equal(feats, where)
    # the no-scale rows keep cols 0-5 and an all-zero scale one-hot
    assert feats[2, :, 6:].abs().sum() == 0 and feats[2, :, :6].abs().sum() > 0 and mask[2].all()
    # a withheld chunk zeroes both rows and masks them; the other chunks are untouched
    feats, mask = where_features(where, withheld=torch.tensor([True, False, False]))
    assert not mask[0].any() and feats[0].abs().sum() == 0
    assert torch.equal(mask[1:], expect[1:]) and torch.equal(feats[1:], where[1:])
    # a caller's where_mask can only remove rows: valid = 0 stays masked
    feats, mask = where_features(where, where_mask=torch.ones(3, 2, dtype=torch.bool))
    assert torch.equal(mask, expect)


def test_t2_policy_passes_examples_to_the_head():
    """The policy's cond path hands the head exactly the example tensors and masks (evaluation mode,
    and a training batch whose every chunk is kept by the sha256 draw)."""
    from vla_heads import withheld_draw
    torch.manual_seed(0)
    cfg = small_config('regression', cond='spatial_readouts', where_dropout=0.2)
    pol = build(cfg)
    where, expect = batch_of_examples()
    seen = {}
    forward = pol.head.forward
    pol.head.forward = lambda inputs: seen.update(where=inputs.where, mask=inputs.where_mask) or forward(inputs)
    batch = full_batch(cfg, stub_batch(3), 3)
    batch['cond'] = {'where': where}
    pol.eval().predict(batch)
    assert torch.equal(seen['where'], where) and torch.equal(seen['mask'], expect)
    episode = 'libero_spatial/task03/demo_007'
    assert not withheld_draw(episode, 40)  # example 1's draw, 0.6110 >= 0.2
    batch['cond'] = {'where': where, 'episode': [episode] * 3, 't': [40] * 3}
    pol.train().loss(batch)
    assert torch.equal(seen['where'], where) and torch.equal(seen['mask'], expect)


def test_t1_regression_where_map_input():
    """Head side of T-1: the zero-initialised where map reads the two records flattened in entity
    order and multiplied by where_mask (36 numbers)."""
    cfg = small_config('regression', cond='spatial_readouts')
    from vla_heads import RegressionHead
    head = RegressionHead(cfg)
    assert head.where.in_features == 36
    seen = []
    head.where.register_forward_hook(lambda m, args, out: seen.append(args[0]))
    where, mask = batch_of_examples()
    inputs = HeadInputs(torch.randn(3, 5, 32), torch.ones(3, 5, dtype=torch.bool), torch.randn(3, cfg.chunk, 32),
                        proprio=torch.zeros(3, 8), where=where, where_mask=mask)
    head(inputs)
    expect = (where * mask[..., None]).flatten(1)
    assert torch.equal(seen[0], expect) and torch.equal(seen[0][1, :18], torch.zeros(18))


VLA_WHERE = Path('/scratch/jjyeung/orch_cd/vla_where/work/vla_where')


def test_t2_vla_where_records_match():
    """Cross-lane check (skips when vla_where is absent): vla_where's Entity records for examples 1-3
    are the vectors the encoder reads, with the same masks."""
    if not (VLA_WHERE / 'vla_where' / 'types.py').exists():
        pytest.skip('vla_where package not present')
    sys.path.insert(0, str(VLA_WHERE))
    try:
        from vla_where.types import Entity
    except Exception as exc:  # noqa: BLE001 - another lane's package; report and skip
        pytest.skip(f'vla_where.types does not import: {exc}')
    finally:
        sys.path.remove(str(VLA_WHERE))

    def ent(role, row, valid=True, metric=True):
        return Entity(role=role, presence=row[0], valid=valid, reason='ok', uv_agent=row[2:4], uv_wrist=row[4:6],
                      X_wrist=row[6:9] if metric else None, reach_base=row[9:12] if metric else None,
                      size=row[12:15] if metric else None, scale_source='proprio_handeye' if metric else None)
    records = [
        [ent('target', EX1_TARGET), ent('place', EX1_PLACE)],
        [Entity(role='target', reason='cross_view'), ent('place', EX1_PLACE)],
        [ent('target', EX3_TARGET, metric=False), ent('place', EX3_PLACE, metric=False)],
    ]
    vec = torch.from_numpy(np.array([[e.vector() for e in rec] for rec in records]))
    where, expect = batch_of_examples()
    torch.testing.assert_close(vec, where, atol=1e-6, rtol=0)
    assert torch.equal(where_features(vec)[1], expect)


# T-12 -------------------------------------------------------------------------------------------
RESERVED = FIX / 'reserved' / 'qwen35_9b_c2022362_rare_ids_1025.json'
FAST_FIXTURE = FIX / 'fast_fixture_v2' / 'fast_fixture_v2.json'
FIRST_ID, END_ID = 247019, 248043
EX7_FAST_BPE = [34, 362, 85, 199, 118, 123, 718, 54, 207]  # example 7 under fast_fixture_v2
EX7_FAST_LM_IDS = [247053, 247381, 247104, 247218, 247137, 247142, 247737, 247073, 247226, 248043]  # + the end id


def test_t12_bins_codes_and_ids():
    from vla_heads import UniformBins
    from vla_heads.codecs import reserved
    y = torch.from_numpy(se.example_chunk())[None]
    codes = UniformBins(8, 7, 256).encode(y)[0]
    assert codes == [168, 107, 46, 153, 128, 102, 255, 164, 109, 54, 151, 128, 104, 255, 160, 111, 62, 148, 128, 107,
                     255, 156, 113, 70, 145, 128, 110, 255, 152, 115, 78, 143, 128, 112, 0, 148, 117, 87, 140, 128, 115,
                     0, 144, 119, 95, 138, 128, 117, 0, 140, 121, 103, 135, 128, 120, 0]
    assert UniformBins(8, 7, 256).encode(y.float())[0] == codes  # fp32 gives the same codes
    ids = reserved.load_ids(RESERVED, 1025, '87a74b676da1fae8b6f94bbe77079ba0216bb7800b31f8f1d7566cab4e4c2860')
    assert ids == list(range(FIRST_ID, END_ID + 1))
    assert [ids[c] for c in codes[:7]] == [247187, 247126, 247065, 247172, 247147, 247121, 247274]
    with pytest.raises(ValueError):  # the pin is the ids' sha256, not the file bytes' (4493a6fc...)
        reserved.load_ids(RESERVED, 1025, '4493a6fc5b79ded93aae8a8b2e9422d15df3d333c166f17cc597ae85c2d5320e')


def test_t12_digits_text():
    from vla_heads import CharTokenizer, DigitsCodec
    codec = DigitsCodec(8, 7, CharTokenizer(alphabet='0123456789 '))
    text = codec.text(torch.from_numpy(se.example_chunk())[None])[0]
    assert text == ('660 420 180 600 500 400 1000 644 428 212 590 500 410 1000 628 436 244 580 500 420 1000 612 444 276 '
                    '570 500 430 1000 596 452 308 560 500 440 0 580 460 340 550 500 450 0 564 468 372 540 500 460 0 548 '
                    '476 404 530 500 470 0')
    y, ok = codec.parse(text)
    assert ok and (y - torch.from_numpy(se.example_chunk()).float()).abs().max() <= 1e-3
    for bad in (text + ' 5', text.replace(' 0', ' -0', 1), text.replace(' ', '  ', 1), text + ',', '1001 ' + text[4:]):
        assert not codec.parse(bad)[1], bad


def test_t12_fast_fixture_and_example_chunk():
    import hashlib
    from vla_heads import FastCodec
    assert hashlib.sha256(FAST_FIXTURE.read_bytes()).hexdigest() == 'cab2442cc376ab1ee68f13097bce41462b2db0d1655152a086a04df3e00352b5'
    codec = FastCodec(8, 7, 1024, 10.0, path=str(FAST_FIXTURE))
    assert (codec.processor.min_token, codec.max_token) == (-28, 28)
    refit = FastCodec(8, 7, 1024, 10.0).fit(se.fast_fixture_chunks())  # the fixture is the reference's fit
    assert refit.sha256 == codec.sha256
    y = se.example_chunk()[None]
    want = [0] * 56
    for i, v in {0: 6, 1: -3, 2: -12, 3: 4, 5: -4, 7: 2, 8: -1, 9: -4, 10: 1, 12: -1, 13: 26, 27: -9, 41: 6, 55: -5}.items():
        want[i] = v
    assert codec.integers(y)[0].astype(int).tolist() == want
    seq = codec.encode(y)[0]
    assert seq == EX7_FAST_BPE and [FIRST_ID + s for s in seq] + [END_ID] == EX7_FAST_LM_IDS
    assert codec.symbol_integers(seq) == want  # encode then decode recovers the 56 integers exactly
    dec, ok = codec.decode([seq])
    assert ok[0] and np.abs(dec[0].numpy() - y[0]).max() <= 0.0361 + 1e-4
    assert max(seq) < 1024


@pytest.mark.parametrize('codec_name', ['fast', 'bins'])
def test_t12_bound_ids_and_malformed_rows(tiny_student, codec_name):
    """On the real vocabulary: every bound LM id lies in 247019..248043 (FAST end = 248043), and a row
    that does not decode to [8, 7] returns zeros with last_ok False."""
    from vla_heads import FastCodec, HeadInputs
    cfg = small_config('tokens', chunk=8, tok_codec=codec_name, tok_bins=256, tok_vocab=1024, tok_dct_scale=10.0,
                       tok_ids=str(RESERVED), tok_ids_sha256='87a74b676da1fae8b6f94bbe77079ba0216bb7800b31f8f1d7566cab4e4c2860',
                       tok_max_tokens=64)
    codec = FastCodec(8, 7, 1024, 10.0, path=str(FAST_FIXTURE)) if codec_name == 'fast' else None
    pol = build(cfg, 'student', tiny_student, codec=codec)
    ids = pol.head.binding.ids.tolist()
    assert ids[0] == FIRST_ID and all(FIRST_ID <= i <= END_ID for i in ids)
    if codec_name == 'fast':
        assert len(ids) == 1025 and ids[pol.head.end] == END_ID
    else:
        assert ids == list(range(FIRST_ID, FIRST_ID + 256))
    head = pol.head
    d = cfg.hidden_size
    end = head.end if head.variable else 0

    class Script:  # a decoder whose states make the head emit a fixed symbol script
        def __init__(self, script):
            self.script, self.i = script, 0

        def __call__(self, new):
            sym = self.script[min(self.i, len(self.script) - 1)]
            self.i += 1
            return torch.full((1, d), float(sym))

    head._binding = [type('B', (), {'ids': torch.tensor(ids),
                                    'row_logits': staticmethod(lambda states, rows: torch.nn.functional.one_hot(
                                        states[:, 0].long(), len(rows)).float())})()]
    bad = [end] if codec_name == 'fast' else [0] * 56  # FAST: end at once (0 integers); bins: always well formed
    script = bad if codec_name == 'fast' else [0] * 56
    out = head.predict(HeadInputs(torch.zeros(1, 1, d), torch.ones(1, 1, dtype=torch.bool), decoder=Script(script)))
    if codec_name == 'fast':
        assert not head.last_ok[0] and out.abs().sum() == 0
    else:
        assert head.last_ok[0] and out.shape == (1, 8, 7)
