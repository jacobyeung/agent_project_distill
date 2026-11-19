import argparse
import json
import math
from pathlib import Path
import statistics


def summarize(root):
    root = Path(root)
    baseline = [json.loads((root/'off'/f'rank{r}'/'steps.json').read_text()) for r in range(4)]
    print('arm\tsteps\tmedian_wall_all_s\tmedian_wall_2_to_10_s\tmedian_data_maxrank_s\tfirst_step_loss_bitwise')
    results = {}
    for arm in ('off','prefetch','cache','metrics'):
        runs = [json.loads((root/arm/f'rank{r}'/'steps.json').read_text()) for r in range(4)]
        if any(len(run) != 10 for run in runs):
            raise ValueError('Every timing arm must complete exactly ten optimizer steps')
        parity = True
        maximum_error = 0.
        for rank,(base,trial) in enumerate(zip(baseline,runs)):
            if [r['plan_sha256'] for r in trial] != [r['plan_sha256'] for r in base]:
                raise ValueError('Row plan mismatch')
            bm = json.loads((root/'off'/f'rank{rank}'/'manifest.json').read_text())
            tm = json.loads((root/arm/f'rank{rank}'/'manifest.json').read_text())
            for key in ('trainables','config_sha256','start_step','resume','binding'):
                if bm[key] != tm[key]:
                    raise ValueError('Manifest parity failed: '+key)
            expected,actual = base[0]['first_step_micro_losses'],trial[0]['first_step_micro_losses']
            if not expected or len(expected) != len(actual):
                raise ValueError('Loss count is empty or differs')
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in expected+actual):
                raise ValueError('Loss parity requires finite scalar losses')
            parity &= expected == actual
            maximum_error = max([maximum_error]+[abs(a-b) for a,b in zip(actual,expected)])
        wall = [max(r[i]['wall_seconds'] for r in runs) for i in range(10)]
        data = [max(r[i]['data_seconds'] for r in runs) for i in range(10)]
        result = dict(median_wall_all=statistics.median(wall),median_wall_2_to_10=statistics.median(wall[1:]),
                      median_data=statistics.median(data),loss_bitwise=parity,max_abs_loss_error=maximum_error,
                      wall_each=wall,data_each=data)
        results[arm] = result
        print(f"{arm}\t10\t{result['median_wall_all']:.6f}\t{result['median_wall_2_to_10']:.6f}\t{result['median_data']:.6f}\t{parity}")
    (root/'comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    if not all(v['loss_bitwise'] for v in results.values()):
        raise SystemExit('FAIL: loss differed; no tolerance was silently substituted')
    return results


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root')
    summarize(parser.parse_args().root)
