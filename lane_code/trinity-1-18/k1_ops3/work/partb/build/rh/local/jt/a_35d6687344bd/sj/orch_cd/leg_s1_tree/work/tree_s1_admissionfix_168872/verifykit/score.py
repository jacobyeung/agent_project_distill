"""Tune-only logistic calibration, held-out metrics, and candidate selections."""
import argparse
import json
import math
import re
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from .io import SPLIT, rows, dump, sha, digest, validate, write_rows
from .splits import partitions

FEATURES = ['logit_p_yes', 'logit_peak', 'presence', 'support', 'exclusivity_margin']
ARMS = ['sam3', 'score_presence', 'V1', 'V2', 'fusion']


def logit(p):
    p = np.clip(p, 1e-6, 1-1e-6)
    return np.log(p/(1-p))


def predictions(paths):
    v1, v2, bindings, stubs, checkpoints = {}, {}, set(), set(), set()
    for path in paths:
        for row in rows(path):
            bindings.add(row['binding']); stubs.add(bool(row.get('stub')))
            checkpoint = row.get('checkpoint_id', 'STUB' if row.get('stub') else None)
            if checkpoint is None: raise ValueError('Real prediction lacks checkpoint identity')
            checkpoints.add(checkpoint)
            oid = row['object_id']
            if row['form'] == 'V1':
                key = (oid, row['candidate_ids'][0])
                if key in v1 and v1[key] != row['p_yes']: raise ValueError('Conflicting V1 rows')
                v1[key] = float(row['p_yes'])
            elif row['form'] == 'V2':
                ps = row['probabilities'][:len(row['candidate_ids'])+1]
                norm = sum(ps)
                if norm <= 0: raise ValueError('V2 answer mass is zero')
                ps = [p/norm for p in ps]
                for i, cid in enumerate(row['candidate_ids']):
                    key = (oid, cid)
                    val = dict(prob=ps[i+1], chosen=(i+1 == int(np.argmax(ps))), null=ps[0])
                    if key in v2 and v2[key] != val: raise ValueError('Conflicting V2 rows')
                    v2[key] = val
    if len(stubs) > 1: raise ValueError('Cannot mix stub and real results')
    if len(checkpoints) > 1: raise ValueError('Cannot mix checkpoint identities')
    return v1, v2, dict(bindings=sorted(bindings), checkpoints=sorted(checkpoints), stub=bool(stubs and True in stubs))


def features(group, candidate, v1):
    p = v1[(group['object_id'], candidate['candidate_id'])]
    x = [logit(p), logit(candidate['peak']), candidate['presence'], candidate['support'], candidate['exclusivity_margin']]
    if not np.isfinite(x).all(): raise ValueError('Nonfinite fusion input')
    return x


def fit_logistic(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or len(x) == 0: raise ValueError('No tuning candidates')
    mean, std = x.mean(0), x.std(0)
    std[std < 1e-8] = 1
    z = np.column_stack([np.ones(len(x)), (x-mean)/std])
    def loss(w):
        a = z@w
        value = np.mean(np.logaddexp(0, a)-y*a)+.005*np.square(w[1:]).sum()
        grad = z.T@(expit(a)-y)/len(y)
        grad[1:] += .01*w[1:]
        return value, grad
    result = minimize(loss, np.zeros(z.shape[1]), jac=True, method='L-BFGS-B', options=dict(maxiter=1000, ftol=1e-12))
    if not result.success: raise ValueError('Calibration failed: '+result.message)
    return dict(mean=mean.tolist(), std=std.tolist(), weights=result.x.tolist(), l2=.01)


def apply_logistic(model, x):
    z = (np.asarray(x)-model['mean'])/model['std']
    return float(expit(model['weights'][0]+z@np.asarray(model['weights'][1:])))


def selections(groups, v1, v2, frozen):
    result = []
    for g in groups:
        scored = []
        for c in g['candidates']:
            key = (g['object_id'], c['candidate_id'])
            if key not in v1: raise ValueError(f'Missing V1 candidate {key}')
            x = features(g, c, v1)
            scored.append((c['candidate_id'], dict(sam3=c['peak'], V1=v1[key],
                V2=v2[key]['prob'] if key in v2 and v2[key]['chosen'] else -1.,
                score_presence=apply_logistic(frozen['score_presence'], x[1:3]),
                fusion=apply_logistic(frozen['fusion'], x))))
        for arm in ARMS:
            if arm == 'V2' and any((g['object_id'], c['candidate_id']) not in v2 for c in g['candidates']):
                if v2: raise ValueError('Incomplete V2 predictions for '+g['object_id'])
                continue
            eligible = [(cid, scores[arm]) for cid, scores in scored if scores[arm] >= 0]
            cid, confidence = max(eligible, key=lambda x:(x[1], x[0])) if eligible else (None, 0.)
            result.append(dict(object_id=g['object_id'], scene=g['scene'], arm=arm, candidate_id=cid,
                               confidence=float(confidence), oracle=bool(g.get('oracle'))))
    return result


def labels_for(path, scenes=None):
    """Filter by scene before parsing candidate labels."""
    out = {}
    with Path(path).open() as f:
        for line in f:
            match = re.search(r'"scene"\s*:\s*"([^"\\]+)"', line)
            if not match: raise ValueError('Labels require a plain scene key')
            if scenes is not None and match.group(1) not in scenes: continue
            row = json.loads(line)
            if row['object_id'] in out: raise ValueError('Duplicate labels')
            out[row['object_id']] = row
    return out


def correct(row, labels):
    label = labels[row['object_id']]
    return bool(row['candidate_id'] is not None and label['candidates'][row['candidate_id']]['on_target'])


def thresholds(selected, labels):
    cs = [x['confidence'] for x in selected if x['candidate_id'] is not None]
    result = {}
    for coverage in (.8, .9):
        # Thresholds are frozen using tuning scores; held-out coverage is measured, never forced.
        need = math.ceil(len(selected)*coverage)
        result[str(coverage)] = sorted(cs, reverse=True)[min(need, len(cs))-1] if cs else 1.000001
    best, tau = 0, 1.000001
    for t in sorted(set(cs), reverse=True):
        accepted = [x for x in selected if x['candidate_id'] is not None and x['confidence'] >= t]
        if sum(correct(x, labels) for x in accepted)/len(accepted) >= .93 and len(accepted) > best:
            best, tau = len(accepted), t
    result['precision93'] = tau
    return result


def fit(a):
    target = Path(a.out)
    if target.exists(): raise FileExistsError('Frozen calibration already exists; use a distinct file')
    tuning = set(json.loads(Path(a.split_file).read_text())['tuning_scenes'])
    all_groups = validate(rows(a.candidates))
    partition = partitions({g['scene'] for g in all_groups}, tuning)
    groups = [g for g in all_groups if g['scene'] in tuning]
    labels = labels_for(a.labels, tuning)
    v1, v2, predmeta = predictions(a.predictions)
    if not predmeta['stub'] and {g['scene'] for g in groups} != tuning:
        raise ValueError('Real calibration requires all 31 registered tuning scenes')
    x, y = [], []
    for g in groups:
        for c in g['candidates']:
            x.append(features(g, c, v1)); y.append(labels[g['object_id']]['candidates'][c['candidate_id']]['on_target'])
    if not x: raise ValueError('No tuning objects')
    frozen = dict(schema='verify-frozen-v1', features=FEATURES, tuning_scenes=sorted(tuning),
        partitions=partition,
        observed_tuning_scenes=sorted({g['scene'] for g in groups}),
        fusion=fit_logistic(x, y), score_presence=fit_logistic(np.asarray(x)[:,1:3], y),
        input_sha256={str(p):sha(p) for p in [a.candidates,a.labels,a.split_file,*a.predictions]},
        tuning_labels_sha256=digest(labels), predictions=predmeta,
        on_target=sorted({r.get('label_definition', 'Candidate on_target field from supplied scorer labels.') for r in labels.values()}),
        bootstrap=dict(samples=4000,seed=17,unit='scene'))
    selected = selections(groups,v1,v2,frozen)
    frozen['thresholds'] = {arm: thresholds([x for x in selected if x['arm']==arm],labels)
                            for arm in ARMS if any(x['arm']==arm for x in selected)}
    dump(target, frozen)
    return dict(tuning_objects=len(groups), tuning_candidates=len(x), frozen_sha256=sha(target), stub=predmeta['stub'])


def precision_at(selected, labels, threshold):
    accepted = [x for x in selected if x['candidate_id'] is not None and x['confidence'] >= threshold]
    return dict(threshold=threshold, n_accepted=len(accepted), coverage=len(accepted)/max(len(selected),1),
                precision=sum(correct(x,labels) for x in accepted)/len(accepted) if accepted else None)


def metrics(selected, labels, threshold):
    n = len(selected)
    absent = [r for r in selected if labels[r['object_id']]['absent']]
    present = [r for r in selected if not labels[r['object_id']]['absent']]
    null = lambda r: r['candidate_id'] is None or r['confidence'] < threshold['precision93']
    reliability = []
    for lo in np.linspace(0,.9,10):
        chunk = [x for x in selected if x['candidate_id'] is not None and lo <= x['confidence'] < lo+.1+ (1e-10 if lo>.89 else 0)]
        reliability.append(dict(lower=float(lo), n=len(chunk), mean_confidence=float(np.mean([x['confidence'] for x in chunk])) if chunk else None,
            accuracy=float(np.mean([correct(x,labels) for x in chunk])) if chunk else None))
    ranked = sorted([x for x in selected if x['candidate_id'] is not None],key=lambda x:(-x['confidence'],x['object_id']))
    exact = {}
    for cov in (.8,.9):
        take=ranked[:math.ceil(n*cov)]
        exact[str(cov)] = dict(coverage=len(take)/max(n,1), n_accepted=len(take),
            precision=sum(correct(x,labels) for x in take)/len(take) if take else None,
            diagnostic='Ranks use scores only; these are descriptive coverage points, not deployed thresholds.')
    secondary = {}
    for key in ('strict_on_target', 'representative_on_target'):
        if all(key in c for r in labels.values() for c in r['candidates'].values()):
            secondary[key] = sum(bool(r['candidate_id'] is not None and labels[r['object_id']]['candidates'][r['candidate_id']][key]) for r in selected)/max(n,1)
    return dict(n=n, on_target=sum(correct(x,labels) for x in selected)/max(n,1),
        **secondary, present_n=len(present),
        present_on_target=sum(correct(x,labels) for x in present)/len(present) if present else None,
        at_frozen_threshold={k:precision_at(selected,labels,t) for k,t in threshold.items()},
        at_ranked_coverage=exact, reliability=reliability, absent_n=len(absent),
        absent_null_rate=sum(null(x) for x in absent)/len(absent) if absent else None,
        explicit_null_rate=sum(x['candidate_id'] is None for x in absent)/len(absent) if absent else None)


def decision(on_target, baseline, routed=None):
    gain=on_target-baseline
    if routed is None: return dict(verdict='PENDING_ROUTED_READ', gain_points=100*gain)
    rule=routed['rule']; wins=rule['n_wins']
    complete=rule.get('complete') and routed.get('unpaired_routed',0)==0
    if not complete: verdict='INCOMPLETE'
    elif wins>=3: verdict='GO'
    elif gain<.03: verdict='NO-GO'
    elif .82<=on_target<=.88 and wins==2: verdict='Between'
    else: verdict='UNRESOLVED'
    return dict(verdict=verdict,wins=wins,gain_points=100*gain,
        rule='GO: >=3/4 CI-positive types; else NO-GO: <3 pp over score+presence; else Between: 82-88% and 2 wins.')


def evaluate(a):
    frozen=json.loads(Path(a.frozen).read_text()) # Must exist before held-out labels are read.
    tuning=set(frozen['tuning_scenes'])
    groups=validate(rows(a.candidates))
    partition=frozen['partitions']
    allowed={'tuning':tuning,'heldout':set(partition['legacy_read_scenes']),
             'legacy':set(partition['legacy_read_scenes']),'room':set(partition['room_disjoint_scenes'])}
    groups=[g for g in groups if a.split=='all' or g['scene'] in allowed[a.split]]
    if not groups: raise ValueError('No objects in requested evaluation split')
    labels=labels_for(a.labels,{g['scene'] for g in groups})
    v1,v2,predmeta=predictions(a.predictions)
    if predmeta['stub'] != frozen['predictions']['stub']: raise ValueError('Stub/real calibration mismatch')
    if predmeta['checkpoints'] != frozen['predictions']['checkpoints']: raise ValueError('Calibration checkpoint differs')
    # Permit a separate pointing oracle set; dev predictions must match frozen input files exactly.
    if not all(g.get('candidate_source')=='GT_INSTANCES_ORACLE' for g in groups):
        for path in [a.candidates,*a.predictions]:
            if frozen['input_sha256'].get(str(path))!=sha(path): raise ValueError('Frozen inference input differs: '+str(path))
    selected=selections(groups,v1,v2,frozen)
    summary={arm:metrics([x for x in selected if x['arm']==arm],labels,frozen['thresholds'][arm])
        for arm in ARMS if arm in frozen['thresholds'] and any(x['arm']==arm for x in selected)}
    for r in selected:
        r['threshold']=frozen['thresholds'][r['arm']]['precision93']
        r['accepted']=r['candidate_id'] is not None and r['confidence']>=r['threshold']
    report=dict(split=a.split, scenes=len({g['scene'] for g in groups}), objects=len(groups), arms=summary,
        frozen_sha256=sha(a.frozen), stub=predmeta['stub'], oracle=any(g.get('oracle') for g in groups),
        candidate_sources=sorted({g['candidate_source'] for g in groups}),
        inputs={str(p):sha(p) for p in [a.candidates,a.labels,*a.predictions]})
    routed=json.loads(Path(a.routed_report).read_text()) if a.routed_report else None
    if routed is not None and {r['scene'] for r in routed['item_scores']} != {g['scene'] for g in groups}:
        raise ValueError('Routed report scenes do not match the requested object split')
    report['decision']=decision(summary['fusion']['on_target'],summary['score_presence']['on_target'],routed)
    report['split_label']='ROOM_DISJOINT_DECISION' if a.split=='room' else 'DIAGNOSTIC' if a.split in ('heldout','legacy','all') else 'TUNING'
    if a.split != 'room':
        report['decision']['verdict']='DIAGNOSTIC_SPLIT'
    elif report['scenes'] != 33:
        report['decision']['verdict']='INCOMPLETE_33_ROOM_DISJOINT_SCENE_READ'
    if any(g['candidate_source'] != 'E1_LINKED_TOP_K' for g in groups):
        report['decision']['verdict']='PROVISIONAL_CANDIDATES'
    if report['stub'] or report['oracle']: report['decision']['verdict']='TEST_ONLY' if report['stub'] else 'ORACLE_ONLY'
    dump(a.out,report); write_rows(str(a.out)+'.selections.jsonl',selected)
    return report


def main():
    p=argparse.ArgumentParser(__doc__); sub=p.add_subparsers(dest='command',required=True)
    for name in ['fit','evaluate']:
        d=sub.add_parser(name); d.add_argument('--candidates',required=True);d.add_argument('--labels',required=True)
        d.add_argument('--predictions',required=True,nargs='+'); d.add_argument('--out',required=True)
        if name=='fit':d.add_argument('--split-file',default=str(SPLIT))
        else:
            d.add_argument('--frozen',required=True);d.add_argument('--split',choices=['room','legacy','heldout','tuning','all'],default='room');d.add_argument('--routed-report')
    a=p.parse_args();r=fit(a) if a.command=='fit' else evaluate(a)
    print(json.dumps(r if a.command=='fit' else {k:v for k,v in r.items() if k not in ('arms','inputs')}))

if __name__=='__main__':main()
