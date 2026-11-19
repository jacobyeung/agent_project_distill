"""Counting-form admission; this module is never an inference component."""
import re

LIST_RE = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:')
PROC_RE = re.compile(r'count (?:it|each) once')
REGION_RE = re.compile(r'\((?:left|middle|right)\)')


def classify(row):
    """Reproduce the count-fix classifier's cell and form rules exactly."""
    text = row.get('target') or ''
    if row.get('question_type') == 'first_seen_frame':
        return 'first_seen', 'FIRST_SEEN'
    if 'count_kind' in row:
        cell, form = 'totals', 'TOTALS'
    else:
        cell = 'counting'
        form = 'FS_LIST' if LIST_RE.search(text) else ('PROC' if PROC_RE.search(text) else 'OTHER')
    if form in ('FS_LIST', 'TOTALS') and REGION_RE.search(text):
        form += '_REGION'
    return cell, form


def admit(row, cell):
    if cell not in ('counting', 'totals'):
        return
    classified, form = classify(row)
    if cell == 'totals' or classified == 'totals':
        raise ValueError('R1_TOTALS_ROW_REFUSED:'+str(row.get('qid')))
    if form.startswith('FS_LIST'):
        raise ValueError('R1_COUNTING_LIST_FORM_REFUSED:'+str(row.get('qid')))
    if form != 'PROC':
        raise ValueError('R1_COUNTING_PROCEDURE_REQUIRED:'+str(row.get('qid')))
