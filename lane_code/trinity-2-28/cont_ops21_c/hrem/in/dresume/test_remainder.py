"""Local stdlib integration tests; all return/receipt fixtures are synthetic; B5 delivery bytes are authenticated."""
import argparse
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import types
import score_base as base
import score_d
import return_tools as rt
from make_items_remainder import make
from dbuild import make_items_d as itemsmod

HERE = Path(__file__).resolve().parent
DB = HERE.parent/'dbuild'
SOURCE = HERE.parent/'in/B5_1.tgz'
SOURCE_SHA = 'c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a'
sys.path.insert(0,str(HERE/'dbuild'))
from build_support import read_tar, write_tar, bundle_of
import build_d


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=1)+'\n')


def rejected(fn, label):
    try:
        fn()
    except (ValueError, AssertionError, KeyError) as error:
        return dict(test=label,rejected=str(error))
    raise AssertionError('Accepted '+label)


def fixture(root, manifest_path, package, chosen):
    """Create test receipts shaped like a publication; these prove no real execution."""
    m, info = rt.validate_manifest(manifest_path,package)
    settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
                  perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
                  save_own_depth=False,types=['object_abs_distance'])
    op=runpy.run_path(str(package/'a/6.py'))
    inputs={'test_fixture':True,'resume':None}
    identity=dict(plan=info['plan'],inputs=base.canonical({'test_fixture':True}),
                  operator_sha256=info['operator_sha256'],cards=1,
                  reads=op['descriptors'](str(package)),schedule=[[0,3]])
    ret=root/'ret'
    dump(ret/'metadata/IDENTITY.json',identity)
    dump(ret/'metadata/INPUTS.json',inputs)
    readmeta=ret/'metadata/reads/0/metadata'
    dump(readmeta/'READ_IDENTITY.json',dict(identity,read=0,settings_sha256=base.canonical(settings)))
    dump(readmeta/'IDENTITY.json',dict(plan=info['plan'],inputs=identity['inputs'],settings_sha256=base.canonical(settings)))
    pin=dict(base.EXPORTS[info['export_binding']['step']],schema='h1-export-pins-v1',
             config_sha256=info['export_binding']['config_sha256'],
             preparation={k:dict(sha256=v) for k,v in info['export_binding']['preparation_sha256'].items()})
    dump(ret/'metadata/EXPORT_PIN.json',pin)
    bind=dict(settings,arms=['tower'],modes=[{'name':'none'}],lineage='SFT',fixture=False,
              items_sha256=base.digest(manifest_path),item_set_sha256=m['item_set_sha256'],
              step=pin['step'],settings_sha256=base.canonical(settings))
    for key in ('export_sha256','artifact_manifest_sha256')+base.SERVING_KEYS:
        bind[key]='1'*64
    bind['evaluator_code_sha256']=base.canonical(sorted(info['evaluator_files'].items()))
    journal=readmeta/'journals/3/0'
    dump(journal/'environment.json',dict(settings=settings,binding=bind))
    dump(journal/'STARTED.json',{})
    rows=[]
    for i in m['items']:
        if i['id'] not in chosen:
            continue
        ho=i['id'].endswith('_ho')
        rows.append(dict(id=i['id'],room_key=i['room_key'],type='object_abs_distance',
            arm='tower',mode='none',complete=True,output=dict(scores=dict(answer=.75 if ho else .5),
            calls={'records':[{'call':'fixture'}]} if ho else [],finish='eos')))
    (journal/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    complete=len(chosen)==m['count']
    dump(ret/'SUMMARY.json',dict(expected=m['count'],completed=len(rows),complete=complete))
    token=info['token']+'00000001'
    dump(ret/'metadata/RETURN_ID.json',dict(token=token,job='1'))
    archive=root/'0.tgz'
    with tarfile.open(str(archive),'w:gz') as t:
        for path in sorted(ret.rglob('*')):
            if path.is_file():
                t.add(str(path),arcname=str(path.relative_to(ret)),recursive=False)
    ex=dict(plan_sha256=info['plan'],token=token,job='1',synthetic=False,
            archive_bytes=archive.stat().st_size,archive_sha256=base.digest(archive),
            complete=complete,status='COMPLETE' if complete else 'FAILED',
            archive_complete=True,conflicting_terminal_markers=False)
    dump(root/'EXIT.json',ex)
    receipt=dict(plan_sha256=info['plan'],token=token,job='1',returned=True,
                 channels=dict(pool=dict(verified=True,files={n:dict(bytes=p.stat().st_size,sha256=base.digest(p))
                 for n,p in [('EXIT.json',root/'EXIT.json'),('result.tar.gz',archive)]})))
    dump(root/'RETURN_RECEIPT.json',receipt)
    return root


def extract_delivery(path, destination):
    for m, raw in read_tar(path.read_bytes()):
        target=destination/m.name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True)
    p.add_argument('--step',type=int,choices=(200,400,544),default=544)
    p.add_argument('--source',type=Path,default=SOURCE);a=p.parse_args()
    w=Path(a.work);w.mkdir(parents=True,exist_ok=False)
    os.environ['KROOT']=str(w/'deliveries')
    result=dict(synthetic=True,python=sys.version,negative=[])
    source=a.source.resolve();assert base.digest(source)==SOURCE_SHA
    source_files={m.name:raw for m,raw in read_tar(source.read_bytes())}
    payload_files={m.name:raw for m,raw in read_tar(source_files['0.tgz'])}
    binding=HERE/'dbuild'/('bind_D%d.json'%a.step)
    walltime='04:00:00'
    # Build a full parent with the unmodified upstream builder and actual D items.
    original=runpy.run_path(str(DB/'build_d.py'))
    origitems=runpy.run_path(str(DB/'make_items_d.py'))
    original['build'].__globals__['make_items_d']=types.SimpleNamespace(**origitems)
    items=DB/'evidence/actual544/payload/items/dist580.json'
    m=rt.read(items)
    parent_report=original['build'](w/'parent',source,base.digest(source),items,
        binding,DB/'TIMING_D.json',walltime)
    parent=w/'parent_package'
    extract_delivery(Path(parent_report['delivery_dir'])/'1.tgz',parent)
    # Run the real restore function body with only its filesystem/hash dependencies.
    tree=ast.parse(payload_files['orchard_h10/job.py'].decode())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='restore_resume')
    scope=dict(Path=Path,sha=base.digest,tarfile=tarfile,json=json)
    module=ast.parse('');module.body=[fn]
    exec(compile(module,'job.py:restore_resume','exec'),scope)
    def relative(name):
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe path')
    def restore(archive,out,plan):
        scope['restore_resume'](dict(path=str(archive),bytes=archive.stat().st_size,sha256=base.digest(archive)),
            out,dict(plan_sha256=plan),types.SimpleNamespace(relative=relative))
    # Preserve the B5 nested-journal restore checks with an explicitly synthetic return.
    b5plan=json.loads(source_files['0.json'])['plan_sha256']
    b5return=w/'B5_partial.tgz'
    members=[]
    for name,value in [('metadata/IDENTITY.json',dict(plan=b5plan)),
                       ('metadata/reads/0/metadata/journals/4/0/items.jsonl',{})]:
        members.append((tarfile.TarInfo(name),json.dumps(value).encode()))
    b5return.write_bytes(write_tar(members))
    result['negative'].append(rejected(lambda:restore(b5return,w/'b5_restore',parent_report['plan_sha256']),'B5 plan mismatch'))
    restore(b5return,w/'b5_same_plan',b5plan)
    assert sorted(str(p.relative_to(w/'b5_same_plan')) for p in (w/'b5_same_plan').rglob('*') if p.is_file())==['metadata/IDENTITY.json']
    chosen={r['id'] for r in m['items'][:330]}
    partial=fixture(w/'partial',items,parent,chosen)
    restore(partial/'0.tgz',w/'d_restore',parent_report['plan_sha256'])
    assert not list((w/'d_restore').rglob('items.jsonl'))
    result['restore']=dict(b5_return_synthetic=True,b5_same_plan_restored_journals=0,synthetic_D_restored_journals=0,
                           verdict='Same-plan restore accepts identity but loses routed journals')
    remaining=w/'remainder.json'
    selected=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(HERE/'make_items_remainder.py'),
        '--items',str(items),'--package',str(parent),'--archive',str(partial/'0.tgz'),
        '--exit',str(partial/'EXIT.json'),'--receipt',str(partial/'RETURN_RECEIPT.json'),
        '--work',str(w/'unpacked'),'--out',str(remaining)]).decode())
    assert selected['remaining']==250
    rest=rt.read(remaining)
    assert rest['items']==m['items'][330:]
    # Exercise the public build wrapper and its staged placement/CPU/submission helpers.
    subprocess.run(['/usr/bin/python3','-B',str(HERE/'build_remainder.py'),
        '--stage',str(w/'child'),'--source',str(source),'--source-sha',SOURCE_SHA,
        '--items',str(remaining),'--binding',str(binding),'--time',walltime],check=True)
    report=rt.read(w/'child/BUILD.json')['D']
    for name in ('place_fill_d.py','dryres_d.py','build_support.py','make_items_d.py','o_cpu_D.sh','o_sub_D.sh'):
        assert (w/'child'/name).read_bytes()==(HERE/'dbuild'/name).read_bytes()
    assert (w/'child/binding.json').read_bytes()==binding.read_bytes()
    assert report['walltime']==walltime and report['budget_fits']
    child=w/'child_package';extract_delivery(Path(report['delivery_dir'])/'1.tgz',child)
    assert report['count']==250 and report['token']!=parent_report['token']
    assert report['plan_sha256']!=parent_report['plan_sha256']
    with tarfile.open(str(child/'0.tgz')) as t:
        payload={v.name:t.extractfile(v).read() for v in t if v.isfile()}
    rooms=json.loads(payload['items/room134.json'].decode());dev=set(payload['auth/R0_DEV_ROOMS.txt'].decode().splitlines())
    itemsmod.validate(rest,rooms,dev)
    inner={}
    exec(compile(payload['h1eval/dist580.py'],'dist580.py','exec'),inner)
    inner['validate'](rest,rooms,dev)
    op=runpy.run_path(str(child/'a/6.py'))
    assert op['COUNTS']==(0,0,0,250,0) and op['descriptors']('unused')[0]['expected']==250
    assert op['memory_bound']()['reads'][0]['captures']==len({r['room_key'] for r in rest['items']})
    bundle=dict((v.name,d) for v,d in read_tar(bundle_of((child/'BATCH.sh').read_bytes())[1]))
    assert bundle['7.py']==(child/'a/6.py').read_bytes()
    final=fixture(w/'final',remaining,child,{r['id'] for r in rest['items']})
    rows,merged=score_d.merge(items,parent,partial/'ret',remaining,child,final/'ret')
    assert merged['complete'] and len(rows)==580
    assert merged['groups']['all']['call_rate']==.5
    assert merged['reworded_minus_twin']['all']['answer']['n']==290
    result['merge']=dict(completed=580,pairs=290,answer=merged['groups']['all']['mra_answer'])
    # A single unfinished item exercises an absent set and a completed twin.
    singleton=itemsmod.subset(m,[r['id'] for r in m['items'][:-1]],rest['remainder'])
    itemsmod.validate(singleton,rooms,dev)
    raw=build_d.operator(source_files['a/6.py'],singleton)
    scope={};exec(compile(raw,'singleton operator','exec'),scope)
    assert scope['COUNTS']==(0,0,0,1,0)
    assert "for ordinal,name in enumerate(('R0-dev-reworded',))" in raw.decode()
    result['singleton']=dict(count=1,twin_absent=True)
    for label, mutate in [('changed answer',lambda x:x['items'][0].update(answer=-1)),
                          ('changed count',lambda x:x.update(count=251)),
                          ('duplicate completed',lambda x:x['remainder']['completed_ids'].append(x['remainder']['completed_ids'][0]))]:
        bad=copy.deepcopy(rest);mutate(bad)
        result['negative'].append(rejected(lambda:itemsmod.validate(bad,rooms,dev),label))
    result['negative'].append(rejected(lambda:itemsmod.subset(m,[r['id'] for r in m['items']],{}),'already complete'))
    result['negative'].append(rejected(lambda:build_d.build(w/'wrong_step',source,base.digest(source),remaining,
        DB/('bind_D%d.json'%(544 if a.step==200 else 200)),DB/'TIMING_D.json','04:00:00'),'mixed export'))
    journal=final/'ret/metadata/reads/0/metadata/journals/3/0/items.jsonl'
    raw=journal.read_text()
    journal.write_text(raw+raw.splitlines(True)[0])
    result['negative'].append(rejected(lambda:rt.load(final/'ret',remaining,child),'duplicate row'))
    journal.write_text(raw[:-1])
    result['negative'].append(rejected(lambda:rt.load(final/'ret',remaining,child),'incomplete journal tail'))
    journal.write_text(raw)
    envpath=journal.parent/'environment.json';env=rt.read(envpath)
    changed=copy.deepcopy(env);changed['binding']['reader_sha256']='2'*64;dump(envpath,changed)
    result['negative'].append(rejected(lambda:score_d.merge(items,parent,partial/'ret',remaining,child,final/'ret'),'serving mismatch'))
    dump(envpath,env)
    ex=rt.read(partial/'EXIT.json');ex['token']='f'*21;dump(w/'wrong_exit.json',ex)
    result['negative'].append(rejected(lambda:rt.unpack(partial/'0.tgz',w/'wrong_exit.json',partial/'RETURN_RECEIPT.json',parent,w/'wrong_unpack'),'wrong token'))
    group=dict(items=str(items),parent_package=str(parent),partial_archive=str(partial/'0.tgz'),
        partial_exit=str(partial/'EXIT.json'),partial_receipt=str(partial/'RETURN_RECEIPT.json'),
        remainder_items=str(remaining),remainder_package=str(child),remainder_archive=str(final/'0.tgz'),
        remainder_exit=str(final/'EXIT.json'),remainder_receipt=str(final/'RETURN_RECEIPT.json'))
    dump(w/'score_spec.json',dict(current=group))
    subprocess.run(['/usr/bin/python3','-B',str(HERE/'score_d.py'),'--spec',str(w/'score_spec.json'),
                    '--work',str(w/'score_work'),'--out',str(w/'scores.json')],check=True)
    for path in list(HERE.glob('*.py'))+list((HERE/'dbuild').glob('*.py')):
        compile(path.read_text(),str(path),'exec')
    for name in ('o_cpu_D.sh','o_sub_D.sh'):
        subprocess.run(['bash','-n',str(HERE/'dbuild'/name)],check=True)
    result.update(passed=True,work=str(w),source_sha256=base.digest(source),parent_build=parent_report,
                  remainder_build=report,selection=selected)
    result['step']=a.step
    dump(w/'TEST_RESULTS.json',result)
    print(json.dumps(dict(passed=True,negative_cases=len(result['negative']),work=str(w))))


if __name__=='__main__':
    main()
