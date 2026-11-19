"""Registration record for out/BARS.json (bash run.sh registration.py), per review sb_phrev finding 1.

The bars file was written after the first scores existed, so it carries written_before_any_score = false and no
pre-score certification. It records instead where the numeric bars already stood: the design lane's spec, first version
(in/) and v2 (in/v2), with sha256 and mtime, beside the mtimes of the earliest score files, for the reader to judge.
Every other field of the bars file stays equal to the version the arms were priced under (sha256 150d16a2...)."""
import datetime, gzip, hashlib, json, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path('/scratch/jjyeung/orch_n30/sb_mask_phrase')
REVIEW = Path('/scratch/jjyeung/orch_n30/sb_phrev/REVIEW_VERDICT.md')
BARS, BARS_SHA = HERE/'out/BARS.json', HERE/'work/BARS.sha256'
ORIGINAL = HERE/'work/orig_out/BARS_150d16a2.json'
ORIGINAL_SHA = '150d16a232b42d86b33c6df792133f3a001d92f7b3b723c96dfc3391f0f17bc6'
STATUS = 'diagnostic pending orchestrator ruling on registration'
SPECS = {'in/KIT_SPEC_mask_phrase.md': ('first version', 'P_cf', ('phrase_worth', 'phrase_safe')),
         'in/v2/KIT_SPEC_mask_phrase.md': ('v2, the version the bars file names as governing', 'W_cf', ('phrase_worth', 'phrase_safe'))}
SCORE_GLOBS = ('work/caps/*.json.gz', 'work/caps2/*.json.gz', 'work/stale_v1_out/*.json*', 'out/PER_ITEM.jsonl', 'out/DECISION.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(ns):
    return datetime.datetime.fromtimestamp(ns/1e9, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'


def times(path):
    st = os.stat(path)
    return dict(mtime_utc=utc(st.st_mtime_ns), ctime_utc=utc(st.st_ctime_ns))


def spec_record(rel, version, arm, bars):
    src, copy = SOURCE/rel, HERE/rel
    assert sha(src) == sha(copy) and os.stat(src).st_mtime_ns == os.stat(copy).st_mtime_ns, rel
    lines = src.read_text().splitlines()
    quoted = {b: next(f'line {i+1}: {t.strip()}' for i, t in enumerate(lines) if t.lstrip().startswith(f'- `{b}`')) for b in bars}
    assert '+1.5' in quoted['phrase_worth'] and 'lower bound above 0' in quoted['phrase_worth'], quoted
    assert 'lower bound above -1.0' in quoted['phrase_safe'], quoted
    return dict(path=str(src), version=version, sha256=sha(src), mtime_utc=times(src)['mtime_utc'], arrived_in_lane_utc=times(src)['ctime_utc'],
                bars_apply_to=arm, bar_lines=quoted)


def priced(path):
    """True when the file holds row predictions with their labels (a score can be read from it)."""
    if path.suffix == '.gz':
        items = json.loads(gzip.decompress(path.read_bytes())).get('items', [])
        return any('prediction' in it and 'label' in it for it in items)
    if path.name == 'PER_ITEM.jsonl':
        with path.open() as f:
            first = json.loads(f.readline())
        return 'prediction' in first and 'label' in first
    arms = json.loads(path.read_text()).get('arms', {})
    return any(isinstance(v, dict) and v.get('mra') is not None for v in arms.values())


def earliest_scores():
    files = sorted((p for g in SCORE_GLOBS for p in SOURCE.glob(g)), key=lambda p: os.stat(p).st_mtime_ns)
    first = next(p for p in files if priced(p))
    aggregate = next(p for p in files if p.suffix != '.gz' and priced(p))
    return (dict(path=str(first), mtime_utc=times(first)['mtime_utc'], holds='per-row predictions with labels (the stopped session\'s v1 capture files)'),
            dict(path=str(aggregate), mtime_utc=times(aggregate)['mtime_utc'], holds='arm MRA and contrasts (the stopped session\'s v1 aggregate)'))


def main():
    assert sha(ORIGINAL) == ORIGINAL_SHA == sha(SOURCE/'out/BARS.json')
    original = json.loads(ORIGINAL.read_text())
    first, aggregate = earliest_scores()
    specs = {rel: spec_record(rel, *v) for rel, v in SPECS.items()}
    registration = dict(
        status=STATUS,
        written_before_any_score=False,
        finding=('Review sb_phrev finding 1: score files existed before this bars file, so it is not a pre-score registration. '
                 'A later hash check shows only that the file did not change after it was written.'),
        numeric_bars=('phrase_worth: arm minus A0 >= +1.5 type points with 95% lower bound > 0; phrase_safe: 95% lower bound > -1.0 on the rows '
                      'whose two operands are good under A0. Both thresholds appear in the design lane\'s spec in both versions below; '
                      'the first version applies them to P_cf, v2 to the cross-fitted W arm.'),
        spec=specs,
        earliest_score_file=first,
        earliest_aggregate_score_file=aggregate,
        bars_file=dict(path=str(SOURCE/'out/BARS.json'), sha256=ORIGINAL_SHA, written_utc=original['written_utc'],
                       mtime_utc=times(SOURCE/'out/BARS.json')['mtime_utc']),
        changed_fields=['written_before_any_score', 'registration'],
        unchanged='every other field equals the bars file the arms were priced under (sha256 150d16a2...): bars, arms, fold rule, guards, decision',
        review=dict(path=str(REVIEW), sha256=sha(REVIEW)))
    bars = dict(original, written_before_any_score=False, registration=registration)
    assert {k: v for k, v in bars.items() if k not in registration['changed_fields']} == \
        {k: v for k, v in original.items() if k not in registration['changed_fields']}
    if BARS.exists():
        BARS.chmod(0o644)
    BARS.write_text(json.dumps(bars, indent=1, ensure_ascii=False)+'\n')
    BARS.chmod(0o444)
    BARS_SHA.write_text(f'{sha(BARS)}  out/BARS.json\n')
    print(json.dumps(dict(sha256=sha(BARS), spec={k: (v['sha256'][:16], v['mtime_utc']) for k, v in specs.items()},
                          earliest_score_file=first, earliest_aggregate_score_file=aggregate), indent=1))


if __name__ == '__main__':
    main()
