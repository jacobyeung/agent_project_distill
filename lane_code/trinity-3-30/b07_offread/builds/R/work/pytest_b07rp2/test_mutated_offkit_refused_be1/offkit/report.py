raise RuntimeError('UNVERIFIED_MODULE_EXECUTED')
"""Official aggregation and reports for the official read kit (brief 07).

Input is a list of unified item records, one per cohort item and arm:
  id, question_type, score (0..1), status ('complete' or anything else = error),
  error, forced_close (bool), calls (int, calls the model emitted), calls_served (int),
  refusal (bool: a refusal status or a non-answer), parse_failed (bool),
  optional source_capped / continuation_capped (direct kits).
A missing, errored or refused item scores 0 and stays in the denominator.

Aggregation: a group's score is the equal mean of its subtype means; the headline is
the equal mean of the groups read. Intervals: percentile 2.5/97.5 over scene-cluster
bootstrap replicates (scenes = (dataset, scene_name), resampled jointly across groups),
with the draw scheme of the accepted direct kits f42aa1a4 and ea1a1b2d, so their
numbers reproduce exactly.
"""
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from . import spec as S

HARNESS_WORDS = 'harness-served, not an end-to-end result'
DISTANCE_DISCLOSURE = ('distance route first selected on VSI-Bench ScanNet items (POLICY_AUDIT row 1); its dev-S1 '
                       'confirmation (+8.1) is unit conversion; the route has no clean confirmation (amendment 3 item 5)')
ROOM_PRIMARY_LABEL = ('served routed room, post-read deviation from D2, no gain established, room rule from C4 '
                      '(incumbent rv, selected on VSI-Bench ScanNet items)')
READER_KINDS = ('direct', 'harness', 'e2e')

_UNITS = (
    ('square_feet', r'square\s+f(?:ee|oo)t|sq\.?\s*ft|ft\^?2|ft²'),
    ('square_meters', r'square\s+met(?:er|re)s?|sq\.?\s*m\b|m\^?2|m²'),
    ('centimeters', r'centimet(?:er|re)s?|\bcm\b'),
    ('millimeters', r'millimet(?:er|re)s?|\bmm\b'),
    ('inches', r'\binch(?:es)?\b'),
    ('feet', r'\bfeet\b|\bfoot\b|\bft\b'),
    ('yards', r'\byards?\b'),
    ('meters', r'\bmet(?:er|re)s?\b'),
)


def asked_unit(question):
    """Unit asked in the question text, from the text alone (first parenthesised 'in X' wins)."""
    text = ' '.join(str(question).lower().split())
    found = re.findall(r'\(in ([^)]*)\)', text) or [text]
    for chunk in found:
        for name, pattern in _UNITS:
            if re.search(pattern, chunk):
                return name
    return 'unstated'


def facing(question):
    text = ' '.join(str(question).lower().split())
    if 'facing in the opposite direction of ' in text:
        return 'away'
    if ' and facing the ' in text:
        return 'toward'
    return None


def read_jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def key(row):
    return str(row.get('example_id', row.get('id')))


def index(rows, what):
    out = {}
    for r in rows:
        k = key(r)
        if k in out:
            raise ValueError(f'duplicate {what} item {k}')
        out[k] = r
    return out


def _valid_score(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0 <= x <= 1


class ReadMode:
    """Which groups a read covers and how many items the cohort must hold."""

    def __init__(self, bench, reader_kind):
        if bench not in S.BENCHMARKS:
            raise ValueError('unknown benchmark ' + str(bench))
        if reader_kind not in READER_KINDS:
            raise ValueError('unknown reader kind ' + str(reader_kind))
        self.spec = S.BENCHMARKS[bench]
        self.reader_kind = reader_kind
        if reader_kind == 'direct':
            self.groups = S.direct_groups(self.spec)
            self.items = self.spec['direct_items']
            self.headline = f"{len(self.groups)}-group direct-only mean (not the {self.spec['headline']})"
        else:
            self.groups = tuple(self.spec['groups'])
            self.items = self.spec['items']
            self.headline = self.spec['headline']
        self.types = sorted(t for g in self.groups for t in self.spec['groups'][g])
        self.type_group = {t: g for g in self.groups for t in self.spec['groups'][g]}


def check_cohort(mode, cohort):
    """Denominators are fixed: a full read covers every item; no group can be absent."""
    if len(cohort) != mode.items:
        raise ValueError(f'cohort holds {len(cohort)} items; {mode.spec["label"]} under a {mode.reader_kind} reader requires {mode.items}')
    bad = sorted({r['question_type'] for r in cohort} - set(mode.types))
    if bad:
        raise ValueError('cohort carries types outside the read: ' + ','.join(bad))
    present = {r['question_type'] for r in cohort}
    missing = [t for t in mode.types if t not in present]
    if missing:
        raise ValueError('read type has no item in the cohort (an unread type is impossible): ' + ','.join(missing))
    if mode.reader_kind != 'direct':
        scenes = {(r['dataset'], r['scene_name']) for r in cohort}
        if len(scenes) != mode.spec['scenes']:
            raise ValueError(f'cohort covers {len(scenes)} scenes; {mode.spec["scenes"]} required')


def item_details(mode, cohort, items):
    expected = index(cohort, 'cohort')
    observed = index(items, 'scored')
    foreign = sorted(set(observed) - set(expected))
    if foreign:
        raise ValueError('scored items outside the cohort: ' + ','.join(foreign[:5]))
    detail = []
    for k, t in expected.items():
        r = observed.get(k)
        if r is not None and r.get('question_type', t['question_type']) != t['question_type']:
            raise ValueError('question type differs for item ' + k)
        error = r is None or r.get('status') != 'complete' or bool(r.get('derivation_error'))
        refusal = bool(r and r.get('refusal'))
        score = 0.0 if (error or refusal) else r.get('score')
        if not _valid_score(score):
            raise ValueError('invalid stored score for item ' + k)
        detail.append(dict(
            id=k, question_type=t['question_type'], group=mode.type_group[t['question_type']],
            dataset=t['dataset'], scene_name=t['scene_name'], score=float(score),
            error=(('missing record' if r is None else r.get('error') or 'status ' + str(r.get('status'))) if error else None),
            refusal=refusal, forced_close=bool(r and r.get('forced_close')),
            calls=int(r.get('calls', 0)) if r else 0, calls_served=int(r.get('calls_served', 0)) if r else 0,
            parse_failed=bool(r and r.get('parse_failed')), unparsed=bool(error or (r and (r.get('parse_failed') or r.get('unparsed')))),
            source_capped=bool(r and r.get('source_capped')), continuation_capped=bool(r and r.get('continuation_capped')),
            unit=asked_unit(t.get('question', '')) if mode.type_group[t['question_type']] in (mode.spec['distance_group'], mode.spec['room_group']) else None,
            facing=facing(t.get('question', '')) if 'rel_direction' in t['question_type'] else None))
    return detail


class Bootstrap:
    def __init__(self, scenes, repetitions, seed):
        import numpy as np
        self.np = np
        self.scenes = scenes
        self.scene_index = {s: i for i, s in enumerate(scenes)}
        rng = np.random.default_rng(seed)
        self.weights = rng.multinomial(len(scenes), np.full(len(scenes), 1 / len(scenes)), size=repetitions)
        self.repetitions = repetitions

    def column(self, rows):
        np = self.np
        tot = np.zeros(len(self.scenes)); cnt = np.zeros(len(self.scenes))
        for d in rows:
            i = self.scene_index[(d['dataset'], d['scene_name'])]
            tot[i] += d['score']; cnt[i] += 1
        num = self.weights @ tot; den = self.weights @ cnt
        point = tot.sum() / cnt.sum() if cnt.sum() else float('nan')
        return point, np.divide(num, den, out=np.full(self.repetitions, np.nan), where=den > 0)

    def ci(self, draw):
        valid = draw[self.np.isfinite(draw)]
        return dict(percentile_95=self.np.percentile(valid, [2.5, 97.5]).tolist() if len(valid) else None,
                    valid_replicates=int(len(valid)))


def _counts(rows):
    n = len(rows)
    called = sum(d['calls'] > 0 for d in rows)
    return dict(items=n, errors=sum(d['error'] is not None for d in rows), refusals=sum(d['refusal'] for d in rows),
                forced_closes=sum(d['forced_close'] for d in rows), unparsed=sum(d['unparsed'] for d in rows),
                items_with_calls=called, call_rate=(called / n if n else None),
                calls=sum(d['calls'] for d in rows), calls_served=sum(d['calls_served'] for d in rows),
                source_capped=sum(d['source_capped'] for d in rows), continuation_capped=sum(d['continuation_capped'] for d in rows))


def _mean_draws(points, draws, np):
    point = float(np.mean(points)) if points else None
    draw = np.mean(draws, axis=0) if draws else None
    return point, draw


def aggregate(mode, cohort, items, *, repetitions=10000, seed=544):
    """One arm's report dictionary (no labels; see label_report)."""
    check_cohort(mode, cohort)
    detail = item_details(mode, cohort, items)
    scenes = sorted({(d['dataset'], d['scene_name']) for d in detail})
    boot = Bootstrap(scenes, repetitions, seed)
    np = boot.np
    by_type = defaultdict(list)
    for d in detail:
        by_type[d['question_type']].append(d)
    type_point, type_draw = {}, {}
    for t in mode.types:
        type_point[t], type_draw[t] = boot.column(by_type[t])
    groups = {}; group_draws = []
    for g in mode.groups:
        ts = [t for t in mode.spec['groups'][g] if by_type[t]]
        point, draw = _mean_draws([type_point[t] for t in ts], [type_draw[t] for t in ts], np)
        rows = [d for t in ts for d in by_type[t]]
        groups[g] = dict(score=point, subtypes={t: dict(items=len(by_type[t]), score=type_point[t]) for t in ts},
                         **_counts(rows), **boot.ci(draw),
                         error_list=[dict(id=d['id'], error=d['error']) for d in rows if d['error'] is not None][:50])
        group_draws.append(draw)
    head_point = float(np.mean([groups[g]['score'] for g in mode.groups]))
    head = dict(name=mode.headline, groups=list(mode.groups), score=head_point, **boot.ci(np.mean(group_draws, axis=0)))
    by_unit = {}
    for g in (mode.spec['distance_group'], mode.spec['room_group']):
        if g not in mode.groups:
            continue
        units = defaultdict(list)
        for d in detail:
            if d['group'] == g:
                units[d['unit']].append(d)
        by_unit[g] = {}
        for u, rows in sorted(units.items()):
            # Within a group, a unit slice keeps the group's equal-subtype weighting.
            ts = sorted({d['question_type'] for d in rows})
            cols = [boot.column([d for d in rows if d['question_type'] == t]) for t in ts]
            point, draw = _mean_draws([c[0] for c in cols], [c[1] for c in cols], np)
            by_unit[g][u] = dict(score=point, **_counts(rows), **boot.ci(draw))
    facing_split = {}
    if 'object_rel_direction' in mode.groups:
        for label in ('toward', 'away'):
            rows = [d for d in detail if d['group'] == 'object_rel_direction' and d['facing'] == label]
            if not rows:
                continue
            ts = sorted({d['question_type'] for d in rows})
            cols = [boot.column([d for d in rows if d['question_type'] == t]) for t in ts]
            point, draw = _mean_draws([c[0] for c in cols], [c[1] for c in cols], np)
            facing_split[label] = dict(score=point, **_counts(rows), **boot.ci(draw), diagnostic='question text; not an official leaf')
    return dict(benchmark=mode.spec['name'], benchmark_label=mode.spec['label'], reader_kind=mode.reader_kind,
                items=len(detail), scenes=len(scenes), headline=head, groups=groups,
                per_type={t: dict(score=type_point[t], **_counts(by_type[t])) for t in mode.types},
                by_asked_unit=by_unit, direction_by_question_text=facing_split,
                not_read=[g for g in mode.spec['groups'] if g not in mode.groups],
                bootstrap=dict(unit='(dataset, scene_name)', repetitions=repetitions, seed=seed,
                               interval='percentile 2.5, 97.5', grouping='equal subtype means, then equal group means',
                               zero_denominator='replicate undefined; excluded from that interval and counted'),
                rows=detail)


def label_report(report, *, binding, arm, role, arm_label=None):
    """Attach the reader / EAT-1 / export / mode / arm labels every report must carry.

    The labels come from a verified BINDING only: its reader kind and benchmark must equal the
    aggregate's, so a harness aggregate can never carry end-to-end wording.
    """
    from . import bind as B
    B.verify_binding(binding)
    reader, export = binding['reader'], binding['export']
    kind = reader.get('kind')
    if kind not in READER_KINDS:
        raise ValueError('unknown reader kind ' + repr(kind))
    if kind != report.get('reader_kind'):
        raise ValueError('binding reader %r differs from the aggregate reader %r' % (kind, report.get('reader_kind')))
    if binding.get('benchmark') != report.get('benchmark'):
        raise ValueError('binding benchmark differs from the aggregate benchmark')
    if arm not in binding.get('arms', ()):
        raise ValueError('arm %r is not an arm of this binding' % arm)
    eat = reader.get('eat1') or {}
    eat_state = 'PASSED' if eat.get('passed') is True else ('FAILED' if eat.get('passed') is False else 'NOT RUN')
    words = []
    if kind == 'harness':
        words.append(HARNESS_WORDS)
    elif kind == 'e2e' and eat_state != 'PASSED':
        words.append('end-to-end reader without an EAT-1 pass: not a claimable result')
    elif kind == 'direct':
        words.append('direct-only: routed types not read')
    if binding['mode'] != 'production':
        words.append(binding['mode'] + ' binding: not a benchmark result')
    fr = binding.get('frames') or {}
    if fr.get('layout_override_reason'):
        words.append('frame layout differs from training: ' + fr['layout_override_reason'])
    first = (f"READER {kind} [{reader.get('id', '?')}]; EAT-1 {eat_state} for this reader; MODE {binding['mode']}; "
             f"EXPORT {export.get('kind')} sha256 {export.get('sha256')}; BENCHMARK {report['benchmark_label']}; "
             f"FRAMES {fr.get('count')} {fr.get('layout')}; BINDING {binding['binding_sha256'][:12]}; "
             f"ARM {arm} ({role}){'; ' + '; '.join(words) if words else ''}")
    report = dict(report)
    report.update(first_line=first, reader=reader, export=export, arm=arm, role=role, arm_label=arm_label,
                  number_words=words, binding_sha256=binding['binding_sha256'], mode=binding['mode'],
                  frames=fr)
    notes = {}
    if kind != 'direct' and report['benchmark'] in S.BENCHMARKS:
        spec = S.BENCHMARKS[report['benchmark']]
        notes[spec['distance_group']] = DISTANCE_DISCLOSURE
        if arm == 'primary':
            notes[spec['room_group']] = ROOM_PRIMARY_LABEL
    report['group_notes'] = notes
    return report


def _pct(x):
    return 'undefined' if x is None else f'{100 * x:.2f}'


def _ci(r):
    c = r.get('percentile_95')
    return 'undefined' if c is None else f'[{100 * c[0]:.2f}, {100 * c[1]:.2f}]'


def render(report):
    w = report['number_words']
    tag = (' (' + '; '.join(w) + ')') if w else ''
    lines = [report['first_line']]
    if report.get('arm_label'):
        lines.append('Arm label: ' + report['arm_label'])
    h = report['headline']
    lines.append(f"{h['name']}: {_pct(h['score'])} 95% CI {_ci(h)}{tag}; groups {', '.join(h['groups'])}; items {report['items']}; scenes {report['scenes']}")
    for g, r in report['groups'].items():
        note = report['group_notes'].get(g)
        lines.append(f"{g}: {_pct(r['score'])} {_ci(r)}{tag}; n={r['items']}; call rate={_pct(r['call_rate'])}%; "
                     f"calls={r['calls']} served={r['calls_served']}; refusals={r['refusals']}; forced closes={r['forced_closes']}; "
                     f"errors={r['errors']}; unparsed={r['unparsed']}" + (f"; NOTE {note}" if note else ''))
        if len(r['subtypes']) > 1:
            lines.append('  subtypes: ' + ', '.join(f"{t} {_pct(s['score'])} (n={s['items']})" for t, s in r['subtypes'].items()))
    for g, units in report['by_asked_unit'].items():
        for u, r in units.items():
            lines.append(f"{g} asked in {u}: {_pct(r['score'])} {_ci(r)}{tag}; n={r['items']}; call rate={_pct(r['call_rate'])}%; refusals={r['refusals']}; forced closes={r['forced_closes']}")
    for label, r in report['direction_by_question_text'].items():
        lines.append(f"direction {label} (question-text diagnostic, not an official leaf): {_pct(r['score'])} {_ci(r)}{tag}; n={r['items']}")
    for g in report['not_read']:
        lines.append(f"{g}: not read by this reader")
    return '\n'.join(lines) + '\n'


def write(report, out_dir, stem):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=1, allow_nan=False, sort_keys=False) + '\n'
    (out / f'{stem}.json').write_text(text)
    (out / f'{stem}.txt').write_text(render(report))
    return hashlib.sha256(text.encode()).hexdigest()
