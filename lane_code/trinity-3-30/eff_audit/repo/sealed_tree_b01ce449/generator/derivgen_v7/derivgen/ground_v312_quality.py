"""Set admission: identities, deterministic options, and canonical miss eligibility."""
import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())


def question_identity(row):
    # Preserve the source identity across option permutation and rendering.
    if 'question_identity' in row:
        return row['question_identity']
    roles = row.get('roles', {})
    objects = sorted(normalized(v) for k, value in roles.items() if k != 'parser'
                     for v in (value if isinstance(value, list) else [value]))
    value = [row.get('scene'), row.get('frame_indices'), normalized(row.get('question', row['qid'])), objects]
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


def deduplicate(rows):
    unique, seen, refused = [], set(), Counter()
    for row in sorted(rows, key=lambda r: r['qid']):
        identity = question_identity(row)
        if identity in seen:
            refused[row['type']] += 1
        else:
            seen.add(identity)
            unique.append(row)
    return unique, dict(refused)


def source_join(item):
    return item.get('source_join', {k:item.get(k) for k in
        ('scene', 'frame_indices', 'question', 'options', 'gt_answer')})


def validate_join(item, direct):
    from .ground_v312 import RowRefusal
    source = source_join(item)
    for key in ('scene', 'frame_indices', 'question', 'options'):
        if key not in direct or direct[key] != source[key]:
            raise RowRefusal('direct_join_mismatch_' + key)
    if str(direct.get('answer')) != str(source['gt_answer']):
        raise RowRefusal('direct_join_mismatch_answer')


def noun_is_plural(name, explicit=None):
    """Use supplied number when available, otherwise the English noun head."""
    if explicit in ('singular', 'plural'):
        return explicit == 'plural'
    head = re.split(r'\s+(?:of|with|in|on)\s+', normalized(name))[0].split()[-1]
    if head in {'people', 'men', 'women', 'children', 'feet', 'teeth', 'mice', 'geese'}:
        return True
    if head in {'glass', 'grass', 'moss', 'canvas', 'bus', 'gas', 'dress', 'chest of drawers'}:
        return False
    return head.endswith('s') and not head.endswith(('ss', 'us', 'is'))


def direction_question(item, ordered_contents=()):
    """Keep the benchmark's direction order independent of lettered options."""
    r = item['roles']
    if item['type'].endswith('_easy'):
        return (f"If I am standing by the {r['stand']} and facing the {r['face']}, "
                f"is the {r['query']} to the left or the right of the {r['face']}?")
    choices = ('left, right, or back' if item['type'].endswith('medium')
               else 'front-left, front-right, back-left, or back-right')
    text = (f"If I am standing by the {r['stand']} and facing the {r['face']}, "
            f"is the {r['query']} to my {choices}?\n")
    if item['type'].endswith('medium'):
        return text + 'An object is to my back if I would have to turn at least 135 degrees in order to face it.'
    return text + ('The directions refer to the quadrants of a Cartesian plane '
                   '(if I am standing at the origin and facing along the positive y-axis).')


def distance_question(item, ordered_contents=()):
    """Preserve the benchmark's closest-point wording for both distance types."""
    r = item['roles']
    prefix = 'Measuring from the closest point of each object, '
    if item['type'] == 'object_abs_distance':
        return prefix + f"what is the distance between the {r['a']} and the {r['b']} (in meters)?"
    return prefix + (f"which of these objects ({', '.join(ordered_contents)}) "
                     f"is the closest to the {r['target']}?")


def selection_refusal(row):
    """The review builder has no verifier for admitted VQA continuations."""
    if row.get('not_seen'):
        return 'diagnostic_miss_without_admitted_vqa'
    if not row.get('gt_agrees'):
        return 'gt_mismatch'
    return None


def candidate_identity(item, simulated_misses=()):
    """Identify a rendered variant independently of its source-question ID."""
    payload = [item['qid'], item.get('scene'), item.get('frame_indices'),
               item['type'], item['question'], item.get('options', []),
               sorted(simulated_misses), item.get('trace_revision', '3.12.2'), 'phrases-v3']
    return 'ground-' + hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()


def shuffled_item(item):
    from .ground_v312 import option_map
    if item.get('option_shuffle') == 'qid-sha256-benchmark-v4':
        if item['type'].startswith('object_rel_direction'):
            return dict(item, question=direction_question(item))
        return item
    row = copy.deepcopy(item)
    row['question_identity'] = question_identity(item)
    row['source_join'] = copy.deepcopy(source_join(item))
    options = option_map(item.get('options', []))
    if not options:
        if item['type'] == 'object_abs_distance':
            row['question'] = distance_question(item)
        return row
    order = sorted(options, key=lambda k: hashlib.sha256((item['qid']+'\0'+k).encode()).digest())
    row['options'] = [f'{chr(65+i)}. {options[k]}' for i,k in enumerate(order)]
    mapping = {k:chr(65+i) for i,k in enumerate(order)}
    # Rewrite complete enumerations, retaining each source spelling (rear/behind).
    aliases = {v.lower():v for v in options.values()}
    if item['type'].startswith('object_rel_direction') and 'back' in aliases:
        aliases.update(rear='back', behind='back')
    atom = '|'.join(re.escape(v) for v in sorted(aliases,key=len,reverse=True))
    enum = re.compile(r'(?<![\w-])(?:'+atom+r')(?:\s*(?:,\s*(?:or\s+)?|\s+or\s+)(?:'+atom+r'))+(?![\w-])',re.I)
    def reorder(match):
        text = match.group()
        words = re.findall(atom,text,re.I)
        spellings = {aliases[w.lower()].lower():w for w in words}
        if len(words)!=len(options) or set(spellings)!={v.lower() for v in options.values()}:
            return text
        values = [spellings[options[k].lower()] for k in order]
        return ', '.join(values[:-1])+(', or ' if ', or ' in text else ' or ' if ' or ' in text else ', ')+values[-1]
    row['question'] = enum.sub(reorder,item['question'])
    # Labelled options may be newline-separated or embedded in a prompt.
    pattern = '|'.join(re.escape(o) for o in sorted(item['options'],key=len,reverse=True))
    matches = list(re.finditer(pattern,row['question']))
    if len(matches)==len(options) and {m.group() for m in matches}==set(item['options']):
        it = iter(row['options'])
        row['question'] = re.sub(pattern,lambda m:next(it),row['question'])
    if item['type'].startswith('object_rel_direction'):
        row['question'] = direction_question(item)
    if item['type']=='object_rel_distance' and 'roles' in row:
        row['roles']['cands'] = [options[k] for k in order]
        row['question'] = distance_question(row, row['roles']['cands'])
    if 'gt_answer' in item:
        row['gt_answer'] = mapping[str(item['gt_answer'])]
    if str(item.get('source_answer')) in mapping:
        row['source_answer'] = mapping[str(item['source_answer'])]
    row['option_shuffle'] = 'qid-sha256-benchmark-v4'
    row['option_letter_map'] = mapping
    return row


def continuation_reason(item, body, answer):
    """Reject contradictory assertions without rewriting the admitted body."""
    from .ground_v312 import option_map
    source = source_join(item)
    content = option_map(source.get('options') or []).get(str(answer), str(answer)).lower()
    if re.search(r'\b(?:answer|option|choice)\s*(?:(?:is|:|=)\s*)?[A-Z]\b', body, re.I):
        return 'canonical_letter_prose'
    if item['type'].startswith('object_rel_direction'):
        hard = item['type'].endswith('hard')
        for m in re.finditer(r'(\d+(?:\.\d+)?)\s*degrees?\s*(left|right) of straight ahead(?:,\s*(in front|behind))?', body, re.I):
            angle, side, desc = float(m[1]), m[2].lower(), (m[3] or '').lower()
            predicted = (('front-' if angle < 90 else 'back-') + side if hard
                         else 'back' if angle >= 135 else side)
            if predicted != content:
                return 'canonical_wording_contradiction'
            if desc == 'behind' and not content.startswith('back'):
                return 'canonical_wording_contradiction'
            if desc == 'in front' and content.startswith('back'):
                return 'canonical_wording_contradiction'
        assertions = re.findall(r'\b(?:is|lies)\s+(?:at my|on my|on the|to my)\s+(front-left|front-right|back-left|back-right|left|right|back)\b', body, re.I)
        assertions += ['back'] if re.search(r'\b(?:is|lies) behind me\b', body, re.I) else []
        if any(a.lower() != content for a in assertions):
            return 'canonical_wording_contradiction'
    elif item['type'] == 'object_rel_distance':
        m = re.search(r'The closest is (?:the )?(.+?)\.', body, re.I)
        if m and normalized(m[1]) != normalized(content):
            return 'canonical_wording_contradiction'
    return None


def miss_candidates(items, rate, seed=0):
    from .ground_v312 import RowRefusal, direct_continuation
    eligible, reasons = [], defaultdict(Counter)
    for item in items:
        try:
            direct_continuation(item)
        except RowRefusal as exc:
            reasons[item['type']][str(exc)] += 1
        else:
            eligible.append(item)
    eligible.sort(key=lambda r: hashlib.sha256((str(seed)+':'+r['qid']).encode()).digest())
    selected = eligible[:round(rate*len(items))]
    return {r['qid'] for r in selected}, {t:dict(c) for t,c in reasons.items()}, len(eligible)


def set_report(rows):
    result = {}
    for typ in sorted({r['type'] for r in rows}):
        group = [r for r in rows if r['type']==typ]
        result[typ] = dict(rows=len(group), unique_questions=len({question_identity(r) for r in group}),
            letters=dict(Counter(r.get('answer', r.get('gt_answer')) for r in group)))
        if typ == 'object_rel_distance' and all('options' in r for r in group):
            result[typ]['by_option_count'] = {str(n):dict(
                rows=sum(len(r['options'])==n for r in group),
                letters=dict(Counter(r.get('answer',r.get('gt_answer')) for r in group if len(r['options'])==n)))
                for n in sorted({len(r['options']) for r in group})}
    return result
