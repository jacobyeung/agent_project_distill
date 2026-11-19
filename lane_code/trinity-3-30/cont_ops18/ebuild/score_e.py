"""Score E returns and paired room-bootstrap differences; Python 3.6 syntax."""
import argparse
import gzip
import re
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

A4 = '/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4/ret'
BASE544 = '/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s/bases/b1/work/ret'
SCORERS_SHA = '2736e479888481cda4c1682f2db3d8b54f0b6d5957d8a4603d86469dc2b493fd'
ITEMS_SHA = '2849206e3eb66f40b3e2fba49cfe84abe3c0465a318f85aaeaeca6ff6f26fe21'
TYPE = 'object_abs_distance'


def read(path): return json.loads(Path(path).read_text())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

PACKAGE_KIND = 'E'
EXPECTED_COUNT = 150
SERVING_KEYS = ('reader_sha256', 'parity_code_sha256', 'evaluator_code_sha256', 'maker_sha256')
EXPORTS = {200: {'run': '359fcc3c', 'step': 200, 'member_directory': 'm200', 'object': 'q8/8865619b/359fcc3c_m200.tar', 'lineage': 'SFT', 'archive_sha256': '6bd9eb26e22c7bdd26fe6e5a932502fa7d1aebd57024861bca786b027ff7d61b'}}


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


def scorer_records(src):
    # Load the exact pure function without importing numpy or modern-syntax serving code.
    path=Path(src)/'h1eval/scorers.py'
    if digest(path)!=SCORERS_SHA:raise ValueError('Scorer differs from A4')
    text=path.read_text();start=text.index('def records(');end=text.index('\ndef signature(',start)
    namespace={};exec(compile(text[start:end],str(path)+':records','exec'),namespace)
    return namespace['records']


def unit(item):
    question=item['question'].lower();found=[]
    for name,pattern in [('cm',r'\b(?:centimeters?|centimetres?|cm)\b'),
                         ('mm',r'\b(?:millimeters?|millimetres?|mm)\b'),
                         ('ft',r'\b(?:feet|foot|ft)\b'),('in',r'\b(?:inches|inch)\b'),
                         ('m',r'\b(?:meters?|metres?|m)\b')]:
        if re.search(pattern,question):found.append(name)
    if len(found)!=1:raise ValueError('Ambiguous or missing question unit: '+item['id'])
    return found[0]


def manifest(path):
    if digest(path)!=ITEMS_SHA:raise ValueError('Expected unchanged A4 routed manifest')
    value=read(path)
    if canonical(value['items'])!=value['item_set_sha256']:raise ValueError('Item-set hash differs')
    items=[r for r in value['items'] if r['question_type']==TYPE]
    if len(items)!=150 or len({r['id'] for r in items})!=150:raise ValueError('Expected 150 distinct distance items')
    for r in items:unit(r)
    return value,items


def groups(items):
    result={'all':[r['id'] for r in items]}
    for u in sorted({unit(r) for r in items}):result['unit/'+u]=[r['id'] for r in items if unit(r)==u]
    return result


def load(root, value, items, read_index=0):
    journal=Path(root)/('metadata/reads/%d/metadata/journals/3'%read_index)
    paths=sorted(journal.glob('*/items.jsonl'))+sorted(journal.glob('*/items.jsonl.gz'))
    if not paths:raise ValueError('No distance journals: '+str(journal))
    for started in journal.glob('*/STARTED.json'):
        if not any(p.parent==started.parent for p in paths):raise ValueError('Started segment lacks journal')
    expected_ids=[r['id'] for r in items];by_id={r['id']:r for r in items}
    rows={};seen=set();sources=[];shared=None;encountered=[]
    for path in paths:
        env=read(path.parent/'environment.json');b=env['binding'];settings=env['settings']
        expected=dict(arms=['tower'],modes=[{'name':'none'}],lineage='SFT',fixture=False,
                      stage1_select_rule='candidates_argmax',perception_memo_modules=['g3t'],save_own_depth=False,
                      items_sha256=ITEMS_SHA,item_set_sha256=value['item_set_sha256'],ids=expected_ids,count=636)
        for key,want in expected.items():
            if b.get(key)!=want:raise ValueError('Journal binding differs: '+key)
        if b['settings_sha256']!=canonical(settings):raise ValueError('Settings hash differs')
        for key in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):
            if settings.get(key)!=b[key]:raise ValueError('Setting differs: '+key)
        if b['perception_memo']=='on':
            if b['perception_memo_verify_ids']!=[]:raise ValueError('Unexpected verification IDs')
        elif b['perception_memo']=='verify':
            if b['step']!=544 or b['perception_memo_verify_ids']!=expected_ids[:30]:raise ValueError('Unrecognized memo verification')
        else:raise ValueError('Unsupported memo mode')
        if settings.get('types',[TYPE])!=[TYPE]:raise ValueError('Settings type differs')
        current={k:b[k] for k in ('step','export_sha256','settings_sha256','artifact_manifest_sha256',
                    'reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256',
                    'perception_memo','perception_memo_verify_ids','mapping_sha256')}
        if shared is not None and shared!=current:raise ValueError('Mixed distance journals')
        shared=current
        raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
        if raw and not raw.endswith(b'\n'):raise ValueError('Uncommitted journal tail')
        for line in raw.decode().splitlines():
            row=json.loads(line);key=row['id']
            if key in seen or key not in by_id:raise ValueError('Duplicate or unplanned item: '+key)
            seen.add(key);encountered.append(key)
            if row.get('arm')!='tower' or row.get('mode')!='none' or row.get('type')!=TYPE:raise ValueError('Wrong arm/mode/type')
            if row['room_key']!=by_id[key]['room_key']:raise ValueError('Room differs')
            if row.get('intervention')!={'name':'none'} or row.get('applied') is not False:raise ValueError('Intervention differs')
            if row.get('complete') is not True:continue
            for metric in ('answer','released_answer'):
                score=row['output'].get('scores',{}).get(metric)
                if score is None and metric=='released_answer':continue
                if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
                    raise ValueError('Invalid sealed score: '+metric)
            rows[key]=row
        sources.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),stored_sha256=digest(path)))
    if encountered!=[k for k in expected_ids if k in seen]:raise ValueError('Distance item order differs')
    return rows,dict(read=read_index,step=shared['step'],binding=shared,sources=sources)


def evaluate(root,value,items,records,read_index=0):
    rows,meta=load(root,value,items,read_index)
    return rows,dict(meta,groups={name:metrics(rows,keys,records) for name,keys in groups(items).items()})


def load_return(root, value, items, package, reference, read_index=0):
    identity = authenticate_return(root, package, read_index)
    rows, report = load(root, value, items, read_index)
    authenticate_journals(report, identity)
    for key in SERVING_KEYS:
        checked_sha(reference[key], key)
        if report['binding'][key] != reference[key]:
            raise ValueError('Serving pin differs from baselines: '+key)
    report['identity'] = identity
    return rows, report


def evaluate_return(root, value, items, records, package, reference, read_index=0):
    rows, meta = load_return(root, value, items, package, reference, read_index)
    return rows, dict(meta, groups={name:metrics(rows, keys, records) for name,keys in groups(items).items()})


def comparison(current,baseline,items,records):
    by_id={r['id']:r for r in items};result={}
    for name,keys in groups(items).items():
        result[name]={}
        for metric in ('answer','released_answer','call_rate'):
            if metric=='call_rate':
                a={k:float(bool(records(current[k]['output']))) for k in keys if k in current}
                b={k:float(bool(records(baseline[k]['output']))) for k in keys if k in baseline}
            else:a=scores(current,keys,metric);b=scores(baseline,keys,metric)
            result[name][metric]=dict(bootstrap([(by_id[k]['room_key'],a[k]-b[k]) for k in sorted(a.keys()&b.keys())]),expected_pairs=len(keys))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('items');p.add_argument('--src',required=True);p.add_argument('--out',required=True)
    p.add_argument('--package',help='Trusted E package directory or BUILD.json for this return')
    p.add_argument('--return',dest='root');p.add_argument('--read',type=int,default=0)
    p.add_argument('--a4',default=A4);p.add_argument('--baseline544',default=BASE544)
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args();value,items=manifest(a.items);records=scorer_records(a.src)
    r1,r1report=evaluate(a.a4,value,items,records)
    b544,b544report=evaluate(a.baseline544,value,items,records,1)
    if r1report['step']!=200 or b544report['step']!=544:raise ValueError('Baseline step differs')
    if len(r1)!=150 or len(b544)!=150:raise ValueError('Baseline is incomplete')
    for key in SERVING_KEYS:
        checked_sha(r1report['binding'][key], key)
        if r1report['binding'][key] != b544report['binding'][key]:
            raise ValueError('Baseline serving pins differ: '+key)
    if a.self_test:
        if a.root or a.package:p.error('--self-test cannot score a return')
        current=r1;report=r1report
    else:
        if not a.root or not a.package:p.error('--return and --package are required')
        current,report=evaluate_return(a.root,value,items,records,a.package,r1report['binding'],a.read)
    against_r1=comparison(current,r1,items,records)
    if a.self_test:
        assert all(v['value']==0 and v['ci95']==[0,0] for g in against_r1.values() for v in g.values())
    result=dict(current=report,baselines=dict(A4=r1report,step544=b544report),
                current_minus_A4=against_r1,current_minus_step544=comparison(current,b544,items,records),
                self_test=a.self_test,bootstrap=dict(draws=10000,seed=17,unit='room_key',interval=.95),
                score_source='output.scores.answer and output.scores.released_answer; question units',
                call_source='h1eval.scorers.records (authenticated pure function)',
                call_rate_denominator='150 planned items or planned unit count; completed-only rate also reported',
                difference_units='MRA and call-rate fractions; only completed pairs enter bootstrap')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(out=str(out),self_test=a.self_test,all=report['groups']['all']),sort_keys=True))

if __name__=='__main__':main()
