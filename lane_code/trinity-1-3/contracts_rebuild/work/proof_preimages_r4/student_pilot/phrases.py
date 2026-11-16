"""Open-vocabulary operand identity. Aliases retain their full referring phrase."""
import re
import unicodedata
from trace_format.contracts import new_contracts

SINGULAR = {'shelves':'shelf', 'bookshelves':'bookshelf', 'clothes':'clothing',
            'blinds':'window blind', 'people':'person', 'mice':'mouse', 'microwaves':'microwave', 'curves':'curve', 'nerves':'nerve', 'stoves':'stove', 'gloves':'glove', 'glasses':'glass', 'mattresses':'mattress',
            'buses':'bus', 'knives':'knife', 'wives':'wife', 'lives':'life', 'leaves':'leaf',
            'wolves':'wolf', 'halves':'half', 'loaves':'loaf', 'calves':'calf',
            'lenses':'lens', 'cases':'case', 'houses':'house', 'noses':'nose',
            'vases':'vase', 'roses':'rose', 'dresses':'dress', 'classes':'class', 'passes':'pass'}
UNCHANGED = {'glass','grass','gas','canvas','status','stairs','pants','trousers','scissors',
             'series','species','news','lens','canvas','chess','physics','headphones'}


def normalize_phrase(name):
    if not isinstance(name, str) or not name.strip() or any(
            ord(c) < 32 or ord(c) == 127 or c in '<>"' for c in name):
        raise ValueError('invalid_object_name')
    text = ' '.join(unicodedata.normalize('NFKC',name).casefold().replace('_',' ').split())
    prefix, _, word = text.rpartition(' ')
    if word in SINGULAR:
        word = SINGULAR[word]
    elif word not in UNCHANGED:
        if word.endswith('ies') and len(word) > 3:
            word = word[:-3]+'y'
        elif word.endswith(('ches','shes','xes','zes')):
            word = word[:-2]
        elif word.endswith('s') and not word.endswith(('ss','us','is','ses','ves')):
            word = word[:-1]
    return (prefix+' ' if prefix else '')+word


def phrase_set(names):
    return tuple(sorted({normalize_phrase(n) for n in names}))


def annotation_phrase(name):
    if new_contracts():
        return normalize_phrase(name)
    return ' '.join(unicodedata.normalize('NFKC', str(name)).casefold().split())


def annotation_labels(name, labels, sealed_match):
    if not new_contracts():
        return sealed_match(name, labels)
    return [label for label in labels if normalize_phrase(label) == normalize_phrase(name)]


# Complete angle-question templates from the admitted native POOL. Each slot
# retains its entire referring phrase; none comes from the generated tool calls.
ANGLE_TEMPLATES = (
    'At the location of the {stand}, facing the {face}, what angle (in degrees) {sense} do I rotate to directly see the {query}?',
    "At the {stand}, facing the {face}, what's the precise angle of {sense} rotation required to turn toward the {query}?",
    'At the {stand}, when facing the {face}, how many degrees should I turn {sense} to face toward the {query}?',
    'From my position at the {stand}, looking toward the {face}, how many degrees should I rotate {sense} to view the {query}?',
    'From my standpoint at the {stand}, facing toward the {face}, how many degrees {sense} must I rotate to directly face the {query}?',
    'From the {stand} and facing the {face}, how many degrees {sense} do I precisely rotate to face the {query}?',
    "From the {stand}, oriented toward the {face}, what's the angle of rotation {sense} needed to look directly at the {query}?",
    "I'm at the {stand} facing the {face}; how many degrees {sense} must I rotate to align my view with the {query}?",
    "I'm at the {stand}, looking towards the {face}. How many degrees {sense} should I rotate to look at the {query}?",
    "If I'm located at the {stand}, viewing the {face}, how many degrees of rotation {sense} are necessary to face the {query}?",
    "If I'm positioned at the {stand}, looking directly at the {face}, how many degrees must I rotate {sense} to align myself with the {query}?",
    "If I'm standing at the {stand}, looking at the {face}, what's the {sense} degree measurement needed to see the {query}?",
    'If at the {stand} and directly facing the {face}, what {sense} angle adjustment is needed to look at the {query}?',
    'Located at the {stand} and facing toward the {face}, how many degrees {sense} rotation will it take to directly face the {query}?',
    'Positioned at the {stand} and oriented toward the {face}, how many degrees {sense} should I turn to face the {query}?',
    "Standing at the {stand} and directed toward the {face}, what's the degree measurement I need to rotate {sense} to face the {query}?",
    'Standing at the {stand} and oriented to the {face}, how much should I rotate {sense}, in degrees, to face the {query}?',
    'Standing at the {stand} with eyes toward the {face}, how many degrees must I rotate {sense} to point toward the {query}?',
    'Standing at the {stand}, facing the {face}, how many degrees do I have to rotate in {sense} to face the {query} exactly?',
    'Standing at the {stand}, facing toward the {face}, how far {sense} do I rotate (in degrees) to see the {query}?',
    "Standing at the {stand}, looking toward the {face}, what's the number of degrees needed to rotate {sense} to look directly at the {query}?",
    'Standing by the {stand} and facing toward the {face}, how far in degrees do I turn {sense} to face the {query}?',
    'Standing by the {stand}, looking toward the {face}, how far {sense} in degrees must I turn to see the {query}?',
    'Starting from the {stand} and looking at the {face}, how many degrees of {sense} rotation are required to look at the {query}?',
    "When positioned at the {stand} and viewing the {face}, what's the required angle of {sense} rotation to face the {query}?",
)
ANGLE_PATTERNS = tuple(re.compile(''.join(
    r'(?:counterclockwise|clockwise)' if part == '{sense}' else
    r'(?P<'+part[1:-1]+r'>.+?)' if part in ('{stand}', '{face}', '{query}') else re.escape(part)
    for part in re.split(r'(\{[a-z]+\})', template)), re.I) for template in ANGLE_TEMPLATES)


def source_template_candidates(question, options, option_map):
    from generator.derivgen_v7.derivgen.paraphrase import parse_paraphrase
    from generator.derivgen_v7.derivgen.ground_v312_quality import direction_question
    from types import SimpleNamespace
    canonical = re.match(r'If I am standing by the (.+?) and facing the (.+?), is the (.+?) to ', question)
    if canonical:
        roles = dict(zip(('stand', 'face', 'query'), canonical.groups()))
        for kind in ('object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard'):
            if question == direction_question(dict(type=kind, roles=roles)):
                return phrase_set(roles.values())
    for kind in ('object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
                 'object_rel_distance', 'obj_appearance_order'):
        roles = parse_paraphrase(dict(question=question, question_type=kind, options=list(options)),
                                SimpleNamespace(option_texts=option_map))
        if roles:
            return phrase_set(n for key, v in roles.items() if key != 'parser'
                              for n in (v if isinstance(v, list) else [v]))
    count = re.fullmatch(r'Are there more, fewer, or the same number of (.+?)\(s\) as (.+?)\(s\) in this room\?', question, re.I)
    if count:
        return phrase_set(count.groups())
    for pattern in ANGLE_PATTERNS:
        match = pattern.fullmatch(question)
        if match:
            names = set(phrase_set(match.groupdict().values()))
            # Native generation can name a category by its bound annotation label
            # (dose_t0.rename_roles). Cache-backed candidates never use this path.
            from trace_format.category_vocab import vocabulary
            for category, labels in vocabulary().items():
                if normalize_phrase(category) in names:
                    names.update(phrase_set(labels))
            aliases = {'sofa': 'couch', 'computer tower': 'tower',
                       'computer mouse': 'mouse', 'ceiling light': 'ceiling lamp'}
            names.update(aliases[n] for n in tuple(names) if n in aliases)
            return tuple(sorted(names))
    return None


def candidate_phrases(question, options=(), cache_phrases=None):
    # Cache phrases are the capture-wide competition universe, including names
    # not mentioned in this particular question. Admission checks that same set.
    if cache_phrases is not None:
        return phrase_set(cache_phrases)
    question = question.replace(chr(34), '').replace('<', '').replace('>', '')
    options = [o.replace(chr(34), '').replace('<', '').replace('>', '') for o in options]
    # Native MDG has no phrase cache. Parse source question operands, not labels.
    from generator.derivgen_v7.derivgen.bindings import parse_f17
    from types import SimpleNamespace
    from trace_format.ground_v312 import option_map
    parsed = source_template_candidates(question, options, option_map)
    if parsed is not None:
        return parsed
    kinds = ('absolute_distance_object','relative_distance_object','absolute_size_object',
             'relative_direction_object','absolute_direction_object','absolute_count','relative_count')
    for kind in kinds:
        roles = parse_f17(dict(question=question, question_type=kind, options=list(options)),
                          SimpleNamespace(option_texts=option_map))
        if roles:
            values = [v for k,v in roles.items() if k != 'parser']
            return phrase_set(n for v in values for n in (v if isinstance(v,list) else [v]) if isinstance(n,str))
    values = list(option_map(list(options)).values()) if options else []
    # Common distance wording also used by the native head's prompt.
    match = re.search(r'(?:distance between|far is) (?:the )?(.+?) (?:and|from) (?:the )?(.+?)(?:\s+\(in [^()]+\))?(?:[?.]|$)', question, re.I)
    if match:
        values.extend(match.groups())
    return phrase_set(values)


def cache_key(cache, name):
    wanted = normalize_phrase(name)
    keys = [key for key in cache['phrases'] if normalize_phrase(key) == wanted]
    if not keys:
        return wanted
    canonical = min(keys, key=lambda key: (key != wanted, key.casefold(), key))
    if len(keys) > 1:
        import json
        for frame in cache.get('frames', {}).values():
            records = frame['phrases']
            entries = [records[key] for key in sorted(keys) if key in records]
            if not entries:
                continue
            merged = dict(entries[0])
            merged['presence'] = max(float(e.get('presence', 0)) for e in entries)
            instances = {json.dumps(i, sort_keys=True): i for e in entries for i in e.get('instances', [])}
            merged['instances'] = [instances[k] for k in sorted(instances)]
            frame['phrases'] = {**{k: v for k, v in records.items() if k not in keys}, canonical: merged}
        cache['phrases'] = sorted({k for k in cache['phrases'] if k not in keys} | {canonical})
    return canonical
