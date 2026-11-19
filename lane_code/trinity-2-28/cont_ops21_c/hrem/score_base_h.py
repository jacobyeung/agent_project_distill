"""Score authenticated H camera returns; stdlib only, Python 3.6.
Answer uses output.scores.answer, with max_calls forced to zero as in patched accuracy().
Missing items are reported explicitly. Paired estimates use complete pairs only.
"""
import argparse
import gzip
import hashlib
import json
import math
import random
import sys
from collections import Counter,defaultdict
from pathlib import Path
from heldout_h import TYPES, PINS, ITEM_NAMES, validate_payload
PACKAGE_KIND='H'
EXPECTED_COUNT=900
SERVING_KEYS=('reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256','expected_calls_sha256')
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
EXPORTS={}
EXPORTS[200]={'run': '673bc60f', 'step': 200, 'member_directory': 'm200', 'object': 'q8/8865619b/673bc60f_m200.tar', 'lineage': 'SFT', 'archive_sha256': '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'}
EXPORTS[544]={'run': '469ddece', 'step': 544, 'member_directory': 'm544', 'object': 'q8/8865619b/469ddece_mstop.tar', 'lineage': 'SFT', 'archive_sha256': '3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7'}

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
                      export_binding=plan['export_binding'], serving_pins=plan['serving_pins'])
    else:
        value = read(path)
        build = value.get(PACKAGE_KIND, value)
        result = dict(plan=build['plan_sha256'],
                      operator_sha256=build['changed_members']['a/6.py']['after'],
                      export_binding=build['export_binding'], serving_pins=build['serving_pins'])
    for key in ('plan', 'operator_sha256'):
        checked_sha(result[key], key)
    binding = result['export_binding']
    step = binding.get('step')
    if step not in EXPORTS:
        raise ValueError('Unreviewed '+PACKAGE_KIND+' step')
    for key, want in EXPORTS[step].items():
        if key != 'archive_sha256' and binding.get(key) != want:
            raise ValueError('Package export binding differs: '+key)
    for key in SERVING_KEYS:checked_sha(result['serving_pins'][key],key)
    return result


def authenticate_return(root, package, read_index=0, m=None):
    count = m["count"] if m else 900
    active = [t for t,k in enumerate(TYPES) if not m or any(i["question_type"]==k for i in m["items"])]
    expected = package_identity(package)
    root = Path(root)
    identity = read(root/'metadata/IDENTITY.json')
    for key in ('plan', 'operator_sha256'):
        if identity.get(key) != expected[key]:
            raise ValueError('Return plan/operator differs: '+key)
    descriptor = dict(arm='tower', modes=['none'], types=active, expected=count,
                      stage1_select_rule='candidates_argmax', save_own_depth=False,
                      perception_memo='on', perception_memo_modules=['g3t'], perception_memo_verify_ids=[])
    if (read_index != 0 or identity.get('cards') != 1 or identity.get('reads') != [descriptor]
            or identity.get('schedule') != [[0,t] for t in active]):
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
                export_pin=pin, serving_pins=expected['serving_pins'], read_identity=read_identity, reader_identity=reader_identity)


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


def manifest(items_path,twins_path):
    if digest(items_path)!=PINS[ITEM_NAMES[0]] or digest(twins_path)!=PINS[ITEM_NAMES[1]]:
        raise ValueError('Frozen H input differs')
    m=read(items_path);validate_payload(m)
    twins=read(twins_path)['twins'];assert len(twins)==450
    return m,twins


def records(output):
    value=output.get('calls',output.get('hook',{}))
    return value.get('records',[]) if isinstance(value,dict) else value


def metric(row,name):
    output=row['output']
    if name=='call_rate':return float(bool(records(output)))
    if name=='answer':return 0.0 if output.get('finish')=='max_calls' else float(output['scores']['answer'])
    raise ValueError(name)


def load_return(root,package,m):
    identity=authenticate_return(root,package,m=m)
    root=Path(root);by={i['id']:i for i in m['items']};all_rows={};common=None;sources=[]
    for t,kind in enumerate(TYPES):
        journal=root/('metadata/reads/0/metadata/journals/%d'%t)
        paths=sorted(journal.glob('*/items.jsonl'))+sorted(journal.glob('*/items.jsonl.gz'))
        for started in journal.glob('*/STARTED.json'):
            if not any(p.parent==started.parent for p in paths):raise ValueError('Started segment lacks journal')
        ids=[i['id'] for i in m['items'] if i['question_type']==kind];seen=set();encountered=[]
        for path in paths:
            env=read(path.parent/'environment.json');b=env['binding'];settings=env['settings']
            expect=dict(schema='h10-shard-v1',arms=['tower'],modes=[{'name':'none'}],fixture=False,
                lineage='SFT',step=identity['export_pin']['step'],stage1_select_rule='candidates_argmax',
                perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,
                items_sha256=m.get("sealed_sha256",PINS[ITEM_NAMES[0]]),item_set_sha256=m['item_set_sha256'],ids=ids,count=m['count'],
                shard='0/1',r0_pin=m['r0_check']['pin'],reader_entry='e2e_reader.parity:make_real',maker_name='make_capped_real')
            expect.update(identity['serving_pins'])
            for key,want in expect.items():
                if b.get(key)!=want:raise ValueError('Journal binding differs: '+key)
            if canonical(settings)!=b['settings_sha256']:raise ValueError('Settings hash differs')
            for key in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):
                if settings.get(key)!=b[key]:raise ValueError('Settings differ: '+key)
            tasks=settings.get('tasks',[])
            if len(tasks)!=1 or not tasks[0].endswith('/items/HELDOUT_NATIVE_TASKS.jsonl'):raise ValueError('Native tasks differ')
            authenticate_journals(dict(binding=b),identity)
            for key in ('mapping_sha256','r0_code_sha256'):checked_sha(b[key],key)
            shared={k:v for k,v in b.items() if k not in ('ids','shard','device')}
            if common is not None and shared!=common:raise ValueError('Mixed H journal bindings')
            common=shared
            raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
            if raw and not raw.endswith(b'\n'):raise ValueError('Uncommitted journal tail')
            for line in raw.splitlines():
                row=json.loads(line);key=row['id']
                if key not in ids or key in seen:raise ValueError('Duplicate or unplanned item')
                seen.add(key);encountered.append(key)
                if row.get('arm')!='tower' or row.get('mode')!='none' or row.get('type')!=kind:raise ValueError('Arm/mode/type differs')
                if row.get('room_key')!=by[key]['room_key']:raise ValueError('Room differs')
                if row.get('intervention')!={'name':'none'} or row.get('applied') is not False:raise ValueError('Intervention differs')
                if row.get('complete') is not True:continue
                value=row['output'].get('scores',{}).get('answer')
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:raise ValueError('Invalid sealed answer')
                calls=records(row['output'])
                if not isinstance(calls,list) or any(not isinstance(c,dict) or not isinstance(c.get('call'),str) for c in calls):raise ValueError('Invalid call records')
                all_rows[key]=row
            sources.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),stored_sha256=digest(path)))
        if encountered!=[i for i in ids if i in seen]:raise ValueError('Item order differs')
    if common is None:raise ValueError('No H journals')
    return all_rows,dict(identity=identity,binding=common,sources=sources)


def cells(m,twins):
    by={i['id']:i for i in m['items']};result={}
    for kind in TYPES:
        for label in ('original','reworded'):
            result[kind+'/'+label]=[t[label+'_id'] for t in twins if t['type']==kind]
    return result


def metrics(rows,ids):
    have=[k for k in ids if k in rows];n=len(have)
    return dict(expected=len(ids),completed=n,missing=[k for k in ids if k not in rows],
        call_items=sum(metric(rows[k],'call_rate') for k in have),
        call_rate=sum(metric(rows[k],'call_rate') for k in have)/n if n else None,
        answer=sum(metric(rows[k],'answer') for k in have)/n if n else None,
        call_rate_all_planned=sum(metric(rows[k],'call_rate') for k in have)/len(ids),
        max_calls=sum(rows[k]['output'].get('finish')=='max_calls' for k in have))


def paired(rows,m,twins):
    by={i['id']:i for i in m['items']};out={}
    for kind in TYPES:
        ts=[t for t in twins if t['type']==kind];out[kind]={}
        for name in ('call_rate','answer'):
            pairs=[(by[t['original_id']]['room_key'],metric(rows[t['reworded_id']],name)-metric(rows[t['original_id']],name))
                   for t in ts if t['original_id'] in rows and t['reworded_id'] in rows]
            out[kind][name]=dict(bootstrap(pairs),expected_pairs=len(ts))
    return out


def compare(current,other,m,twins):
    by={i['id']:i for i in m['items']};out={}
    for name,ids in cells(m,twins).items():
        out[name]={metric_name:dict(bootstrap([(by[k]['room_key'],metric(current[k],metric_name)-metric(other[k],metric_name))
            for k in ids if k in current and k in other]),expected_pairs=len(ids)) for metric_name in ('call_rate','answer')}
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--items',default=str(Path(__file__).parent/'in/HELDOUT_CAMERA_ITEMS.json'))
    p.add_argument('--twins',default=str(Path(__file__).parent/'in/HELDOUT_CAMERA_TWINS.json'))
    p.add_argument('--return',dest='root');p.add_argument('--package');p.add_argument('--other-return');p.add_argument('--other-package')
    p.add_argument('--out',required=True);p.add_argument('--self-test',action='store_true')
    a=p.parse_args();m,twins=manifest(a.items,a.twins)
    if a.self_test:
        if a.root or a.package:p.error('Self-test cannot score production returns')
        from test_score_h import run
        result=run(m,twins)
    else:
        if not a.root or not a.package:p.error('--return and --package required')
        rows,meta=load_return(a.root,a.package,m)
        result=dict(meta=meta,cells={k:metrics(rows,v) for k,v in cells(m,twins).items()},reworded_minus_original=paired(rows,m,twins))
        if a.other_return or a.other_package:
            if not a.other_return or not a.other_package:p.error('Both comparison arguments required')
            other,other_meta=load_return(a.other_return,a.other_package,m)
            if meta['binding']['step']==other_meta['binding']['step']:raise ValueError('Step comparison requires distinct steps')
            result.update(other_meta=other_meta,current_minus_other=compare(rows,other,m,twins))
    result.update(bootstrap=dict(draws=10000,seed=17,unit='room_key',interval=.95),
        answer_source='patched scorers.accuracy task_accuracy: sealed output.scores.answer, max_calls=0',
        denominator='Completed items for cell rates; complete pairs for differences; missing IDs reported')
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
