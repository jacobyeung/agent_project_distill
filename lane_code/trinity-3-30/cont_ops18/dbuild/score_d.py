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

PACKAGE_KIND = 'D'
EXPECTED_COUNT = 580
SERVING_KEYS = ('reader_sha256', 'parity_code_sha256', 'evaluator_code_sha256', 'maker_sha256')
EXPORTS = {200: {'run': '673bc60f', 'step': 200, 'member_directory': 'm200', 'object': 'q8/8865619b/673bc60f_m200.tar', 'lineage': 'SFT', 'archive_sha256': '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'}, 544: {'run': '469ddece', 'step': 544, 'member_directory': 'm544', 'object': 'q8/8865619b/469ddece_mstop.tar', 'lineage': 'SFT', 'archive_sha256': '3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7'}}


def checked_sha(value, name):
    if (not isinstance(value, str) or len(value) != 64 or value == '0'*64
            or any(ch not in '0123456789abcdef' for ch in value)):
        raise ValueError('Invalid SHA256: '+name)
    return value


def package_identity(path):
    """Read trusted build evidence supplied separately from the return."""
    path = Path(path)
    if path.is_dir():
        public = read(path/'0.json')
        import tarfile
        with tarfile.open(str(path/'0.tgz')) as archive:
            plan = json.loads(archive.extractfile('9.json').read().decode())
        # Plans use the builder's ASCII canonical serialization.
        plan_sha = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if plan_sha != public['plan_sha256'] or plan['token'] != public['token']:
            raise ValueError('Package plan differs')
        if digest(path/'0.tgz') != public['payload_sha256']:
            raise ValueError('Package payload differs')
        result = dict(plan=plan_sha, operator_sha256=digest(path/'a/6.py'),
                      export_binding=plan['export_binding'])
    else:
        value = read(path)
        build = value.get(PACKAGE_KIND, value)
        result = dict(plan=build['plan_sha256'],
                      operator_sha256=build['changed_members']['a/6.py']['after'],
                      export_binding=build['export_binding'])
    for key in ('plan', 'operator_sha256'):
        checked_sha(result[key], key)
    binding = result['export_binding']
    step = binding.get('step')
    if step not in EXPORTS:
        raise ValueError('Unreviewed '+PACKAGE_KIND+' step')
    for key, want in EXPORTS[step].items():
        if key != 'archive_sha256' and binding.get(key) != want:
            raise ValueError('Package export binding differs: '+key)
    return result


def authenticate_return(root, package, read_index=0):
    expected = package_identity(package)
    root = Path(root)
    identity = read(root/'metadata/IDENTITY.json')
    for key in ('plan', 'operator_sha256'):
        if identity.get(key) != expected[key]:
            raise ValueError('Return plan/operator differs: '+key)
    descriptor = dict(arm='tower', modes=['none'], types=[3], expected=EXPECTED_COUNT,
                      stage1_select_rule='candidates_argmax', save_own_depth=False,
                      perception_memo='on', perception_memo_modules=['g3t'], perception_memo_verify_ids=[])
    if (read_index != 0 or identity.get('cards') != 1 or identity.get('reads') != [descriptor]
            or identity.get('schedule') != [[0, 3]]):
        raise ValueError('Return read plan differs')
    directory = root/'metadata/reads/0/metadata'
    read_identity = read(directory/'READ_IDENTITY.json')
    if {k:v for k,v in read_identity.items() if k not in ('read','settings_sha256')} != identity:
        raise ValueError('Read identity differs')
    if read_identity.get('read') != 0:
        raise ValueError('Read index differs')
    reader_identity = read(directory/'IDENTITY.json')
    for key in ('plan', 'inputs'):
        if reader_identity.get(key) != identity.get(key):
            raise ValueError('Reader identity differs: '+key)
    pin = read(root/'metadata/EXPORT_PIN.json')
    step = expected['export_binding']['step']
    for key, want in EXPORTS[step].items():
        if pin.get(key) != want:
            raise ValueError('Export pin differs: '+key)
    if pin.get('schema') != 'h1-export-pins-v1':
        raise ValueError('Export pin schema differs')
    binding = expected['export_binding']
    if pin.get('config_sha256') != binding['config_sha256']:
        raise ValueError('Export config differs')
    for key, want in binding['preparation_sha256'].items():
        if pin['preparation'][key]['sha256'] != want:
            raise ValueError('Export preparation differs: '+key)
    return dict(package=str(package), plan=expected['plan'], operator_sha256=expected['operator_sha256'],
                export_pin=pin, read_identity=read_identity, reader_identity=reader_identity)


def authenticate_journals(meta, identity):
    binding = meta['binding']
    if binding['step'] != identity['export_pin']['step']:
        raise ValueError('Journal export step differs')
    for key in ('export_sha256', 'artifact_manifest_sha256') + SERVING_KEYS:
        checked_sha(binding[key], key)
    for key in ('read_identity', 'reader_identity'):
        if identity[key]['settings_sha256'] != binding['settings_sha256']:
            raise ValueError('Read settings differ')


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


def load_return(root, manifest, items_path, package):
    identity = authenticate_return(root, package)
    rows, report = load(root, manifest, items_path)
    authenticate_journals(report, identity)
    report['identity'] = identity
    return rows, report


def evaluate_return(root, manifest, items_path, records, package):
    rows, meta = load_return(root, manifest, items_path, package)
    return rows, dict(meta, groups={n:metrics(rows, ks, records) for n,ks in groups(manifest).items()},
                     reworded_minus_twin=paired(rows, manifest))


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
    p.add_argument('--package',help='Trusted D package directory or BUILD.json for --return')
    p.add_argument('--compare-package',help='Trusted D package directory or BUILD.json for --compare')
    p.add_argument('--src',required=True,help='Unpacked D payload (h1eval, b, tree)')
    p.add_argument('--out',required=True,help='Output JSON file');p.add_argument('--self-test',metavar='NEW_DIRECTORY')
    a=p.parse_args();src=Path(a.src).resolve()
    if digest(src/'h1eval/scorers.py')!=SCORERS_SHA:raise ValueError('Scorer source differs from B5/A4')
    sys.path[:0]=[str(src),str(src/'b'),str(src/'tree')]
    from h1eval.scorers import records
    from h1eval.items import load_manifest
    manifest=load_manifest(a.items)
    if manifest['name']!='dist580':raise ValueError('Expected D manifest')
    if a.self_test:
        if a.root or a.compare or a.package or a.compare_package:p.error('--self-test cannot score a return')
        result=self_test(a.self_test,manifest,a.items,records)
    else:
        if not a.root or not a.package:p.error('--return and --package are required')
        if a.compare and not a.compare_package:p.error('--compare requires --compare-package')
        rows,current=evaluate_return(a.root,manifest,a.items,records,a.package);result=dict(current=current)
        if a.compare:
            base,baseline=evaluate_return(a.compare,manifest,a.items,records,a.compare_package)
            result.update(baseline=baseline,step_difference=comparison(rows,base,manifest))
    result.update(bootstrap=dict(draws=10000,seed=17,unit='room_key',interval=.95),
                  score_source='output.scores.answer uses item answer; released_answer is reported only when present',
                  difference_units='MRA fraction',call_rate_denominator='all planned items; completed-only rate also reported')
    text=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text);print(text,end='')

if __name__=='__main__':main()
