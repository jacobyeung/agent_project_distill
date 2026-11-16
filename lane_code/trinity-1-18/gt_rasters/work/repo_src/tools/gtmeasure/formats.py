# Template harvesting adapts tools/vstigen/formats.py at e2f387e (vstigen-membership-v4-20260922).
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
import re

from .authority import VSI_TYPES
from .conventions import structure_conventions
from .io import canonical, digest, new_output, pin, read_json, write_json


UNIT_METERS = {'meters': Decimal('1'), 'centimeters': Decimal('0.01'),
               'feet': Decimal('0.3048'), 'inches': Decimal('0.0254'),
               'square meters': Decimal('1'), 'square feet': Decimal('0.09290304'),
               'instances': Decimal('1')}
UNITS = re.compile(r'\b(square meters|square feet|centimeters|meters|feet|inches)\b')
OPTIONS = re.compile(r'^([A-Z])\. ([^\n]+)$', re.MULTILINE)
CAMERA = re.compile(r'What is the approximate distance \(in meters\) between the camera \(or the person filming\) '
                    r'and the nearest point of the (?P<target>[^\n]+?) in frame (?P<frame_index>\d+) of (?P<frame_count>\d+)\?')
TYPE_FAMILY = {'absolute_count': 'gtm_object_count', 'absolute_size_object': 'gtm_object_size',
               'absolute_distance_object': 'gtm_object_distance', 'relative_distance_object': 'gtm_object_distance',
               'absolute_size_room': 'gtm_room_size', 'camera_obj_abs_dist': 'gtm_camera_object_distance'}


def text_parts(text):
    text = text.removeprefix('<image>\n')
    options = OPTIONS.findall(text)
    if options and [letter for letter, _ in options] != list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:len(options)]):
        raise ValueError('authority option letters are not in pool order')
    return text, options


def replace_spans(text, spans):
    for (start, end), value in sorted(spans, reverse=True):
        text = text[:start] + value + text[end:]
    return text


def harvest_template(kind, row, vocabulary):
    text, options = text_parts(row['question'])
    if kind == 'camera_obj_abs_dist':
        match = CAMERA.fullmatch(text)
        if not match or not 1 <= int(match['frame_index']) <= int(match['frame_count']) == 32:
            raise ValueError('unsupported camera-object authority wording')
        template = replace_spans(text, [(match.span(k), '{' + k + '}') for k in match.groupdict()])
        return template, 'meters', [], []
    units = set(UNITS.findall(text))
    if len(units) > 1:
        raise ValueError('multiple unit meanings in an authority question')
    unit = next(iter(units)) if units else 'instances' if kind == 'absolute_count' else None
    body = text.split('\nOptions:', 1)[0]
    pattern = re.compile(r'(?<![\w])(?:' + '|'.join(re.escape(word) for word in sorted(vocabulary, key=lambda s: (-len(s), s))) + r')(?![\w])')
    matches = list(pattern.finditer(body))
    names = list(dict.fromkeys(match[0] for match in matches))
    expected = {'absolute_count': 1, 'absolute_size_object': 1, 'absolute_distance_object': 2,
                'absolute_size_room': 0, 'relative_count': 2, 'relative_size_object': 2}
    if kind in expected and len(names) != expected[kind]:
        raise ValueError(f'cannot bind object slots on {kind} line {row["line"]}: {names}: {text}')
    if kind == 'relative_distance_object':
        choices = [value for _, value in options]
        references = set(names) - set(choices)
        if len(choices) != 4 or len(set(choices)) != 4 or len(references) != 1:
            raise ValueError(f'cannot bind closest-point MC pool on line {row["line"]}: {text}')
        slots = {value: f'option_{i}' for i, value in enumerate(choices)}
        slots[next(iter(references))] = 'reference'
    else:
        slots = {value: ('target' if len(names) == 1 else f'object_{i}') for i, value in enumerate(names)}
    template = replace_spans(text, [(match.span(), '{' + slots[match[0]] + '}') for match in pattern.finditer(text)])
    if template.format(**{slot: name for name, slot in slots.items()}) != text:
        raise ValueError('authority template does not reproduce its source wording')
    option_order = [slots.get(value, value) for _, value in options]
    return template, unit, [letter for letter, _ in options], option_order


def harvest(samples, structure='v1'):
    vocabulary = set()
    for kind in ('relative_size_object', 'relative_distance_object'):
        for row in samples['vsi']['samples'][kind]:
            vocabulary.update(value for _, value in text_parts(row['question'])[1])
    boundary = re.compile(r'\b(?:many|of|to|with|as|than|by|do|have|more|fewer|contain|are|equal|and)\s+|,\s*', re.I)
    for kind in ('absolute_count', 'relative_count'):
        for row in samples['vsi']['samples'][kind]:
            for match in re.finditer(r'\(s\)', row['question']):
                label = boundary.split(row['question'][:match.start()])[-1].strip()
                if re.fullmatch(r'[a-z][a-z -]*', label):
                    vocabulary.add(label)
    for row in samples['vsi']['samples']['relative_distance_object']:
        body = row['question'].split('\nOptions:', 1)[0].removeprefix('<image>\n').removeprefix('These are frames of a video.\n')
        body = re.split(r'[?.]', body, maxsplit=1)[0]
        for match in re.finditer(r'\b(?:to the|nearest the) ([a-z][a-z -]*?)(?=,| when | based | from |$)', body):
            vocabulary.add(match[1])
    templates, precisions = {}, defaultdict(Counter)
    precision_lines = defaultdict(dict)
    errors = []
    families = dict(samples['vsi']['samples'], camera_obj_abs_dist=samples['vsti']['samples'])
    for kind, rows in families.items():
        templates[kind] = {}
        for row in rows:
            try:
                text, unit, letters, order = harvest_template(kind, row, vocabulary)
            except ValueError as error:
                errors.append(str(error))
                continue
            key = digest([text, unit, letters, order])[:20]
            if key not in templates[kind]:
                templates[kind][key] = {'id': key, 'template': text, 'unit': unit, 'option_letters': letters,
                                        'option_order': order, 'source_line': row['line'], 'source_lines': [],
                                        'example_question': row['question'], 'example_answer': row['answer']}
            templates[kind][key]['source_lines'].append(row['line'])
            if not letters:
                if not re.fullmatch(r'\d+(?:\.\d+)?', row['answer']):
                    raise ValueError('numeric wording authority has a nonnumeric answer')
                places = len(row['answer'].partition('.')[2])
                precisions[kind, unit][places] += 1
                precision_lines[kind, unit].setdefault(places, row['line'])
    if errors:
        raise ValueError(f'{len(errors)} unbound wording samples; first failures:\n' + '\n'.join(errors[:15]))
    rounding = {}
    for (kind, unit), counts in sorted(precisions.items()):
        rounding.setdefault(kind, {})[unit] = {'decimal_places': max(counts), 'minimum_decimal_places': min(counts),
                                               'observed_decimal_places': {str(k): v for k, v in sorted(counts.items())},
                                               'source_lines': {str(k): v for k, v in sorted(precision_lines[kind, unit].items())},
                                               'rule': 'nearest at the observed maximum precision; retain at least the observed minimum precision; defer exact midpoint ties'}
    result = {'schema': 'gtmeasure-conventions-v1', 'authorities': {key: value['authority'] for key, value in samples.items() if key in ('vsi', 'vsti', 'vsibench')},
              'sampling': samples['vsi']['sampling'],
              'templates': {kind: sorted(values.values(), key=lambda v: v['source_line']) for kind, values in templates.items()},
              'rounding': rounding, 'unit_meters_or_square_meters': {key: str(value) for key, value in UNIT_METERS.items()},
              'vsibench_mc_question_types': samples['vsibench']['mc_question_types'],
              'emitted_mc_types': ['relative_distance_object'] if 'object_rel_distance' in samples['vsibench']['mc_question_types'] else [],
              'non_emitted_mc_types': ['relative_count', 'relative_size_object'],
              'mc_rule': 'four real co-present category labels, listed and lettered in pool order; nearest instance; unique closest option',
              'object_vocabulary': sorted(vocabulary)}
    return structure_conventions(result, structure)


def format_observation_value(value):
    value = Decimal(str(float(value)))
    if not value.is_finite():
        raise ValueError('observation measurement must be finite')
    rounded = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    return f'{rounded.copy_abs() if rounded.is_zero() else rounded:.2f}'


def render_question(spec, **values):
    question = spec['template'].format(**values)
    options = [value for _, value in OPTIONS.findall(question)]
    if [letter for letter, _ in OPTIONS.findall(question)] != spec['option_letters']:
        raise ValueError('generated option order differs from authority')
    return question, options


def format_value(value_si, kind, unit, conventions):
    if unit not in UNIT_METERS:
        raise ValueError('unit is not present in the harvested authority')
    value = Decimal(str(value_si)) / UNIT_METERS[unit]
    if not value.is_finite() or value < 0:
        raise ValueError('measurement must be finite and nonnegative')
    rule = conventions['rounding'][kind][unit]
    places = rule['decimal_places']
    scaled = value.scaleb(places)
    if scaled - scaled.to_integral_value(rounding='ROUND_FLOOR') == Decimal('0.5'):
        raise ValueError('rounding_midpoint_not_specified_by_authority')
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    text = f'{rounded:.{places}f}'
    minimum = rule['minimum_decimal_places']
    if places and minimum < places:
        text = text.rstrip('0').rstrip('.')
        present = len(text.partition('.')[2])
        if present < minimum:
            text += ('.' if '.' not in text else '') + '0' * (minimum - present)
    return text


def main():
    parser = argparse.ArgumentParser(description='Derive all sampled wording, unit, and precision variants with source lines.')
    parser.add_argument('--authorities', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = harvest(read_json(args.authorities))
    result['sample_cache'] = pin(args.authorities)
    output = new_output(args.output)
    write_json(output / 'CONVENTIONS.json', result)
    for kind, rows in result['templates'].items():
        print(kind, len(rows), canonical(result['rounding'].get(kind, {})))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
