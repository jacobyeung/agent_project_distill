"""Unified item records from a native routed-read journal (C8r record schema, job 170056 form).

State definitions follow the reviewed analysis 44468e72 (`answer_states`):
  no final answer (no_answer, parse failure, call limit, no </think>) or a geometry / program
  refusal -> refusal=True, scores 0, stays in the denominator;
  a budget-forced close with a parsed answer -> forced_close=True, scored as recorded.
`calls` is the record's call_count; `calls_served` excludes call errors and budget-truncated calls.
"""
import ast
import json
import re
from pathlib import Path


SCRIPTED = 'scripted'


def _val(x):
    if isinstance(x, str) and x[:1] in '{[' :
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return x
    return x


def _bool(x):
    return x is True or (isinstance(x, str) and x == 'True')


def _int(x):
    return int(x) if x not in (None, '', 'None') else 0


def states(row):
    dec = _val(row.get('decode')) or {}
    if not isinstance(dec, dict):
        dec = {}
    if row.get('geometry_refusal') not in (None, '', 'None', False):
        return dict(refusal=True, forced_close=False, reason='geometry_refusal')
    if dec.get('finish') == 'program_refusal':
        return dict(refusal=True, forced_close=False, reason='program_refusal')
    no_final = (_bool(row.get('no_answer')) or _bool(row.get('parse_failed')) or _bool(row.get('strict_no_answer'))
                or _bool(row.get('call_limit')) or _bool(dec.get('strict_no_answer')) or _bool(dec.get('parse_failed'))
                or dec.get('finish') == 'call_limit' or row.get('finish_reason') == 'call_limit')
    if 'text' in dec:
        no_final = no_final or not re.search(r'</think\s*>', dec.get('text') or '', re.I)
    db = _val(dec.get('decode_budget'))
    fired = isinstance(db, dict) and _bool(db.get('fired'))
    budget = (_bool(row.get('capped')) or _bool(row.get('forced_close')) or _bool(row.get('hit_token_cap')) or fired
              or dec.get('finish') in ('max_new_tokens', 'context_exhaustion'))
    if no_final:
        return dict(refusal=True, forced_close=False, reason='no_final_answer')
    return dict(refusal=False, forced_close=bool(budget), reason=None)


def producer_error(row):
    dec = _val(row.get('decode')) or {}
    dec = dec if isinstance(dec, dict) else {}
    return bool(row.get('finish_reason') == 'error' or row.get('finish') == 'error' or _bool(row.get('derivation_error'))
                or _bool(row.get('producer_error')) or dec.get('finish') == 'error' or _bool(dec.get('producer_error')))


SCRIPT_FIELDS = ('script_mode', 'script_answer')


def check_not_scripted(row):
    """Refuse a C8r scripted record. perception.scripted() writes script_answer / script_mode into the
    decoded record, which the journal stores as row['decode'], so the fields are checked in the row
    and in its decode, in dict or string form, and the arm label is compared case- and space-blind."""
    if str(row.get('arm', '')).strip().lower() == SCRIPTED:
        raise ValueError('row %s is from the scripted arm; it is never scored' % row.get('key'))
    raw = row.get('decode')
    dec = _val(raw)
    for d in (row, dec if isinstance(dec, dict) else {}):
        if any(d.get(f) is not None for f in SCRIPT_FIELDS):
            raise ValueError('row %s carries a script answer; it is never scored' % row.get('key'))
    if isinstance(raw, str) and not isinstance(dec, dict) and any(f in raw for f in SCRIPT_FIELDS):
        raise ValueError('row %s carries a script answer; it is never scored' % row.get('key'))


def unify(row, *, id_of=lambda r: str(r['key']), score_field='answer'):
    check_not_scripted(row)
    st = states(row)
    scores = _val(row.get('scores')) or {}
    err = producer_error(row)
    calls = _int(row.get('call_count'))
    bad = _int(row.get('call_errors')) + _int(row.get('budget_truncated_calls'))
    return dict(id=id_of(row), question_type=row['question_type'], score=scores.get(score_field),
                status='error' if err else 'complete', error='producer error' if err else None,
                refusal=st['refusal'], refusal_reason=st['reason'], forced_close=st['forced_close'],
                calls=calls, calls_served=max(0, calls - bad), parse_failed=False, arm=row.get('arm'))


def from_journal(path, arm, **kw):
    """Rows of one arm. The C8r `scripted` arm answers through a harness unit conversion (c8r
    perception.py), which USER ruling 4 (2026-11-16) bans, so it is refused, as is any row that
    carries a script answer."""
    if str(arm).strip().lower() == SCRIPTED:
        raise ValueError('the scripted arm answers through a harness unit conversion; it is never scored')
    out = []
    with Path(path).open() as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get('arm') == arm:
                    out.append(unify(r, **kw))
    return out
