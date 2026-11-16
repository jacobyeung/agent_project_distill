"""Compact records from authenticated B2048 report rows and journals."""
import json
from pathlib import Path


def records(family, report, journal, step):
    if report['arm'] != 'B2048':
        raise ValueError('Expected B2048')
    scored = {r['key']: r for r in report['rows']}
    if len(scored) != len(report['rows']):
        raise ValueError('Duplicate report key')
    result = []
    seen = set()
    for raw in journal:
        r = json.loads(raw) if isinstance(raw, str) else raw
        key = r['key']
        if key in seen or key not in scored or r['status'] != 'complete':
            raise ValueError('Journal membership or completion differs')
        seen.add(key)
        s = scored[key]
        if (r['question_type'], r['room']) != (s['question_type'], s['room']):
            raise ValueError('Journal metadata differs')
        task = s['question_type']
        level = next((x for x in ('easy', 'medium', 'hard') if task.endswith('_'+x)), None)
        basis = 'released_answer' if family == 'main' and s['stratum'] == 'primary' else 'answer'
        value = s['scores'][basis]
        if value is None:
            raise ValueError('Missing score')
        pair = None
        if family == 'away':
            pair = r['id']
        elif family == 'forward':
            pair = r['label_provenance']['paired_away_qid']
        prediction = r['extracted_answer']
        # Compare semantic option contents, not letters from permuted options.
        content = None
        for i, option in enumerate(r.get('options', [])):
            letter = chr(65+i)
            body = str(option).strip()
            if body.startswith(letter+'.') or body.startswith(letter+')'):
                body = body[2:].strip()
            if str(prediction).strip().upper() == letter or str(prediction).strip().casefold() == body.casefold():
                content = ' '.join(body.casefold().split())
        result.append(dict(id=r['id'], family=family, task_type=task, level=level,
            room=s['room'], scene=r['scene'], prediction=prediction, answer_content=content,
            score=value, scoring_basis=basis, budget=2048, step=step, pair_id=pair,
            count_kind='single' if task == 'object_counting' else None))
    if seen != set(scored):
        raise ValueError('Incomplete journal')
    return result


def write(path, values):
    Path(path).write_text(''.join(json.dumps(r, sort_keys=True, allow_nan=False)+'\n' for r in values))
