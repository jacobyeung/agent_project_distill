"""Bracketed, repeat-level paired estimates; insufficient precision is explicit."""
import argparse
import json
import math
from pathlib import Path
import statistics
import struct


def precision(values):
    n = len(values)
    mean = statistics.mean(values)
    if n < 3:
        return dict(repeats=n, mean_gain_s=mean, ci95_halfwidth_s=None,
                    minimum_detectable_difference_s=None, resolved=False)
    # Conservative two-sided Student-t 95% critical values (round df down).
    df = n - 1
    critical, power = next((t,p) for d,t,p in [(29,2.046,.855),(19,2.094,.861),(9,2.263,.884),
        (5,2.571,.920),(4,2.777,.942),(3,3.183,.979),(2,4.303,1.061)] if df >= d)
    se = statistics.stdev(values) / math.sqrt(n)
    mdd = (critical + power) * se  # t(.975,df) + t(.80,df); approximate power
    return dict(repeats=n, mean_gain_s=mean, ci95_halfwidth_s=critical*se,
                minimum_detectable_difference_s=mdd,
                resolved=mean > max(mdd, critical*se),
                target_1s_resolved=mdd <= 1.,
                samples='independent repeat means; steps within a repeat are not independent samples')


def summarize(root):
    root = Path(root)
    paths = sorted(root.glob('r*_l*_*'))
    paths = [p for p in paths if p.is_dir()]
    if not paths:
        raise ValueError('No bracketed timing arms')
    reference = root/'r0_l0_off'
    baseline = [json.loads((reference/f'rank{r}/steps.json').read_text()) for r in range(4)]
    bm = [json.loads((reference/f'rank{r}/manifest.json').read_text()) for r in range(4)]
    arms, mismatches = {}, []
    # Diagnose OFF reproducibility before attributing a difference to a switch.
    for path in sorted(paths, key=lambda p: (not p.name.endswith('_off'), p.name)):
        runs = [json.loads((path/f'rank{r}/steps.json').read_text()) for r in range(4)]
        for rank, (base, trial) in enumerate(zip(baseline,runs)):
            tm = json.loads((path/f'rank{rank}/manifest.json').read_text())
            for key in ('trainables','config_sha256','start_step','resume','binding','threads','warmup','measured_steps'):
                if bm[rank][key] != tm[key]:
                    raise ValueError('Manifest parity failed: ' + key)
            if len(trial) != tm['warmup'] + tm['measured_steps']:
                raise ValueError('Incomplete arm; all warmup and measured steps required')
            if [r['plan_sha256'] for r in trial] != [r['plan_sha256'] for r in base]:
                raise ValueError('Row plan mismatch')
            expected, actual = base[0]['first_step_micro_losses'], trial[0]['first_step_micro_losses']
            if not expected or len(expected) != len(actual):
                raise ValueError('Loss count is empty or differs')
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in expected+actual):
                raise ValueError('Loss parity requires finite scalar losses')
            if [struct.pack('d',v) for v in expected] != [struct.pack('d',v) for v in actual]:
                mismatches.append(dict(arm=path.name, rank=rank))
        warmup = bm[0]['warmup']
        count = bm[0]['measured_steps']
        if warmup < 10 or count < 10:
            raise ValueError('Need at least ten discarded and ten measured steps')
        values = {key:[max(r[i][key] for r in runs) for i in range(warmup,warmup+count)]
                  for key in ('wall_seconds','data_seconds')}
        for label in ('forward_total','backward_including_recompute_and_fsdp'):
            values[label] = [max(sum(r[i]['microstep_host'][label]) for r in runs)
                             for i in range(warmup,warmup+count)]
        arms[path.name] = values
    results = {}
    for arm in ('prefetch','cache','metrics'):
        deltas = {key:[] for key in next(iter(arms.values()))}
        paired = []
        for name, values in arms.items():
            repeat, leg, kind = name.split('_',2)
            if kind != arm:
                continue
            index = int(leg[1:])
            before, after = f'{repeat}_l{index-1}_off', f'{repeat}_l{index+1}_off'
            if before not in arms or after not in arms:
                raise ValueError('ON arm lacks both OFF brackets')
            sample = {key:[(a+b)/2-c for a,b,c in zip(arms[before][key],arms[after][key],values[key])]
                      for key in deltas}
            for key in deltas:
                deltas[key].append(statistics.mean(sample[key]))
            paired.append(dict(repeat=repeat, gains_by_step=sample))
        if not paired:
            continue
        results[arm] = dict(wall=precision(deltas['wall_seconds']),
                            data=precision(deltas['data_seconds']),
                            host={key:precision(deltas[key]) for key in deltas if key not in ('wall_seconds','data_seconds')},
                            paired=paired, first_step_loss_bitwise=not any(m['arm'].endswith('_'+arm) for m in mismatches))
    off_equal = not any(m['arm'].endswith('_off') for m in mismatches)
    for arm, result in results.items():
        result['parity_valid'] = off_equal and result['first_step_loss_bitwise']
        if not result['parity_valid']:
            result['wall']['resolved'] = result['data']['resolved'] = False
            for value in result['host'].values():
                value['resolved'] = False
        print('SO_TIMING ' + json.dumps(dict(arm=arm, **result['wall'])), flush=True)
    results['_parity'] = dict(off_brackets_bitwise=off_equal, mismatches=mismatches,
                             switch_attribution_valid=off_equal)
    (root/'comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    if not off_equal:
        raise SystemExit('FAIL: OFF brackets loss differed; switch attribution is invalid; see comparison.json')
    if mismatches:
        raise SystemExit('FAIL: loss differed; see comparison.json; no tolerance was silently substituted')
    return results


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root')
    summarize(parser.parse_args().root)
