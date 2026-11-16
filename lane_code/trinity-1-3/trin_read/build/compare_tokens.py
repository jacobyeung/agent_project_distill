#!/usr/bin/env python3
"""Exact accepted/actual token comparison, with explicit missing data and timing scope."""
import argparse
import json
import math
from pathlib import Path

ARMS = {'ON16k':'0', 'B2048':'budget_2048/0', 'B4096':'budget_4096/0'}


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    path = Path(path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def compare_row(accepted, actual):
    actual = actual or {}
    left, right = accepted.get('token_ids'), actual.get('token_ids')
    valid = (isinstance(left, list) and isinstance(right, list)
             and all(type(i) is int and i >= 0 for i in left+right))
    divergence = None
    if valid:
        divergence = next((i for i, (a,b) in enumerate(zip(left,right)) if a != b), None)
        if divergence is None and len(left) != len(right): divergence = min(len(left),len(right))
    fields = ('raw_generation','extracted_answer','score')
    return dict(example_id=accepted['example_id'], present=bool(actual), token_ids_identical=valid and left == right,
                first_divergence_index=divergence, accepted_length=len(left) if isinstance(left,list) else None,
                actual_length=len(right) if isinstance(right,list) else None,
                **{key+'_equal':key in accepted and key in actual and accepted[key] == actual[key] for key in fields},
                accepted_answer=accepted.get('extracted_answer'), actual_answer=actual.get('extracted_answer'),
                accepted_score=accepted.get('score'), actual_score=actual.get('score'))


def unique(values):
    result = {}
    for row in values:
        key = row['example_id']
        if key in result: raise ValueError('Duplicate result ID: '+key)
        result[key] = row
    return result


def positive_seconds(row):
    value = row.get('seconds')
    return float(value) if isinstance(value, (int,float)) and math.isfinite(value) and value > 0 else None


def timing(dest, arm, ids):
    # Read worker journals; budget meta distinguishes reused ON rows from fresh generations.
    base = Path(dest)/'results/0'
    path = base/'g0.jsonl' if arm == 'ON16k' else base/('budget_'+arm[1:]+'.g0.jsonl')
    journal = unique(rows(path)); meta = {}
    if arm != 'ON16k':
        for row in rows(path.with_suffix('.meta.jsonl')):
            key = row.get('source_key', '').split(':', 1)[-1]
            if key in meta and meta[key] != row: raise ValueError('Conflicting budget timing receipts')
            meta[key] = row
    items = []
    for key in ids:
        row = journal.get(key, {}); receipt = meta.get(key, {})
        reused = arm != 'ON16k' and receipt.get('answer_cap_policy') == 'reuse_full_on_answer'
        generated = arm == 'ON16k' or (receipt.get('answer_cap_policy') == 'continuation_64' and not receipt.get('derivation_error'))
        seconds = positive_seconds(row) if generated else None
        count = len(row['token_ids']) if generated and isinstance(row.get('token_ids'),list) else None
        items.append(dict(example_id=key, seconds=seconds, generated_tokens=count,
                          generated_tokens_per_second=count/seconds if count is not None and seconds else None,
                          reused_on_generation=reused,
                          timing_kind='generation_latency' if generated else 'no_new_generation_or_missing_receipt'))
    measured = [r for r in items if r['seconds'] is not None and r['generated_tokens'] is not None]
    return dict(items=items, measured_items=len(measured),
                mean_seconds_per_measured_item=sum(r['seconds'] for r in measured)/len(measured) if measured else None,
                generated_tokens_per_sum_latency=sum(r['generated_tokens'] for r in measured)/sum(r['seconds'] for r in measured) if measured else None,
                note='Concurrent per-request latencies, not wall-clock throughput. Reused ON rows are not counted as new budget generations.')


def compare(reference, actual_by_arm):
    ids = reference['ids']; arms = {}; passed = True
    if not ids or len(ids) != len(set(ids)): raise ValueError('Invalid reference membership')
    for arm in ARMS:
        expected = unique(reference['arms'][arm]); actual = unique(actual_by_arm.get(arm, []))
        if set(expected) != set(ids): raise ValueError('Reference arm membership differs')
        checks = [compare_row(expected[key], actual.get(key)) for key in ids]
        equal = all(c['token_ids_identical'] and all(c[k+'_equal'] for k in ('raw_generation','extracted_answer','score')) for c in checks)
        complete = set(actual) == set(ids)
        scores = [actual[key].get('score') for key in ids if key in actual]
        numeric = len(scores) == len(ids) and all(isinstance(s,(int,float)) and math.isfinite(s) for s in scores)
        arms[arm] = dict(items=checks, identical_items=sum(c['token_ids_identical'] for c in checks),
                         membership_equal=complete, unexpected_ids=sorted(set(actual)-set(ids)),
                         mean_score_actual=sum(scores)/len(ids) if numeric else None,
                         mean_score_accepted=sum(expected[key]['score'] for key in ids)/len(ids))
        passed = passed and equal and complete
    return dict(passed=passed, items=len(ids), arms=arms)


def write_report(reference_path, dest, attempt, out, memory=None, exit_path=None):
    from trinity_read import writable
    reference = load(reference_path); dest = Path(dest); out = writable(out)
    errors = []; actual = {}
    for arm,rel in ARMS.items():
        try:
            actual[arm] = rows(dest/'results'/rel/('items_'+attempt+'.jsonl'))
            unique(actual[arm])
        except (ValueError, KeyError, OSError) as error:
            errors.append(arm+' results: '+str(error)); actual[arm] = []
    report = compare(reference, actual)
    for arm in ARMS:
        try: report['arms'][arm]['timing'] = timing(dest,arm,reference['ids'])
        except (ValueError, KeyError, OSError) as error:
            errors.append(arm+' timing: '+str(error))
            report['arms'][arm]['timing'] = dict(items=[dict(example_id=k,seconds=None,generated_tokens_per_second=None) for k in reference['ids']], error=str(error))
    try: samples = rows(memory) if memory else []
    except (ValueError, OSError) as error:
        errors.append('memory: '+str(error)); samples = []
    report['peak_card_memory_mib'] = max((s['memory_used_mib'] for s in samples), default=None)
    report['memory_samples'] = len(samples)
    report['memory_note'] = 'Maximum observed 1 s nvidia-smi sample; shorter peaks may be missed.'
    exit_info = load(exit_path) if exit_path and Path(exit_path).exists() else None
    report['execution'] = exit_info
    report['bwrap'] = exit_info.get('bwrap') if exit_info else None
    report['llguidance_stub'] = exit_info.get('llguidance_stub') if exit_info else None
    report['host_dev_shm_ours'] = exit_info.get('host_dev_shm_ours') if exit_info else None
    report['host_dev_shm_ours_before'] = exit_info.get('host_dev_shm_ours_before') if exit_info else None
    report['stub_usage'] = exit_info.get('stub_usage') if exit_info else None
    if report['stub_usage'] or (report['llguidance_stub'] and report['llguidance_stub'].get('enabled')):
        usage = report['stub_usage']
        if not usage or not usage.get('passed'):
            errors.extend(usage.get('errors', ['llguidance audit failed']) if usage else ['Missing llguidance audit'])
    report['sandbox'] = load(out/'SANDBOX.json') if (out/'SANDBOX.json').exists() else None
    report['errors'] = errors
    report['passed'] = report['passed'] and not errors and bool(samples) and bool(exit_info and exit_info['returncode'] == 0 and not exit_info.get('sampler_errors'))
    report['accepted_job'] = 169526
    report['accepted_source'] = str(reference_path)
    report['first_divergence_note'] = 'Zero-based; a pure length difference diverges at the shorter length. Null also means tokens were unavailable; consult present and lengths.'
    out.mkdir(parents=True, exist_ok=True)
    (out/'PROOF.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+'\n')
    text = ['Token proof passed: '+str(report['passed'])+'.', '',
            'Peak sampled card memory (MiB): '+str(report['peak_card_memory_mib'])+'.', '',
            '| Arm | Identical token arrays | Mean actual score | Mean accepted score |',
            '|---|---:|---:|---:|']
    for arm,a in report['arms'].items():
        text.append('| {} | {}/{} | {} | {} |'.format(arm,a['identical_items'],len(reference['ids']),a['mean_score_actual'],a['mean_score_accepted']))
    text += ['', 'Per-item comparison (zero-based divergence; no numerical rounding):', '',
             '| Arm | ID | Tokens equal | First divergence | Accepted length | Actual length | Raw equal | Answer equal | Score equal | Seconds | Tokens/s |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for arm,a in report['arms'].items():
        times = {r['example_id']:r for r in a['timing']['items']}
        for r in a['items']:
            t = times[r['example_id']]
            values = [arm,r['example_id'],r['token_ids_identical'],r['first_divergence_index'],r['accepted_length'],r['actual_length'],
                      r['raw_generation_equal'],r['extracted_answer_equal'],r['score_equal'],t['seconds'],t['generated_tokens_per_second']]
            text.append('| '+' | '.join(str(v) for v in values)+' |')
    text += ['', 'llguidance audit: '+json.dumps(report['stub_usage'], sort_keys=True), 'Failure reasons: '+json.dumps(errors), '', report['memory_note'], '', 'Timing uses worker journals and budget receipts. Reused rows have no new budget latency. Missing values remain null. Concurrent request latency is not wall-clock throughput.', '']
    (out/'PROOF.md').write_text('\n'.join(text))
    return report


def write_repeated(root, token, out, failure=None):
    """Compare completed phase-B packets without rerunning a failed execution."""
    from trinity_read import dump
    paths = [Path(root)/'runs'/(token+'_r'+str(i)) for i in (1, 2)]
    proofs = [load(p/'PROOF.json') if (p/'PROOF.json').exists() else None for p in paths]
    errors = [failure] if failure else []
    ids = []
    for proof in proofs:
        if proof:
            ids = [r['example_id'] for r in proof['arms']['ON16k']['items']]
            break
    arms = {}; passed = bool(ids)
    for arm, rel in ARMS.items():
        data = []
        for path in paths:
            try: data.append(unique(rows(path/'b0/d0/results'/rel/'items_b0.jsonl')))
            except (ValueError, KeyError, OSError) as error:
                errors.append(str(error)); data.append({})
        left, right = data
        checks = [compare_row(left.get(key, dict(example_id=key)), right.get(key)) for key in ids]
        complete = bool(ids) and set(left) == set(right) == set(ids)
        tokens = complete and all(c['token_ids_identical'] for c in checks)
        answers = complete and all(c['extracted_answer_equal'] for c in checks)
        scores = complete and all(c['score_equal'] for c in checks)
        raw = complete and all(c['raw_generation_equal'] for c in checks)
        arms[arm] = dict(items=checks, membership_equal=complete, token_ids_equal=tokens,
                         answers_equal=answers, scores_equal=scores, raw_generation_equal=raw)
        passed = passed and tokens and answers and scores and raw
    comparison = dict(passed=bool(passed and not errors), runs=[str(p) for p in paths], arms=arms, errors=errors,
                      labels=dict(accepted='run1', actual='run2'),
                      first_divergence_note='Zero-based; missing arrays cannot pass, even if both runs are missing.')
    dump(out/'RUN_TO_RUN.json', comparison)
    summary = dict(passed=comparison['passed'] and all(p and p['passed'] for p in proofs),
                   runs=[dict(path=str(path), vs_accepted=proof) for path, proof in zip(paths, proofs)],
                   run_to_run=comparison)
    dump(out/'PROOF.json', summary)
    text = ['Repeated token proof passed: '+str(summary['passed'])+'.', '',
            '| Comparison | ON16k tokens | B2048 tokens | B4096 tokens | Passed |',
            '|---|---|---|---|---|']
    for i, proof in enumerate(proofs, 1):
        counts = [str(proof['arms'][arm]['identical_items'])+'/'+str(proof['items']) if proof else 'not executed/completed' for arm in ARMS]
        text.append('| Run {} vs accepted | {} | {} |'.format(i, ' | '.join(counts), bool(proof and proof['passed'])))
    text.append('| Run 1 vs run 2 | {} | {} |'.format(' | '.join(str(arms[arm]['token_ids_equal']) for arm in ARMS), comparison['passed']))
    text += ['', '| Arm | Answers equal between runs | Scores equal between runs |', '|---|---|---|']
    for arm in ARMS: text.append('| {} | {} | {} |'.format(arm, arms[arm]['answers_equal'], arms[arm]['scores_equal']))
    text += ['', 'Per-item arrays and first divergence are in RUN_TO_RUN.json. Each run retains its full accepted comparison and sandbox receipt.',
             'Failure reasons: '+json.dumps(errors), '']
    (out/'PROOF.md').write_text('\n'.join(text))
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('reference','dest','attempt','out'): p.add_argument('--'+name, required=True)
    p.add_argument('--memory'); p.add_argument('--exit', dest='exit_path')
    a = p.parse_args()
    result = write_report(a.reference,a.dest,a.attempt,a.out,a.memory,a.exit_path)
    raise SystemExit(0 if result['passed'] else 1)
