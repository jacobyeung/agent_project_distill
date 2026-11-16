"""Paired scene-stratified bootstrap, exact McNemar and Holm families."""
import argparse
import numpy as np
from scipy.stats import binomtest
from .io import read_json, write_json

def holm(pvalues):
    pvalues = np.asarray(pvalues, float)
    if np.any((pvalues < 0) | (pvalues > 1)):
        raise ValueError('Invalid p value')
    order = np.argsort(pvalues, kind='stable')
    out = np.zeros(len(pvalues))
    running = 0.
    for rank, i in enumerate(order):
        running = max(running, min(1., (len(pvalues)-rank)*pvalues[i]))
        out[i] = running
    return out.tolist()

def outcome(ci95, ci90, adjusted_p=None):
    gate = adjusted_p is None or adjusted_p < .05
    if gate and ci95[0] > 0:
        return 'GAIN'
    if gate and ci95[1] < 0:
        return 'HARM'
    if ci90[0] > -.03 and ci90[1] < .03:
        return 'EQUIVALENT'
    return 'INCONCLUSIVE'

def paired(a, b, scenes=None, seed=0, resamples=10000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.ndim != 1 or len(a) == 0 or not np.isfinite(a+b).all():
        raise ValueError('Need finite paired scores')
    if np.any(~np.isin(a, [0, 1])) or np.any(~np.isin(b, [0, 1])):
        raise ValueError('SR comparison needs binary outcomes')
    scenes = np.asarray(scenes if scenes is not None else ['all']*len(a))
    if scenes.shape != a.shape:
        raise ValueError('Scene shape mismatch')
    d, rng = a-b, np.random.RandomState(seed)
    samples = np.zeros(resamples)
    for scene in sorted(set(scenes)):
        values = d[scenes == scene]
        # Bounded batches avoid a resamples-by-full-dataset allocation.
        for start in range(0, resamples, 256):
            n = min(256, resamples-start)
            samples[start:start+n] += values[rng.randint(len(values), size=(n, len(values)))].sum(1)
    samples /= len(a)
    ci95, ci90 = np.quantile(samples, [.025, .975]).tolist(), np.quantile(samples, [.05, .95]).tolist()
    wins, losses = int(np.sum(d > 0)), int(np.sum(d < 0))
    p = float(binomtest(wins, wins+losses, .5).pvalue) if wins+losses else 1.
    return dict(n=len(a), delta=float(d.mean()), ci95=ci95, ci90=ci90,
                discordant=[wins, losses], mcnemar_p=p, outcome=outcome(ci95, ci90))

def family(comparisons):
    adjusted = holm([r['mcnemar_p'] for r in comparisons])
    return [dict(r, holm_p=p, outcome=outcome(r['ci95'], r['ci90'], p)) for r, p in zip(comparisons, adjusted)]

def compare_records(a, b, **kwargs):
    da, db = {r['episode_id']:r for r in a}, {r['episode_id']:r for r in b}
    if len(da) != len(a) or len(db) != len(b) or set(da) != set(db):
        raise ValueError('Comparison requires identical unique episode ids')
    ids = sorted(da)
    if any(da[k]['scene'] != db[k]['scene'] for k in ids):
        raise ValueError('Scene mismatch')
    return paired([da[k]['SR'] for k in ids], [db[k]['SR'] for k in ids], [da[k]['scene'] for k in ids], **kwargs)

def main():
    p = argparse.ArgumentParser();p.add_argument('a',nargs='?');p.add_argument('b',nargs='?');p.add_argument('--output')
    p.add_argument('--family',help='JSON list of {a: result_path, b: result_path, name: label}')
    args = p.parse_args()
    def records(path):
        data=read_json(path)
        return data['results'] if isinstance(data,dict) else data
    if args.family:
        specifications=read_json(args.family)
        result=family([dict(compare_records(records(c['a']),records(c['b'])),name=c['name']) for c in specifications])
    else:
        if not args.a or not args.b: p.error('provide two result files or --family')
        result = compare_records(records(args.a), records(args.b))
    if args.output: write_json(args.output, result)
    print(result)
if __name__ == '__main__': main()
