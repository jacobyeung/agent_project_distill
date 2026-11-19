"""Score D returns and paired room-bootstrap differences; Python 3.6 syntax."""
import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

SETS = ('R0-dev-reworded', 'R0-dev-twin')
SCORERS_SHA = '2736e479888481cda4c1682f2db3d8b54f0b6d5957d8a4603d86469dc2b493fd'


def read(path): return json.loads(Path(path).read_text())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bootstrap(pairs):
    groups = defaultdict(list)
    for room,value in pairs: groups[room].append(float(value))
    if not groups: return dict(value=None, ci95=None, n=0, rooms=0)
    grouped = [(sum(groups[k]), len(groups[k])) for k in sorted(groups)]
    rng = random.Random(17); samples = []
    for _ in range(10000):
        draw = rng.choices(grouped, k=len(grouped))
        samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    samples.sort()
    def quantile(q):
        index=(len(samples)-1)*q; lo=int(index); hi=min(lo+1,len(samples)-1)
        return samples[lo]+(samples[hi]-samples[lo])*(index-lo)
    return dict(value=sum(s for s,n in grouped)/sum(n for s,n in grouped),
                ci95=[quantile(.025),quantile(.975)], n=sum(n for s,n in grouped), rooms=len(grouped))


def load(root, manifest, items_path):
    root=Path(root); items={r['id']:r for r in manifest['items']}; rows={}; sources=[]; shared=None; seen=set()
    journal=root/'metadata/reads/0/metadata/journals'
    for started in journal.glob('*/*/STARTED.json'):
        if not (started.parent/'items.jsonl').is_file(): raise ValueError('Started segment lacks journal')
    paths=sorted(journal.glob('*/*/items.jsonl'))
    if not paths: raise ValueError('No journals')
    for path in paths:
        env=read(path.parent/'environment.json'); b=env['binding']
        expected=dict(arms=['tower'],modes=[{'name':'none'}],lineage='SFT',fixture=False,
                      stage1_select_rule='candidates_argmax',perception_memo='on',
                      perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,
                      items_sha256=digest(items_path),item_set_sha256=manifest['item_set_sha256'])
        for k,v in expected.items():
            if b.get(k)!=v: raise ValueError('Journal binding differs: '+k)
        if b['settings_sha256']!=canonical(env['settings']): raise ValueError('Settings hash differs')
        for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):
            if env['settings'].get(k)!=expected[k]: raise ValueError('Settings differ: '+k)
        if env['settings'].get('types')!=['object_abs_distance']: raise ValueError('Settings type differs')
        current={k:b[k] for k in ('step','export_sha256','settings_sha256','artifact_manifest_sha256',
                                  'reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256')}
        if shared is not None and shared!=current: raise ValueError('Mixed journals')
        shared=current; text=path.read_text()
        if text and not text.endswith('\n'): raise ValueError('Uncommitted journal tail')
        for line in text.splitlines():
            r=json.loads(line); k=r['id']
            if k in seen or k not in items: raise ValueError('Duplicate or unplanned item: '+k)
            seen.add(k)
            if r.get('arm')!='tower' or r.get('mode')!='none' or r.get('type')!='object_abs_distance':
                raise ValueError('Wrong arm/mode/type')
            if r['room_key']!=items[k]['room_key']: raise ValueError('Room differs')
            if r.get('complete') is not True: continue
            for metric in ('answer','released_answer'):
                score=r['output'].get('scores',{}).get(metric)
                if score is None and metric=='released_answer':continue
                if isinstance(score,bool) or not isinstance(score,(float,int)) or not math.isfinite(score) or not 0<=score<=1:
                    raise ValueError('Invalid sealed score: '+metric)
            rows[k]=r
        sources.append(dict(path=str(path),sha256=digest(path)))
    return rows, dict(step=shared['step'],binding=shared,sources=sources)


def scores(rows, keys, metric):
    return {k:float(rows[k]['output']['scores'][metric]) for k in keys if k in rows
            and rows[k]['output'].get('scores',{}).get(metric) is not None}


def metrics(rows, keys, records):
    available=[k for k in keys if k in rows]; finishes=Counter(rows[k]['output'].get('finish') for k in available)
    called=sum(bool(records(rows[k]['output'])) for k in available)
    result=dict(n=len(keys),completed=len(available),missing=sorted(set(keys)-set(available)),call_items=called,
                call_rate=called/len(keys) if keys else None,
                call_rate_completed=called/len(available) if available else None,
                capped=sum(finishes[f] for f in ('max_calls','max_new_tokens','length')),
                call_capped=finishes['max_calls'],token_capped=finishes['max_new_tokens']+finishes['length'])
    for metric in ('answer','released_answer'):
        s=scores(rows,keys,metric);result['mra_'+metric]=sum(s.values())/len(s) if s else None
        result['n_'+metric]=len(s)
    return result


def groups(manifest):
    items={r['id']:r for r in manifest['items']}; result={'all':sorted(items)}
    for name in SETS:
        result[name]=manifest['sets'][name]
        for unit in ('m','ft','in','cm'):
            result[name+'/'+unit]=[k for k in result[name] if items[k]['unit']==unit]
    for unit in ('m','ft','in','cm'):result['unit/'+unit]=[k for k in items if items[k]['unit']==unit]
    return result


def paired(rows,manifest):
    items={r['id']:r for r in manifest['items']}; result={}
    for unit in ('all','m','ft','in','cm'):
        keys=[k for k in manifest['sets'][SETS[0]] if unit=='all' or items[k]['unit']==unit]
        result[unit]={}
        for metric in ('answer','released_answer'):
            s=scores(rows,items,metric)
            pairs=[(items[k]['room_key'],s[k]-s[items[k]['twin_id']]) for k in keys
                   if k in s and items[k]['twin_id'] in s]
            result[unit][metric]=dict(bootstrap(pairs),expected_pairs=len(keys))
    return result


def evaluate(root,manifest,items_path,records):
    rows,meta=load(root,manifest,items_path)
    result=dict(meta,groups={n:metrics(rows,ks,records) for n,ks in groups(manifest).items()},
                reworded_minus_twin=paired(rows,manifest))
    return rows,result


def comparison(current,baseline,manifest):
    items={r['id']:r for r in manifest['items']}; result={}
    for name,keys in groups(manifest).items():
        result[name]={}
        for metric in ('answer','released_answer'):
            a=scores(current,keys,metric);b=scores(baseline,keys,metric)
            result[name][metric]=dict(bootstrap([(items[k]['room_key'],a[k]-b[k]) for k in sorted(a.keys()&b.keys())]),expected_pairs=len(keys))
    return result


def self_test(directory,manifest,items_path,records):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    for step in (200,544):
        journal=directory/str(step)/'metadata/reads/0/metadata/journals/3/0';journal.mkdir(parents=True)
        settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],
                      perception_memo_verify_ids=[],save_own_depth=False,types=['object_abs_distance'])
        binding=dict(settings,arms=['tower'],modes=[{'name':'none'}],lineage='SFT',fixture=False,
                     items_sha256=digest(items_path),item_set_sha256=manifest['item_set_sha256'],step=step,
                     settings_sha256=canonical(settings))
        for key in ('export_sha256','artifact_manifest_sha256','reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256'):
            binding[key]='0'*64
        (journal/'environment.json').write_text(json.dumps(dict(settings=settings,binding=binding)))
        rows=[]
        for i in manifest['items']:
            reworded=i['id'].endswith('_ho');score=(.75 if reworded else .5) if step==200 else (.5 if reworded else .25)
            rows.append(dict(id=i['id'],room_key=i['room_key'],type='object_abs_distance',arm='tower',mode='none',complete=True,
                output=dict(scores=dict(answer=score,released_answer=score if reworded else None),
                            calls={'records':[{'call':'<gap a=1 b=2>'}]} if reworded else [],
                            finish='max_calls' if reworded else 'eos')))
        (journal/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    a,ra=evaluate(directory/'200',manifest,items_path,records);b,rb=evaluate(directory/'544',manifest,items_path,records)
    assert ra['groups']['all']['completed']==580 and ra['groups']['all']['call_rate']==.5
    assert ra['groups'][SETS[0]]['capped']==290 and ra['groups'][SETS[1]]['n_released_answer']==0
    assert ra['reworded_minus_twin']['all']['answer']['ci95']==[.25,.25]
    comp=comparison(a,b,manifest)
    assert comp['all']['answer']['value']==.25 and comp['all']['answer']['ci95']==[.25,.25]
    # Missing rows affect denominators and pair counts, never become zero scores.
    small=dict(a);small.pop(manifest['sets'][SETS[0]][0])
    assert metrics(small,list(a),records)['completed']==579
    assert paired(small,manifest)['all']['answer']['n']==289
    # A nonconstant, unequal-room example verifies ratio weighting and determinism.
    probe=[('a',0),('a',0),('b',1)]
    assert bootstrap(probe)==bootstrap(probe) and bootstrap(probe)['value']==1/3
    journal=directory/'200/metadata/reads/0/metadata/journals/3/0'
    path=journal/'items.jsonl';raw=path.read_text()
    path.write_text(raw+raw.splitlines(True)[0])
    try:load(directory/'200',manifest,items_path)
    except ValueError:pass
    else:raise AssertionError('Accepted duplicate journal row')
    path.write_text(raw)
    envpath=journal/'environment.json';envraw=envpath.read_text();env=json.loads(envraw)
    env['binding']['items_sha256']='f'*64;envpath.write_text(json.dumps(env))
    try:load(directory/'200',manifest,items_path)
    except ValueError:pass
    else:raise AssertionError('Accepted wrong item binding')
    envpath.write_text(envraw)
    return dict(passed=True,synthetic=True,current=ra,baseline=rb,step_difference=comp)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('items');p.add_argument('--return',dest='root');p.add_argument('--compare',help='Baseline return; differences are current minus baseline')
    p.add_argument('--src',required=True,help='Unpacked D payload (h1eval, b, tree)')
    p.add_argument('--out',required=True,help='Output JSON file');p.add_argument('--self-test',metavar='NEW_DIRECTORY')
    a=p.parse_args();src=Path(a.src).resolve()
    if digest(src/'h1eval/scorers.py')!=SCORERS_SHA:raise ValueError('Scorer source differs from B5/A4')
    sys.path[:0]=[str(src),str(src/'b'),str(src/'tree')]
    from h1eval.scorers import records
    from h1eval.items import load_manifest
    manifest=load_manifest(a.items)
    if manifest['name']!='dist580':raise ValueError('Expected D manifest')
    if a.self_test: result=self_test(a.self_test,manifest,a.items,records)
    else:
        if not a.root:p.error('--return is required')
        rows,current=evaluate(a.root,manifest,a.items,records);result=dict(current=current)
        if a.compare:
            base,baseline=evaluate(a.compare,manifest,a.items,records)
            result.update(baseline=baseline,step_difference=comparison(rows,base,manifest))
    result.update(bootstrap=dict(draws=10000,seed=17,unit='room_key',interval=.95),
                  score_source='output.scores.answer uses item answer; released_answer is reported only when present',
                  difference_units='MRA fraction',call_rate_denominator='all planned items; completed-only rate also reported')
    text=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text);print(text,end='')

if __name__=='__main__':main()
