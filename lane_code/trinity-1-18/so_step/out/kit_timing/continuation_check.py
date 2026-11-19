"""Read-only continuation kill-rule check; nonzero exit means keep prefetch OFF."""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from replay_compare import pooled_loss_acceptance


def metrics(path):
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for record in records:
        if (len(record['ranks']) != 4 or any(r['rank'] != i or r['step'] != record['step']
                for i,r in enumerate(record['ranks']))):
            raise ValueError('Missing, reordered or inconsistent rank/step records')
    if any(b['step'] != a['step']+1 for a,b in zip(records,records[1:])):
        raise ValueError('Metrics must contain consecutive completed updates')
    return records


def median_slowest(records, key):
    values = [r[key] for record in records for r in record['ranks']]
    if len(records) != 20 or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Need 20 complete updates with finite nonnegative timers')
    return statistics.median(max(r[key] for r in record['ranks']) for record in records)


def check(replay_out, continuation, launch=None, first_only=False):
    off = [[json.loads((replay_out/arm/f'rank{r}'/'steps.json').read_text())[0]
            for r in range(4)] for arm in ('off1','off2')]
    current = metrics(continuation)
    if not current or any(r['step'] != current[0]['step'] for arm in off for r in arm):
        raise ValueError('First continuation update must match the OFF replay step')
    for rank,record in enumerate(current[0]['ranks']):
        expected = json.loads((replay_out/'on'/f'rank{rank}'/'manifest.json').read_text())['switches']
        if expected['C1_CPU_PREFETCH'] != '1' or any(record.get('performance',{}).get(k,'0') != v
                                                   for k,v in expected.items()):
            raise ValueError('Continuation switch provenance differs from ON replay')
    loss = pooled_loss_acceptance(*off,current[0]['ranks'],micro=False)
    report = dict(accepted=loss['accepted'], loss=loss, wall_pending=first_only,
                  scope='first-update losses' if first_only else 'loss and wall kill rules')
    if not first_only:
        if launch is None:
            raise ValueError('--launch is required for the wall rule')
        baseline = metrics(launch)[-20:]
        for key,label in (('wall_seconds','wall'),('data_seconds','data')):
            before,after = median_slowest(baseline,key),median_slowest(current[1:21],key)
            if label == 'wall' and before <= 0:
                raise ValueError('Launch timer median must be positive')
            report.update({label+'_launch_median':before,label+'_continuation_median':after,
                           label+'_ratio':after/before if before else None})
        report['accepted'] &= report['wall_ratio'] < 1.
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-out',type=Path,required=True)
    parser.add_argument('--continuation',type=Path,required=True)
    parser.add_argument('--launch',type=Path)
    parser.add_argument('--first-only',action='store_true',help='Check update 1 now; wall rule remains pending')
    args = parser.parse_args()
    result = check(**vars(args))
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'kit_profile'))
    from privacy import filter_streams
    filter_streams()
    raise SystemExit(main())
