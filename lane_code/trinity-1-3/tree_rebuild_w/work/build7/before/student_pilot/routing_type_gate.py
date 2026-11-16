"""Type admission after the sealed lexical grammar; no inference policy."""
import hashlib
from collections import Counter

NO_HEAD_GRAMMAR = {'object_size_estimation', 'object_rel_direction_easy'}


def refusal(qtype, answer_form, policy):
    if answer_form not in ('direct', 'routed'):
        return 'unknown_answer_form'
    if answer_form == 'routed':
        if qtype in NO_HEAD_GRAMMAR:
            return 'no_head_grammar'
        if qtype not in policy['route'] + policy.get('both', ()):
            return 'program_type_not_admitted'
    elif qtype not in policy['direct'] + policy.get('both', ()):
        return 'direct_type_not_admitted'
    return None


def validate(row, policy, artifact_heads):
    form = row.get('answer_form')
    reason = refusal(row['question_type'], form, policy)
    if reason:
        raise ValueError(reason)
    if form == 'routed' and (not row.get('response_heads') or
                            not set(row['response_heads']) <= set(artifact_heads)):
        raise ValueError('routed_head_outside_artifact')
    return row


def sample(rows, policy, winning_forms, totals, minority_count=2000, seed='b08-20261116'):
    """Select per-item forms from admitted rows using registered counts, never answers."""
    if type(minority_count) is not int or minority_count <= 0:
        raise ValueError('minority_count must be pinned and positive')
    cells = {}
    seen = set()
    for row in rows:
        key = (row['question_type'], row['answer_form'])
        identity = (row['question_type'], row['qid'])
        if identity in seen:
            raise ValueError('answer_form must be assigned once per item')
        seen.add(identity)
        reason = refusal(*key, policy)
        if reason: raise ValueError(reason)
        cells.setdefault(key, []).append(row)
    result = []
    for kind, total in sorted(totals.items()):
        majority = winning_forms[kind]
        both = kind in policy.get('both', ()) and kind not in NO_HEAD_GRAMMAR
        if both and total <= 2 * minority_count:
            raise ValueError('minority must remain smaller than the winning form')
        counts = {majority: total - minority_count if both else total}
        if both: counts['direct' if majority == 'routed' else 'routed'] = minority_count
        for form, count in counts.items():
            candidates = sorted(cells.get((kind, form), []),
                key=lambda r: hashlib.sha256((seed+':'+str(r['qid'])).encode()).hexdigest())
            if len(candidates) < count:
                raise ValueError('rows_lane_missing_minority_form:'+kind+':'+form)
            result.extend(candidates[:count])
    return result
