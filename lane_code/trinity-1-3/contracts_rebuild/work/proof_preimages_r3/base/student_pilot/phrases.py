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
