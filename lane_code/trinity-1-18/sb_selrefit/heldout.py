"""One report-only held-out pass, admitted only by a frozen CV result."""
import collections, json, re, time
import selrefit as S
from selrefit import ROOT, OUT, R, SEL, ROWSETS, read, js, write, pin_code


def rebuild(c,producer):
    geo,cache,meta,_,_=R.geometry(c)
    gt,_=R.gt_arrays(c)
    stage=R.StageOne(R.cache_detect(cache),None,geo,rule='null_argmax')
    features={};inputs=[]
    for name in cache['phrases']:
        accepted,x=stage.features(name);features[name]=accepted
        inputs.extend(dict(object_id=c['canonical']+'::'+name,candidate_id=a['candidate_id'],name=name,x=v) for a,v in zip(accepted,x))
    rows,pairs=producer.label(c,features,R.F.Geometry(geo),gt)
    return dict(capture=c['canonical'],room=c['room'],split=c['k1_split'],rows=rows,inputs=inputs,geometry=meta)


def main():
    assert not (OUT/'HELDOUT.json').exists(),'Held-out was already printed; no repeated evaluation.'
    frozen=js(OUT/'CV_FROZEN.json');data=js(OUT/'TRAIN_DATA.json')
    ids=set(read(ROWSETS/'K1_HELDOUT_216.txt').decode().splitlines())
    allowed=set(read(ROWSETS/'K1_CAPTURES_HELDOUT_57.txt').decode().splitlines())
    manifest_path=next(iter(js(S.SOURCE/'train_manifest.json')['input_sha256']))
    manifest=js(manifest_path)
    # Preserve the manifest's membership and physical-room authority.
    caps=[c for c in manifest['captures'] if c['canonical'] in allowed]
    assert len(caps)==len(allowed)==57
    assert not (allowed & {c['canonical'] for c in data['captures']})
    assert not ({c['room'] for c in caps} & set(data['folds']))
    assert all(c['k1_split']=='heldout' for c in caps)
    label_path='/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl'
    labels={}
    for line in read(label_path).decode().splitlines():
        match=re.search(r'"id"\s*:\s*"([^"\\]+)"',line)
        if match and match[1] in ids:labels[match[1]]=json.loads(line)
    assert labels.keys()==ids
    registry=js('/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json')
    producer=R.producers(allowed)
    old,_=S.load_head(SEL/'work/run_iso');refit=S.custom_head('selector_head_refit')
    assert frozen['final_weights_sha256']==S.js(OUT/'selector_head_refit.json')['weights_sha256']
    dest=OUT/'heldout_captures';dest.mkdir(exist_ok=True);records=[]
    for i,c in enumerate(caps):
        p=dest/(c['canonical'].replace('/','__')+'.json')
        if p.exists():rec=js(p)
        else:
            c['gt']=registry[c['canonical']]
            tab=rebuild(c,producer)
            arms=list(S.evaluate_capture(c,tab,dict(old=old,refit=refit),labels,ids))
            pin_code();rec=dict(capture=c['canonical'],room=c['room'],arms=arms)
            write(p,rec)
        records.append(rec)
        print('HELDOUT_CAPTURE',i+1,len(caps),c['canonical'],flush=True)
    seen={r['row_id'] for rec in records for a in rec['arms'] for r in a['items']};assert seen==ids
    metrics={}
    for arm in ['old','refit']:
        rr=[r for rec in records for a in rec['arms'] if a['arm']==arm for r in a['items']]
        cc=[r for rec in records for a in rec['arms'] if a['arm']==arm for r in a['choices']]
        metrics[arm]=dict(distance_rows=len(rr),gap_mra=float(S.np.mean([r['mra'] for r in rr])),
            refused=sum(r['prediction'] is None for r in rr),objects=len(cc),choice_accuracy=float(S.np.mean([r['correct'] for r in cc])))
    pin_code();write(OUT/'HELDOUT.json',dict(metrics=metrics,captures=len(caps),rooms=len({c['room'] for c in caps}),
        frozen_cv_sha256=S.PINS[str(OUT/'CV_FROZEN.json')],report_only=True,completed_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    S.status('Cross-validation and final coefficients remain frozen. The single report-only held-out pass is complete. Final report and archive assembly are next.')
    print('HELDOUT_REPORT_ONLY',json.dumps(metrics),flush=True)


if __name__=='__main__':main()
