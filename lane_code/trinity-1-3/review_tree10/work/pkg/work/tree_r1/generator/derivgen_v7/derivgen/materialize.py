"""Faithful replay of published canonical rows using printed head values.

The only dependency is the standard-library printed-point-calculator-v3. In derivgen
it is imported from .calculator; when vendored beside p3_printed_calculator.py that
module is used instead. No GT assets, geometry libraries, filesystem or network are
used. Inputs are never mutated.

printed maps every head call_id to one of:
  depth_at: {"points": {label: {"camera": [x,y,z], "f1": [x,y,z], "spread": s}}}
            (an ordered point list or a direct label mapping also works)
  move: {"delta": [dx,dy,dz], "distance": d}
  turn: {"value": integer_degrees}
  pose: {"t": [x,y,z], "yaw": integer_degrees}
The original tool_response objects (including their values dictionaries) are also
accepted. Numbers must already have the printed precision. Move distance is the
head's fixed-layer distance, never a norm recomputed from rounded components.

Unknown prose refuses rather than silently preserving a response-dependent claim.
Published v3.9 verbose direction conclusions imply their 0.30 m floor limit;
v3.10's concise conclusions imply 0.50 m. direction_floor_limit_m overrides this
when explicitly supplied. Category ties refuse. Frame-gap rows retain their admitted
frame choice independently of head values. Legacy turn choices use frame separation
and frame numbers; legacy score ties refuse. Equal point witnesses use
the calculator's documented input-order minimum (they do not choose a category).
"""
import copy
import math
import re
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext

if __package__:
    try:
        from .calculator import CalculatorError, PrintedPointRegistry
    except ModuleNotFoundError as exc:
        if exc.name != __package__ + '.calculator':
            raise
        from .p3_printed_calculator import CalculatorError, PrintedPointRegistry
else:
    from p3_printed_calculator import CalculatorError, PrintedPointRegistry

SUPPORTED_TYPES = (
    "camera_displacement", "camera_movement_direction", "camera_rotation",
    "object_rel_direction_medium", "object_rel_direction_hard",
    "object_abs_distance", "absolute_distance_object",
    "object_rel_distance", "relative_distance_object", "camera_obj_abs_dist",
)
SIGN_RULE = ("On the frame-1 floor (x right, z forward, y up) the calculator uses u = F - S and v = Q - S; "
             "cross = u_x*v_z - u_z*v_x > 0 means left and dot = u_x*v_x + u_z*v_z > 0 means front.")


class MaterializeRefusal(ValueError):
    """A stable machine-readable reason; the consumer should retain its GT row."""
    def __init__(self, reason):
        self.reason = str(reason)
        super().__init__(self.reason)


def _require(ok, reason):
    if not ok:
        raise MaterializeRefusal(reason)


def _number(value):
    _require(type(value) in (int, float), "invalid_printed_number")
    _require(math.isfinite(value), "nonfinite_printed_number")
    _require(Decimal(str(value)) == Decimal(str(value)).quantize(Decimal('.01')),
             "unrounded_printed_number")
    return value + 0.0


def _vector(value):
    _require(isinstance(value, (list, tuple)) and len(value) == 3, "invalid_printed_vector")
    return [_number(x) for x in value]


def _angle(value):
    value = _number(value)
    _require(value == int(value) and -180 <= value <= 180, "invalid_printed_angle")
    return int(value)


def _r2(value):
    return round(float(value), 2) + 0.0


def _f2(value):
    return f"{_r2(value):.2f}"


def _vec(value):
    return '(' + ', '.join(_f2(x) for x in value) + ')'


def _noun(name):
    name = name.replace("(s)", "").strip()
    prefix, _, word = name.rpartition(" ")
    singular = {"books": "book", "doors": "door", "chairs": "chair", "tables": "table",
                "lamps": "lamp", "cabinets": "cabinet", "shelves": "shelf", "bookshelves": "bookshelf",
                "boxes": "box", "benches": "bench", "couches": "couch", "sofas": "sofa",
                "beds": "bed", "windows": "window", "pictures": "picture", "frames": "frame"}
    word = singular.get(word, word)
    name = (prefix+" " if prefix else "") + word
    return "picture frame" if name == "frame" else name


def _poss(name):
    return _noun(name) + ("'" if name.endswith('s') else "'s")


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]


def _limit(uv):
    return .10 if min(*uv, *(1000-x for x in uv)) <= 40 else .25


def _options(options):
    if isinstance(options, dict):
        result = {str(k): str(v).strip() for k, v in options.items()}
    else:
        _require(isinstance(options, list), 'invalid_options')
        result = {}
        for i, text in enumerate(options):
            _require(isinstance(text, str), 'invalid_options')
            match = re.fullmatch(r'([A-Z])[.)]\s*(.+)', text.strip())
            key, value = match.groups() if match else (chr(65+i), text.strip())
            _require(key not in result, 'invalid_options')
            result[key] = value
    _require(all(re.fullmatch('[A-Z]', k) for k in result), 'invalid_options')
    return result


def _letter(options, value):
    matches = [k for k, v in options.items() if v.strip().lower() == str(value).strip().lower()]
    _require(bool(matches), 'answer_outside_options')
    _require(len(matches) == 1, 'option_tie')
    return matches[0]


def _scalar(payload, cid, key):
    if key in payload:
        return payload[key]
    if key == 'turn' and 'value' in payload:
        return payload['value']
    values = payload.get('values', payload)
    value = values[cid + '.' + key]
    return value['value'] if isinstance(value, dict) else value


def _render(events, answer):
    parts = ['<think>\n']
    for e in events:
        kind = e['kind']
        if kind == 'plan': parts.append(e['text'] + '\n\n')
        elif kind in ('canonical_text', 'correction'): parts.append(e['text'])
        elif kind == 'canonical_paragraph': parts.append('\n\n')
        elif kind in ('tool_call', 'calculator_call'):
            parts.append(e.get('prefix', '') + (e['command'] if kind == 'calculator_call' else e['token']))
        elif kind in ('tool_response', 'calculator_response'):
            text = e['response']['text'] if kind == 'calculator_response' else e['text']
            parts.append('<tool_response>' + text + '</tool_response>')
        elif kind != 'decision': raise MaterializeRefusal('unknown_event_kind')
    return ''.join(parts) + '\n</think>\n\n' + str(answer)


class _State:
    def __init__(self, row, decision, *, verify_metadata=False):
        self.row, self.decision = row, decision
        self.verify_metadata = verify_metadata
        self.registry = PrintedPointRegistry()
        self.calls, self.points, self.point_objects, self.point_uv = {}, {}, {}, {}
        self.heads, self.calcs, self.moves, self.turns = {}, [], {}, {}
        self.initials = {e['initial_label'] for e in row['events'] if e['kind'] == 'correction'}
        self.options = _options(row['options'])

    def noun(self, name):
        if self.row.get('trace_revision') in ('3.10.2', '3.11'): return name
        if self.row.get('trace_revision') in ('3.10.1', '3.10.2', '3.11'):
            return _noun(name)
        return 'picture frame' if name == 'frame' else name

    def poss(self, name):
        return self.noun(name) + ("'" if name.endswith('s') else "'s")

    def head(self, e, payload):
        _require(isinstance(payload, dict), 'invalid_printed_response')
        cid, name = e['call_id'], e['name']
        call = self.calls[cid]
        _require(call['name'] == name, 'invalid_program')
        out = copy.deepcopy(e)
        if name == 'depth_at':
            supplied = payload.get('points', payload)
            if isinstance(supplied, list):
                _require(len(supplied) == len(e['points']), 'point_coverage')
                _require(all(isinstance(p, dict) and 'label' in p for p in supplied), 'point_coverage')
                labels = [p['label'] for p in supplied]
                _require(len(set(labels)) == len(labels), 'point_coverage')
                supplied = {p['label']: p for p in supplied}
            _require(isinstance(supplied, dict) and set(supplied) == {p['label'] for p in e['points']}, 'point_coverage')
            _require(len(call['arguments']['pts']) == len(e['points']), 'point_coverage')
            points, values = [], {}
            for i, (p, uv) in enumerate(zip(e['points'], call['arguments']['pts'])):
                label = p['label']; new = supplied[label]
                # Only values change; caller-supplied frame/label metadata cannot retarget a click.
                for key in ('label', 'requested_frame', 'actual_frame'):
                    _require(key not in new or new[key] == p[key], 'program_changed')
                point = self.registry.register(camera=new['camera'], f1=new['f1'], spread=new['spread'],
                    requested_frame=p['requested_frame'], actual_frame=p['actual_frame'], label=label)
                _require(point['camera'][2] > 0, 'invalid_printed_depth')
                if label in self.initials:
                    _require(point['spread'] > _limit(uv), 'correction_trigger_changed')
                else:
                    _require(point['spread'] <= _limit(uv), 'new_spread_trigger')
                self.points[label] = point
                self.point_objects[label] = call['object']
                self.point_uv[label] = uv
                points.append(point)
                prefix = '' if len(e['points']) == 1 else str(i) + '.'
                for key, unit in (('camera', 'm'), ('f1', 'm'), ('spread', '1')):
                    values[cid + '.' + prefix + key] = {'value': point[key], 'unit': unit}
            out.update(points=points, values=values, text='\n'.join(p['line'] for p in points))
        elif name == 'move':
            delta, distance = _vector(_scalar(payload, cid, 'delta')), _number(_scalar(payload, cid, 'distance'))
            _require(distance >= 0, 'invalid_printed_distance')
            out['values'] = {cid+'.delta': {'value': delta, 'unit': 'm'}, cid+'.distance': {'value': distance, 'unit': 'm'}}
            out['text'] = (f'dx = {delta[0]:+.2f} m, dy = {delta[1]:+.2f} m, dz = {delta[2]:+.2f} m, '
                           f'distance = {_f2(distance)} m')
            self.moves[(call['arguments']['from'], call['arguments']['to'])] = distance
        elif name == 'turn':
            turn = _angle(_scalar(payload, cid, 'turn'))
            _require(turn != -180, 'invalid_printed_angle')
            out['values'] = {cid+'.turn': {'value': turn, 'unit': 'degree'}}
            out['text'] = f'turn = {turn:+d} deg'
            self.turns[(call['arguments']['from'], call['arguments']['to'])] = turn
        elif name == 'pose':
            t, yaw = _vector(_scalar(payload, cid, 't')), _angle(_scalar(payload, cid, 'yaw'))
            out['values'] = {cid+'.t': {'value': t, 'unit': 'm'}, cid+'.yaw': {'value': yaw, 'unit': 'degree'}}
            out['text'] = f'f1 centre {_vec(t)} m, yaw {yaw} deg'
        else:
            raise MaterializeRefusal('unsupported_head')
        self.heads[cid] = out
        return out

    def calculate(self, e):
        command = self.calls[e['call_id']]['command']
        result = self.registry.execute(command)
        _require(result['op'] in ('dist', 'closest', 'cam_dist', 'angle'), 'unsupported_calculator')
        args = result['arguments']
        refs = [p for k, v in args.items() if k != 'rule' for p in (v if isinstance(v, list) else [v])]
        _require(not self.initials.intersection(refs), 'correction_operand')
        self.calcs.append(result)
        return {**e, 'response': result}

    def pair(self, pair):
        key = tuple(pair)
        d, t = self.moves[key], self.turns[key]
        return d, t, _r2(d + abs(t)/50)

    def movement(self):
        heads = [e for e in self.heads.values() if e['name'] == 'move']
        _require(len(heads) == 1, 'invalid_program')
        e = heads[0]; cid = e['call_id']
        dx, _, dz = e['values'][cid+'.delta']['value']
        scores = {'forward': dz, 'backward': _r2(-dz), 'right': dx, 'left': _r2(-dx)}
        labels = [v.lower() for v in self.options.values()]
        _require(len(labels) >= 2 and all(l in scores for l in labels), 'unsupported_movement_option')
        ranked = sorted(labels, key=lambda l: -scores[l])
        _require(scores[ranked[0]] > 0, 'movement_no_positive_option')
        cp2 = self.row.get('frame_pair_rule')=='frame_gap' or 'margin_m' in self.row or 'margin_rel' in self.row
        if cp2:
            top,second = (Decimal(str(scores[l])) for l in ranked[:2])
            gap = top-second
            _require(gap>=Decimal('.10') and gap>=Decimal('.10')*top,'near_tie')
            if self.verify_metadata:
                _require(self.row.get('margin_m')==float(gap) and self.row.get('margin_rel')==float(gap/top),
                         'camera_margin_metadata')
        else:
            _require(scores[ranked[0]] != scores[ranked[1]], 'movement_tie')
        expl = {'forward': 'dz', 'backward': '-dz', 'right': 'dx', 'left': '-dx'}
        scoring = 'Scoring each option by the matching component: ' + '; '.join(
            f'{l} = {expl[l]} = {_f2(scores[l])} m' for l in labels) + '.'
        result = ranked[0]
        comparison = f'The largest is {self.noun(result)}.' + (
            ' It is a narrow call: the margin is under 0.10 m.' if not cp2 and _r2(scores[result]-scores[ranked[1]]) < .10 else '')
        return result, scoring, comparison

    def conclusion(self):
        family, binding = self.row['question_type'], self.decision['binding']
        result, value = None, None
        if family == 'camera_displacement':
            heads = [e for e in self.heads.values() if e['name'] == 'move']
            _require(len(heads) == 1, 'invalid_program')
            e = heads[0]; value = e['values'][e['call_id']+'.distance']['value']
            variants = [f'The printed distance is {_f2(value)} m, so the camera moved about {_f2(value)} m.']
        elif family == 'camera_rotation':
            heads = [e for e in self.heads.values() if e['name'] == 'turn']
            _require(len(heads) == 1, 'invalid_program')
            e = heads[0]; value = e['values'][e['call_id']+'.turn']['value']
            variants = [f'The camera rotation is {value} degrees; positive yaw means left.']
        elif family == 'camera_movement_direction':
            result, _, comparison = self.movement()
            variants = [comparison]
        elif family in ('object_rel_direction_medium', 'object_rel_direction_hard'):
            angles = [c for c in self.calcs if c['op'] == 'angle']
            _require(len(angles) == 1, 'invalid_program')
            c = angles[0]; r = c['result']; rule = family.rsplit('_', 1)[1]
            _require(c['arguments']['rule'] == rule, 'direction_rule_changed')
            texts = [e['text'].strip() for e in self.row['events'] if e['kind'] == 'canonical_text']
            legacy = texts[-1].startswith('The calculator puts ')
            floor = self.row.get('direction_floor_limit_m', .30 if legacy else .50)
            _require(type(floor) in (int, float) and math.isfinite(floor) and floor > 0, 'invalid_floor_limit')
            _require(min(math.hypot(*r[v]) for v in ('u', 'v')) >= floor, 'direction_degenerate_floor')
            if self.row.get('trace_revision') in ('3.10.1', '3.10.2', '3.11'):
                boundaries = (0,90,-90,180) if rule == 'hard' else (0,135,-135)
                margin = min(abs((r['theta']-b+180)%360-180) for b in boundaries)
                _require(margin >= 10, 'near_boundary_refused')
            result = r['label']
            variants = [f"The calculator puts the {self.noun(binding['query'])} at theta {r['theta']} deg, which the rule labels {result}.", '']
        elif family in ('object_abs_distance', 'absolute_distance_object'):
            cs = [c for c in self.calcs if c['op'] == 'closest']
            _require(len(cs) == 1, 'invalid_program')
            r = cs[0]['result']; value, witness = r['value'], r['witness']
            variants = [f"The closest pair is {witness['a']}-{witness['b']}, so the shortest distance between the {self.noun(binding['a'])} and the {self.noun(binding['b'])} is {_f2(value)} m."]
        elif family in ('object_rel_distance', 'relative_distance_object'):
            candidates, target = binding['cands'], binding['target']
            measured = {c: [] for c in candidates}
            for c in self.calcs:
                if c['op'] != 'closest': continue
                aa = {self.point_objects[p] for p in c['arguments']['A']}
                bb = {self.point_objects[p] for p in c['arguments']['B']}
                _require(aa == {target} and len(bb) == 1 and next(iter(bb)) in measured, 'invalid_distance_binding')
                measured[next(iter(bb))].append(c['result']['value'])
            _require(all(measured.values()), 'invalid_distance_binding')
            scores = [min(measured[c]) for c in candidates]
            order = sorted(range(len(scores)), key=lambda i: scores[i])
            _require(len(order) >= 2, 'invalid_distance_binding')
            if self.row.get('trace_revision') in ('3.10.2', '3.11'):
                low, second = (Decimal(str(scores[i])) for i in order[:2])
                _require(second-low >= Decimal('0.10') and second and (second-low)/second >= Decimal('0.10'), 'near_tie')
            else:
                _require(scores[order[0]] != scores[order[1]], 'distance_tie')
            result = candidates[order[0]]
            listing = ', '.join(f'{self.noun(c)} {_f2(s)} m' for c, s in zip(candidates, scores))
            variants = [f'The closest-point distances to the {self.noun(target)} are {listing}; the smallest is the {self.noun(result)}.']
        else:  # camera_obj_abs_dist
            cs = [c for c in self.calcs if c['op'] == 'cam_dist']
            _require(len(cs) == 1, 'invalid_program')
            c = cs[0]; r = c['result']; value = r['value']
            objects = {self.point_objects[p] for p in c['arguments']['points']}
            _require(len(objects) == 1, 'invalid_distance_binding')
            obj = next(iter(objects))
            variants = [f"The nearest clicked point of the {self.noun(obj)} is {r['witness']['point']} at {_f2(value)} m from the camera."]
        if value is not None:
            _require(self.decision['mode'] == 'numeric', 'invalid_decision')
            unit = self.decision['unit']
            factor, decimals = unit['factor'], unit['decimals']
            _require(type(decimals) is int and 0 <= decimals <= 12, 'invalid_unit')
            _require(type(factor) in (int, float) and math.isfinite(factor) and factor > 0, 'invalid_unit')
            if factor != 1:
                converted = Decimal(str(value)) * Decimal(str(factor))
                answer = format(converted.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN), f'.{decimals}f')
                variants = [text + f" {unit['unit']} = {_f2(value)} * {factor} = {answer}." for text in variants]
            else:
                answer = f'{value * factor:.{decimals}f}'
            if self.options:
                _require(any(v == answer for v in self.options.values()), 'answer_outside_options')
            return answer, answer, variants
        _require(self.decision['mode'] == 'option', 'invalid_decision')
        answer = _letter(self.options, result)
        return answer, result, [(text + f' That matches option {answer}.').strip() for text in variants]

    def layout(self, meta):
        a, b = meta['A'], meta['B']
        A, B = self.points[a]['f1'], self.points[b]['f1']
        dx, dz = B[0]-A[0], B[2]-A[2]
        lateral = 'to the right' if dx > 0 else 'to the left' if dx < 0 else 'at the same x'
        depth = 'ahead' if dz > 0 else 'behind' if dz < 0 else 'at the same z'
        x = f'{lateral} (x {_f2(B[0])} vs {_f2(A[0])})'
        z = f'{depth} (z {_f2(B[2])} vs {_f2(A[2])})'
        main = z + ' and ' + x if abs(dz) > abs(dx) else x + ' and ' + z
        return (f"In frame-1 coordinates (x right, z forward), relative to the {self.poss(self.point_objects[a])} middle {a}, "
                f"the {self.poss(self.point_objects[b])} middle {b} is {main}.")

    def sentence(self, e, final=False):
        if final:
            return self.conclusion()[2]
        if e['kind'] == 'correction':
            p = self.points[e['initial_label']]
            _require(self.point_uv[e['initial_label']] == e['initial'], 'invalid_correction')
            obj = self.noun(self.point_objects[e['initial_label']])
            goals = {'middle': f'nearer the middle of the {obj}',
                     'near': f'a little further inside the {obj}, nearer its front',
                     'replacement': f'another point on the {obj}'}
            _require(e['goal'] in goals, 'unknown_prose_template')
            return [f"The spread is {_f2(p['spread'])}, above {_f2(_limit(e['initial']))}, so this click is probably on an edge; I click {goals[e['goal']]}, at {e['next']}."]
        if 'candidate_group' in e:
            return [f"For the {self.noun(e['candidate_group']['object'])}:"]
        if 'pair_reuse' in e:
            m = e['pair_reuse']; i,j = m['from'],m['to']
            _require((i,j) in self.turns, 'reuse_before_readout')
            return [f"I reuse the printed turn for frames {i} and {j}."]
        if 'pair_score' in e:
            m = e['pair_score']; i, j = m['from'], m['to']; d, t, r = self.pair((i, j))
            return [f'r({i}, {j}) = {_f2(d)} + {abs(t)}/50 = {_f2(d)} + {_f2(abs(t)/50)} = {_f2(r)}.']
        if 'pair_pick' in e:
            m = e['pair_pick']; pairs = m['pairs']; i, j = m['selected']
            if m.get('rule') == 'frame_gap':
                _require(bool(pairs) and not m.get('skipped'), 'invalid_pair_choice')
                _require(all(isinstance(p, list) and len(p) == 2 and
                             all(type(k) is int and 1 <= k <= 32 and
                                 (self.row.get('head_layout') != 'paired_anchor' or k % 2 == 0)
                                 for k in p) for p in pairs), 'invalid_pair_choice')
                _require(len({tuple(p) for p in pairs}) == len(pairs), 'invalid_pair_choice')
                _require(isinstance(m['selected'], list) and all(type(k) is int for k in m['selected']) and
                         m['selected'] in pairs and
                         min(pairs,key=lambda p:(abs(p[0]-p[1]),*p)) == m['selected'], 'invalid_frame_gap_choice')
                return [f"I use frames {i} and {j}: among usable visible pairs, they have the smallest frame separation, with ties settled by the lower first frame, then the second."]
            _require('rule' not in m, 'invalid_pair_rule')
            if self.row.get('trace_revision') in ('3.10.1', '3.10.2', '3.11'):
                _require(bool(pairs) and not m.get('skipped'), 'invalid_pair_choice')
                _require(all(tuple(p) in self.turns for p in pairs), 'missing_pair_turn')
                selected = min(pairs, key=lambda p:(abs(self.turns[tuple(p)]),abs(p[0]-p[1]),*p))
                _require(selected == m['selected'], 'frame_pair_changed')
                if self.row.get('trace_revision') in ('3.10.2', '3.11'):
                    return [f"I use frames {i} and {j}, the only pair that shows both." if len(pairs) == 1 else
                            f"I use frames {i} and {j}: they have the smallest absolute printed turn, with ties settled by frame separation, then frame number."]
                return [f"I use frames {i} and {j}: they have the smallest absolute printed turn, with ties settled by time separation, then frame number."]
            if len(pairs) == 1:
                _require(pairs[0] == m['selected'], 'invalid_pair_choice')
                return [f'Frames {i} and {j} are the only candidate pair, so I use them.']
            usable = [p for p in pairs if p not in m.get('skipped', [])]
            _require(bool(usable), 'invalid_pair_choice')
            ranked = sorted(usable, key=lambda p: (self.pair(p)[2], abs(p[0]-p[1]), *p))
            # A printed r tie cannot justify "the smallest" unambiguously.
            if len(ranked) > 1:
                _require(self.pair(ranked[0])[2] != self.pair(ranked[1])[2], 'frame_pair_tie')
            _require(ranked[0] == m['selected'], 'frame_pair_changed')
            r = self.pair((i, j))[2]
            return [f'{opening}, frames {i} and {j} have the smallest r, {_f2(r)}, so I use them.' for opening in
                    ('Of these measured pairs', 'Among the usable measured pairs')]
        if 'common_layout' in e:
            return [self.layout(e['common_layout'])]
        if 'pair_context' in e:
            m = e['pair_context']; i, j = m['from'], m['to']
            return [f"For frames {i} and {j}, move components are in frame {i}'s level frame (x right, y up, z forward)."]
        if 'pair_skip' in e:
            m = e['pair_skip']
            return [f"The objects in frames {m['from']} and {m['to']} do not provide reliable interior clicks, so I skip this pair."]
        if 'click_object' in e:
            m = e['click_object']
            if e.get('click_covered'): return ['']
            return [f"I click the {self.noun(m['object'])} in frame {m['frame']}."]
        if 'selected_views' in e:
            m = e['selected_views']
            return ['I use ' + _join(f'the {self.noun(o)} in frame {k}' for o, k in zip(m['objects'], m['frames'])) + '.']
        if 'substitution' in e:
            m = e['substitution']
            return [f"The heads read out one frame per temporal pair, the even one, so for frame {m['from']} I use frame {m['to']}."]
        if 'frame_look' in e:
            m = e['frame_look']; fs, objs = m['frames'], m['objects']
            if len(set(fs)) == 1:
                return [f"Frame {fs[0]} shows {'both ' if len(objs) == 2 else ''}" + _join('the '+self.noun(o) for o in objs) + ', so one view is enough.']
            return ['The objects appear in different views; I will compare candidate views before combining the points.']
        if 'image_region' in e:
            m = e['image_region']; uv, middle = m['uv'], self.point_uv[m['middle']]
            horizontal = 'left' if uv[0] < middle[0] else 'right' if uv[0] > middle[0] else 'same column'
            vertical = 'upper' if uv[1] < middle[1] else 'lower' if uv[1] > middle[1] else 'same row'
            return [f"For the {self.noun(m['object'])} in frame {m['frame']}, I selected {uv}: {horizontal}, {vertical} relative to middle click {m['middle']} at {middle}."]
        family, binding = self.row['question_type'], self.decision['binding']
        if family == 'camera_movement_direction' and e['text'].strip().startswith('Scoring each option'):
            return [self.movement()[1]]
        static = ['First I locate both objects with a click near each middle.',
                  'The smallest distance over these click pairs is the closest-point distance.']
        if family.startswith('object_rel_direction_'):
            static.append(SIGN_RULE + (' The question counts an object as behind when I would turn at least 135 degrees.'
                                       if family.endswith('_medium') else ''))
        for call in self.calls.values():
            if call['kind'] != 'tool_call': continue
            args = call['arguments']
            if call['name'] == 'move' and family.startswith('camera_'):
                i, j = args['from'], args['to']
                static.append(f"The move tool gives the camera displacement from frame {i} to frame {j} in frame {i}'s level frame (x right, y up, z forward).")
            if call['name'] == 'depth_at' and family == 'camera_obj_abs_dist':
                k = args.get('image_frame', args['frame'])
                static.append(f"In frame {k} I click the part of the {self.noun(call['object'])} nearest the camera.")
        for candidate in binding.get('cands', []):
            static += [f'Now the {self.noun(candidate)}.', f'Now another {self.noun(candidate)}.',
                       f'Now one of the {self.noun(candidate)} (there is more than one, so I measure each and keep the nearest).']
        return static


def materialize(row, printed):
    """Return {events, answer, target}, or raise MaterializeRefusal(reason).

    This is fail-closed for changed programs, missing values, unknown templates and
    ambiguous decisions. A direction may change label if its rule, regenerated
    conclusion and available option agree; exact calculator boundaries refuse.
    """
    try:
        with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):
            return _materialize(row, printed)
    except MaterializeRefusal:
        raise
    except CalculatorError as exc:
        reason = {'rounding_boundary': 'direction_boundary', 'degenerate_heading': 'direction_degenerate_floor',
                  'degenerate_printed_angle': 'direction_degenerate_floor'}.get(exc.reason, 'calculator_' + exc.reason)
        raise MaterializeRefusal(reason) from exc
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError, DecimalException) as exc:
        raise MaterializeRefusal('invalid_input') from exc


def _materialize(row, printed):
    _require(isinstance(row, dict) and row.get('question_type') in SUPPORTED_TYPES, 'unsupported_type')
    events = row['events']
    _require(isinstance(events, list) and isinstance(printed, dict), 'invalid_input')
    revision = row.get('trace_revision')
    _require(revision in ('3.8', '3.9', '3.10', '3.10.1', '3.10.2', '3.11'), 'invalid_trace_revision')
    if revision == '3.11':
        _require(row.get('frame_pair_rule') == 'frame_gap', 'invalid_pair_rule')
    else:
        _require(row.get('frame_pair_rule') in (None, 'frame_gap'), 'invalid_pair_rule')
    if row.get('frame_pair_rule') == 'frame_gap':
        _require(row.get('frame_pair_turn') == [] and all(
            e['pair_pick'].get('rule') == 'frame_gap' for e in events if e.get('pair_pick')), 'invalid_pair_rule')
    decisions = [e for e in events if e['kind'] == 'decision']
    _require(len(decisions) == 1 and events[-1]['kind'] == 'decision', 'invalid_decision')
    decision = decisions[0]
    _require(decision['family'] == row['question_type'], 'invalid_decision')
    calls = {e['call_id']: e for e in events if e['kind'] in ('tool_call', 'calculator_call')}
    _require(len(calls) == sum(e['kind'] in ('tool_call', 'calculator_call') for e in events), 'duplicate_call_id')
    head_ids = {cid for cid, e in calls.items() if e['kind'] == 'tool_call'}
    _require(head_ids == set(printed), 'printed_call_coverage')
    _require(decision['call_ids'] == list(calls), 'invalid_program')
    final_index = max(i for i, e in enumerate(events) if e['kind'] == 'canonical_text')
    old, new = _State(row, decision, verify_metadata=True), _State(row, decision)
    # Static click-intent sentences can precede their calls. Dynamic data is added
    # only in event order, so prose cannot read a future response.
    old.calls = new.calls = calls
    output, seen_calls, seen_responses = [], set(), set()
    for index, e in enumerate(events):
        kind = e['kind']
        if kind in ('tool_call', 'calculator_call'):
            seen_calls.add(e['call_id'])
            changed = copy.deepcopy(e)
        elif kind in ('tool_response', 'calculator_response'):
            cid = e['call_id']
            _require(cid in seen_calls and cid not in seen_responses, 'invalid_program')
            seen_responses.add(cid)
            if kind == 'tool_response':
                baseline, changed = old.head(e, e), new.head(e, printed[cid])
                _require(baseline['text'] == e['text'], 'gt_response_mismatch')
            else:
                baseline, changed = old.calculate(e), new.calculate(e)
                _require(baseline['response']['text'] == e['response']['text'], 'gt_response_mismatch')
        elif kind in ('canonical_text', 'correction'):
            before = old.sentence(e, index == final_index)
            after = new.sentence(e, index == final_index)
            text = e['text'].lstrip(' '); prefix = e['text'][:len(e['text'])-len(text)]
            _require(text in before, 'unknown_prose_template')
            changed = {**copy.deepcopy(e), 'text': prefix + after[before.index(text)]}
        elif kind == 'decision':
            old_answer, old_result, _ = old.conclusion()
            answer, result, _ = new.conclusion()
            # R2 admission adds the trace's answer envelope. Compare the same
            # representation, and retain it on the regenerated training target.
            if re.fullmatch(r'<answer>[^<>]+</answer>', str(row['answer'])):
                old_answer = '<answer>' + str(old_answer) + '</answer>'
                answer = '<answer>' + str(answer) + '</answer>'
            _require(old_answer == row['answer'] and old_result == e['result'], 'gt_decision_mismatch')
            changed = {**copy.deepcopy(e), 'result': result}
        elif kind in ('plan', 'canonical_paragraph'):
            changed = copy.deepcopy(e)
        else:
            raise MaterializeRefusal('unknown_event_kind')
        output.append(changed)
    _require(seen_calls == seen_responses, 'invalid_program')
    for e in events:
        if e['kind'] == 'correction':
            label = e['corrected_label']
            _require(new.point_uv[label] == e['next'] and new.points[label]['actual_frame'] == e['frame'], 'invalid_correction')
    _require(_render(events, row['answer']) == row['target'], 'gt_target_mismatch')
    return {'events': output, 'answer': answer, 'target': _render(output, answer)}
