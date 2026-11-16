"""SPEC v3.12 rows. Geometry is delegated to the decode-time lifting backend."""
import importlib.util
import math
import re
from decimal import Decimal
from collections import Counter, defaultdict
from pathlib import Path

from .calculator import PrintedPointRegistry

TYPES = ('object_abs_distance', 'object_rel_distance',
         'object_rel_direction_medium', 'object_rel_direction_hard', 'object_rel_direction_easy')
NAME = r'[^"<>\x00-\x1f\x7f]+'
GROUND = re.compile(r'<ground obj="(' + NAME + r')">')
GAP = re.compile(r'<gap a="(' + NAME + r')"((?: b="' + NAME + r'")+)>')


class RowRefusal(ValueError):
    pass


def load_backend(path):
    """Explicit file path and receipt pin; never choose a different backend silently."""
    spec = importlib.util.spec_from_file_location('v312_decode_lifting', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ('lift_object', 'render_ground', 'gap_objects', 'render_gap', 'render_gaps'):
        if not callable(getattr(mod, name, None)):
            raise ValueError('backend missing ' + name)
    return mod


def valid_name(name):
    if not isinstance(name, str) or not re.fullmatch(NAME, name) or name != name.strip():
        raise RowRefusal('invalid_object_name')
    return name


def wrap(body):
    return '<tool_response>\n' + body + '\n</tool_response>'


class Session:
    """A fresh registry per row; masks are callback(name)->(mask, probability)."""
    def __init__(self, backend, geometry, masks, tau=.5, simulated_misses=()):
        self.backend, self.geometry, self.masks, self.tau = backend, geometry, masks, tau
        self.registry, self.objects, self.events = PrintedPointRegistry(), {}, []
        self.simulated_misses = set(simulated_misses)

    def execute(self, call):
        match = GROUND.fullmatch(call)
        if match:
            name = valid_name(match[1])
            masks, prob = self.masks(name)
            result = self.backend.lift_object(name, masks, prob, self.geometry, tau=self.tau)
            if name in self.simulated_misses:
                if not result['seen']:
                    raise RowRefusal('simulated_miss_requires_visible_object')
                result = dict(result, seen=False, simulated_miss=True)
            self.objects[name] = result
            body = self.backend.render_ground(result, self.registry)
        elif (match := GAP.fullmatch(call)):
            a = valid_name(match[1])
            bs = [valid_name(n) for n in re.findall(r' b="(' + NAME + r')"', match[2])]
            if len(set(bs)) != len(bs):
                raise RowRefusal('duplicate_gap_candidate')
            if not all(n in self.objects and self.objects[n]['seen'] for n in [a, *bs]):
                body = 'not seen'
            elif len(bs) > 1:
                body = self.backend.render_gaps(self.objects[a], [self.objects[b] for b in bs])
            else:
                body = self.backend.render_gap(self.objects[a], self.objects[bs[0]])
        else:
            if call.startswith(('<ground', '<gap')):
                raise RowRefusal('malformed_ground_call')
            body = self.registry.execute(call)['text']
        event = dict(call=call, response=wrap(body))
        self.events.append(event)
        return body


def option_map(options):
    result = {}
    for option in options:
        m = re.fullmatch(r'([A-Z])\.\s*(.+)', option)
        if not m or m[1] in result:
            raise RowRefusal('invalid_options')
        result[m[1]] = m[2].strip()
    return result


def letter(options, content):
    found = [k for k, v in option_map(options).items() if v.lower() == content.lower()]
    if len(found) != 1:
        raise RowRefusal('nonunique_answer_option')
    return found[0]


def direct_continuation(item):
    from .ground_v312_quality import validate_join, continuation_reason
    value = item.get('direct_canonical')
    if not isinstance(value, dict):
        raise RowRefusal('missing_direct_canonical')
    validate_join(item, value)
    body = value.get('body', '')
    if (value.get('form') != 'vqa_canonical' or not value.get('source_sha256')
            or len(body.split()) < 12 or '<' in body or re.search(r'\btool\b', body, re.I) or re.search(r'\bP[1-9][0-9]*\b', body)):
        raise RowRefusal('invalid_direct_canonical')
    reason = continuation_reason(item, body, value['answer'])
    if reason:
        raise RowRefusal(reason)
    return body, item.get('option_letter_map', {}).get(value['answer'], value['answer'])


def parse_roles(item, T):
    q = dict(question_type=item['type'], question=item['question'], options=item.get('options', []))
    try:
        return T.parse_vsi(q)
    except (AttributeError, KeyError, ValueError):
        from .paraphrase import parse_paraphrase
        roles = parse_paraphrase(q, T)
        if not roles:
            raise RowRefusal('unparsed_question')
        return roles


def render(item, session, token_count):
    """Use supplied semantic roles; caller binds them to the original question."""
    typ, roles = item['type'], item['roles']
    if typ not in TYPES:
        raise RowRefusal('direct_type')
    if typ == 'object_abs_distance':
        names = [roles['a'], roles['b']]
        plan = 'I will ground both objects and read their closest-point distance.'
    elif typ == 'object_rel_distance':
        names = [roles['target'], *roles['cands']]
        if len(roles['cands']) < 2 or len(set(roles['cands'])) != len(roles['cands']):
            raise RowRefusal('invalid_candidates')
        plan = 'I will ground the objects and compare their closest-point distances.'
    else:
        names = [roles[k] for k in ('stand', 'face', 'query')]
        plan = 'I will ground the three objects and compare their directions on the floor.'
    if session.events:
        raise ValueError('render requires a fresh session')
    lines, points, absent, audit = ['<think>', plan], {}, False, {}
    miss_name = None

    def emit(call):
        body = session.execute(call)
        lines.extend([call, wrap(body)])
        return body

    for name in dict.fromkeys(names):
        body = emit(f'<ground obj="{valid_name(name)}">')
        if body == name + ': not seen':
            miss_name = name
            absent = True
            break
        m = re.search(r'^([P][1-9][0-9]*): cam', body, re.M)
        if not m:
            raise RowRefusal('backend_missing_point')
        points[name] = m[1]
    content = answer = 'not seen'
    if not absent and typ == 'object_abs_distance':
        body = emit(f'<gap a="{roles["a"]}" b="{roles["b"]}">')
        absent = body == 'not seen'
        if not absent:
            answer = content = body.splitlines()[0].removesuffix(' m')
            raw = session.backend.gap_objects(session.objects[roles['a']], session.objects[roles['b']])
            audit['unrounded_gap_m'] = raw
            if 'gt_answer' in item:
                gt = float(item['gt_answer'])
                if (abs(raw-gt) <= .05*abs(gt)) != (abs(float(answer)-gt) <= .05*abs(gt)):
                    raise RowRefusal('rounding_tolerance_flip')
                audit.update(gt_absolute_error=abs(float(answer)-gt),
                             gt_relative_error=abs(float(answer)-gt)/abs(gt) if gt else None)
            lines.append(f'The closest-point distance is {answer} m.')
    elif not absent and typ == 'object_rel_distance':
        body = emit(f'<gap a="{roles["target"]}"' + ''.join(f' b="{c}"' for c in roles['cands']) + '>')
        absent = body == 'not seen'
        if not absent:
            gap_lines = [line for line in body.splitlines() if not re.match(r'^P[1-9][0-9]*:', line)]
            if len(gap_lines) != len(roles['cands'])+1:
                raise RowRefusal('malformed_gap_response')
            distances = [(Decimal(line.rsplit(': ', 1)[1].removesuffix(' m')), candidate)
                         for candidate, line in zip(roles['cands'], gap_lines[:-1])]
            distances.sort()
            first, second = distances[:2]
            if second[0] - first[0] < max(Decimal('.10'), Decimal('.10') * second[0]):
                raise RowRefusal('near_tie')
            match = re.fullmatch(r'min "(' + NAME + r')" [0-9]+\.[0-9]{2} m', gap_lines[-1])
            if not match:
                raise RowRefusal('nonunique_printed_minimum')
            content = match[1]
            raw = [(session.backend.gap_objects(session.objects[roles['target']], session.objects[c]), c)
                   for c in roles['cands']]
            raw.sort()
            if raw[0][1] != content or first[1] != content:
                raise RowRefusal('rounding_decision_flip')
            if raw[1][0]-raw[0][0] < max(.10, .10*raw[1][0]):
                raise RowRefusal('unrounded_near_tie')
            audit.update(unrounded_gaps=raw, margin_m=float(second[0]-first[0]),
                         margin_rel=float((second[0]-first[0])/second[0]))
            answer = letter(item['options'], content)
            lines.append(f'The tool names {content} as the minimum, so the answer is {answer}.')
    elif not absent:
        from .ground_v312_degenerate import lifted_facing_too_short
        if lifted_facing_too_short(item, session.objects):
            raise RowRefusal('lifted_facing_vector_below_object_extent')
        rule = typ.rsplit('_', 1)[1]
        lines.append('On the floor, cross > 0 means left; cross < 0 means right.')
        call = '<angle ' + ' '.join(f'{a}={points[roles[r]]}' for a, r in
                                    [('S', 'stand'), ('F', 'face'), ('Q', 'query')]) + f' rule={rule}>'
        body = emit(call)
        result = session.registry.execute(call)['result']
        if min(math.hypot(*result[k]) for k in ('u', 'v')) < .50:
            raise RowRefusal('short_floor_vector')
        boundaries = (0, 180) if rule == 'easy' else (0, 90, 180, 270) if rule == 'hard' else (0, 135, 225)
        margin = 5 if rule == 'easy' else 10
        if min(abs((result['theta']-b+180) % 360-180) for b in boundaries) < margin:
            raise RowRefusal('near_boundary_refused')
        content = body.rsplit('; ', 1)[1]
        S, F, Q = [session.objects[roles[r]]['f1'] for r in ('stand', 'face', 'query')]
        u, v = [(p[0]-S[0], p[2]-S[2]) for p in (F, Q)]
        theta = math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0], u[0]*v[0]+u[1]*v[1]))
        raw_content = (('front-' if abs(theta)<90 else 'back-') + ('left' if theta>0 else 'right')
                       if rule=='hard' else 'back' if rule == 'medium' and abs(theta)>=135 else 'left' if theta>0 else 'right')
        if raw_content != content:
            raise RowRefusal('rounding_decision_flip')
        if min(math.hypot(*p) for p in (u,v)) < .50 or min(abs((theta-b+180)%360-180) for b in boundaries)<margin:
            raise RowRefusal('unrounded_direction_margin')
        audit.update(unrounded_theta_deg=theta, printed_theta_deg=result['theta'],
                     floor_vectors_m=[math.hypot(*p) for p in (u,v)],
                     boundary_margin_deg=min(abs((theta-b+180)%360-180) for b in boundaries))
        answer = letter(item['options'], content)
        lines.append(f'The printed direction is {content}, so the answer is {answer}.')
    if absent:
        if miss_name is None:
            raise RowRefusal('gap_unavailable')
        continuation, answer = direct_continuation(item)
        content = option_map(item['options']).get(answer, answer)
        lines.append(f'The tool did not find {miss_name}, so I estimate from the frames.')
        lines.append(continuation)
    lines.extend(['</think>', f'<answer>{answer}</answer>'])
    suffix = '\n'.join(lines)
    tokens = token_count(suffix)
    if type(tokens) is not int or tokens < 0:
        raise ValueError('token counter must return a nonnegative integer')
    if tokens > 5000:
        raise RowRefusal('suffix_cap')
    from .ground_v312_quality import candidate_identity
    return dict(candidate_id=candidate_identity(item, session.simulated_misses),
                qid=item['qid'], type=typ, question=item['question'], options=item.get('options', []),
                suffix=suffix, answer=answer, answer_content=content, suffix_tokens=tokens,
                events=list(session.events), spec_version=getattr(session, 'spec_version', '3.12.2'), not_seen=absent,
                simulated_misses=sorted(session.simulated_misses), program_audit=audit)


def replay(row, session):
    """Replay exact events through a new decode backend, including calculator state."""
    validate_evidence(row)
    for event in row['events']:
        if wrap(session.execute(event['call'])) != event['response']:
            raise RowRefusal('replay_text_mismatch')
    return True


def validate_evidence(row):
    """Reject detached event logs, edited responses and invented public references."""
    remaining = row['suffix']
    printed = set()
    for event in row['events']:
        block = event['call'] + '\n' + event['response']
        if block not in remaining:
            raise RowRefusal('suffix_event_mismatch')
        before, remaining = remaining.split(block, 1)
        if '<tool_response>' in before:
            raise RowRefusal('unrecorded_response')
        if re.search(r'\bP[1-9][0-9]*\b', before) and not set(re.findall(r'\bP[1-9][0-9]*\b', before)) <= printed:
            raise RowRefusal('unprinted_point_reference')
        printed.update(re.findall(r'^(P[1-9][0-9]*): (?:[^\n]* )?cam[1-9][0-9]* ', event['response'], re.M))
        if event['call'].startswith(('<angle ', '<dist ', '<turn ')):
            if not set(re.findall(r'\bP[1-9][0-9]*\b', event['call'])) <= printed:
                raise RowRefusal('unprinted_point_reference')
    if '<tool_response>' in remaining:
        raise RowRefusal('unrecorded_response')
    if not set(re.findall(r'\bP[1-9][0-9]*\b', remaining)) <= printed:
        raise RowRefusal('unprinted_point_reference')
    return True


def histogram(rows):
    out = defaultdict(Counter)
    for row in rows:
        out[row['type']][row['answer_content']] += 1
    return {t: dict(sorted(c.items())) for t, c in sorted(out.items())}


def select_balanced(rows, distributions, per_type):
    from .ground_v312_balance import balance
    return balance(rows, distributions, per_type, _select_content)


def _select_content(rows, distributions, per_type):
    """Largest-remainder quotas from benchmark content; no duplication or relabeling."""
    buckets, seen = defaultdict(list), set()
    def key(row):
        if row['type'] == 'object_rel_distance':
            return row['answer']
        if row['type'] == 'object_abs_distance':
            bins = distributions.get(row['type'], {}).get('bins', [])
            value = float(row.get('gt_answer', row['answer']))
            matches = [b['key'] for b in bins if value >= b['lo']
                       and (b['hi'] is None or value < b['hi'])]
            if len(matches) > 1:
                raise ValueError('overlapping_benchmark_bins')
            return matches[0] if matches else 'unbinned'
        return row['answer_content']
    for row in sorted(rows, key=lambda r: r['qid']):
        identity = (row['type'], row['qid'])
        if identity in seen:
            raise ValueError('duplicate_qid')
        seen.add(identity)
        buckets[row['type'], key(row)].append(row)
    selected, report = [], {}
    for typ in sorted({r['type'] for r in rows}):
        distribution = distributions.get(typ, {}).get('letters' if typ=='object_rel_distance' else 'content', {})
        if typ == 'object_abs_distance' and not distributions.get(typ, {}).get('bins'):
            distribution = {}
        if not distribution:
            report[typ] = dict(status='PENDING-INPUT benchmark distribution', selected=0)
            continue
        if any(type(n) is not int or n <= 0 for n in distribution.values()):
            raise ValueError('invalid_benchmark_counts')
        total = sum(distribution.values())
        raw = {label: per_type * n / total for label, n in distribution.items()}
        quota = {label: math.floor(n) for label, n in raw.items()}
        for label in sorted(raw, key=lambda k: (-(raw[k]-quota[k]), k))[:per_type-sum(quota.values())]:
            quota[label] += 1
        if typ=='object_abs_distance' and 'cap_per_bin' in distributions[typ]:
            cap = distributions[typ]['cap_per_bin']
            if type(cap) is not int or cap <= 0:
                raise ValueError('invalid distance_bin_cap')
            quota = {label:min(n,cap) for label,n in distribution.items()}
        shortage = {}
        for label, n in sorted(quota.items()):
            available = buckets[typ, label]
            selected.extend(available[:n])
            shortage[label] = max(0, n-len(available))
        report[typ] = dict(target=quota, shortage=shortage,
                          axis='answer_letter' if typ=='object_rel_distance' else 'distance_bin' if typ=='object_abs_distance' else 'answer_content',
                          source=distributions[typ].get('source','pinned existing benchmark aggregate'),
                          unsupported_content=sorted({key(r) for r in rows if r['type']==typ}-set(quota)))
    return selected, report
