import math
import re

from student.compact_targets.compact_counted_v1 import ANSWER, MARKER, numeric_tokens


STUDENT_KEYS = {'fps', 'frame_indices', 'frames', 'options', 'question', 'timestamps', 'total_num_frames'}


def render_target(observations, answer, derivations=()):
    if not observations or not isinstance(answer, str) or not ANSWER.fullmatch(answer):
        raise ValueError('compact target needs observations and a bare numeric or letter answer')
    if any(not isinstance(line, str) or not line or '\n' in line or '\r' in line for line in [*observations, *derivations]):
        raise ValueError('observations and derivations must be nonempty single lines')
    grounded = numeric_tokens('\n'.join([*observations, *derivations]))
    if any(token not in grounded for token in numeric_tokens(answer)):
        raise ValueError('ungrounded numeric answer token')
    lines = [f'Observations ({len(observations)})']
    lines += [f'{index}. {text}' for index, text in enumerate(observations, 1)]
    if derivations:
        lines += [f'Derivations ({len(derivations)})']
        lines += [f'{index}. {text}' for index, text in enumerate(derivations, 1)]
    return '\n'.join([*lines, MARKER, answer])


def validate_target(target):
    if not isinstance(target, str) or target.endswith('\n'):
        raise ValueError('compact target must not have a trailing newline')
    lines = target.split('\n')
    first = re.fullmatch(r'Observations \(([1-9]\d*)\)', lines[0])
    if first is None:
        raise ValueError('invalid compact observations header')
    count = int(first[1])
    observations = []
    for index in range(1, count + 1):
        prefix = f'{index}. '
        if index >= len(lines) or not lines[index].startswith(prefix):
            raise ValueError('invalid compact observation numbering')
        observations.append(lines[index][len(prefix):])
    cursor, derivations = count + 1, []
    if cursor < len(lines) and lines[cursor].startswith('Derivations'):
        match = re.fullmatch(r'Derivations \(([1-9]\d*)\)', lines[cursor])
        if match is None:
            raise ValueError('invalid compact derivations header')
        cursor += 1
        for index in range(1, int(match[1]) + 1):
            prefix = f'{index}. '
            if cursor >= len(lines) or not lines[cursor].startswith(prefix):
                raise ValueError('invalid compact derivation numbering')
            derivations.append(lines[cursor][len(prefix):])
            cursor += 1
    if len(lines) != cursor + 2 or lines[cursor] != MARKER:
        raise ValueError('invalid compact terminal layout')
    if render_target(observations, lines[-1], derivations) != target:
        raise ValueError('compact byte fidelity failed')
    return {'counted_layout': True, 'numeric_tokens': True, 'terminal_answer': True,
            'observation_count': count, 'derivation_count': len(derivations)}


def validate_student_input(value):
    if not isinstance(value, dict) or set(value) != STUDENT_KEYS:
        raise ValueError('student input must contain only RGB, timing, question, and options')
    frames, indices, times = value['frames'], value['frame_indices'], value['timestamps']
    if len(frames) != 32 or len(indices) != 32 or len(times) != 32:
        raise ValueError('student input requires exactly 32 RGB slots')
    if (any(type(index) is not int or index < 0 for index in indices) or sorted(set(indices)) != indices
            or type(value['total_num_frames']) is not int or value['total_num_frames'] <= indices[-1]
            or not isinstance(value['fps'], (int, float)) or not math.isfinite(value['fps']) or value['fps'] <= 0):
        raise ValueError('invalid RGB timing schema')
    for frame, index, time in zip(frames, indices, times):
        if (not isinstance(frame, dict) or set(frame) != {'path', 'sha256'} or not isinstance(frame['path'], str)
                or not re.fullmatch('[0-9a-f]{64}', frame['sha256'])
                or not isinstance(time, (int, float)) or not math.isclose(time, index / value['fps'], rel_tol=1e-9, abs_tol=1e-9)):
            raise ValueError('invalid RGB frame pin or timestamp')
    if not isinstance(value['question'], str) or not value['question'] or not isinstance(value['options'], list) or any(not isinstance(x, str) for x in value['options']):
        raise ValueError('invalid question/options schema')
    return True
