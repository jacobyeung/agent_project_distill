raise RuntimeError('UNVERIFIED_MODULE_EXECUTED')
"""Unified item records from a direct-kit return (kits f42aa1a4 / ea1a1b2d and their re-binds).

Reads a0/results/0/budget_<B>.jsonl (scored rows) and the matching .meta.jsonl (forced-close
flags). Items of a direct read emit no call by construction of the scoring here: a row whose
generated text opens a routing call is counted (calls=1, calls_served=0) so the report prints the
call rate of a direct reader too.
"""
import json
import re
from pathlib import Path

CALL_RE = re.compile(r'<(?:ground|gap|move|turn|pose)\b|<tool_call>')


def _rows(path):
    with Path(path).open() as s:
        return [json.loads(l) for l in s if l.strip()]


def from_return(a0_dir, budget=2048):
    base = Path(a0_dir) / 'results' / '0'
    rows = _rows(base / f'budget_{budget}.jsonl')
    meta_path = base / f'budget_{budget}.meta.jsonl'
    meta = {m.get('source_key', m['key']): m for m in _rows(meta_path)} if meta_path.exists() else {}
    out = []
    for r in rows:
        m = meta.get(r.get('key'), {})
        text = str(r.get('raw_generation') or r.get('response_text') or '')
        calls = len(CALL_RE.findall(text))
        out.append(dict(
            id=str(r.get('example_id', r.get('id'))), question_type=r['question_type'],
            score=r.get('score'), status=r.get('status'), error=r.get('error'),
            derivation_error=bool(m.get('derivation_error', r.get('derivation_error', False))),
            forced_close=bool(m.get('forced_close', False)), refusal=False,
            calls=calls, calls_served=0, parse_failed=bool(r.get('parse_failed', False)),
            continuation_capped=r.get('max_new_tokens') == 64 and (r.get('output_tokens', 0) >= 64 or r.get('finish_reason') == 'length')))
    return out
