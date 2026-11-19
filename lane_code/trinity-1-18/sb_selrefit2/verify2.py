"""Validate the paired experiment using saved inputs, coefficients, and predictions."""
import collections
import gzip
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
PINS={}
sys.path.insert(0,str(ROOT/'inputs/code'))
from selector_head import SelectorHead


def read(path):
    path=Path(path)
    assert path.resolve().is_relative_to('/scratch')
    data=path.read_bytes()
    PINS[str(path)]=hashlib.sha256(data).hexdigest()
    return data


def js(path):
    return json.loads(read(path))


def main():
    torch.set_num_threads(8)
    d=js(OUT/'TRAIN_DATA.json'); s=js(OUT/'SELREFIT2.json')
    pins={}
    outputs=[OUT/'TRAIN_DATA.json',OUT/'FIT.json',OUT/'SCORE_COMPLETE.json',OUT/'SELREFIT2.json']
    outputs += [OUT/f'{a}_fold_{k}.json' for a in ['S','V'] for k in range(5)]
    outputs += [OUT/'cv_captures'/(c['canonical'].replace('/','__')+'.json') for c in d['captures']]
    for path in outputs:
        rec=js(path)
        assert 'input_sha256' in rec
        for name,sha in rec['input_sha256'].items():
            assert 'heldout' not in name.lower(),name
            assert name not in pins or pins[name]==sha,('input_changed',name)
            pins[name]=sha
    for name,sha in sorted(pins.items()):
        path=Path(name)
        assert path.resolve().is_relative_to('/scratch'),name
        with path.open('rb') as f:
            actual=hashlib.file_digest(f,'sha256').hexdigest()
        assert actual==sha,('hash_mismatch',name)
    bycap={c['canonical']:c for c in d['captures']}
    assert all(c['k1_split']=='train' for c in bycap.values())
    for rows in d['rows'].values():
        assert all(r['capture'] in d['common_captures'] and r['scene']==r['capture']
                   and r['object_id'].startswith(r['capture']+'::')
                   and r['room']==bycap[r['capture']]['room'] for r in rows)
    heads={}
    for arm in ['S','V']:
        for k in range(5):
            meta=js(OUT/f'{arm}_fold_{k}.json')
            weights=OUT/meta['weights_file']
            assert hashlib.sha256(read(weights)).hexdigest()==meta['weights_sha256']
            sd=load_file(str(weights))
            head=SelectorHead(hidden=32,name_mode='none',n_hash=4096)
            head.load_state_dict(sd);heads[arm,k]=head.eval()
            rows=[r for r in d['rows'][arm] if d['folds'][r['room']]!=k]
            # Match group sorting, while deriving the training membership independently.
            rows=sorted(rows,key=lambda r:r['object_id'])
            x=torch.tensor([r['x'] for r in rows],dtype=torch.float64)
            std=x.std(0);std=torch.where(std>1e-12,std,torch.ones_like(std))
            assert torch.equal(x.mean(0),sd['feat_mean'])
            assert torch.equal(std,sd['feat_std'])
            caps={r['capture'] for r in rows};rooms={r['room'] for r in rows}
            eligible={cap for cap in d['common_captures'] if d['folds'][bycap[cap]['room']]!=k}
            assert caps<=eligible and eligible==set(meta['training_captures'])
            assert not any(r['capture'] in eligible-caps for r in d['rows'][arm])
            assert rooms==set(meta['training_rooms'])
            assert not rooms & set(meta['validation_rooms'])
            assert all(d['folds'][r]!=k for r in rooms)
            assert all(torch.equal(sd[key],torch.tensor(value,dtype=sd[key].dtype)) for key,value in meta['coefficients'].items())
    labels={r['id']:r['corrected'] for r in js(ROOT/'inputs/train_labels.json')['rows']}
    ids=set(read(ROOT/'inputs/K1_TRAIN_1037.txt').decode().splitlines())
    seen=set(); recs=[]
    for cap,c in bycap.items():
        rec=js(OUT/'cv_captures'/(cap.replace('/','__')+'.json')); recs.append(rec)
        assert rec['fold']==d['folds'][c['room']]
        assert rec['in_primary']==(cap in d['common_captures'])
        a,b=rec['arms']; assert [a['arm'],b['arm']]==['S','V']
        assert a['geometry']==b['geometry']
        aa={r['row_id']:r for r in a['items']};bb={r['row_id']:r for r in b['items']}
        assert aa.keys()==bb.keys() and not seen & aa.keys();seen.update(aa)
        assert {r['object_id'] for r in a['choices']}=={r['object_id'] for r in b['choices']}
        tab=json.loads(gzip.decompress(read(ROOT/'inputs/tables/V'/(cap.replace('/','__')+'.json.gz'))))
        vectors={(r['object_id'],r['candidate_id']):r['x'] for r in tab['inputs']}
        groups=collections.defaultdict(list)
        for r in tab['rows']:groups[r['object_id']].append(r)
        for arm in [a,b]:
            assert all(x['exact_serving_features'] for x in arm['checks'])
            assert {x['object_id'] for x in arm['choices']}==set(groups)
            for choice in arm['choices']:
                rows=groups[choice['object_id']]
                x=torch.tensor([vectors[r['object_id'],r['candidate_id']] for r in rows],dtype=torch.float64)
                with torch.no_grad():
                    selected=int(heads[arm['arm'],rec['fold']].with_null(x,None,rows[0]['name']).argmax())
                cid=None if selected==len(rows) else rows[selected]['candidate_id']
                correct=not any(r['y'] for r in rows) if cid is None else bool(rows[selected]['y'])
                assert choice['choice']==cid and choice['correct']==correct
            for row in arm['items']:
                assert row['room']==c['room'] and row['label']==labels[row['row_id']]
                match=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',row['printed'])
                assert row['prediction']==(float(match[1]) if match else None)
                pred=row['prediction'];gt=row['label']
                expected=0. if pred is None else float(np.mean([abs(pred-gt)/abs(gt)<1-t for t in np.arange(.5,.96,.05)]))
                assert row['mra']==expected
    assert seen==ids and len(seen)==1037 and len(recs)==239
    for name,subset in [('primary',[r for r in recs if r['in_primary']]),('all_training',recs),
                        ('missing_s4_g1_only',[r for r in recs if not r['in_primary']])]:
        result=s['results'][name];gains=[]
        for k in range(5):
            fold=[r for r in subset if r['fold']==k]
            paired=[v['mra']-u['mra'] for r in fold for u,v in zip(r['arms'][0]['items'],r['arms'][1]['items'])]
            gains.append(statistics.mean(paired))
            assert math.isclose(gains[-1],result['folds'][k]['paired_gap_mra_gain'],abs_tol=1e-12)
        assert math.isclose(statistics.mean(gains),result['mean_paired_gap_mra_gain'],abs_tol=1e-12)
        assert math.isclose(2*statistics.stdev(gains),result['spread_2sd'],abs_tol=1e-12)
        for ai,arm in enumerate(['S','V']):
            rows=[x for r in subset for x in r['arms'][ai]['items']]
            choices=[x for r in subset for x in r['arms'][ai]['choices']]
            m=result['pooled'][arm]
            assert m['distance_rows']==len(rows) and m['objects']==len(choices)
            assert m['refused']==sum(x['prediction'] is None for x in rows)
            assert math.isclose(m['gap_mra'],statistics.mean(x['mra'] for x in rows),abs_tol=1e-12)
            assert math.isclose(m['choice_accuracy'],statistics.mean(x['correct'] for x in choices),abs_tol=1e-12)
    p=s['results']['primary']
    # Independently reproduce the paired bootstrap with room multiplicities.
    subset=[r for r in recs if r['in_primary']]
    rooms=sorted({r['room'] for r in subset});sums=[];counts=[]
    for room in rooms:
        rr=[r for r in subset if r['room']==room]
        sa=[x['mra'] for r in rr for x in r['arms'][0]['items']]
        va=[x['mra'] for r in rr for x in r['arms'][1]['items']]
        sums.append([sum(sa),sum(va)]);counts.append(len(sa))
    sums=np.asarray(sums);counts=np.asarray(counts)
    rng=np.random.default_rng(20261119);draws=[]
    for _ in range(10000):
        weights=np.bincount(rng.integers(0,len(rooms),len(rooms)),minlength=len(rooms))
        means=(weights@sums)/(weights@counts)
        draws.append(means[1]-means[0])
    assert np.allclose(np.quantile(draws,[.025,.975]),p['bootstrap']['ci95']['gap_mra_V_minus_S'],rtol=0,atol=1e-12)
    assert s['serving_labels_win']==(p['mean_paired_gap_mra_gain']>p['spread_2sd'])
    assert (OUT/'READ_REQUEST.md').exists()==s['serving_labels_win']
    assert len(d['missing_s4_g1'])==24 and len(d['common_captures'])==215
    assert all(x['status']=='MISSING' and not Path(x['expected']).exists() for x in d['missing_s4_g1'])
    assert len(read(OUT/'REPORT.md').decode().splitlines())<=40
    read(ROOT/'verify2.py');read(ROOT/'run.sh')
    result=dict(status='PASS',output_jsons_checked=len(outputs),unique_inputs_checked=len(pins),
        captures=len(recs),distance_rows=len(seen),room_separation=True,fold_normalization=True,
        paired_coverage=True,printed_distance_scoring=True,all_input_hashes_match=True,
        coefficient_argmax_and_choice_correctness=True,independent_primary_bootstrap=True,
        input_sha256=PINS)
    (OUT/'VALIDATION.json').write_text(json.dumps(result,indent=1)+'\n')
    (ROOT/'STATUS.md').write_text('Validation passed: fold training rooms are disjoint from validation rooms; normalization uses only fold training rows; all input hashes, coefficients, paired row coverage, printed-distance scores, and reported aggregates match. The archive is next. No held-out data has been read.\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}),flush=True)


if __name__=='__main__':
    main()
