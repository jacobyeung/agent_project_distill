"""Strict standalone tally gate. This module does not change N's validator."""
import re

def validate(row):
    question = row['student_input']['question']
    categories = re.findall(r'"([a-z][a-z -]*)"', question)
    if len(categories) != 2 or len(set(categories)) != 2:
        raise ValueError('Exactly two distinct quoted categories are required')
    lines = row['target'].splitlines()
    if (len(lines) != 8 or lines[:2] != ['<think>', 'Tally new instances at their first sampled frame:']
            or lines[5:7] != ['</think>', ''] or lines[7] != row['answer']):
        raise ValueError('Wrong tally layout or answer suffix')
    totals, tallies = [], []
    for category, line in zip(categories, lines[2:4]):
        match = re.fullmatch(re.escape(category) + r': (.+) -> ([1-9][0-9]*)\.', line)
        if not match:
            raise ValueError('Asked category is missing or out of order')
        entries = match[1].split('; ')
        if not 1 <= len(entries) <= 32:
            raise ValueError('Tally length must be within 1..32')
        previous, total, histogram = 0, 0, {}
        for entry in entries:
            m = re.fullmatch(r'frame ([1-9][0-9]*): ([1-9][0-9]*)', entry)
            if not m:
                raise ValueError('Each entry needs a frame and a positive new-instance count')
            frame, count = map(int, m.groups())
            if not previous < frame <= 32:
                raise ValueError('Frames must increase strictly within 1..32')
            previous = frame
            total += count
            histogram[frame] = count
        if total != int(match[2]):
            raise ValueError('Category sum differs from the tally')
        totals.append(total)
        tallies.append(histogram)
    a, b = totals
    op, meaning = ('>', 'more') if a > b else ('<', 'fewer') if a < b else ('=', 'equal number')
    if lines[4] != f'{a} {op} {b}.':
        raise ValueError('Comparison differs from the category sums')
    choices = {}
    for option in row['student_input']['options']:
        match = re.fullmatch(r'([ABC])\. (more|fewer|equal number)', option)
        if not match or match[1] in choices:
            raise ValueError('Invalid or repeated option letter')
        choices[match[1]] = match[2]
    if set(choices) != set('ABC') or set(choices.values()) != {'more', 'fewer', 'equal number'}:
        raise ValueError('Options must cover each count relation exactly once')
    if choices.get(row['answer']) != meaning:
        raise ValueError('Final option letter disagrees with the comparison')
    if row['question_type'] != 'relative_count':
        raise ValueError('Wrong question type')
    return {'categories': categories, 'totals': totals, 'tallies': tallies, 'relation': meaning}
