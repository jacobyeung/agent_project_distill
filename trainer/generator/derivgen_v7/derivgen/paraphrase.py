"""Complete recognized source templates for direction, appearance and distance.

Only parser-local case/whitespace normalization is allowed. Unknown wording returns
None. These bindings establish source semantics, never label agreement or admission.
"""
import re

DIRECTION = {
    'object_rel_direction_easy': [
        'Standing at the {S} facing the {F}, does the {Q} lie on its left or right?',
        'Positioned by the {S} and facing toward the {F}, on which side—left or right—is the {Q}?',
        "If I stand near the {S}, looking toward the {F}, is the {Q} on the {R}'s left or right?",
        "If I'm next to the {S} looking at the {F}, will the {Q} be seen to its left or right?",
        'Standing next to the {S} and looking toward the {F}, is the {Q} on the left or right of the {R}?',
        'Facing the {F} from the {S}, can you confirm if the {Q} is on its left side or its right side?',
        "If I'm at the {S}, looking directly at the {F}, does the {Q} sit on its left or right side?",
        "If I'm located by the {S} and oriented toward the {F}, would the {Q} be positioned to its left or right side?",
        "If I'm standing by the {S}, looking toward the {F}, would the {Q} appear on the left or right side of it?",
        "If I'm standing near the {S} looking at the {F}, is the {Q} to the left or to the right of it?",
        'Standing adjacent to the {S} and viewing the {F}, is the {Q} on the left side or the right side?',
        'When at the {S}, facing the {F}, is the {Q} found to the left or to the right?',
        'When positioned beside the {S} and looking at the {F}, is the {Q} placed on the left or right?',
        'While standing at the {S} and facing the {F}, which side of the {R} is the {Q} on—left or right?',
        'From my position at the {S}, facing toward the {F}, is the {Q} to the left or right of the {R}?',
        "I'm standing near the {S} and facing toward the {F}; is the {Q} situated to the left or right of the {R}?",
        "If I'm positioned at the {S} and oriented toward the {F}, would the {Q} be to the left or right of it?",
        "When I'm at the {S}, looking directly toward the {F}, is the {Q} located to the left or right?",
        'From the perspective of standing at the {S} and facing toward the {F}, does the {Q} lie to its left or right?',
        'Standing beside the {S} and facing the {F}, which side—left or right—is the {Q} located on?',
        'Standing next to the {S}, and facing the {F}, do you see the {Q} positioned to the left or to the right?',
        'With the {S} next to me and the {F} ahead, is the {Q} positioned on the left or right of the {R}?',
        'If I stand alongside the {S} and face the {F}, will I find the {Q} to the left or the right of the {R}?',
        'Standing next to the {S} and looking toward the {F}, should I expect the {Q} to my left or right of the {R}?',
        "When I'm beside the {S} facing toward the {F}, is the {Q} located to its left or right?",
    ],
    'object_rel_direction_hard': [
        'From the viewpoint at the {S} looking toward the {F}, is the {Q} at my front-left, front-right, back-left, or back-right?',
        'Standing at the {S}, oriented toward the {F}, would the {Q} appear at my front-left, front-right, back-left, or back-right?',
        'Standing by the {S}, directed toward the {F}, does the {Q} lie front-left, front-right, back-left, or back-right from my viewpoint?',
        'From the position of the {S} facing the {F}, where is the {Q} relative to me: front-left, front-right, back-left, or back-right?',
        "If I'm positioned at the {S} and facing the {F}, would the {Q} be in my front-left, front-right, back-left, or back-right?",
        'If located at the {S} and looking toward the {F}, in what direction is the {Q}: front-left, front-right, back-left, or back-right?',
        'Standing near the {S} and looking at the {F}, is the {Q} positioned at my front-left, front-right, back-left, or back-right?',
        'At the point of the {S}, facing the {F}, identify if the {Q} is at my front-left, front-right, back-left, or back-right.',
        'At the {S}, with my gaze fixed on the {F}, is the {Q} positioned front-left, front-right, back-left, or back-right relative to me?',
        'From the place of the {S} looking at the {F}, can you confirm if the {Q} is toward my front-left, front-right, back-left, or back-right?',
        'If standing near the {S} and facing the {F}, would the {Q} be front-left, front-right, back-left, or back-right relative to my view?',
        'When positioned at the {S} and looking toward the {F}, in which direction would I find the {Q}: front-left, front-right, back-left, or back-right?',
        'With the {S} as my location and looking at the {F}, in which direction is the {Q}: front-left, front-right, back-left, or back-right?',
        'At the location of the {S}, while facing the {F}, is the {Q} situated front-left, front-right, back-left, or back-right of me?',
        'At the spot of the {S}, facing toward the {F}, is the {Q} in my front-left, front-right, back-left, or back-right?',
        'From the standpoint of the {S} and facing the {F}, is the {Q} found front-left, front-right, back-left, or back-right?',
        "I'm at the {S}, looking toward the {F}. Is the {Q} located at my front-left, front-right, back-left, or back-right?",
        'With my position at the {S} looking toward the {F}, determine if the {Q} is at my front-left, front-right, back-left, or back-right.',
    ],
    'object_rel_direction_medium': [
        'Looking at the {F} from my spot by the {S}, is the {Q} situated left, right, or behind?',
        'From my stance at the {S}, looking straight towards the {F}, is the {Q} positioned on my left, right, or at my back?',
        "Standing by the {S}, if I'm looking towards the {F}, is the {Q} situated to my left, right, or behind?",
        'When standing next to the {S} and gazing at the {F}, would the {Q} be on my left, right, or behind?',
        'From my position near the {S}, looking directly at the {F}, is the {Q} on my left side, right side, or behind?',
        "I'm positioned at the {S}, looking toward the {F}; is the {Q} placed to my left, right, or behind me?",
        'If I am near the {S}, turned toward the {F}, is the {Q} found on my left, right, or rear?',
        'Standing at the {S} and facing directly towards the {F}, is the {Q} on my left, right, or to my back?',
        'Facing the {F} from the {S}, would the {Q} be placed left, right, or behind me?',
        'If I position myself at the {S}, aiming toward the {F}, is the {Q} to my left, right, or behind me?',
        "If I'm positioned near the {S} and looking at the {F}, would the {Q} be found to my left, right, or back?",
        "If my location is beside the {S} and I'm facing towards the {F}, is the {Q} to my left, right, or rear?",
        'Standing alongside the {S} and facing the {F}, does the {Q} lie to my left, right, or behind?',
        'Standing near the {S} and facing the {F}, would the {Q} be positioned to my left, right, or rear?',
        'When next to the {S}, viewing the {F}, is the {Q} situated on my left, right, or behind?',
        "I'm near the {S}, oriented toward the {F}. Is the {Q} found to my left, right, or behind?",
        "If I'm at the {S}, looking at the {F}, is the {Q} located to my left, right, or behind me?",
        'Standing close to the {S}, facing the {F}, where is the {Q}: to my left, right, or behind?',
        'Standing near the {S}, directing my view towards the {F}, is the {Q} located left, right, or behind?',
        'When next to the {S} and directed towards the {F}, does the {Q} lie to my left, right, or behind me?',
        'From my place by the {S}, facing the {F}, is the {Q} on my left side, right side, or behind?',
        'If I stand by the {S}, oriented toward the {F}, where is the {Q}: left, right, or behind?',
        "If I'm next to the {S}, looking towards the {F}, is the {Q} on my left, right, or behind me?",
        'Facing the {F} while positioned by the {S}, is the {Q} located to my left, right, or back?',
        'If I stand beside the {S}, directed towards the {F}, would I find the {Q} to my left, right, or behind?',
    ],
}

# Each definition belongs to the medium main sentence at the same index. All
# express a minimum 135-degree turn from facing F to face Q; no free-form tail.
MEDIUM_TAILS = [
    'Behind means I must rotate at least 135 degrees.',
    "'Back' means a turn of at least 135 degrees.",
    'Behind requires turning at least 135 degrees to face it.',
    'Behind indicates needing to turn 135 degrees or more to face it.',
    "'Behind' involves turning at least 135 degrees to face it.",
    "'Behind' suggests turning at least 135 degrees to see it.",
    'To my rear means rotating at least 135 degrees.',
    "'To my back' means I'd need a 135-degree or greater rotation.",
    "'Behind' means I'd have to turn at least 135 degrees.",
    'Behind signifies at least a 135-degree rotation is required.',
    "'Back' means rotating at least 135 degrees to face it.",
    "'Rear' means I'd need to rotate at least 135 degrees.",
    'Behind means a minimum 135-degree turn is needed.',
    "'Rear' implies needing at least a 135-degree rotation to face it.",
    'Behind involves turning at least 135 degrees.',
    "'Behind' implies I need at least a 135-degree turn.",
    'Behind means rotating 135 degrees or more to see it clearly.',
    "'Behind' means turning at least 135 degrees around.",
    'Behind means I would turn 135 degrees or more to face it.',
    "'Behind' means turning at least 135 degrees around to face it.",
    "'Behind' indicates needing to rotate at least 135 degrees.",
    'An object behind requires turning 135 degrees or more to face it directly.',
    "'Behind' means turning at least 135 degrees to face it.",
    "'Back' means I'd have to turn at least 135 degrees to face it.",
    "'Behind' implies turning 135 degrees or more.",
]

# C is the entire ordered category list, with the stated list punctuation.
# Each instruction asks for earliest occurrence in ascending video time.
APPEARANCE = [
    ('Arrange these categories by their initial appearance in the video: {C}.', 'comma'),
    ('Determine the initial appearance order of these categories in the video: {C}.', 'comma'),
    ('How will {C} appear sequentially for the first time in the video?', 'oxford'),
    ('Identify the order of first occurrences of these categories in the video: {C}.', 'comma'),
    ('Provide the order of the first appearances of these categories within the video: {C}.', 'comma'),
    ('What will be the sequence of first-time occurrences for the following video categories: {C}?', 'comma'),
]

# C lists candidate categories; T is the target. Every complete instruction
# specifies closest points and chooses the closest instance for multiplicities.
REL_DISTANCE = [
    'Based on measuring from their closest points, which among ({C}) lies nearest to the {T}? If several exist, measure to the closest one.',
    'By using the closest points, identify which of these ({C}) is nearest to the {T}. If there are multiple objects, select the closest one.',
    "Considering each object's nearest point, which of these objects ({C}) is nearest the {T}? In case of duplicates, measure to the closest.",
    'Considering the nearest points, which of these ({C}) is closest to the {T}? If there are multiple, identify the closest instance.',
    'Measure from the closest point: among these options ({C}), which is nearest to the {T}? Use the closest instance if multiples occur.',
    'Measuring distance from the nearest points, select the closest object ({C}) to the {T}. If multiple exist, use the nearest instance.',
    'Using proximity from their closest points, determine the closest object from ({C}) to the {T}. For multiples, measure the nearest one.',
    'Which of these ({C}) is closest to the {T}, measuring from their nearest points? If more than one exists, use the closest instance.',
]

OBJECT = r"[^\W\d_](?:[^\W\d_]|[ -])*?"
GROUPS = {"S": f"(?P<stand>{OBJECT})", "F": f"(?P<face>{OBJECT})",
          "Q": f"(?P<query>{OBJECT})", "R": "(?P=face)"}
FULL_DIRECTION = {
    t: [s + (' ' + MEDIUM_TAILS[i] if t == 'object_rel_direction_medium' else '')
        for i, s in enumerate(templates)] for t, templates in DIRECTION.items()
}


def _compile(template, groups):
    return re.compile(''.join(groups[p[1]] if p in {'{' + k + '}' for k in groups}
                              else re.escape(p)
                              for p in re.split(r'(\{[A-Z]\})', template)), re.I)


COMPILED = {t: [_compile(s, GROUPS) for s in templates]
            for t, templates in FULL_DIRECTION.items()}
DISTANCE_COMPILED = [_compile(s, {'C': f'(?P<cands>{OBJECT}(?:, {OBJECT})+)',
                                 'T': f'(?P<target>{OBJECT})'}) for s in REL_DISTANCE]
CHOICES = {
    'object_rel_direction_easy': {'left', 'right'},
    'object_rel_direction_medium': {'left', 'right', 'back'},
    'object_rel_direction_hard': {'front-left', 'front-right', 'back-left', 'back-right'},
}


def _norm(s):
    return ' '.join(s.lower().split())


def _referents(q, T):
    options = list(T.option_texts(q['options']).values())
    normalized = [_norm(o) for o in options]
    if (len(options) != len(q['options']) or not all(normalized)
            or len(set(normalized)) != len(normalized)):
        return [], []
    return options, normalized


def _direction(q, T):
    _, normalized = _referents(q, T)
    if set(normalized) != CHOICES[q['question_type']]: return None
    text = ' '.join(q['question'].split())
    found = [m for m in (rx.fullmatch(text) for rx in COMPILED[q['question_type']]) if m]
    if len(found) != 1: return None
    plan = {k: found[0].group(k).strip() for k in ('stand', 'face', 'query')}
    if len({_norm(v) for v in plan.values()}) != 3 or any(len(v.split()) > 4 for v in plan.values()): return None
    return {**plan, 'parser': 'paraphrase-v2'}


def _occurrences(text, phrase):
    return [m.start() for m in re.finditer(r'(?<![\w-])' + re.escape(phrase) + r'(?![\w-])', text)]


def _single_category(phrase):
    # These slots name one bare category. Conjunctions, predicates, conditions
    # and imperative modifiers need a separately reviewed referring grammar.
    operators = {'and', 'or', 'nor', 'not', 'no', 'never', 'but', 'then', 'if',
                 'unless', 'except', 'instead', 'ignore', 'ignoring', 'choose',
                 'select', 'use', 'reverse', 'is', 'are', 'was', 'were', 'be',
                 'which', 'that', 'than', 'should', 'must', 'do', 'does'}
    words = _norm(phrase).replace('-', ' ').split()
    return bool(re.fullmatch(OBJECT, phrase)) and 1 <= len(words) <= 4 and not operators.intersection(words)


def _appearance(q, T):
    options, _ = _referents(q, T)
    lists = [[_norm(c) for c in o.split(',')] for o in options]
    cats = lists[0] if lists else []
    if (len(lists) < 2 or len(cats) < 3 or not all(cats)
            or len(set(cats)) != len(cats)
            or any(not _single_category(c) for c in cats)
            or any(sorted(x) != sorted(cats) for x in lists)): return None
    text = _norm(q['question'])
    spots = {c: _occurrences(text, c) for c in cats}
    if any(len(v) != 1 for v in spots.values()): return None
    ordered = sorted(cats, key=lambda c: spots[c][0])
    matches = []
    for template, style in APPEARANCE:
        listing = (', '.join(ordered) if style == 'comma'
                   else ', '.join(ordered[:-1]) + ', and ' + ordered[-1])
        if text == _norm(template.format(C=listing)): matches.append(template)
    if len(matches) != 1: return None
    original = {_norm(c): c.strip() for c in options[0].split(',')}
    return {'cats': [original[c] for c in ordered], 'parser': 'paraphrase-v2'}


def _rel_distance(q, T):
    text = ' '.join(q['question'].split())
    found = [m for m in (rx.fullmatch(text) for rx in DISTANCE_COMPILED) if m]
    if len(found) != 1: return None
    cands = [c.strip() for c in found[0].group('cands').split(',')]
    _, normalized = _referents(q, T)
    if len(cands) < 2 or sorted(map(_norm, cands)) != sorted(normalized): return None
    target = _norm(found[0].group('target'))
    if (target in normalized or not _single_category(target)
            or any(not _single_category(c) for c in normalized)
            or len(_occurrences(_norm(text), 'the ' + target)) != 1): return None
    return {'cands': cands, 'target': target, 'parser': 'paraphrase-v2'}


def parse_paraphrase(q, T):
    t = q['question_type']
    if t in DIRECTION: return _direction(q, T)
    if t == 'obj_appearance_order': return _appearance(q, T)
    if t == 'object_rel_distance': return _rel_distance(q, T)
    return None
