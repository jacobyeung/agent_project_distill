"""Shared, item-weighted room bootstrap for the serialized-capture audit."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import resource
resource.setrlimit(resource.RLIMIT_AS, (15 * 1024**3, 15 * 1024**3))
import hashlib
import json
import random
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
CAP = ROOT.parent/'cap'
OUT = CAP/'score_t1'
LABELS = ['S0','S1','S2','S3','S4','S5','no-GT','censored']

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def table(headers, rows):
    return '\n'.join(['| '+' | '.join(map(str,headers))+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'

def fmt(value):
    if value['mean'] is None:
        return 'undefined'
    return f"{value['mean']:.2f} [{value['ci95'][0]:.2f}, {value['ci95'][1]:.2f}]"

class Bootstrap:
    def __init__(self, refs):
        self.rooms = sorted({r['task']['room'] for r in refs.values()})
        self.lookup = {r:i for i,r in enumerate(self.rooms)}
        rng = random.Random(20261120)
        self.draws = np.zeros((10000,len(self.rooms)), dtype=np.int16)
        for row in self.draws:
            for _ in self.rooms:
                row[self.lookup[rng.choice(self.rooms)]] += 1

    def samples(self, rows, key):
        n = np.zeros(len(self.rooms)); total = n.copy()
        for r in rows:
            i=self.lookup[r['room']]; n[i]+=1; total[i]+=r[key]
        dn=self.draws@n
        values=np.divide(self.draws@total,dn,out=np.full(10000,np.nan),where=dn>0)
        return values, dn

    @staticmethod
    def summarize(mean, values):
        valid=values[np.isfinite(values)]
        return dict(mean=mean,ci95=np.percentile(valid,[2.5,97.5]).tolist() if len(valid) else None,
                    defined_draws=len(valid),undefined_draws=10000-len(valid))

    def metric(self, rows, key):
        values,_=self.samples(rows,key)
        return self.summarize(float(np.mean([r[key] for r in rows])) if rows else None,values)

    def contrast(self, a, b, key):
        av,_=self.samples(a,key);bv,_=self.samples(b,key)
        return self.summarize(float(np.mean([r[key] for r in a])-np.mean([r[key] for r in b])) if a and b else None,av-bv)

def inputs():
    refs={r['item_id']:r for r in read(ROOT/'kit2/kit/rerun2/items544.json')['items']}
    p=read(OUT/'SCORE_POINT_T1.json');d=read(OUT/'SCORE_DENSE_T1.json')
    dm={r['item_id']:r for r in d['rows']}
    rows=[]
    for r in p['rows']:
        q=dm[r['item_id']]
        assert r['baseline']==r['T1']==q['T1']==q['baseline']
        rows.append(dict(item_id=r['item_id'],capture=r['capture'],room=r['room'],
                         t1=r['T1'],points=r['points'],dense64=q['dense64']))
    assert len(rows)==150
    return refs, rows
