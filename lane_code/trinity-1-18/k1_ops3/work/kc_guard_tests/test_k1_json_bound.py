"""Compare the K1 candidate reader to the frozen reader on pinned primary inputs."""
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'kc_guard/k1_build/work/kit_k1a/work'
sys.path.insert(0, str(WORK))
import k1_pipeline as K
K._native()
B = K.B
OUT = ROOT / 'patch4_json_bound'
OUT.mkdir()
start = time.monotonic()
m = B.load(ROOT.parent / 'manifest_v2/a40fbc19.json')
captures, _ = K.G.select(m, K.G.load(ROOT.parent / 'gt_sets/GT_SET_PRIMARY_296.json'))
evidence = []
for i, c in enumerate(captures):
    dest = Path('/scratch/jjyeung/k1/run_convert_2') / B.digest(c['canonical'])[:16]
    receipt = B.load(dest / 'CACHE_COMPLETE.json')
    p = B.checked(receipt['files']['candidates.json'])
    assert p == dest / 'candidates.json'
    actual = K.load_candidates(p)
    small = p.stat().st_size <= 20_000_000
    if small:
        assert actual == B.load(p), c['canonical']
    else:
        assert actual == json.loads(p.read_text()), c['canonical']
    evidence.append(dict(canonical=c['canonical'], bytes=p.stat().st_size,
                         sha256=receipt['files']['candidates.json']['sha256'],
                         frozen_reader_equal=small, loaded=True))
    if (i + 1) % 50 == 0:
        print(f'Compared {i + 1}/{len(captures)} captures', flush=True)
assert sum(x['frozen_reader_equal'] for x in evidence) == 284
assert sum(not x['frozen_reader_equal'] for x in evidence) == 12

# Compare accepted values and exact exception types/messages for parser edge cases.
cases = [b'{"x":1,"x":2}', b'[NaN,Infinity,-Infinity]',
         '{"unicode":"caf\u00e9"}'.encode(), b'{\r\n"x": 1\r\n}',
         b'\xef\xbb\xbf{}', b'\xff', b'{', b'{} {}']
def outcome(loader, p):
    try:
        return ('value', json.dumps(loader(p), sort_keys=True))
    except Exception as error:
        return ('error', type(error).__name__, str(error))
for i, payload in enumerate(cases):
    p = OUT / f'parser_{i}.json'
    p.write_bytes(payload)
    assert outcome(K.load_candidates, p) == outcome(B.load, p)

# Valid JSON at the inclusive boundary; one MiB more must fail before reading.
p = OUT / 'synthetic_65mib.json'
with p.open('xb') as stream:
    stream.write(b'0')
    chunk = b' ' * (1024 * 1024)
    for _ in range(63):
        stream.write(chunk)
    stream.write(chunk[:-1])
assert p.stat().st_size == K.JSON_BOUND_BYTES
assert K.load_candidates(p) == 0
with p.open('ab') as stream:
    stream.write(chunk)
assert p.stat().st_size == 65 * 1024 * 1024
with patch.object(Path, 'read_text', side_effect=AssertionError('Oversized input read')):
    try:
        K.load_candidates(p)
    except ValueError as error:
        assert str(error) == 'Metadata exceeds bounded reader'
    else:
        raise AssertionError('65 MiB input accepted')

# An authentication failure must prevent the local candidate parser from running.
c = captures[0]
dest = Path('/scratch/jjyeung/k1/run_convert_2') / B.digest(c['canonical'])[:16]
with patch.object(B, 'checked', side_effect=ValueError('Input hash mismatch: fixture')), \
        patch.object(K, 'load_candidates') as loader:
    try:
        K.cached(c, dest)
    except ValueError as error:
        assert str(error) == 'Input hash mismatch: fixture'
    else:
        raise AssertionError('Pin failure accepted')
    loader.assert_not_called()
summary = dict(primary_captures=len(evidence), equal_to_bindings_load=284,
               large_files_loaded=12, max_bytes=max(x['bytes'] for x in evidence),
               json_bound_bytes=K.JSON_BOUND_BYTES, inclusive_64mib_accepted=True,
               synthetic_65mib_refused_before_read=True, parser_cases_equal=len(cases),
               pin_check_precedes_loader=True, runtime_seconds=time.monotonic()-start)
(ROOT / 'patch4_json_bound.json').write_text(json.dumps(dict(summary=summary, captures=evidence), indent=2)+'\n')
print(json.dumps(summary), flush=True)
