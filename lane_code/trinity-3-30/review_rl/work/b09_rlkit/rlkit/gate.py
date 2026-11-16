"""Gate g of one rollout: grammar, provenance and counterfactual replay.

g = 1 only when every check passes:
  1. termination: the decoder ended on EOS, not on the sampled-token budget, a call limit,
     a tower failure or context exhaustion;
  2. layout and grammar: the sealed validator a41ba191 (vendored, pinned) accepts the
     row built from the rollout (`<think>` body, then `\\n\\n<answer>` for a direct trace or
     `\\n<answer>X</answer>` for a program trace with tool responses);
  3. provenance: the answer follows from what the trace cites
       - program trace, numeric answer: a chain from printed response values through the
         trace's own explicit arithmetic lines (`a x b = c`) to the answer; every operand is a
         printed value, an earlier result, a unit-conversion constant or a question constant;
       - program trace, option answer: nearest option to a derived value (numeric options),
         or argmin/argmax over printed gap distances (closest/farthest questions);
       - direct trace: the answer is not detached (a final statement naming another option,
         or a stated count different from the answer, fails);
       - a program trace whose every call failed is a recovery trace: direct checks apply;
  4. counterfactual replay (program traces with a derivation): scale every printed value
     by 1.37 (numeric) or swap the printed candidate distances (closest/farthest) and
     recompute; the answer must change. A constant-only computation fails.
Unsupported projections fail with an explicit reason; nothing passes silently.
"""
import re

from .vendor import trace_grammar as grammar

SPECIAL_TAIL = re.compile(r'(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$')
NUM = r'[+\-]?(?:\d+(?:\.\d+)?|\.\d+)'
MEASURE = re.compile(r'(' + NUM + r')\s*(?:m\^2|m²|m2|sq\s*m|square met(?:er|re)s?|m|cm|mm|ft|feet|in|inches|deg|degrees|°)(?![A-Za-z])')
HEAD_LINE = re.compile(r'^\s*(?:distance|area|count|total|instances?|height|length|width|angle|turn|dx|dy|dz)\b[^\n]*?(' + NUM + r')', re.I | re.M)
COUNT_LINE = re.compile(r'(' + NUM + r')\s+instances?\b', re.I)
ARITH = re.compile(r'(?P<a>' + NUM + r')\s*(?P<op>[+*/x×−-])\s*(?P<b>' + NUM + r')\s*=\s*(?P<c>' + NUM + r')')
RESPONSE = re.compile(r'<tool_response>(.*?)</tool_response>', re.S)
CALL_GAP = re.compile(r'<gap a="([^"]+)"((?: b="[^"]+")+)[^>]*>\s*<tool_response>(.*?)</tool_response>', re.S)
FAILED_RESPONSE = re.compile(r'^\s*(?:error:|[^\n]*:\s*not seen\s*$)', re.I | re.M)
CONVERSIONS = (100.0, 1000.0, 3.28084, 39.3701, 10.7639, 0.3048, 2.54, 0.01, 0.001, 12.0)
STATED_COUNT = re.compile(r'\b(?:there (?:are|is)|count(?:s| is)?|total(?: is)?|so)\s*(?:of\s*)?(\d+)\b', re.I)
SCALE = 1.37
FAIL_FINISH = ('max_new_tokens', 'context_exhaustion', 'call_limit', 'tower_error')


def decimals(s):
    s = str(s)
    return len(s.split('.')[1]) if '.' in s else 0


def tol_of(s):
    v = abs(float(s))
    return max(0.5 * 10 ** -decimals(s) + 1e-9, 0.005 * v)


def close(x, s):
    return abs(x - float(s)) <= tol_of(s)


def split(text):
    """(body, tail, form) of a generated suffix; raise ValueError on a broken layout."""
    text = SPECIAL_TAIL.sub('', text)
    if text.count('</think>') != 1 or '<think>' in text:
        raise ValueError('layout_think_tags')
    body, tail = text.split('</think>')
    form = 'program' if '<tool_response>' in body else 'direct'
    return text, body, tail, form


def printed_values(body):
    out = []
    for m in RESPONSE.finditer(body):
        resp = m.group(1)
        seen = set()
        for rx in (HEAD_LINE, COUNT_LINE, MEASURE):
            for v in rx.finditer(resp):
                key = (v.start(1), v.group(1))
                if key not in seen:
                    seen.add(key)
                    out.append(float(v.group(1)))
    return out


def all_calls_failed(body):
    resps = [m.group(1) for m in RESPONSE.finditer(body)]
    return bool(resps) and all(FAILED_RESPONSE.search(r) for r in resps)


def outside_responses(body):
    return RESPONSE.sub('', body)


def _apply(op, a, b):
    if op == '+':
        return a + b
    if op in ('-', '−'):
        return a - b
    if op in ('*', 'x', '×'):
        return a * b
    if op == '/':
        return a / b if b else float('nan')
    raise ValueError(op)


def derive(body, question):
    """Explicit derivation graph: nodes are printed values ('p', i), constants ('k', v) and
    arithmetic results ('op', op, left, right, written). Returns (printed, nodes)."""
    printed = printed_values(body)
    qconst = [float(x) for x in re.findall(NUM, question or '')]
    nodes = [('p', i) for i in range(len(printed))]

    def value(node, scale=1.0):
        if node[0] == 'p':
            return printed[node[1]] * scale
        if node[0] == 'k':
            return node[1]
        return _apply(node[1], value(node[2], scale), value(node[3], scale))

    def resolve(s):
        # exact value first, then an exact constant, then a value that rounds to the operand
        x = float(s)
        for node in reversed(nodes):
            if abs(value(node) - x) <= 1e-9 + 1e-9 * abs(x):
                return node
        for k in CONVERSIONS + tuple(qconst):
            if abs(k - x) <= 1e-9 + 1e-6 * abs(k):
                return ('k', k)
        for node in reversed(nodes):
            if close(value(node), s):
                return node
        return None

    errors = []
    for m in ARITH.finditer(outside_responses(body)):
        left, right = resolve(m['a']), resolve(m['b'])
        if left is None or right is None:
            errors.append('untraced_operand:' + m.group(0))
            continue
        node = ('op', m['op'], left, right, m['c'])
        if not close(value(node), m['c']):
            errors.append('wrong_arithmetic:' + m.group(0))
            continue
        nodes.append(node)
    return printed, nodes, value, errors


def uses_printed(node):
    if node[0] == 'p':
        return True
    if node[0] == 'op':
        return uses_printed(node[2]) or uses_printed(node[3])
    return False


def option_texts(options):
    out = []
    for o in options or []:
        m = re.match(r'^\s*([A-Z])[.:)]\s*(.*)$', o)
        if m:
            out.append((m[1], m[2].strip()))
    return out


def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9,\- ]', ' ', s.lower())).strip()


def mentioned(line, options):
    """Letters whose option text appears in the line (word-bounded; longer texts first, consumed)."""
    rest = ' ' + _norm(line) + ' '
    hits = []
    for letter, txt in sorted(options, key=lambda kv: -len(kv[1])):
        t = _norm(txt)
        if not t:
            continue
        pat = re.compile(r'(?<![a-z0-9\-])' + re.escape(t) + r'(?![a-z0-9\-])')
        if pat.search(rest):
            hits.append(letter)
            rest = pat.sub(' ', rest)
    return hits


def direct_checks(body, prompt, answer):
    options = option_texts(prompt.get('options'))
    lines = [ln for ln in outside_responses(body).splitlines() if ln.strip()]
    if options:
        for ln in reversed(lines):
            hits = mentioned(ln, options)
            if hits:
                if answer not in hits:
                    return ['answer_detached_from_trace']
                return [] if len(hits) == 1 else []  # ambiguous final statement: not detached
        return []
    if 'count' in str(prompt.get('type', '')):
        for ln in reversed(lines):
            m = STATED_COUNT.search(ln)
            if m:
                return [] if close(float(m[1]), answer) else ['stated_count_differs_from_answer']
    return []


def program_numeric(body, prompt, answer):
    printed, nodes, value, errors = derive(body, prompt.get('question', ''))
    if errors:
        return errors, None
    match = None
    for node in reversed(nodes):
        if close(value(node), answer):
            match = node
            break
    if match is None:
        return ['answer_not_derived_from_printed_values'], None
    if not uses_printed(match):
        return ['constant_only_computation'], None
    if close(value(match, SCALE), answer):
        return ['replay_invariant'], None
    return [], dict(kind='numeric_chain', printed=len(printed), steps=sum(n[0] == 'op' for n in nodes))


def program_option(body, prompt, answer):
    options = option_texts(prompt.get('options'))
    q = (prompt.get('question') or '').lower()
    gaps = []
    for m in CALL_GAP.finditer(body):
        bs = re.findall(r' b="([^"]+)"', m.group(2))
        vals = [float(v) for v in MEASURE.findall(m.group(3))]
        if len(bs) == 1 and len(vals) == 1:
            gaps.append((bs[0], vals[0]))
    want = 'min' if any(w in q for w in ('closest', 'nearest')) else 'max' if any(w in q for w in ('farthest', 'furthest')) else None
    if gaps and want and options:
        by_name = {_norm(name): v for name, v in gaps}
        cand = [(letter, by_name[_norm(t)]) for letter, t in options if _norm(t) in by_name]
        if len(cand) < 2:
            return ['unsupported_projection:too_few_measured_candidates'], None
        pick = (min if want == 'min' else max)(cand, key=lambda kv: kv[1])
        ties = [c for c in cand if abs(c[1] - pick[1]) < 1e-9]
        if len(ties) > 1:
            return ['unresolved_tie'], None
        if pick[0] != answer:
            return ['answer_not_projected_from_printed_values'], None
        other = next(c for c in cand if c[0] != pick[0])
        swapped = {**dict(cand), pick[0]: other[1], other[0]: pick[1]}
        repick = (min if want == 'min' else max)(swapped.items(), key=lambda kv: kv[1])[0]
        if repick == answer:
            return ['replay_invariant'], None
        return [], dict(kind='gap_extreme', candidates=len(cand))
    numeric = []
    for letter, t in options:
        m = re.fullmatch(r'\s*(' + NUM + r')\s*[a-zA-Z°^²2 ]*', t)
        if m:
            numeric.append((letter, float(m[1])))
    if numeric and len(numeric) == len(options):
        printed, nodes, value, errors = derive(body, prompt.get('question', ''))
        if errors:
            return errors, None
        for node in reversed(nodes):
            if not uses_printed(node):
                continue
            x = value(node)
            pick = min(numeric, key=lambda kv: abs(kv[1] - x))[0]
            if pick == answer:
                xs = value(node, SCALE)
                if min(numeric, key=lambda kv: abs(kv[1] - xs))[0] == answer and len(numeric) > 1:
                    # scaled witness lands on the same option: try each other option's value
                    if all(min(numeric, key=lambda kv: abs(kv[1] - v))[0] == answer for _, v in numeric):
                        return ['replay_invariant'], None
                return [], dict(kind='nearest_numeric_option')
        return ['answer_not_projected_from_printed_values'], None
    return ['unsupported_projection:categorical_option'], None


def gate(prompt, rec, scored, *, allow_stated_option=False):
    """dict(g, form, recovery, reasons, provenance)."""
    reasons = []
    if rec.get('budget_hit'):
        reasons.append('budget_hit')
    if rec.get('finish') != 'eos':
        reasons.append('finish_' + str(rec.get('finish')))
    if rec.get('tower_error'):
        reasons.append('tower_error')
    answer = scored.get('answer')
    if answer is None:
        reasons.append('parse_' + str(scored.get('parse_failure')))
    try:
        text, body, tail, form = split(rec['text'])
    except ValueError as exc:
        return dict(g=0, form=None, recovery=False, reasons=reasons + [str(exc)], provenance=None)
    if reasons:
        return dict(g=0, form=form, recovery=False, reasons=reasons, provenance=None)
    qtype = prompt['type']
    row = dict(question_type=qtype, form=form, target='<think>\n' + text, answer=tail.strip().replace(
        '<answer>', '').replace('</answer>', '') if form == 'program' else tail.strip(),
        question=prompt.get('question', ''), options=prompt.get('options') or [],
        frame_indices=prompt.get('frame_indices') or list(range(prompt.get('n_frames', 32))))
    violations = grammar.validate_row(row)
    if violations:
        return dict(g=0, form=form, recovery=False, provenance=None,
                    reasons=sorted({'grammar_' + v.rule_id for v in violations}))
    recovery = form == 'program' and all_calls_failed(body)
    prov = dict(kind='direct')
    if form == 'direct' or recovery:
        reasons = direct_checks(body, prompt, answer)
        prov = dict(kind='recovery' if recovery else 'direct')
    elif prompt.get('options'):
        reasons, prov = program_option(body, prompt, answer)
        if reasons == ['unsupported_projection:categorical_option'] and allow_stated_option:
            reasons = direct_checks(body, prompt, answer)
            prov = dict(kind='stated_option_only')
    else:
        reasons, prov = program_numeric(body, prompt, answer)
    return dict(g=0 if reasons else 1, form=form, recovery=recovery, reasons=reasons, provenance=prov)
