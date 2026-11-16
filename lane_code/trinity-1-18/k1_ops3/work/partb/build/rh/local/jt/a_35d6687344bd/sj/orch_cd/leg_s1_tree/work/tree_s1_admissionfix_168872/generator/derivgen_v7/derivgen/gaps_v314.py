"""Additional scene programs using only forms parsed by the fixed 3.14 runtime."""
import math
import re
from . import ground_v312 as G
from .ground_v312_quality import candidate_identity

NEW_TYPES = ('object_rel_direction_easy', 'object_counting', 'relative_count', 'absolute_direction_object')
COUNT_TYPES = ('object_counting', 'relative_count')


def circular_error(a, b):
    a, b = float(a), float(b)
    if not math.isfinite(a) or not math.isfinite(b):
        return math.inf
    return abs((a - b + 180) % 360 - 180)


def rotation_sense(text):
    text = text.lower()
    ccw = bool(re.search(r'counter[ -]?clockwise|anti[ -]?clockwise', text))
    rest = re.sub(r'counter[ -]?clockwise|anti[ -]?clockwise', '', text)
    cw = 'clockwise' in rest
    if ccw == cw:
        raise G.RowRefusal('rotation_sense_ambiguous')
    return ccw


def question(item):
    r, t = item['roles'], item['type']
    if t == 'object_counting':
        return f"How many {r['obj']}(s) are in this room?"
    if t == 'relative_count':
        return (f"Are there more, fewer, or the same number of {r['a']}(s) "
                f"as {r['b']}(s) in this room?")
    if t == 'absolute_direction_object':
        text = item.get('source_question', item['question'])
        if rotation_sense(text) != bool(r['ccw']):
            raise G.RowRefusal('rotation_sense_mismatch')
        return text
    from .ground_v312_quality import direction_question
    return direction_question(item)


def comparison(a, b, options):
    relation = 'more' if a > b else 'fewer' if a < b else 'equal'
    def normalized(s):
        s = s.lower().strip()
        if s.startswith('more'): return 'more'
        if s.startswith(('fewer', 'less')): return 'fewer'
        if s.startswith('equal') or 'same' in s: return 'equal'
        return None
    matches = [(k,v) for k,v in G.option_map(options).items() if normalized(v) == relation]
    if len(matches) != 1:
        raise G.RowRefusal('nonunique_comparison_option')
    return (*matches[0], relation)


def printed_count(body):
    lines = body.splitlines()
    m = re.fullmatch(r'.+: (\d+) found', lines[0])
    if not m:
        raise G.RowRefusal('malformed_instance_list')
    entries = re.findall(r'^P[1-9][0-9]*: .+ instance (\d+) cam\d+ .*; first (\d+)$', body, re.M)
    n = int(m[1])
    if len(entries) != n or [int(i) for i,_ in entries] != list(range(1,n+1)):
        raise G.RowRefusal('instance_list_count_mismatch')
    if any(not 1 <= int(k) <= 32 for _,k in entries):
        raise G.RowRefusal('instance_frame_invalid')
    return n


def count_visible(item, session, name):
    """Check all native identities, including identities the session would skip."""
    expected = item.get('expected_instance_ids', {}).get(name)
    if expected is None and hasattr(session.instances, 'labels_for'):
        expected = [str(e['instance_id']) for e in session.instances(name)]
    if expected is not None:
        if hasattr(session.instances, 'clip'):
            from .instance_policy314 import valid_mask
            geo = session.instances.clip.geo
            for iid in expected:
                if not any(geo.has(k) and valid_mask(geo.inst[k-1] == int(iid)) for k in range(1,33)):
                    raise G.RowRefusal('instance_not_visible')
        found = [str(e['instance_id']) for e in session._instances(name)]
        if len(found) != len(set(found)) or set(found) != set(map(str, expected)):
            raise G.RowRefusal('instance_not_visible')


def render(item, session, token_count):
    t, r = item['type'], item['roles']
    if t == 'object_rel_direction_easy':
        return G.render(item, session, token_count)
    if session.events:
        raise ValueError('render requires a fresh session')
    if not item.get('gt_authority'):
        raise G.RowRefusal('independent_gt_authority_missing')
    lines, audit = ['<think>'], {}
    def emit(call):
        body = session.execute(call)
        lines.extend([call, G.wrap(body)])
        return body
    if t in COUNT_TYPES:
        names = [r['obj']] if t == 'object_counting' else [r['a'], r['b']]
        if len(set(names)) != len(names):
            raise G.RowRefusal('duplicate_count_operand')
        counts = {}
        lines.append('I count each observed instance once across the sampled frames.')
        for name in names:
            count_visible(item, session, name)
            body = emit(f'<ground obj="{G.valid_name(name)}" mode="instances">')
            counts[name] = printed_count(body)
        if t == 'object_counting':
            content = str(counts[names[0]])
            answer = G.letter(item['options'], content) if item.get('options') else content
            lines.append(f'So there are {content}.')
        else:
            a,b = (counts[n] for n in names)
            answer,content,rel = comparison(a,b,item['options'])
            op = {'more':'>','fewer':'<','equal':'='}[rel]
            lines.append(f'The counts satisfy {a} {op} {b}, so the answer is {answer} ({content}).')
        if str(item['gt_answer']) != answer:
            raise G.RowRefusal('independent_count_disagreement')
        audit['observed_counts'] = counts
        audit['native_instance_ids'] = item.get('expected_instance_ids', {})
    elif t == 'absolute_direction_object':
        if rotation_sense(item['question']) != bool(r['ccw']):
            raise G.RowRefusal('rotation_sense_mismatch')
        names = [r[k] for k in ('stand','face','query')]
        if len(set(names)) != 3:
            raise G.RowRefusal('duplicate_direction_operand')
        lines.append('I compute the signed floor angle from the three printed centres.')
        points = []
        for name in names:
            body = emit(f'<ground obj="{G.valid_name(name)}">')
            m = re.search(r'^(P[1-9][0-9]*): cam', body, re.M)
            if not m: raise G.RowRefusal('object_not_visible_drop')
            points.append(m[1])
        from .ground_v312_degenerate import lifted_facing_too_short
        if lifted_facing_too_short(item, session.objects):
            raise G.RowRefusal('lifted_facing_vector_below_object_extent')
        # The pinned runtime has no rule=signed. Its medium response exposes theta.
        call = '<angle S=%s F=%s Q=%s rule=medium>' % tuple(points)
        body = emit(call)
        result = session.registry.execute(call)['result']
        theta = int(re.search(r'; theta (-?\d+) deg;', body)[1])
        S,F,Q = [session.objects[n]['f1'] for n in names]
        u,v = [(p[0]-S[0],p[2]-S[2]) for p in (F,Q)]
        raw = math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]))
        if min(math.hypot(*p) for p in (u,v,result['u'],result['v'])) < .5:
            raise G.RowRefusal('short_floor_vector')
        if min(circular_error(theta,0), circular_error(raw,0)) <= 2:
            raise G.RowRefusal('rotation_wrap_margin')
        rotation = (theta if r['ccw'] else -theta) % 360
        raw_rotation = (raw if r['ccw'] else -raw) % 360
        if circular_error(rotation,raw_rotation) > 1:
            raise G.RowRefusal('rotation_rounding_disagreement')
        answer = content = str(rotation)
        if circular_error(answer,item['gt_answer']) > 15:
            raise G.RowRefusal('independent_rotation_disagreement')
        sense = 'counterclockwise' if r['ccw'] else 'clockwise'
        operand = str(theta) if r['ccw'] else f'-({theta})'
        lines.append(f'The {sense} rotation is ({operand}) mod 360 = {answer} degrees.')
        audit.update(printed_theta_deg=theta,unrounded_theta_deg=raw,ccw=r['ccw'])
    else:
        raise G.RowRefusal('unsupported_gap_type')
    lines += ['</think>', f'<answer>{answer}</answer>']
    suffix = '\n'.join(lines);tokens = token_count(suffix)
    if type(tokens) is not int or not 0 <= tokens <= 5000:
        raise G.RowRefusal('suffix_cap')
    return dict(candidate_id=candidate_identity(item),qid=item['qid'],type=t,question=item['question'],
        options=item.get('options',[]),answer=answer,answer_content=content,suffix=suffix,suffix_tokens=tokens,
        events=list(session.events),spec_version='3.14',trace_program_version='3.14',not_seen=False,
        simulated_misses=[],program_audit=audit)


def validate_computation(row):
    """Re-derive the final answer from public responses, without private audits."""
    t = row['type']
    bodies = [e['response'].removeprefix('<tool_response>\n').removesuffix('\n</tool_response>') for e in row['events']]
    if t in COUNT_TYPES:
        counts = [printed_count(b) for b in bodies]
        if len(counts) != (1 if t == 'object_counting' else 2):
            raise G.RowRefusal('wrong_count_calls')
        if t == 'object_counting':
            value = str(counts[0]);answer = G.letter(row['options'],value) if row['options'] else value
        else:
            answer,_,_ = comparison(*counts,row['options'])
    elif t == 'absolute_direction_object':
        theta = int(re.search(r'; theta (-?\d+) deg;',bodies[-1])[1])
        ccw = rotation_sense(row['question'])
        answer = str((theta if ccw else -theta)%360)
        sense = 'counterclockwise' if ccw else 'clockwise'
        operand = str(theta) if ccw else f'-({theta})'
        if f'The {sense} rotation is ({operand}) mod 360 = {answer} degrees.' not in row['suffix']:
            raise G.RowRefusal('rotation_computation_mismatch')
    else:
        answer = G.letter(row['options'],bodies[-1].rsplit('; ',1)[1])
    if answer != row['answer'] or not row['suffix'].endswith(f'<answer>{answer}</answer>'):
        raise G.RowRefusal('printed_answer_mismatch')
    return True
