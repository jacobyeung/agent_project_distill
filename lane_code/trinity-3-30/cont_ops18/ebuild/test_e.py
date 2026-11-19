"""Offline E integration tests. All generated files stay in --work under /dev/shm/c18e."""
import argparse
import ast
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import subprocess
import tarfile
from pathlib import Path
import build_e
import score_e
from build_support import read_tar,write_tar,bundle_of

HERE=Path(__file__).resolve().parent
A4=Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4')
SOURCE_SHA='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'


def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def extract(raw,root):
    for m,d in read_tar(raw):
        assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def rejects(fn):
    try:fn()
    except (AssertionError,ValueError,KeyError):return
    raise AssertionError('Accepted malformed input')


def test_scan(fill,w):
    data=b'weights';heads=b'heads';index=b'{}'
    artifact=dict(heads={'sha256':sha(heads)},full_weights={'sha256':''})
    full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='weights',sha256=sha(data),bytes=len(data))],index=dict(name='index',sha256=sha(index)))
    fullraw=json.dumps(full).encode();artifact['full_weights']['sha256']=sha(fullraw)
    files={'m200/artifact.json':json.dumps(artifact).encode(),'m200/heads.pt':heads,'m200/full_weights/full_weights.json':fullraw,
           'm200/full_weights/weights':data,'m200/full_weights/index':index}
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for n,d in sorted(files.items()):
            m=tarfile.TarInfo(n);m.size=len(d);t.addfile(m,io.BytesIO(d))
    raw=buf.getvalue();paths=[]
    for i in range(4):
        path=w/('part%d'%i);path.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4]);paths.append(path)
    done=w/'tiny.done';done.write_text('tiny %d %s\n'%(len(raw),sha(raw)))
    export,art,archive=fill.scan(paths,done,'tiny')
    assert archive['sha256']==sha(raw) and len(archive['parts'])==4
    assert [p['sha256'] for p in archive['parts']]==[sha(p.read_bytes()) for p in paths]
    done.write_text('tiny %d %s\n'%(len(raw),'0'*64));rejects(lambda:fill.scan(paths,done,'tiny'))
    return dict(parts=4,whole_hash_verified=True,bad_whole_hash_rejected=True,per_part_hashes_computed=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True)
    p.add_argument('--planning-python',default='/scratch/jjyeung/envs/p1cpu/bin/python');a=p.parse_args()
    w=Path(a.work).resolve();assert str(w).startswith('/dev/shm/c18e/');w.mkdir(parents=True,exist_ok=False)
    source=A4/'1.tgz';raw=source.read_bytes();assert sha(raw)==SOURCE_SHA
    original=read_tar(raw);before=dict((m.name,d) for m,d in original)
    # Reproduce every unwrapped A4 delivery member byte and its tar metadata.
    reconstructed=write_tar(original)
    assert dict((m.name,d) for m,d in read_tar(reconstructed))==before
    assert all(d==(A4/'package'/m.name).read_bytes() for m,d in original)
    (w/'A4_reproduced.tgz').write_bytes(reconstructed)
    os.environ['KROOT']=str(w/'K')
    report=build_e.build(w/'stage',source,SOURCE_SHA,HERE/'bind_E200.json',HERE/'TIMING_E.json','02:00:00')
    delivery=(Path(report['delivery_dir'])/'1.tgz').read_bytes();extract(delivery,w/'package')
    after=dict((m.name,d) for m,d in read_tar(delivery));extract(after['0.tgz'],w/'src')
    oldpay=dict((m.name,d) for m,d in read_tar(before['0.tgz']));newpay=dict((m.name,d) for m,d in read_tar(after['0.tgz']))
    assert oldpay.keys()==newpay.keys()
    assert {n for n in oldpay if oldpay[n]!=newpay[n]}=={'9.json'}
    allowed={'0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','PACKAGE.json','SUBMIT.cmd','a/0.json','a/4.py','a/5.py','a/6.py'}
    assert {n for n in before if before[n]!=after[n]}==allowed
    oldplan=json.loads(oldpay['9.json']);plan=json.loads(newpay['9.json'])
    assert {k for k in plan if plan[k]!=oldplan[k]}=={'token','budget_gpu_seconds','export_binding'}
    b=read(HERE/'bind_E200.json');assert plan['export_binding']=={k:b[k] for k in build_e.KEYS}
    assert not report['budget_fits'] and report['budget_gpu_seconds']==6402
    batch=after['BATCH.sh'];assert batch.count(b'trap fin EXIT')==1 and batch.count(b'trap \'kill -USR1')==1
    oldbundle=dict((m.name,d) for m,d in read_tar(bundle_of(before['BATCH.sh'])[1]));newbundle=dict((m.name,d) for m,d in read_tar(bundle_of(batch)[1]))
    assert {n for n in oldbundle if oldbundle[n]!=newbundle[n]}=={'0.json','7.py'}
    assert newbundle['7.py']==after['a/6.py'] and newbundle['0.json']==after['0.json']
    base_before=json.loads(before['a/0.json']);base_after=json.loads(after['a/0.json'])
    assert {k for k in base_before if base_before[k]!=base_after[k]}=={'types'}
    assert base_after['types']==['object_abs_distance']
    fill=module(w/'package/a/4.py','fill_e');assert fill.reviewed_binding()==dict(plan['export_binding'],archive_bytes=b['archive_bytes'],archive_sha256=b['archive_sha256'])
    from types import SimpleNamespace
    arg=SimpleNamespace(object=b['object'],step=b['step'],lineage=b['lineage'])
    artifact=dict(step=200,**{k:b[k] for k in ('base_identity','config_sha256','frame_layout')})
    for n,tail in [('heads','heads.pt'),('full_weights','full_weights/full_weights.json')]:artifact[n]={'path':'/runs/'+b['run']+'/m200/'+tail}
    export={'member_directory':'m200'};archive=dict(sha256=b['archive_sha256'],parts=b['parts'])
    prep={k:{'sha256':v} for k,v in b['preparation_sha256'].items()}
    fill.bind_review(arg,export,artifact,archive,prep,fill.reviewed_binding())
    for key in ('step','base_identity','config_sha256','frame_layout'):
        bad=dict(artifact);bad[key]='wrong';rejects(lambda:fill.bind_review(arg,export,bad,archive,prep,fill.reviewed_binding()))
    bad=copy.deepcopy(prep);bad['receipt']['sha256']='0'*64
    rejects(lambda:fill.bind_review(arg,export,artifact,archive,bad,fill.reviewed_binding()))
    scan=test_scan(fill,w)
    # Entrypoint guards must reject before any check or submission is dispatched.
    for args in [['--time','04:00:00'],['--gpus','2'],['--gpus','1','--gpus','1'],['--time=01:00:00']]:
        r=subprocess.run(['/usr/bin/python3','-B',str(w/'package/3.py'),'submit']+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert r.returncode!=0 and (b'E requires' in r.stderr or b'Duplicate' in r.stderr)
    # Actual Python 3.6 compilation of all Orchard helpers and modified delivery scripts.
    paths=list(HERE.glob('*.py'))+[w/'package'/n for n in ('3.py','a/4.py','a/5.py','a/6.py')]
    for i,path in enumerate(paths):py_compile.compile(str(path),cfile=str(w/('compile%d.pyc'%i)),doraise=True)
    subprocess.run([a.planning_python,'-B',str(HERE/'plan_e.py'),str(w)],check=True,
                   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    value,items=score_e.manifest(w/'src/items/devs1_routed.json');records=score_e.scorer_records(w/'src')
    rows,meta=score_e.load(A4/'ret',value,items);assert list(rows)==[r['id'] for r in items]
    # Missing data changes completed/pair counts, not the planned call denominator.
    small=dict(rows);small.pop(items[0]['id']);m=score_e.metrics(small,list(rows),records)
    assert m['n']==150 and m['completed']==149
    paired=score_e.comparison(small,rows,items,records);assert paired['all']['answer']['n']==149
    assert paired['all']['answer']['ci95']==[0,0]
    assert score_e.bootstrap([('a',0),('a',0),('b',1)])['value']==1/3
    j=w/'bad_return/metadata/reads/0/metadata/journals/3/0';j.mkdir(parents=True)
    src=A4/'ret/metadata/reads/0/metadata/journals/3/0';envraw=(src/'environment.json').read_bytes();journal=(src/'items.jsonl').read_bytes()
    (j/'environment.json').write_bytes(envraw)
    for name,raw in [('duplicate',journal+journal.splitlines(True)[0]),('tail',journal[:-1]),('order',b''.join(reversed(journal.splitlines(True))))]:
        (j/'items.jsonl').write_bytes(raw);rejects(lambda:score_e.load(w/'bad_return',value,items))
    (j/'items.jsonl').write_bytes(journal)
    env=json.loads(envraw);env['binding']['items_sha256']='0'*64;(j/'environment.json').write_text(json.dumps(env))
    rejects(lambda:score_e.load(w/'bad_return',value,items))
    subprocess.run(['/usr/bin/python3','-B',str(HERE/'score_e.py'),str(w/'src/items/devs1_routed.json'),'--src',str(w/'src'),'--self-test','--out',str(w/'SCORES.json')],check=True)
    for name in ('o_build_E.sh','o_place_fill_E.sh','o_cpu_E.sh','o_sub_E.sh'):subprocess.run(['bash','-n',str(HERE/name)],check=True)
    result=dict(passed=True,source_sha256=SOURCE_SHA,source_members=len(original),payload_members_unchanged=len(oldpay)-1,
                changed_delivery=sorted(allowed),changed_payload=['9.json'],compile_files=len(paths),python='3.6.8',
                baseline_order_matches=True,planning=True,scorer_self_test=True,scan=scan,
                negative_tests=['artifact_step','base_identity','config_identity','frame_layout','preparation_hash','whole_archive_hash','walltime','gpu_count','duplicate_flag','duplicate_row','journal_tail','item_order','items_binding'],
                build=report,work=str(w))
    dump(w/'TEST_RESULTS.json',result);print('E integration passed: '+str(w/'TEST_RESULTS.json'))

if __name__=='__main__':main()
