"""Paired erosion estimates with 90% scene-bootstrap CIs; no pass/fail rule."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evaluator'))
from common import save
from erosion_bind import TOOL, bounded_json
from score_pointing import indexed, read_records, score_rows


def paired_estimate(rows, macro=False, draws=10000, seed=17):
    import numpy as np
    if not rows:return dict(n=0,scenes=0,base=None,candidate=None,difference=None,ci90=None)
    scenes = sorted({r['scene'] for r in rows})
    types = sorted({r['question_type'] if macro else 'all' for r in rows})
    si,ti = {s:i for i,s in enumerate(scenes)},{t:i for i,t in enumerate(types)}
    counts = np.zeros((len(scenes),len(types)))
    sums = np.zeros((2,len(scenes),len(types)))
    for r in rows:
        i,j = si[r['scene']],ti[r['question_type'] if macro else 'all']
        counts[i,j] += 1
        sums[:,i,j] += [r['base'],r['candidate']]
    # Official VSI combines the three relative-direction levels into one task.
    rel = ['object_rel_direction_'+k for k in ('easy','medium','hard')]
    weights = np.ones(len(types))
    if macro and set(rel)<=set(types):
        for k in rel:weights[ti[k]] = 1/3
    weights /= weights.sum()
    means = (sums.sum(axis=1)/counts.sum(axis=0)) @ weights
    rng = np.random.default_rng(seed)
    boots = []
    rejected = 0
    # Retain every paired item and resample entire scenes, with multiplicity.
    for _ in range(100):
        if len(boots)>=draws:break
        n = min(1024,draws-len(boots))
        w = rng.multinomial(len(scenes),np.full(len(scenes),1/len(scenes)),size=n)
        den = w @ counts
        valid = np.all(den>0,axis=1)
        rejected += int((~valid).sum())
        den = den[valid];w = w[valid]
        if len(w):
            b,c = ((w@sums[k])/den @ weights for k in (0,1))
            boots.extend((c-b).tolist())
    if len(boots)<draws:raise ValueError('Too few scene-bootstrap draws cover every type')
    lo,hi = np.quantile(boots[:draws],[.05,.95])
    return dict(n=len(rows),scenes=len(scenes),base=float(means[0]),candidate=float(means[1]),
        difference=float(means[1]-means[0]),ci90=[float(lo),float(hi)],
        difference_pp=float(100*(means[1]-means[0])),ci90_pp=[float(100*lo),float(100*hi)],
        bootstrap=dict(unit='scene',confidence=.90,draws=draws,seed=seed,
                       rejected_missing_type=rejected),metric='official task macro' if macro else 'item mean')


def vsi_pairs(base, candidate, members):
    from scoring import score_item
    b,c = indexed(base,'vsi500_slice'),indexed(candidate,'vsi500_slice')
    expected = {str(r['example_id']):r for r in members['items']}
    if (set(b)|set(c))-set(expected):raise ValueError('Unexpected VSI IDs')
    missing = {k:sorted(set(expected)-{i for i,r in rs.items() if r.get('status')=='complete'})
               for k,rs in (('base',b),('candidate',c))}
    rows=[]
    for key in sorted(set(b)&set(c)):
        br,cr = b[key],c[key]
        if br.get('status')!='complete' or cr.get('status')!='complete':continue
        m = expected[key]
        for r in (br,cr):
            if (r['question_type'],r['dataset'],r['scene_name']) != (m['question_type'],m['dataset'],m['scene']):
                raise ValueError('VSI pair scene/type differs: '+key)
        if any(br.get(k)!=cr.get(k) for k in ('question','options','ground_truth','video_path')):
            raise ValueError('VSI paired task differs: '+key)
        scores = [score_item(r,r['raw_generation'],r.get('output_tokens',0))['score'] for r in (br,cr)]
        rows.append(dict(scene=m['dataset']+'/'+m['scene'],question_type=m['question_type'],base=scores[0],candidate=scores[1]))
    return dict(complete=not any(missing.values()),missing_or_failed=missing,
        overall=paired_estimate(rows,macro=True),item_mean=paired_estimate(rows),
        per_type={t:paired_estimate([r for r in rows if r['question_type']==t]) for t in sorted({r['question_type'] for r in rows})},
        diagnostics={name:dict(cap_hits=sum(bool(r.get('hit_token_cap')) for r in rs.values()),
                              parse_failures=sum(bool(r.get('parse_failed')) for r in rs.values()),
                              errors=sum(r.get('status')!='complete' for r in rs.values())) for name,rs in (('base',b),('candidate',c))})


def pointing_pairs(base,candidate):
    b,c = ({r['example_id']:r for r in result['items']} for result in (base,candidate))
    rows = []
    for key in sorted(set(b)&set(c)):
        br,cr = b[key],c[key]
        if (br['scene'],br['visible']) != (cr['scene'],cr['visible']):raise ValueError('Pointing pair GT differs')
        metric = 'inside' if br['visible'] else 'none_score'
        rows.append(dict(scene=br['scene'],visible=br['visible'],base=br[metric],candidate=cr[metric]))
    return dict(complete=base['complete'] and candidate['complete'],
                inside=paired_estimate([r for r in rows if r['visible']]),
                none=paired_estimate([r for r in rows if not r['visible']]),
                diagnostics={name:{k:v for k,v in r.items() if k!='items'} for name,r in (('base',base),('candidate',candidate))})


def embedded(pin, archive):
    name = pin['path'].removeprefix('$Q/')
    if pin['path'] != '$Q/'+name:raise ValueError('Require bound metadata pin')
    with tarfile.open(archive) as tf:
        m = tf.getmember(name)
        if not m.isfile() or m.size>8*1024*1024:raise ValueError('Bound metadata exceeds read limit')
        raw = tf.extractfile(m).read()
    if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Bound membership pin differs')
    return json.loads(raw)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,default=ROOT/'inputs/REQUEST.json')
    p.add_argument('--metadata',type=Path,default=ROOT/'kit/k/1.tar')
    p.add_argument('--runs',required=True,type=Path,help='Locally collected output root containing cell directories')
    p.add_argument('--attempt',required=True)
    p.add_argument('--gt-root',type=Path,default=TOOL/'gt/scannet')
    p.add_argument('--programs',type=Path,default=TOOL/'tp/programs.py')
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    cfg=bounded_json(a.request)
    payload={k:v for k,v in cfg.items() if k not in ('binding','output')}
    if hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()!=cfg['binding']:
        raise ValueError('Request binding hash differs')
    datasets={s['benchmark']:s for s in cfg['datasets']}
    if set(datasets)!={'vsi500_slice','pointing'} or cfg.get('smoke_items'):
        raise ValueError('Require full erosion request')
    point=embedded(datasets['pointing']['membership'],a.metadata)
    vsi=embedded(datasets['vsi500_slice']['slice_membership'],a.metadata)
    if point.get('review_only'):raise ValueError('Review bundle cannot produce erosion scores')
    if point['sources']['programs']!=hashlib.sha256(a.programs.read_bytes()).hexdigest():
        raise ValueError('GTGround source differs from bind')
    loaded={}
    for i,cell in enumerate(cfg['cells']):
        if cell['layout']!='spread':raise ValueError('Erosion requires spread cells')
        root=a.runs/str(i)
        summary=bounded_json(root/('summary_'+a.attempt+'.json'))
        from evalpath.items import digest
        identity=digest(dict(request=cfg['binding'],cell=i))
        if (summary['binding']!=identity or summary['model']!=cell['model'] or summary['layout']!='spread'
                or summary['attempt']!=a.attempt or summary.get('smoke_items')):
            raise ValueError('Run summary binding differs')
        rows=read_records(root/('items_'+a.attempt+'.jsonl'))
        if any(r['binding']!=identity for r in rows):raise ValueError('Item journal binding differs')
        loaded[cell['model']]=dict(summary=summary,rows=rows,
            point=score_rows(rows,point,a.gt_root,a.programs))
    base=loaded.pop('base')
    results={}
    for name,run in loaded.items():
        vs=vsi_pairs(base['rows'],run['rows'],vsi)
        pt=pointing_pairs(base['point'],run['point'])
        eligible=vs['complete'] and pt['complete'] and all(r['summary']['parity_pass'] for r in (base,run))
        results[name]=dict(numbers_status='eligible' if eligible else 'do not count',vsi500_slice=vs,pointing=pt)
    report=dict(binding=cfg['binding'],difference='candidate minus base',units='rates in [0,1]; pp fields in percentage points',
                decision='orchestrator applies erosion rule',
                model_pins=cfg.get('models',{}),
                membership_pins={k:{f:v for f,v in s.items() if f in ('membership','slice_membership')}
                                 for k,s in datasets.items()},
                pointing_none_convention='toolprog: no valid parsed points; malformed replies also counted as parse failures',
                candidates=results)
    save(a.output,report)
    lines=['Candidate | Measure | Base | Candidate | Difference (pp) | 90% CI (pp)',
           '--- | --- | ---: | ---: | ---: | ---']
    for name,result in results.items():
        values=[('VSI overall',result['vsi500_slice']['overall']),
                *[(t,r) for t,r in result['vsi500_slice']['per_type'].items()],
                ('point inside',result['pointing']['inside']),('point none',result['pointing']['none'])]
        for label,r in values:
            if r['n']:
                lines.append(f"{name} | {label} | {100*r['base']:.2f}% | {100*r['candidate']:.2f}% | {r['difference_pp']:+.2f} | [{r['ci90_pp'][0]:+.2f}, {r['ci90_pp'][1]:+.2f}]")
    lines.append('')
    for name,result in results.items():
        lines.append(f"{name}: {result['numbers_status']}; VSI cap/parse counts: {json.dumps(result['vsi500_slice']['diagnostics'])}; pointing cap/parse counts: "+json.dumps({k:{f:v[f] for f in ('cap_hits','parse_failures','missing_or_failed')} for k,v in result['pointing']['diagnostics'].items()})+'\n')
    a.output.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({name:r['numbers_status'] for name,r in results.items()}))


if __name__=='__main__':main()
