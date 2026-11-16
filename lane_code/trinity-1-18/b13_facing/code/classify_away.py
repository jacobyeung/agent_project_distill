"""Classify why each facing-away answer of a direct read is right or wrong.

Input: the B2048 reader journals of the away family and the forward (toward)
family of one read (rows with question, options, ground_truth, question_type,
raw_generation, extracted_answer and, for dev twins, label_provenance.backdir).
ReVSI backward items run with --away only (no toward twin).

Classes per away item, decided from the generated trace and the labels:
  a  no facing clause written (sub: none | toward_clause | empty_trace)
  b  clause written, relation not turned (answer = the forward relation)
  c  turned on one axis only (front/back or left/right flipped, not both)
  d  forward relation itself wrong (stated forward line wrong; or, with no
     stated forward line, the toward twin is also wrong)
  e  correct
  f  other or unparsed (sub: unparsed | mapping | other)
Precedence for a wrong answer: f.unparsed, a, d, b, c, f.

Relations: easy = side; medium = band (A <45, O 45-135, B >=135) + side;
hard = front/back + side. A half turn flips the side and maps A<->B, O->O,
front<->back. Positive forward bearing = left (checked against labels).
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

LEVELS = ('easy', 'medium', 'hard')
CLASSES = ('a', 'b', 'c', 'd', 'e', 'f')
CLASS_NAMES = {'a': 'no facing clause', 'b': 'clause, not turned', 'c': 'one axis only',
               'd': 'forward relation wrong', 'e': 'correct', 'f': 'other/unparsed'}
OPP = {'left': 'right', 'right': 'left'}
HALF_TURN_CONTENT = {'left': 'right', 'right': 'left', 'front-left': 'back-right',
                     'front-right': 'back-left', 'back-left': 'front-right',
                     'back-right': 'front-left'}

AWAY_MENTION = re.compile(
    r"(?:fac(?:e|es|ed|ing)|turn(?:s|ed)?|stand(?:ing)?|look(?:s|ed|ing)?)\s+(?:directly\s+|straight\s+)?away\s+from"
    r"|with\s+my\s+back\s+(?:turned\s+)?to|my\s+back\s+(?:is\s+)?(?:turned\s+)?to"
    r"|(?:in\s+)?the\s+opposite\s+direction\s+(?:of|from|to)|opposite\s+(?:way|direction)\s+(?:of|from)"
    r"|\bface\s+away\b|\bfacing\s+away\b|\bturned\s+away\b")
TURN_OP = re.compile(
    r"half[\s-]turn|turn(?:ed|s)?\s+around|about[\s-]face|(?:turn(?:ed|s)?|rotat\w*)\s+(?:by\s+)?180"
    r"|180[\s-]degree\s+(?:turn|rotation)|left\s+and\s+right\s+swap|\bswap\w*|\brevers\w*|\bflip\w*"
    r"|ahead\s+is\s+now\s+behind|behind\s+(?:is\s+)?now\s+ahead")
TOWARD_CLAUSE = re.compile(r"no\s+turn\s+applies|keep\s+that\s+heading|so\s+no\s+turn|without\s+turning")
FORWARD_LINE = re.compile(r"^\s*if\s+i\s+(?:stood|were\s+standing|was\s+standing|faced|were\s+facing)\b.*?\bwould\s+be\b(.*)$")
DEGREE = re.compile(r"(\d+(?:\.\d+)?)\s+degrees?\s+(left|right)?")


def level_of(row):
    """Answer form from the option contents; dev and ReVSI share these forms."""
    contents = sorted(option_contents(row).values())
    if contents == ['left', 'right']:
        return 'easy'
    if contents == ['back', 'left', 'right']:
        return 'medium'
    if contents == ['back-left', 'back-right', 'front-left', 'front-right']:
        return 'hard'
    raise ValueError('unknown option set %r for %s' % (contents, row.get('id')))


def option_contents(row):
    out = {}
    for opt in row['options']:
        m = re.match(r'^\s*([A-Z])\s*[.)]\s*(.+?)\s*$', opt)
        if not m:
            raise ValueError('bad option %r' % opt)
        out[m.group(1)] = m.group(2).strip().lower()
    return out


def content(rel, level):
    """Answer content of a relation tuple (fb, side)."""
    fb, side = rel
    if level == 'easy':
        return side
    if level == 'medium':
        return 'back' if fb == 'B' else side
    return ('front' if fb == 'F' else 'back') + '-' + side


def half_turn(rel, level):
    fb, side = rel
    if level == 'easy':
        return (None, OPP[side])
    if level == 'medium':
        return ({'A': 'B', 'B': 'A', 'O': 'O'}[fb], OPP[side])
    return ('B' if fb == 'F' else 'F', OPP[side])


def one_axis(rel, level):
    """Relations reached by flipping exactly one axis (empty for easy)."""
    fb, side = rel
    if level == 'easy':
        return []
    if level == 'medium':
        return [(fb, OPP[side]), ({'A': 'B', 'B': 'A', 'O': 'O'}[fb], side)]
    return [(fb, OPP[side]), ('B' if fb == 'F' else 'F', side)]


def rel_from_bearing(theta, level):
    side = 'left' if theta > 0 else 'right'
    a = abs(theta)
    if level == 'easy':
        return (None, side)
    if level == 'medium':
        return ('A' if a < 45 else 'O' if a < 135 else 'B', side)
    return ('F' if a < 90 else 'B', side)


def rel_from_words(text, level):
    """Parse a relation phrase; returns (fb, side) or None. Side may be None for medium back."""
    s = text.lower()
    m = DEGREE.search(s)
    side = None
    lefts, rights = [x.start() for x in re.finditer(r'\bleft\b', s)], [x.start() for x in re.finditer(r'\bright\b', s)]
    if lefts and not rights:
        side = 'left'
    elif rights and not lefts:
        side = 'right'
    elif lefts and rights:
        side = 'left' if max(lefts) > max(rights) else 'right'
    if level == 'easy':
        return (None, side) if side else None
    if m:  # sealed step-544 form: "N degrees left of straight ahead, in front|behind|a turn of ..."
        deg = float(m.group(1))
        side = m.group(2) or side
        if level == 'medium':
            fb = 'A' if deg < 45 else 'O' if deg < 135 else 'B'
        else:
            fb = 'F' if deg < 90 else 'B'
            if re.search(r'\bbehind\b', s):
                fb = 'B'
            elif re.search(r'in front', s):
                fb = 'F'
        return (fb, side) if side or fb == 'B' else None
    if level == 'medium':
        if re.search(r'behind me|\bat my back\b|\bbehind\b', s):
            fb = 'B'
        elif re.search(r'slightly|ahead of me|in front', s):
            fb = 'A'
        elif re.search(r'out to my|\bto my (left|right)\b|on my (left|right)', s):
            fb = 'O'
        else:
            return None
        return (fb, side) if side or fb == 'B' else None
    if re.search(r'back-(left|right)|behind', s):
        fb = 'B'
    elif re.search(r'front-(left|right)|in front|ahead', s):
        fb = 'F'
    else:
        return None
    return (fb, side) if side else None


def clause_kind(trace):
    t = trace.lower()
    if not t.strip():
        return 'empty_trace'
    turn, mention, toward = bool(TURN_OP.search(t)), bool(AWAY_MENTION.search(t)), bool(TOWARD_CLAUSE.search(t))
    if turn:
        return 'turn'
    if mention:
        return 'mention'
    if toward:
        return 'toward_clause'
    return 'none'


def think_part(raw):
    if raw is None:
        return ''
    return raw.split('</think>')[0]


def stated_forward(trace, level):
    for line in trace.split('\n'):
        m = FORWARD_LINE.match(line.strip().lower())
        if m:
            return rel_from_words(m.group(1), level)
    return None


def conclusion_content(trace, level):
    lines = [l for l in trace.strip().split('\n') if l.strip()]
    for line in reversed(lines):
        if line.strip().lower().startswith('so '):
            rel = rel_from_words(line, level)
            if rel is None:
                return None
            if level == 'medium' and re.search(r'\bback\b|behind', line.lower()):
                return 'back'
            if rel[1] is None:
                return None
            return content(rel, level)
    return None


def away_phrase(question):
    q = question.lower()
    for name, pat in (('facing in the opposite direction of', r'opposite direction'),
                      ('facing directly away from', r'directly away from'),
                      ('with my back to', r'with my back to'),
                      ('turned away from', r'turned away from'),
                      ('facing away from', r'facing away from')):
        if re.search(pat, q):
            return name
    return 'other'


def true_forward(row, level):
    """Return (list of candidate forward relations, source)."""
    prov = (row.get('label_provenance') or {}).get('backdir') or {}
    audit = prov.get('forward_program_audit') or {}
    theta = audit.get('unrounded_theta_deg')
    if theta is not None:
        rel = rel_from_bearing(float(theta), level)
        return [rel], 'bearing'
    fwd = prov.get('forward_answer_content')
    gt_content = option_contents(row)[row['ground_truth']]
    cands = []
    sides = ('left', 'right')
    fbs = {'easy': (None,), 'medium': ('A', 'O', 'B'), 'hard': ('F', 'B')}[level]
    for fb in fbs:
        for side in sides:
            rel = (fb, side)
            if content(half_turn(rel, level), level) != gt_content:
                continue
            if fwd is not None and content(rel, level) != fwd:
                continue
            cands.append(rel)
    return cands, ('forward_content' if fwd else 'away_label')


def pair_class(away_content, toward_content):
    """f1f2 / step-544 pair classes: unchanged, opposite (half turn of the toward answer), neither."""
    if away_content is None or toward_content is None:
        return 'unparsed'
    if away_content == toward_content:
        return 'unchanged'
    if HALF_TURN_CONTENT.get(toward_content) == away_content:
        return 'opposite'
    return 'neither'


def classify(away, toward=None):
    level = level_of(away)
    opts = option_contents(away)
    gt = opts[away['ground_truth']]
    pred_letter = away.get('extracted_answer')
    pred = opts.get(pred_letter) if pred_letter else None
    trace = think_part(away.get('raw_generation'))
    ck = clause_kind(trace)
    f_stated = stated_forward(trace, level)
    f_true, f_src = true_forward(away, level)
    concl = conclusion_content(trace, level)
    out = dict(id=away['id'], level=level, question_type=away.get('question_type'), wording=away_phrase(away['question']),
               gt=gt, pred=pred, clause=ck, forward_stated=f_stated and list(f_stated),
               forward_true=[list(r) for r in f_true], forward_true_source=f_src, conclusion=concl)
    if f_true and f_src == 'bearing':
        out['transition'] = '%s:%s->%s' % (level, content_band(f_true[0], level), gt)
    else:
        out['transition'] = '%s:?->%s' % (level, gt)
    if toward is not None:
        topts = option_contents(toward)
        tl = toward.get('extracted_answer')
        out['toward_pred'] = topts.get(tl) if tl else None
        out['toward_correct'] = bool(tl) and tl == toward['ground_truth']
        out['pair_class'] = pair_class(pred, out['toward_pred'])
    else:
        out['toward_pred'] = out['toward_correct'] = out['pair_class'] = None
    sub = ''
    if pred is None:
        cls, sub = 'f', 'unparsed'
    elif pred == gt:
        cls = 'e'
    elif ck in ('none', 'toward_clause', 'empty_trace'):
        cls, sub = 'a', ck
    else:
        forward_wrong = None
        if f_stated is not None and f_true:
            forward_wrong = not any(same_rel(f_stated, r, level) for r in f_true)
            sub = 'stated'
        elif toward is not None:
            forward_wrong = not out['toward_correct']
            sub = 'twin'
        if forward_wrong:
            cls = 'd'
        else:
            ref = [f_stated] if (f_stated is not None and f_stated[1] is not None) else f_true
            if not ref:
                cls, sub = 'f', 'other'
            elif any(pred == content(r, level) for r in ref):
                cls, sub = 'b', ''
            elif any(pred == content(x, level) for r in ref for x in one_axis(r, level)
                     if content(x, level) != content(half_turn(r, level), level)):
                cls, sub = 'c', ''
            else:
                cls, sub = 'f', 'mapping' if concl == gt else 'other'
    out['cls'], out['sub'] = cls, sub
    out['conclusion_letter_mismatch'] = bool(concl is not None and pred is not None and concl != pred)
    return out


def same_rel(a, b, level):
    if level == 'easy':
        return a[1] == b[1]
    if a[1] is None or b[1] is None:  # medium "behind me" without side: compare band only
        return a[0] == b[0]
    return a == b


def content_band(rel, level):
    fb, side = rel
    if level == 'easy':
        return side
    if level == 'medium':
        return {'A': 'ahead', 'O': 'out', 'B': 'behind'}[fb] + '-' + side
    return content(rel, level)


def load(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def pair_key(row):
    rid = row['id']
    prov = row.get('label_provenance') or {}
    if prov.get('paired_away_qid'):
        return prov['paired_away_qid']
    return rid


def run(away_rows, toward_rows=None, items=None):
    toward = {}
    if toward_rows is not None:
        for r in toward_rows:
            k = pair_key(r)
            if k in toward:
                raise ValueError('duplicate toward twin %s' % k)
            toward[k] = r
    results = []
    for r in away_rows:
        tw = toward.get(r['id']) if toward_rows is not None else None
        if toward_rows is not None and tw is None:
            raise ValueError('missing toward twin for %s' % r['id'])
        results.append(classify(r, tw))
    if toward_rows is not None and len(toward) != len(away_rows):
        raise ValueError('twin count differs: %d away, %d toward' % (len(away_rows), len(toward)))
    check = None
    if items is not None:  # cross-check against f1f2's normalized ITEMS / A544 records
        idx = {(x['family'], x['id']): x for x in items}
        bad = 0
        for res in results:
            x = idx.get(('away', res['id']))
            if x is None or x.get('answer_content') != res['pred']:
                bad += 1
        check = dict(items_checked=len(results), prediction_mismatches=bad)
    return results, check


def summarize(results, label):
    def table(key):
        t = collections.OrderedDict()
        for r in sorted(results, key=lambda r: (str(r[key]))):
            t.setdefault(r[key], collections.Counter())[r['cls']] += 1
        return {k: dict(v, n=sum(v.values())) for k, v in t.items()}
    by_level = {lv: collections.Counter() for lv in LEVELS}
    for r in results:
        by_level[r['level']][r['cls']] += 1
    s = dict(label=label, n=len(results),
             overall=dict(collections.Counter(r['cls'] for r in results)),
             by_level={lv: dict(v, n=sum(v.values())) for lv, v in by_level.items() if sum(v.values())},
             by_transition=table('transition'), by_wording=table('wording'),
             by_question_type=table('question_type'),
             clause_kinds=dict(collections.Counter(r['clause'] for r in results)),
             subs=dict(collections.Counter('%s.%s' % (r['cls'], r['sub']) for r in results if r['sub'])),
             conclusion_letter_mismatch=sum(r['conclusion_letter_mismatch'] for r in results))
    if results and results[0]['toward_correct'] is not None:
        tw = collections.defaultdict(collections.Counter)
        for r in results:
            tw['toward_correct' if r['toward_correct'] else 'toward_wrong'][r['cls']] += 1
        s['by_toward_status'] = {k: dict(v, n=sum(v.values())) for k, v in tw.items()}
        s['pair_classes'] = dict(collections.Counter(r['pair_class'] for r in results))
        xt = collections.defaultdict(collections.Counter)
        for r in results:
            xt[r['pair_class']][r['cls']] += 1
        s['pair_class_by_cls'] = {k: dict(v) for k, v in xt.items()}
    return s


def markdown(s):
    lines = ['### %s (n=%d)' % (s['label'], s['n']), '',
             '| level | n | ' + ' | '.join('%s %s' % (c, CLASS_NAMES[c]) for c in CLASSES) + ' |',
             '|---|---|' + '---|' * len(CLASSES)]
    for lv, v in list(s['by_level'].items()) + [('all', dict(s['overall'], n=s['n']))]:
        lines.append('| %s | %d | ' % (lv, v['n']) + ' | '.join(str(v.get(c, 0)) for c in CLASSES) + ' |')
    for title, key in (('transition (forward band -> away answer)', 'by_transition'), ('away wording', 'by_wording'),
                       ('toward twin', 'by_toward_status')):
        if key not in s:
            continue
        lines += ['', '| %s | n | ' % title + ' | '.join(CLASSES) + ' |', '|---|---|' + '---|' * len(CLASSES)]
        for k, v in s[key].items():
            lines.append('| %s | %d | ' % (k, v['n']) + ' | '.join(str(v.get(c, 0)) for c in CLASSES) + ' |')
    lines += ['', 'clause kinds: %s; sub-classes: %s; conclusion/letter mismatches: %d' % (
        json.dumps(s['clause_kinds'], sort_keys=True), json.dumps(s['subs'], sort_keys=True), s['conclusion_letter_mismatch'])]
    if 'pair_classes' in s:
        lines.append('pair classes: %s; by class: %s' % (json.dumps(s['pair_classes'], sort_keys=True),
                                                      json.dumps(s['pair_class_by_cls'], sort_keys=True)))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--away', required=True, help='away-family B2048 journal (JSONL)')
    p.add_argument('--toward', help='forward-family B2048 journal (JSONL); omit for ReVSI')
    p.add_argument('--items', help="f1f2 normalized ITEMS.jsonl / A544.jsonl to cross-check predictions")
    p.add_argument('--filter-type', help='keep away rows whose question_type contains this string (ReVSI: backward)')
    p.add_argument('--label', required=True)
    p.add_argument('--out', required=True, help='output prefix: writes .items.jsonl .summary.json .md')
    a = p.parse_args(argv)
    away = load(a.away)
    if a.filter_type:
        away = [r for r in away if a.filter_type in str(r.get('question_type'))]
    results, check = run(away, load(a.toward) if a.toward else None, load(a.items) if a.items else None)
    s = summarize(results, a.label)
    s['inputs'] = dict(away=a.away, toward=a.toward, items=a.items, filter_type=a.filter_type)
    s['items_check'] = check
    with open(a.out + '.items.jsonl', 'w') as fh:
        for r in results:
            fh.write(json.dumps(r, sort_keys=True) + '\n')
    Path(a.out + '.summary.json').write_text(json.dumps(s, indent=1, sort_keys=True) + '\n')
    md = markdown(s)
    Path(a.out + '.md').write_text(md)
    sys.stdout.write(md)
    if check and check['prediction_mismatches']:
        sys.stderr.write('PREDICTION MISMATCH vs items: %d\n' % check['prediction_mismatches'])
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
