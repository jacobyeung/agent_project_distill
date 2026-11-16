"""Three alternative renderings of the D0 facing-away rows (built, validated, not admitted).

Each is a deterministic rewrite of the D0 v5 facing family (rows.sqlite 4af43b40, family 'facing':
17,479 toward/away pairs = 34,958 rows). Toward rows are copied byte-identical; only away rows change.
Labels (answer letter, options, option order, frames) never change; every rewritten away row is checked
so that the relation it states after the turn maps to the row's own answer letter.

  ra  (class a, no clause written)  more away phrasings in the question, including ReVSI's
      "facing in the opposite direction of", assigned by sha256(source qid); the clause line echoes
      the question's own phrase.
  rb  (class b, clause written but relation not turned)  a line that states the turned relation
      in band words, written between the half-turn clause and the conclusion.
  rc  (class c, one axis only)  per-level rules written out: for hard and medium, one line per axis
      (front/back or band, then left/right) for this item; easy keeps the source form.
  rab, rac  ra's phrasings combined with rb's turned-relation line or rc's per-axis lines.

Usage: render_away.py --src facing_v5.jsonl.gz --kind ra|rb|rc|rab|rac --out DIR
"""
import argparse
import collections
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

HALF = ('The question has me face away from the {F}. That is a half turn: what was ahead is now behind me, '
        'what was behind is now ahead, and left and right swap.')
HALF_TAIL = ' That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.'

# question phrase -> clause echo (without the trailing "the F.")
PHRASES = (
    ('facing away from', 'The question has me face away from'),
    ('turned away from', 'The question has me turned away from'),
    ('with my back to', 'The question puts my back to'),
    ('facing in the opposite direction of', 'The question has me facing in the opposite direction of'),
    ('facing directly away from', 'The question has me facing directly away from'),
    ('with my back turned to', 'The question has my back turned to'),
)
SOURCE_PHRASES = ('facing away from', 'turned away from', 'with my back to')

# forward words (as D0 writes them) -> (level, band/fb, side)
FWD = {
    'easy': {'to my left': (None, 'left'), 'to my right': (None, 'right')},
    'medium': {'ahead of me, slightly to my left': ('A', 'left'), 'ahead of me, slightly to my right': ('A', 'right'),
               'out to my left': ('O', 'left'), 'out to my right': ('O', 'right'),
               'behind me, on my left': ('B', 'left'), 'behind me, on my right': ('B', 'right')},
    'hard': {'in front of me, on my left': ('F', 'left'), 'in front of me, on my right': ('F', 'right'),
             'behind me, on my left': ('B', 'left'), 'behind me, on my right': ('B', 'right')},
}
OPP = {'left': 'right', 'right': 'left'}


def words(level, rel):
    for w, r in FWD[level].items():
        if r == rel:
            return w
    raise KeyError((level, rel))


def half_turn(level, rel):
    fb, side = rel
    if level == 'easy':
        return (None, OPP[side])
    if level == 'medium':
        return ({'A': 'B', 'B': 'A', 'O': 'O'}[fb], OPP[side])
    return ('B' if fb == 'F' else 'F', OPP[side])


def content(level, rel):
    fb, side = rel
    if level == 'easy':
        return side
    if level == 'medium':
        return 'back' if fb == 'B' else side
    return ('front' if fb == 'F' else 'back') + '-' + side


def level_of(row):
    return row['question_type'].rsplit('_', 1)[1]


def parse_away(row):
    """Return (lines, names dict, forward rel) and assert the source form exactly."""
    t = row['target']
    m = re.fullmatch(r'<think>\n(?P<body>.*)\n</think>\n\n(?P<ans>[A-Z])', t, re.S)
    if not m or m.group('ans') != row['answer']:
        raise ValueError('layout')
    lines = m.group('body').split('\n')
    if len(lines) != 4:
        raise ValueError('line count')
    sm = re.fullmatch(r'Seen: (.+?) in frame \d+; (.+?) in frame \d+; (.+?) in frame \d+\.', lines[0])
    if not sm:
        raise ValueError('seen line')
    S, F, Q = sm.groups()
    level = level_of(row)
    fm = re.fullmatch(r'If I stood at the (.+) facing the (.+), the (.+) would be (.+)\.', lines[1])
    if not fm or fm.group(1) != S or fm.group(2) != F or fm.group(3) != Q or fm.group(4) not in FWD[level]:
        raise ValueError('forward line')
    if lines[2] != HALF.format(F=F):
        raise ValueError('clause line')
    if not lines[3].startswith('So '):
        raise ValueError('conclusion line')
    rel = FWD[level][fm.group(4)]
    return lines, dict(S=S, F=F, Q=Q), rel


def option_content(row):
    for o in row['student_input']['options']:
        if o.startswith(row['answer'] + '. '):
            return o[3:]
    raise ValueError('answer not in options')


def h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def render(row, kind):
    lines, n, rel = parse_away(row)
    level = level_of(row)
    turned = half_turn(level, rel)
    if content(level, turned) != option_content(row):
        raise ValueError('label: turned relation %r does not map to answer %r' % (turned, option_content(row)))
    new = dict(row)
    si = dict(row['student_input'])
    parts = set(kind[1:])
    if not kind.startswith('r') or not parts or not parts <= set('abc') or parts == set('bc'):
        raise ValueError(kind)
    if 'a' in parts:
        q = si['question']
        found = [p for p in SOURCE_PHRASES if ' and %s the %s,' % (p, n['F']) in q]
        if len(found) != 1:
            raise ValueError('question phrase')
        pick = int(h(row['source_qid'] + ':ra')[:8], 16) % len(PHRASES)
        phrase, echo = PHRASES[pick]
        si['question'] = q.replace(' and %s the %s,' % (found[0], n['F']), ' and %s the %s,' % (phrase, n['F']), 1)
        lines = lines[:2] + ['%s the %s.%s' % (echo, n['F'], HALF_TAIL)] + lines[3:]
        new['rendering_phrase'] = phrase
    if 'b' in parts:
        lines = lines[:3] + ['After the half turn, the %s is %s.' % (n['Q'], words(level, turned))] + lines[3:]
    if 'c' in parts:
        fb, side = rel
        tfb, tside = turned
        if level == 'hard':
            axis = ['Front or back: the %s was %s, so now it is %s.' % (
                        n['Q'], 'in front of me' if fb == 'F' else 'behind me', 'in front of me' if tfb == 'F' else 'behind me'),
                    'Left or right: the %s was on my %s, so now it is on my %s.' % (n['Q'], side, tside)]
        elif level == 'medium':
            band = {'A': 'ahead of me', 'O': 'out to a side', 'B': 'behind me'}
            axis = ['Ahead or behind: the %s was %s, so now it is %s.' % (n['Q'], band[fb], band[tfb]),
                    'Left or right: the %s was on my %s, so now it is on my %s.' % (n['Q'], side, tside)]
        else:
            axis = []
        lines = lines[:3] + axis + lines[3:]
    new['student_input'] = si
    new['target'] = '<think>\n' + '\n'.join(lines) + '\n</think>\n\n' + row['answer']
    prov = dict(row.get('provenance') or {})
    prov['rendering'] = dict(kind=kind, version='b13_v1', source_target_sha256=h(row['target']),
                             source_question_sha256=h(row['student_input']['question']))
    new['provenance'] = prov
    new.pop('rendering_phrase', None)
    if 'a' in parts:
        prov['rendering']['phrase'] = phrase
    return new


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--src', required=True)
    p.add_argument('--kind', required=True, choices=('ra', 'rb', 'rc', 'rab', 'rac'))
    p.add_argument('--out', required=True)
    a = p.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ('facing_%s.jsonl' % a.kind)
    stats = collections.Counter()
    phrases = collections.Counter()
    pairs = collections.defaultdict(dict)
    with gzip.open(a.src, 'rt') as src, open(path, 'w') as dst:
        for line in src:
            d = json.loads(line)
            row = d['row']
            if row['facing'] == 'away':
                new = render(row, a.kind)
                stats['away_rewritten'] += 1
                if 'a' in a.kind[1:]:
                    phrases[(level_of(row), new['provenance']['rendering']['phrase'])] += 1
            else:
                new = row
                stats['toward_copied'] += 1
            for k in ('answer', 'qid', 'pair_id', 'question_type', 'facing', 'scene'):
                if new[k] != row[k]:
                    raise ValueError('field changed: ' + k)
            if new['student_input']['options'] != row['student_input']['options'] or \
                    new['student_input']['frames'] != row['student_input']['frames'] or \
                    new['student_input']['frame_indices'] != row['student_input']['frame_indices']:
                raise ValueError('student input changed')
            pairs[row['pair_id']][row['facing']] = 1
            dst.write(json.dumps({'i': d['i'], 'row': new, 'target_col': d['target_col']}, sort_keys=True) + '\n')
    if any(len(v) != 2 for v in pairs.values()):
        raise ValueError('pair incomplete')
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    man = dict(kind=a.kind, file=str(path), sha256=sha, rows=sum(stats.values()), pairs=len(pairs), stats=dict(stats),
               source=a.src, source_sha256=hashlib.sha256(Path(a.src).read_bytes()).hexdigest(),
               phrases={'%s|%s' % k: v for k, v in sorted(phrases.items())} if phrases else None,
               labels='answer, options, frames, qid, pair_id unchanged on every row (asserted); toward rows the same JSON object as the source')
    (out / ('MANIFEST_%s.json' % a.kind)).write_text(json.dumps(man, indent=1, sort_keys=True) + '\n')
    print(json.dumps(man, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
