"""Aggregate paired predictions by summing room numerators and denominators."""
import hashlib
import json

import numpy as np
import selrefit2 as F


def bootstrap(records):
    rooms=sorted({r['room'] for r in records})
    totals=[]
    for room in rooms:
        recs=[r for r in records if r['room']==room]
        arms={a:[x for r in recs for x in r['arms'] if x['arm']==a] for a in ['S','V']}
        rows={a:[x for rec in arms[a] for x in rec['items']] for a in arms}
        choices={a:[x for rec in arms[a] for x in rec['choices']] for a in arms}
        assert len(rows['S'])==len(rows['V']) and len(choices['S'])==len(choices['V'])
        totals.append([len(rows['S']),len(choices['S']),
            sum(x['mra'] for x in rows['S']),sum(x['mra'] for x in rows['V']),
            sum(x['correct'] for x in choices['S']),sum(x['correct'] for x in choices['V']),
            sum(x['prediction'] is None for x in rows['S']),sum(x['prediction'] is None for x in rows['V'])])
    totals=np.asarray(totals,dtype=np.float64)
    rng=np.random.default_rng(20261119)
    draws=np.empty((10000,9))
    for start in range(0,10000,100):
        sample=rng.integers(0,len(rooms),size=(100,len(rooms)))
        summed=totals[sample].sum(axis=1)
        assert np.all(summed[:,:2]>0), 'A bootstrap draw has no eligible distance rows or choices.'
        for j,denom in enumerate([0,1,0]):
            s=summed[:,2+2*j]/summed[:,denom]
            v=summed[:,3+2*j]/summed[:,denom]
            draws[start:start+100,3*j:3*j+3]=np.column_stack([s,v,v-s])
    names=[f'{metric}_{arm}' for metric in ['gap_mra','choice_accuracy','refusal_rate'] for arm in ['S','V','V_minus_S']]
    return dict(unit='physical room',weighting='pooled rows for gap MRA and refusals; pooled objects for choice accuracy',
        draws=10000,seed=20261119,rooms=len(rooms),paired=True,
        rooms_without_distance_rows=int((totals[:,0]==0).sum()),
        rooms_without_choice_objects=int((totals[:,1]==0).sum()),
        zero_denominator_draws=0,
        ci95={name:np.quantile(draws[:,i],[.025,.975]).tolist() for i,name in enumerate(names)},
        bootstrap_sample_sha256=hashlib.sha256(draws.tobytes()).hexdigest())


if __name__=='__main__':
    F.bootstrap=bootstrap
    F.finalize()
    path=F.OUT/'SELREFIT2.json'
    result=json.loads(path.read_bytes())
    result['commands'][-1]='bash run.sh finalize2.py'
    data=json.loads((F.OUT/'TRAIN_DATA.json').read_bytes())
    result['training_table_coverage']={arm:dict(eligible_captures=len(data['common_captures']),
        candidate_bearing_captures=len({r['capture'] for r in rows}),
        empty_captures=sorted(set(data['common_captures'])-{r['capture'] for r in rows}),
        candidate_rows=len(rows),objects=len({r['object_id'] for r in rows}))
        for arm,rows in data['rows'].items()}
    path.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n')
    path=F.OUT/'REPORT.md'
    report=path.read_text().replace('bash run.sh selrefit2.py finalize','bash run.sh finalize2.py')
    report=report.replace('All secondary fold metrics, coefficients, input SHA-256 hashes, and per-row paired predictions accompany the JSON and archive.',
        'Choice accuracy covers candidate-bearing table objects; bootstrap sums retain rooms with zero distance rows. The JSON includes all fold metrics, coefficients, and input hashes.')
    counts=result['training_table_coverage']
    assert counts['S']['empty_captures']==counts['V']['empty_captures']
    report+=f'Table coverage (`bash run.sh finalize2.py`): {len(counts["S"]["empty_captures"])} shared tables are empty in both arms; {counts["S"]["candidate_bearing_captures"]} captures supply {counts["S"]["objects"]} training objects per arm. Empty tables supply no fit examples under the fixed recipe.\n'
    assert len(report.splitlines())<=40
    path.write_text(report)
