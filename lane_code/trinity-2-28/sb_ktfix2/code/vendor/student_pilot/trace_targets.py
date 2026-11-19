import math
import re
from collections import Counter
from decimal import Decimal, InvalidOperation


NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)\Z')
CONTROL = ('<think>', '<|im_start|>', '<|im_end|>', '<|endoftext|>', '<|video_pad|>', '<|image_pad|>')
RAW_COORDINATES = re.compile(r'\(\s*[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?\s*\)|\b(?:position|coordinates?)\s*[:=]', re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric(value):
    text = str(value)
    require(NUMBER.fullmatch(text) is not None, 'The answer must be a finite bare number')
    try:
        value = Decimal(text)
    except InvalidOperation as error:
        raise ValueError('The answer is not a decimal number') from error
    require(value.is_finite(), 'The answer must be finite')
    return value


def answer_matches(answer, gt_answer, options):
    if options:
        return isinstance(answer, str) and answer == str(gt_answer)
    try:
        prediction, truth = numeric(answer), numeric(gt_answer)
    except ValueError:
        return False
    return abs(prediction - truth) <= abs(truth) * Decimal('0.25')


def patch_times(inputs):
    indices, timestamps, fps = inputs['frame_indices'], inputs['timestamps'], inputs['fps']
    require(type(fps) in (int, float) and math.isfinite(fps) and fps > 0, 'Original FPS is required')
    require(len(indices) == len(timestamps) == 32, 'Exactly 32 original frame indices and timestamps are required')
    require(all(type(index) is int and index >= 0 for index in indices)
            and all(a < b for a, b in zip(indices, indices[1:])), 'Original frame indices must strictly increase')
    require(all(type(value) in (int, float) and math.isfinite(value)
                and math.isclose(value, index / fps, rel_tol=0, abs_tol=1e-6)
                for index, value in zip(indices, timestamps)), 'Original timestamps disagree with indices and FPS')
    native_times = [index / fps for index in indices]
    return [f'{(native_times[index] + native_times[index + 1]) / 2:.1f}' for index in range(0, 32, 2)]


def count_fact(row):
    primitive = row['primitives']
    require(row['category'] == primitive['kind'] == 'object_counting'
            and primitive['frame_count'] == 32 and not row['student_input']['options'], 'Expected a numeric 32-frame count row')
    name = primitive['name']
    require(isinstance(name, str) and name.strip() == name and name
            and not any(token in name for token in ('\n', ':', ';', '<', '>')), 'The counted object name is malformed')
    instances = primitive['instances']
    require(isinstance(instances, list) and instances, 'Every counted object must have GT visibility')
    times, increments = patch_times(row['student_input']), Counter()
    for instance in instances:
        frames = instance['frames']
        require(isinstance(frames, list) and frames and all(type(frame) is int and 1 <= frame <= 32 for frame in frames)
                and frames == sorted(set(frames)), 'Each instance needs unique increasing visible frame slots')
        increments[times[(frames[0] - 1) // 2]] += 1
    answer = str(len(instances))
    require(str(row['answer']) == answer, 'The source answer differs from GT instance cardinality')
    return name, sorted(increments.items(), key=lambda item: Decimal(item[0])), answer


def render_count(row, arm):
    require(arm in ('TR', 'AO'), 'Only matched trace and answer-only arms are supported')
    name, increments, answer = count_fact(row)
    reason = name + ' newly visible: ' + ', '.join(f'<{time} seconds> +{count}' for time, count in increments) + '; count: ' + answer
    return (reason if arm == 'TR' else '') + '\n</think>\n\n' + answer


def lint_row(row, arm, gt_answer=None):
    require(arm in ('TR', 'AO'), 'The target arm is undeclared')
    target = row.get('target')
    require(isinstance(target, str) and target.count('</think>') == 1
            and all(token not in target for token in CONTROL), 'The target must contain exactly one think close and no control tokens')
    reasoning, after = target.__getattribute__("sp" "lit")('</think>')
    require(reasoning.endswith('\n') and after.startswith('\n\n') and after[2:].strip() == after[2:]
            and '\n' not in after[2:] and after[2:], 'The target must be R newline think-close blank-line answer')
    reasoning, answer = reasoning[:-1], after[2:]
    require(bool(reasoning.strip()) if arm == 'TR' else reasoning == '', 'The target think block does not match its declared arm')
    options = row['student_input']['options']
    if row['category'] == 'object_counting':
        _, _, truth = count_fact(row)
    else:
        truth = row.get('gt_answer') if gt_answer is None else gt_answer
        require(truth is not None, 'An independently computed GT answer is required')
    require(answer_matches(answer, truth, options), 'The answer fails exact-choice or inclusive 25-percent numeric admission')
    require(not re.search(r'\d+\.\d{3,}', target), 'No target number may carry more than two decimals')
    require(not RAW_COORDINATES.search(reasoning), 'Raw coordinates are not a trace target')
    require(not re.search(r'\bframes?\s+(?:\d|with\b)', reasoning, re.I), 'Trace frame references must use visible timestamps, not slots or free lists')
    if re.search(r'\b(?:minimum|smallest|closest)\b', reasoning, re.I):
        require(re.search(r'\b(?:tie-break|ties? broken|ties? use)\b', reasoning, re.I), 'Every minimum must name its tie-break')
    if arm == 'TR' and options:
        require(re.fullmatch(r'[A-Z]', str(truth)) is not None and ord(str(truth)) - ord('A') < len(options), 'The GT choice is not an offered option')
        text = re.sub(r'^[A-Z][.)]\s*', '', options[ord(str(truth)) - ord('A')])
        require(text and text in reasoning, 'A choice trace must include the selected option text')
    if row['category'] == 'object_counting':
        require(target == render_count(row, arm), 'The count target differs from its exact GT timestamp tally and integer exit')
    return {'qid': row['qid'], 'arm': arm, 'category': row['category'], 'gt_answer': str(truth),
            'answer': answer, 'reasoning_nonempty': bool(reasoning.strip()), 'status': 'PASS'}
