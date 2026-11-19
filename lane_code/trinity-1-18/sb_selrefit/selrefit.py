"""Frozen-recipe selector refit and paired serving-socket evaluation; CPU only."""
import collections, gzip, hashlib, io, json, random, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
SOURCE = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
SEL = Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector')
ROWSETS = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS')
sys.path[:0] = [str(SEL), str(SOURCE)]
import numpy as np
import torch
import train_selector as T
from selector_head import SelectorHead, load_head
from safetensors.torch import load_file, save_file
import serving_reference as R
from e2e_reader.grounding import StageOneSocket, ground_session
from math_v2 import mra

torch.set_num_threads(8)
torch.use_deterministic_algorithms(True)
PINS = R.PINS
SEED = 20261116


def read(p):
    return R.read(p)


def js(p):
    return json.loads(read(p))


def pin_code():
    for mod in list(sys.modules.values()):
        p = getattr(mod, '__file__', '') or ''
        if p.startswith('/scratch/jjyeung/') and p.endswith('.py') and '/envs/' not in p and '/uv-python/' not in p:
            read(p)
    read(ROOT/'run.sh'); read(OUT/'DECISION.md')


def write(p, d):
    p.write_text(json.dumps(R.clean(dict(d, input_sha256=dict(PINS))), indent=1, allow_nan=False)+'\n')


def status(s):
    (ROOT/'STATUS.md').write_text(s+'\n')


def table(p):
    d = json.loads(gzip.decompress(read(p)))
    return d


def joined(d):
    # The producer returns rows and inputs in different name orders. Join exact keys.
    inputs = {(v['object_id'], v['candidate_id']): v for v in d['inputs']}
    assert len(inputs) == len(d['inputs']) == len(d['rows'])
    return [dict(r, x=inputs[(r['object_id'], r['candidate_id'])]['x'],
                 capture=d['capture'], room=d['room']) for r in d['rows']]


def state(head):
    return {k:v.tolist() for k,v in head.state_dict().items()}


def save_head(head, stem, extra):
    p=OUT/(stem+'.safetensors')
    save_file({k:v.contiguous() for k,v in head.state_dict().items()}, str(p))
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    write(OUT/(stem+'.json'), dict(config=CFG, seed=SEED, weights_sha256=digest,
        weights_file=p.name, coefficients=state(head), **extra))
    return digest


def custom_head(stem):
    meta=js(OUT/(stem+'.json')); p=OUT/meta['weights_file']
    assert hashlib.sha256(read(p)).hexdigest()==meta['weights_sha256']
    h=SelectorHead(**{k:CFG[k] for k in ('hidden','name_mode','n_hash')})
    h.load_state_dict(load_file(str(p))); return h.eval()


@torch.no_grad()
def choose(head, rows):
    if not rows:return None
    x=torch.tensor([r['x'] for r in rows],dtype=torch.float64)
    k=int(head.with_null(x,None,rows[0]['name']).argmax())
    return None if k==len(rows) else rows[k]['candidate_id']


def grouped(rows):
    d=collections.defaultdict(list)
    for r in rows:d[r['object_id']].append(r)
    return d


def prepare():
    gate=js(SOURCE/'out/box_ladder/REFERENCE_REBUILD.json');assert gate['status']=='PASS'
    manifest=js(SOURCE/'train_manifest.json')
    allowed=set(read(ROWSETS/'K1_CAPTURES_TRAIN_239.txt').decode().splitlines())
    caps=[c for c in manifest['captures'] if c['canonical'] in allowed]
    assert len(caps)==len(allowed)==239 and all(c['k1_split']=='train' for c in caps)
    assert {c['capture'] for c in gate['captures']}==allowed
    rooms=sorted({c['room'] for c in caps});random.Random(SEED).shuffle(rooms)
    folds={room:i%5 for i,room in enumerate(rooms)}
    allrows=[];changes=[];counts=collections.Counter();choices=[];coverage=[]
    oldhead,_=load_head(SEL/'work/run_iso')
    for entry in sorted(gate['captures'],key=lambda c:c['capture']):
        d=table(Path(entry['path']));assert PINS[entry['path']]==entry['sha256']
        allrows+=joined(d)
        oldpath=SEL/'data/caps_iso'/Path(entry['path']).name
        coverage.append(dict(capture=d['capture'],serving_candidates=len(d['rows']),old_table_available=oldpath.exists()))
        if not oldpath.exists():
            counts['old_tables_missing']+=1
            changes.append(dict(capture=d['capture'],status='MISSING',expected=str(oldpath)))
            continue
        counts['compared_captures']+=1
        old=table(oldpath)
        old['room']=d['room']; og=grouped(joined(old));ng=grouped(joined(d))
        a={(r['object_id'],r['candidate_id']):r for r in old['rows']}
        b={(r['object_id'],r['candidate_id']):r for r in d['rows']}
        for key in sorted(a.keys()|b.keys()):
            x,y=a.get(key),b.get(key)
            if x is None or y is None:
                kind='serving_added' if x is None else 's4_removed';counts[kind]+=1
                changes.append(dict(capture=d['capture'],object_id=key[0],candidate_id=key[1],kind=kind,
                    old_y=None if x is None else x['y'],serving_y=None if y is None else y['y']))
                continue
            counts['common_id_rows']+=1
            same=x['members']==y['members'];counts['same_member_annotations' if same else 'changed_member_annotations']+=1
            if x['y']!=y['y']:
                counts['label_flips_at_common_ids']+=1
                changes.append(dict(capture=d['capture'],object_id=key[0],candidate_id=key[1],kind='label_flip_at_common_id',
                    old_y=x['y'],serving_y=y['y'],same_member_annotations=same,old_members=x['members'],serving_members=y['members']))
        for oid in sorted(og.keys()&ng.keys()):
            op,npick=choose(oldhead,og[oid]),choose(oldhead,ng[oid])
            oa=any(r['y'] for r in og[oid]);na=any(r['y'] for r in ng[oid])
            counts['common_objects']+=1;counts['null_target_flips']+=int(oa!=na)
            counts['old_model_choice_id_changes']+=int(op!=npick)
            if op!=npick or oa!=na:
                choices.append(dict(object_id=oid,old_choice=op,serving_choice=npick,old_has_positive=oa,serving_has_positive=na))
    pin_code()
    write(OUT/'TRAIN_DATA.json',dict(rows=allrows,captures=caps,folds=folds,seed=SEED,
        label_change_counts=dict(counts),label_change_list=changes,choice_changes=choices,coverage=coverage,
        missing_registered_gt=gate['missing'],reference_summary=gate['summary'],
        label_comparison='Common-ID label flips are table-cell differences, not identity-preserving relabels; IDs and membership may change with geometry. All serving labels are rebuilt from GT, never transferred.'))
    status(f'Preparation complete: {len(caps)} captures, {len(allrows)} serving candidate rows, {len(rooms)} physical rooms. Labels and input hashes are recorded in out/TRAIN_DATA.json. Cross-validation has not run.')
    print(json.dumps(dict(captures=len(caps),rows=len(allrows),rooms=len(rooms),labels=dict(counts))),flush=True)


def train():
    d=js(OUT/'TRAIN_DATA.json');gs=T.groups(d['rows'],{})
    summaries=[]
    for k in range(5):
        tr=[g for g in gs if d['folds'][g['room']]!=k];te=[g for g in gs if d['folds'][g['room']]==k]
        h=T.fit(tr,CFG,seed=SEED)
        pin_code();sha=save_head(h,f'fold_{k}',dict(fold=k,training_objects=len(tr),validation_objects=len(te)))
        summaries.append(dict(fold=k,sha256=sha,training_objects=len(tr),validation_objects=len(te)))
        status(f'Cross-validation fitting: {k+1}/5 fold models complete. The recipe is unchanged; held-out has not been opened.')
        print('FOLD_FIT',k,len(tr),len(te),sha,flush=True)
    h=T.fit(gs,CFG,seed=SEED);sha=save_head(h,'selector_head_refit',dict(training_objects=len(gs),training_captures=len(d['captures']),
        training_objective='sum candidate BCE plus null BCE, divided by candidate+null count per batch of 16 objects',
        optimizer='AdamW',config_source=str(SEL/'work/run_iso/selector_head.json'),
        fit_source=str(SEL/'train_selector.py'),selection_rule='Fixed recorded config; no hyperparameter search'))
    write(OUT/'FIT.json',dict(folds=summaries,final_weights_sha256=sha,objects=len(gs),config=CFG))
    status('All five fold models and the final all-training refit are saved. Paired serving-socket scoring is next; held-out remains unopened.')
    print('FINAL_FIT',sha,flush=True)


def evaluate_capture(c, tab, heads, labels, ids):
    geo,cache,meta,_,_=R.geometry(c)
    stage=R.StageOne(R.cache_detect(cache),None,geo,rule='null_argmax')
    rows=joined(tab);by=grouped(rows);features={};checks=[];metrics=[]
    names=sorted({n for r in c['rows'] if r['id'] in ids for n in r['operands']})
    for name in names:
        accepted,x=stage.features(name);features[name]=(accepted,x)
        expected={r['candidate_id']:r['x'] for r in by.get(c['canonical']+'::'+name,[])}
        actual={a['candidate_id']:v for a,v in zip(accepted,x)}
        assert expected.keys()==actual.keys(),(c['canonical'],name,'candidate set')
        assert all(np.array_equal(expected[k],actual[k]) for k in actual),(c['canonical'],name,'features')
        checks.append(dict(name=name,exact_serving_features=True,candidates=len(x)))
    for arm,head in heads.items():
        selected={}
        for oid,rs in by.items():
            cid=choose(head,rs);selected[rs[0]['name']]=cid
            correct=(not any(r['y'] for r in rs)) if cid is None else bool(next(r['y'] for r in rs if r['candidate_id']==cid))
            metrics.append(dict(arm=arm,object_id=oid,choice=cid,correct=correct))
        def propose(name):
            accepted,x=features[name]
            return [dict(candidate_id=a['candidate_id'],masks=a['masks']) for a in accepted],dict(name=name)
        def select(inputs):
            name=inputs['name'];cid=selected.get(name)
            return next((i for i,a in enumerate(features[name][0]) if a['candidate_id']==cid),-1)
        socket=StageOneSocket(propose,select,R.F.OUTPUT_SHAPE,32)
        predictions=[]
        for row in c['rows']:
            if row['id'] not in ids:continue
            assert row['type']=='object_abs_distance'
            session=ground_session(geo,socket)
            responses=[]
            for name in row['operands']:responses.append(session.execute(f'<ground obj="{name}" mode="box">'))
            a,b=row['operands'];response=session.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
            match=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',response)
            pred=float(match[1]) if match else None
            target=labels[row['id']]['corrected']
            predictions.append(dict(arm=arm,row_id=row['id'],capture=c['canonical'],room=c['room'],dataset=c['canonical'].split('/')[0],
                prediction=pred,label=target,mra=mra(pred,target),printed=response,ground_responses=responses,
                choices={n:selected.get(n) for n in row['operands']}))
        yield dict(arm=arm,items=predictions,choices=[m for m in metrics if m['arm']==arm],checks=checks,geometry=meta)


def aggregate(records,folds):
    out=[]
    for k in range(5):
        rows=[r for rec in records if folds[rec['room']]==k for a in rec['arms'] for r in a['items']]
        choices=[r for rec in records if folds[rec['room']]==k for a in rec['arms'] for r in a['choices']]
        result=dict(fold=k,captures=sum(folds[r['room']]==k for r in records),rooms=len({r['room'] for r in records if folds[r['room']]==k}),
            datasets=dict(collections.Counter(r['capture'].split('/')[0] for r in records if folds[r['room']]==k)))
        for arm in ['old','refit']:
            rr=[r for r in rows if r['arm']==arm];cc=[r for r in choices if r['arm']==arm]
            result[arm]=dict(distance_rows=len(rr),gap_mra=float(np.mean([r['mra'] for r in rr])),
                refused=sum(r['prediction'] is None for r in rr),objects=len(cc),choice_accuracy=float(np.mean([r['correct'] for r in cc])))
        assert result['old']['distance_rows']==result['refit']['distance_rows']
        result['paired_gain']=result['refit']['gap_mra']-result['old']['gap_mra']
        result['choice_gain']=result['refit']['choice_accuracy']-result['old']['choice_accuracy']
        out.append(result)
    return out


def score():
    d=js(OUT/'TRAIN_DATA.json');fit=js(OUT/'FIT.json')
    ids=set(read(ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    labels={r['id']:r for r in js(SOURCE/'train_labels.json')['rows']}
    old,_=load_head(SEL/'work/run_iso');heads=[custom_head(f'fold_{k}') for k in range(5)]
    records=[];dest=OUT/'cv_captures';dest.mkdir(exist_ok=True)
    for i,c in enumerate(d['captures']):
        p=dest/(c['canonical'].replace('/','__')+'.json')
        if p.exists():
            rec=js(p);assert rec['code_sha256']==hashlib.sha256((ROOT/'selrefit.py').read_bytes()).hexdigest()
        else:
            tab=table(R.TABLES/(c['canonical'].replace('/','__')+'.json.gz'))
            arms=list(evaluate_capture(c,tab,dict(old=old,refit=heads[d['folds'][c['room']]]),labels,ids))
            pin_code();rec=dict(capture=c['canonical'],room=c['room'],arms=arms,code_sha256=PINS[str(ROOT/'selrefit.py')])
            write(p,rec)
        records.append(rec)
        print('CV_CAPTURE',i+1,len(d['captures']),c['canonical'],flush=True)
    seen={r['row_id'] for rec in records for a in rec['arms'] for r in a['items']};assert seen==ids
    folds=aggregate(records,d['folds']);gain=float(np.mean([f['paired_gain'] for f in folds]));sd=float(np.std([f['paired_gain'] for f in folds],ddof=1))
    pin_code();write(OUT/'CV_FROZEN.json',dict(folds=folds,mean_paired_gain=gain,paired_gain_sd=sd,spread_2sd=2*sd,refit_wins=gain>2*sd,
        final_weights_sha256=fit['final_weights_sha256'],distance_rows=len(ids),frozen_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        rule=(OUT/'DECISION.md').read_text().splitlines()[0],coefficients_old=state(old),coefficients_refit=state(custom_head('selector_head_refit'))))
    status(f'Cross-validation is frozen: mean paired gap-MRA gain {gain:.6f}; 2 x sample SD {2*sd:.6f}; refit wins = {gain>2*sd}. Final coefficients are frozen. Held-out report-only evaluation may now run.')
    print('CV_FROZEN',json.dumps(dict(folds=folds,mean_paired_gain=gain,spread_2sd=2*sd,refit_wins=gain>2*sd)),flush=True)


META=js(SEL/'work/run_iso/selector_head.json')
read(SEL/'work/run_iso/selector_head.safetensors')
assert PINS[str(SEL/'work/run_iso/selector_head.safetensors')]==META['weights_sha256']
CFG=META['config']
if __name__=='__main__':
    {'prepare':prepare,'train':train,'score':score}[sys.argv[1]]()
