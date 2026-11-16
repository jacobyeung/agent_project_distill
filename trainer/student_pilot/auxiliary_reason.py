"""Query tokens that call perception heads from inside the reasoning text.

A training target writes a query token immediately followed by its value text,
for example "There are <|box_start|>3 tables." Under teacher forcing that value
is ground truth, and it is also the head's regression target, so these heads
need no sidecar. The Qwen3.5 pre-tokenizer isolates every digit, a sign before
a digit and a period between two digits as single-character tokens; a value is
therefore a run of such tokens that starts right after the query token, and
replacing it at the token level equals re-tokenizing the edited text.
"""
import math
import random
import re

# The one mapping from query kind to its single-id Qwen3.5 special token. None of
# these tokens appears in the native prompts. Kind ids follow this order.
QUERY_TOKENS = {
    'COUNT': '<|box_start|>',         # integer number of instances
    'DIST': '<|box_end|>',            # meters, one decimal
    'SIZE': '<|quad_start|>',         # centimeters, integer
    'TIME': '<|quad_end|>',           # seconds, one decimal: a displayed temporal-group timestamp
    'DEPTH': '<|object_ref_start|>',  # meters, one decimal: median depth of a named object or region
    'ANGLE': '<|object_ref_end|>',    # signed integer degrees in (-180, 180], counterclockwise from straight ahead
    'COORD': '<|fim_prefix|>',        # signed meters, one decimal, explicit sign: a gravity-aligned camera-frame
                                      # coordinate (x right, y forward, z up) or a camera displacement component
}
KINDS = tuple(QUERY_TOKENS)
KIND_INDEX = {kind: index for index, kind in enumerate(KINDS)}
INTEGER_KINDS = frozenset({'COUNT', 'SIZE', 'ANGLE'})
SIGNED_KINDS = frozenset({'ANGLE', 'COORD'})
REGRESSION_KINDS = ('COUNT', 'DIST', 'SIZE', 'DEPTH')
CLIP = {'DIST': (0.05, 30.0), 'DEPTH': (0.05, 30.0), 'SIZE': (1.0, 1000.0)}
COUNT_MAX = 999
COORD_LIMIT = 200.0
COORD_SCALE = 1.0
OUTPUT_LIMIT = 50.0
GROUPS = 16
IGNORE = -100

TEXT_KIND = {text: kind for kind, text in QUERY_TOKENS.items()}
QUERY_PATTERN = re.compile('|'.join(re.escape(text) for text in QUERY_TOKENS.values()))
VALUE_PATTERN = {kind: re.compile((r'[+-]?' if kind in SIGNED_KINDS else '') + (r'\d+' if kind in INTEGER_KINDS else r'\d+(?:\.\d+)?'))
                 for kind in KINDS}
DECIMAL_TAIL = re.compile(r'\.\d')
_TABLES = {}


def token_table(tokenizer):
    """Verify the single-id and digit-isolation assumptions on the real tokenizer."""
    query = {}
    for kind, text in QUERY_TOKENS.items():
        single = tokenizer.convert_tokens_to_ids(text)
        if (type(single) is not int or single < 0 or single == getattr(tokenizer, 'unk_token_id', None)
                or tokenizer.encode(text, add_special_tokens=False) != [single]):
            raise ValueError('Query token is not one tokenizer id: ' + text)
        query[single] = KIND_INDEX[kind]
    chars = {}
    for char in '0123456789.+-':
        ids = tokenizer.encode(char, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError('Digit, sign or decimal point is not one tokenizer id: ' + char)
        chars[char] = ids[0]
    if len(set(chars.values())) != len(chars) or set(chars.values()) & set(query):
        raise ValueError('Value characters and query tokens must have distinct ids')
    for text, single in zip(QUERY_TOKENS.values(), query):
        if tokenizer.encode(text + '10.5', add_special_tokens=False) != [single] + [chars[c] for c in '10.5']:
            raise ValueError('Tokenizer does not isolate digits and decimal points after a query token')
        for value in ('+63', '-37'):
            if tokenizer.encode(text + value, add_special_tokens=False) != [single] + [chars[c] for c in value]:
                raise ValueError('Tokenizer does not isolate a leading sign after a query token')
    return {'query': query, 'digits': {chars[c]: c for c in '0123456789'}, 'dot': chars['.'],
            'signs': {chars['+']: '+', chars['-']: '-'}, 'chars': chars}


def cached_table(tokenizer):
    entry = _TABLES.get(id(tokenizer))
    if entry is None or entry[0] is not tokenizer:
        entry = (tokenizer, token_table(tokenizer))
        _TABLES[id(tokenizer)] = entry
    return entry[1]


def text_queries(text):
    """Return [(kind, value)] for every query token in a target string; refuse malformed values."""
    found = []
    for match in QUERY_PATTERN.finditer(text):
        kind = TEXT_KIND[match.group()]
        value = VALUE_PATTERN[kind].match(text, match.end())
        if value is None:
            raise ValueError(f'{kind} query token is not immediately followed by its value')
        if kind in INTEGER_KINDS and DECIMAL_TAIL.match(text, value.end()):
            raise ValueError(f'{kind} query value must be an integer')
        found.append((kind, checked_value(kind, float(value.group()))))
    return found


def checked_value(kind, value):
    if kind == 'ANGLE' and not -180 <= value <= 180:
        raise ValueError('ANGLE query value must lie in [-180, 180] degrees')
    if kind == 'COORD' and not -COORD_LIMIT <= value <= COORD_LIMIT:
        raise ValueError(f'COORD query value must lie in [-{COORD_LIMIT:g}, {COORD_LIMIT:g}] meters')
    return value


def validate_rows(rows):
    """Startup census: prompts carry no query token; every target query has a value."""
    counts, covered = {kind: 0 for kind in KINDS}, 0
    for row in rows:
        inputs = row['student_input']
        prompt = '\n'.join([inputs['question'], *(inputs['options'] or [])])
        if QUERY_PATTERN.search(prompt):
            raise ValueError('A prompt contains a query token: ' + str(row['qid']))
        try:
            found = text_queries(row['target'])
        except ValueError as error:
            raise ValueError(f'{error}: {row["qid"]}') from None
        covered += bool(found)
        for kind, _ in found:
            counts[kind] += 1
    return {'rows': len(rows), 'rows_with_queries': covered, 'queries': counts}


def parse_tokens(ids, labels, table):
    """Return [(position, kind_id, value, value_token_count)] for one unpadded row."""
    query, digits, dot, signs = table['query'], table['digits'], table['dot'], table['signs']
    found = []
    for position, token in enumerate(ids):
        if token not in query:
            continue
        if labels[position] == IGNORE:
            raise ValueError('Query tokens may appear only inside the supervised target')
        kind = KINDS[query[token]]
        end = start = position + 1
        if kind in SIGNED_KINDS and end < len(ids) and ids[end] in signs:
            end = start = end + 1
        while end < len(ids) and ids[end] in digits:
            end += 1
        if end == start:
            raise ValueError(f'{kind} query token is not immediately followed by its value')
        if end + 1 < len(ids) and ids[end] == dot and ids[end + 1] in digits:
            if kind in INTEGER_KINDS:
                raise ValueError(f'{kind} query value must be an integer')
            end += 1
            while end < len(ids) and ids[end] in digits:
                end += 1
        if any(labels[index] == IGNORE for index in range(position + 1, end)):
            raise ValueError('Query values must be supervised target tokens')
        text = ''.join(table_char(table, ids[index]) for index in range(position + 1, end))
        found.append((position, query[token], checked_value(kind, float(text)), end - position - 1))
    return found


def table_char(table, token):
    if token == table['dot']:
        return '.'
    return table['signs'][token] if token in table['signs'] else table['digits'][token]


def displayed_times(seconds):
    """The processor prints each temporal group's timestamp with one decimal."""
    if len(seconds) != GROUPS or not all(math.isfinite(value) for value in seconds):
        raise ValueError('Expected 16 finite temporal-group timestamps')
    return [float(f'{value:.1f}') for value in seconds]


def regression_target(kind, value):
    if kind == 'COUNT':
        return math.log1p(max(value, 0.0))
    low, high = CLIP[kind]
    return math.log(min(max(value, low), high))


def time_class(value, times):
    return min(range(len(times)), key=lambda group: (abs(times[group] - value), group))


def angle_target(degrees):
    """Unit vector (sin, cos) of a counterclockwise angle from straight ahead."""
    radians = math.radians(degrees)
    return math.sin(radians), math.cos(radians)


def coord_target(meters):
    """asinh scaling keeps the loss near-linear for small offsets and logarithmic for large ones."""
    return math.asinh(meters / COORD_SCALE)


def coord_meters(output):
    limit = math.asinh(COORD_LIMIT / COORD_SCALE)
    return math.sinh(min(max(float(output), -limit), limit)) * COORD_SCALE


def angle_degrees(sine, cosine):
    """Rounded atan2 in degrees, folded into (-180, 180]."""
    degrees = round(math.degrees(math.atan2(sine, cosine)))
    return 180 if degrees <= -180 else degrees


def format_value(kind, output, times=None):
    """Text the model reads after a query token: the head's prediction in the target's format."""
    if kind == 'TIME':
        return f'{times[int(output)]:.1f}'
    if kind == 'ANGLE':
        sine, cosine = output
        return f'{angle_degrees(float(sine), float(cosine)):+d}'
    if kind == 'COORD':
        text = f'{coord_meters(output):+.1f}'
        return '+0.0' if text == '-0.0' else text
    output = min(max(float(output), -OUTPUT_LIMIT), OUTPUT_LIMIT)
    if kind == 'COUNT':
        return str(min(COUNT_MAX, max(0, round(math.expm1(output)))))
    low, high = CLIP[kind]
    value = min(max(math.exp(output), low), high)
    return str(int(round(value))) if kind == 'SIZE' else f'{value:.1f}'


def value_ids(text, table):
    if not text or any(char not in table['chars'] for char in text):
        raise ValueError('A query value contains a character outside digits, signs and the decimal point')
    return [table['chars'][char] for char in text]


def choose_rows(positions, weights, probability, key):
    """Pick active rows that contain queries; a private RNG leaves the training RNG untouched."""
    generator = random.Random(key)
    chosen = []
    for row, weight in enumerate(weights):
        draw = generator.random()
        if weight and bool((positions[row] >= 0).any()) and draw < probability:
            chosen.append(row)
    return chosen


def resize_last(tensor, length, fill):
    import torch

    if tensor.shape[-1] >= length:
        if tensor.dtype == torch.bool and tensor[..., length:].any():
            raise ValueError('Resizing would drop marked sequence positions')
        return tensor[..., :length]
    return torch.cat((tensor, tensor.new_full((*tensor.shape[:-1], length - tensor.shape[-1]), fill)), dim=-1)


def apply_mixing(batch, rows, texts, table, pad_token_id):
    """Replace the value tokens after each query of the chosen rows by predicted values.

    texts[row] lists one value string per valid query of that row, in position
    order. The new value tokens are not supervised; every other label, the
    right padding and the query positions are rebuilt for the new lengths.
    """
    import torch

    if not rows:
        return batch, {'rows': 0, 'queries': 0}
    ids, labels, mask = batch['input_ids'], batch['labels'], batch['attention_mask']
    types = batch.get('mm_token_type_ids')
    positions, spans = batch['aux_reason_pos'].clone(), batch['aux_reason_span'].clone()
    sequences, replaced = [], 0
    for row in range(ids.shape[0]):
        length = int(mask[row].sum())
        if not torch.all(mask[row, :length] == 1):
            raise ValueError('Prediction mixing expects right-padded rows')
        row_ids, row_labels = ids[row, :length].tolist(), labels[row, :length].tolist()
        row_types = types[row, :length].tolist() if types is not None else None
        if row in rows:
            valid = [q for q in range(positions.shape[1]) if int(positions[row, q]) >= 0]
            if len(texts[row]) != len(valid):
                raise ValueError('Prediction count differs from the row query count')
            out_ids, out_labels, out_types, cursor = [], [], [], 0
            for q, text in zip(valid, texts[row]):
                start, span = int(positions[row, q]), int(spans[row, q])
                if start < cursor or row_ids[start] not in table['query'] or span < 1:
                    raise ValueError('Query positions are out of order or do not hold query tokens')
                out_ids += row_ids[cursor:start + 1]
                out_labels += row_labels[cursor:start + 1]
                if row_types is not None:
                    out_types += row_types[cursor:start + 1]
                positions[row, q] = len(out_ids) - 1
                tokens = value_ids(text, table)
                out_ids += tokens
                out_labels += [IGNORE] * len(tokens)
                if row_types is not None:
                    out_types += [0] * len(tokens)
                spans[row, q] = len(tokens)
                cursor = start + 1 + span
                replaced += 1
            out_ids += row_ids[cursor:]
            out_labels += row_labels[cursor:]
            if row_types is not None:
                out_types += row_types[cursor:]
            row_ids, row_labels, row_types = out_ids, out_labels, (out_types if row_types is not None else None)
        sequences.append((row_ids, row_labels, row_types))
    width = max(len(item[0]) for item in sequences)

    def stack(index, fill, dtype):
        return torch.tensor([item[index] + [fill] * (width - len(item[index])) for item in sequences],
                            dtype=dtype, device=ids.device)

    result = {**batch, 'input_ids': stack(0, pad_token_id, ids.dtype), 'labels': stack(1, IGNORE, labels.dtype),
              'attention_mask': torch.tensor([[1] * len(item[0]) + [0] * (width - len(item[0])) for item in sequences],
                                             dtype=mask.dtype, device=mask.device),
              'aux_reason_pos': positions, 'aux_reason_span': spans}
    if types is not None:
        result['mm_token_type_ids'] = stack(2, 0, types.dtype)
    if 'aux_category_tokens' in batch:
        result['aux_category_tokens'] = resize_last(batch['aux_category_tokens'], width, False)
    if torch.any(result['labels'][result['attention_mask'] == 0] != IGNORE) or torch.any(result['labels'][:, 0] != IGNORE):
        raise ValueError('Prediction mixing produced supervised padding or prompt starts')
    return result, {'rows': len(rows), 'queries': replaced}
