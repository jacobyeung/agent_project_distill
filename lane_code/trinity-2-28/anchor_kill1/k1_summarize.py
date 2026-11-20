"""Registered K1 contrasts plus explicit frame-perturbation diagnostics."""
import collections
import json
from pathlib import Path
import numpy as np
import anchor_analysis as A

W = Path(__file__).resolve().parent


def summaries(calls, distances):
    result = dict(rows=len(distances),calls=len(calls),rooms=len({r['room'] for r in calls}))
    for key in ['baseline_right','baseline_not_seen','a3x_right','a3x_not_seen']:
        result[key] = A.rate(calls,lambda r:r[key])
    result['paired_on_target_delta'] = A.rate(calls,lambda r:int(r['a3x_right'])-int(r['baseline_right']))
    result['f_fixed_wrong'] = A.rate(calls,lambda r:r['a3x_right'] and not r['baseline_right'],lambda r:not r['baseline_right'])
    result['h_broken_right'] = A.rate(calls,lambda r:r['baseline_right'] and not r['a3x_right'],lambda r:r['baseline_right'])
    for arm in ['baseline','a3x']:
        result[arm+'_distance_mra'] = A.rate(distances,lambda r:r[arm]['mra'])
        result[arm+'_distance_refusal'] = A.rate(distances,lambda r:r[arm]['prediction'] is None)
    result['paired_distance_mra_delta'] = A.rate(distances,lambda r:r['a3x']['mra']-r['baseline']['mra'])
    result['no_eligible_gt_anchor'] = sum(r['best_frame'] is None for r in calls)
    result['no_alternative_visible_anchor'] = sum(r['neighbor_frame'] is None for r in calls)
    for label, selected in [('nearest_visible',[r for r in calls if r['neighbor_frame'] is not None]),
                            ('immediate_adjacent',[r for r in calls if r['adjacent_frame'] is not None])]:
        result[label] = dict(calls=len(selected))
        for key in ['baseline_right','a3x_right','neighbor_right','neighbor_not_seen']:
            result[label][key] = A.rate(selected,lambda r:r[key])
        result[label]['delta_vs_best'] = A.rate(selected,lambda r:int(r['neighbor_right'])-int(r['a3x_right']))
        result[label]['delta_vs_baseline'] = A.rate(selected,lambda r:int(r['neighbor_right'])-int(r['baseline_right']))
        result[label]['candidate_changed'] = A.rate(selected,lambda r:r['chosen_id'] != r['neighbor_id'])
    nr = [r for r in distances if r['neighbor_both_eligible']]
    result['neighbor_distance'] = dict(rows=len(nr),mra=A.rate(nr,lambda r:r['neighbor']['mra']),
        delta_vs_best=A.rate(nr,lambda r:r['neighbor']['mra']-r['a3x']['mra']),
        delta_vs_baseline=A.rate(nr,lambda r:r['neighbor']['mra']-r['baseline']['mra']))
    result['cited_frame_identity'] = dict(
        best=A.rate(calls,lambda r:r['a3x_cited_right']),
        neighbor=A.rate([r for r in calls if r['neighbor_frame'] is not None],lambda r:r['neighbor_cited_right']))
    return result


def main():
    validation = json.loads((W/'k1_adapter_validation.json').read_text())
    assert validation['status'] == 'PASS' and validation['baseline_distances_equal_published'] == 1012
    inputs = [json.loads(l) for l in (W/'k1_calls.jsonl').open()]
    A.kill(W/'k1_calls.jsonl')
    calls = json.loads((W/'kill_calls.json').read_text())
    distances = json.loads((W/'k1_distance_rows.json').read_text())
    # A separate explicit scan checks the production kernel's choices, including
    # empty frames, no eligible GT frame, and the stable first-candidate tie rule.
    ties = 0
    for raw, r in zip(inputs,calls,strict=True):
        r['capture'],r['dataset'] = raw['capture'],raw['dataset']
        for arm,frame_key,id_key in [('a3x','best_frame','chosen_id'),('neighbor','neighbor_frame','neighbor_id')]:
            frame = r[frame_key]
            chosen = None
            largest = -1
            for c in raw['candidates']:
                area = c['members'].get(str(frame))
                if area is not None and area > largest:
                    chosen,largest = c,area
            cid = chosen['id'] if chosen else None
            if arm == 'a3x':
                assert r[id_key] == cid
                ties += bool(chosen and sum(c['members'].get(str(frame)) == largest for c in raw['candidates']) > 1)
            else:
                r[id_key] = cid
            assert r[arm+'_right'] == bool(chosen and chosen['on_target'])
            assert r[arm+'_not_seen'] == (chosen is None)
            value = chosen['cited_ious'][str(frame)] if chosen else None
            r[arm+'_cited_right'] = bool(value is not None and value >= .5)
        if r['adjacent_frame'] is not None:
            assert r['neighbor_frame'] == r['adjacent_frame']
    result = summaries(calls,distances)
    result['by_dataset'] = {ds:summaries([r for r in calls if r['dataset']==ds],[r for r in distances if r['dataset']==ds])
                            for ds in sorted({r['dataset'] for r in calls})}
    unique = {(r['capture'],r['operand']):r for r in calls}
    result['unique_object_diagnostic'] = dict(objects=len(unique),
        baseline=A.rate(list(unique.values()),lambda r:r['baseline_right']),
        a3x=A.rate(list(unique.values()),lambda r:r['a3x_right']))
    paired = collections.defaultdict(list)
    for r in calls:
        paired[r['row_id']].append(r)
    row_hits = [dict(room=rs[0]['room'],baseline=all(r['baseline_right'] for r in rs),a3x=all(r['a3x_right'] for r in rs))
                for rs in paired.values()]
    result['both_operands_right'] = dict(baseline=A.rate(row_hits,lambda r:r['baseline']),
        a3x=A.rate(row_hits,lambda r:r['a3x']),delta=A.rate(row_hits,lambda r:int(r['a3x'])-int(r['baseline'])))
    delta = result['paired_distance_mra_delta']
    result['bars'] = dict(distance_gain=delta['rate']>=.02 and delta['ci95'][0]>0,
        f_fixed_wrong=result['f_fixed_wrong']['rate']>=.5,
        h_broken_right=result['h_broken_right']['rate']<=.05)
    result['decision'] = 'PASS' if all(result['bars'].values()) else 'FAIL: drop ANCHOR under registered kill rule'
    result['failure_breakdown'] = dict(
        damaged_to_not_seen=sum(r['baseline_right'] and r['a3x_not_seen'] for r in calls),
        damaged_to_wrong_track=sum(r['baseline_right'] and not r['a3x_right'] and not r['a3x_not_seen'] for r in calls),
        not_seen_no_eligible_gt_anchor=sum(r['best_frame'] is None for r in calls),
        not_seen_empty_best_frame=sum(r['best_frame'] is not None and r['a3x_not_seen'] for r in calls))
    result['validation'] = dict(explicit_choice_scan=len(calls),best_frame_area_ties=ties,
        baseline_parity_rows=validation['baseline_distances_equal_published'],
        draws=A.DRAWS,seed=A.SEED,independent_review=False)
    A.write_json('k1_summary.json',result)
    A.write_json('kill_summary.json',result)
    A.write_json('k1_scored_calls.json',calls)
    print(json.dumps({k:result[k] for k in ['rows','calls','rooms','baseline_right','a3x_right','a3x_not_seen',
        'paired_on_target_delta','paired_distance_mra_delta','f_fixed_wrong','h_broken_right','bars','decision']},indent=2))


if __name__ == '__main__':
    main()
