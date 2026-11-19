"""Offline D integration tests. Run with p1cpu Python; all outputs go under --work."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import py_compile
import subprocess
import sys
import tarfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_d
from build_support import read_tar,write_tar,bundle_of
import make_items_d


def read(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=1)+'\n')
def extract(raw,root):
    root.mkdir(parents=True,exist_ok=True)
    for m,d in read_tar(raw):
        p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--b5',default='/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/B5/package')
    p.add_argument('--generator',default='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/dist_diag/make_r0_heldout.py')
    a=p.parse_args();w=Path(a.work).resolve();assert str(w).startswith('/dev/shm/c18d/');w.mkdir(parents=True,exist_ok=False)
    b5=Path(a.b5);payload=b5/'0.tgz';src=w/'B5src';extract(payload.read_bytes(),src)
    # Reconstruct a delivery and verify every original member byte, including unlisted mutable templates.
    names=['0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json','PACKAGE.json','SUBMIT.cmd',
           'a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json']
    parts=[]
    for n in names:
        m=tarfile.TarInfo(n);m.mode=(b5/n).stat().st_mode&0o777;parts.append((m,(b5/n).read_bytes()))
    raw=write_tar(parts);assert all(d==(b5/m.name).read_bytes() for m,d in read_tar(raw))
    source=w/'B5.tgz';source.write_bytes(raw);source_sha=hashlib.sha256(raw).hexdigest()
    split=dict(rule='Synthetic local fixture; never use for evaluation',held_out=[
        'What is the closest distance between the {a} and the {b}, in {u}?',
        'Give the minimum separation from the {a} to the {b} in {u}.'])
    dump(w/'split.json',split)
    original=Path(a.generator).read_text()
    old="SRC = '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/in/out/qsets/R0_QUESTIONS_dev_f32.jsonl'"
    assert original.count(old)==1
    gen=original.replace(old,'SRC = '+repr(str(src/'inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl')))
    (w/'make_synthetic.py').write_text(gen)
    subprocess.run(['/usr/bin/python3','-B',str(w/'make_synthetic.py'),str(w/'split.json'),str(w/'synthetic.json')],check=True)
    source_items=read(w/'synthetic.json');rooms=read(src/'items/room134.json');dev=set((src/'auth/R0_DEV_ROOMS.txt').read_text().splitlines())
    m=make_items_d.make(source_items,rooms,dev);assert make_items_d.make(source_items['items'],rooms,dev)==m
    dump(w/'dist580.json',m)
    os.environ['KROOT']=str(w/'K');reports={}
    for step in (200,544):
        stage=w/('D'+str(step));binding=HERE/('bind_D%d.json'%step)
        # Build logs are bounded test outputs, not workspace files.
        with (w/('build%d.log'%step)).open('w') as out:
            subprocess.run(['/usr/bin/python3','-B',str(HERE/'build_d.py'),str(stage),str(source),source_sha,
                            str(w/'dist580.json'),str(binding)],stdout=out,check=True)
        report=read(stage/'BUILD.json')['D'];reports[str(step)]=report
        package=w/('package'+str(step));extract((Path(report['delivery_dir'])/'1.tgz').read_bytes(),package)
        target=w/('src'+str(step));extract((package/'0.tgz').read_bytes(),target)
        assert (target/'items/room134.json').read_bytes()==(src/'items/room134.json').read_bytes()
        before=dict((mi.name,d) for mi,d in read_tar(payload.read_bytes()))
        after=dict((mi.name,d) for mi,d in read_tar((package/'0.tgz').read_bytes()))
        changed={n for n in before if before[n]!=after[n]}
        assert changed=={'9.json','h1eval/items.py','h1eval/h10/parity_adapter.py'}
        assert after.keys()-before.keys()=={'items/dist580.json','h1eval/dist580.py'}
        allowed={'0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','PACKAGE.json','SUBMIT.cmd','a/0.json','a/5.py','a/6.py'}
        if step==544:allowed.add('a/4.py')
        assert {n for n in names if (package/n).read_bytes()!=(b5/n).read_bytes()}==allowed
        b=read(binding);plan=read(target/'9.json');assert plan['export_binding']=={k:b[k] for k in build_d.KEYS}
        fill=module(package/'a/4.py','fill'+str(step));assert fill.reviewed_binding()==dict(plan['export_binding'],archive_bytes=b['archive_bytes'],archive_sha256=b['archive_sha256'])
        receipt=w/('receipt%d'%step);receipt.write_text('%s %s %s\n'%(b['object'],b['archive_bytes'],b['archive_sha256']))
        fill.receipt_review(receipt)
        # Exercise mstop-object/m544-member binding without fabricating archive bytes.
        from types import SimpleNamespace
        arg=SimpleNamespace(object=b['object'],step=b['step'],lineage=b['lineage'])
        artifact=dict(step=b['step'],**{k:b[k] for k in ('base_identity','config_sha256','frame_layout')})
        for n,tail in (('heads','heads.pt'),('full_weights','full_weights/full_weights.json')):
            artifact[n]={'path':'/runs/'+b['run']+'/'+b['member_directory']+'/'+tail}
        export={'member_directory':b['member_directory']};archive={'sha256':b['archive_sha256'],'parts':b['parts']}
        prep={k:{'sha256':h} for k,h in b['preparation_sha256'].items()}
        fill.bind_review(arg,export,artifact,archive,prep,fill.reviewed_binding())
        arg.step+=1
        try:fill.bind_review(arg,export,artifact,archive,prep,fill.reviewed_binding())
        except ValueError:pass
        else:raise AssertionError('Accepted wrong export step')
    # Compile every changed Python member with the actual 3.6 interpreter.
    paths=[p for p in HERE.glob('*.py')]+[w/'package200'/n for n in ('3.py','a/4.py','a/5.py','a/6.py')]+[w/'package544/a/4.py']
    paths += [w/'src200'/n for n in ('h1eval/items.py','h1eval/h10/parity_adapter.py','h1eval/dist580.py')]
    dump(w/'compile_paths.json',[str(p) for p in paths])
    script="import json,py_compile,sys;from pathlib import Path\nw=Path(sys.argv[1]);[(py_compile.compile(p,cfile=str(w/('compile%d.pyc'%i)),doraise=True)) for i,p in enumerate(json.loads((w/'compile_paths.json').read_text()))]"
    subprocess.run(['/usr/bin/python3','-B','-c',script,str(w)],check=True)
    target=w/'src200';sys.path[:0]=[str(target),str(target/'b'),str(target/'tree')]
    from h1eval.items import load_manifest,read_contract
    sys.path.insert(0,str(target/'b'))
    real=load_manifest(target/'items/dist580.json');assert real==m
    from h1eval.h10.parity_adapter import map_items
    settings={'frames_root':str(w/'no_images')};mapped,mapping=map_items(real['items'],settings,name='dist580')
    assert len(mapped)==len(mapping['items'])==580 and len(settings['frames_json']['captures'])==98
    assert all(mapped[k]['answer']==v['answer'] for k,v in {r['id']:r for r in m['items']}.items())
    read_contract(real,['tower'],[{'name':'none'}],'object_abs_distance')
    try:read_contract(real,['own'],[{'name':'none'}],'object_abs_distance')
    except ValueError:pass
    else:raise AssertionError('Accepted own arm')
    # Verify 98 capture identities, independent of question wording and answer units.
    captures={(r['native'],tuple(r['frame_indices']),tuple(r['frame_paths'])) for r in real['items']};assert len(captures)==98
    for edit in ('frame','pair','unit','room','hash'):
        bad=copy.deepcopy(real)
        if edit=='frame':bad['items'][0]['frame_indices'][0]+=1
        if edit=='pair':bad['items'][0]['twin_id']=bad['items'][0]['id']
        if edit=='unit':bad['items'][0]['unit']='km'
        if edit=='room':bad['items'][0]['room_key']='scannet/scene99999'
        bad['item_set_sha256']=make_items_d.digest(bad['items']) if edit!='hash' else '0'*64
        dump(w/'bad.json',bad)
        try:load_manifest(w/'bad.json')
        except (AssertionError,ValueError,KeyError):pass
        else:raise AssertionError('Accepted '+edit)
    op=module(w/'package200/a/6.py','operator_d')
    conf=dict(package=str(target),output=str(w/'rehearsal'),settings=str(w/'settings.json'),plan_sha256='a'*64,
              inputs_sha256='b'*64,operator_sha256=hashlib.sha256((w/'package200/a/6.py').read_bytes()).hexdigest(),
              python=sys.executable,export=str(w/'export'),binding=str(w/'binding'),export_pin=str(w/'pin'),device='cpu',prefix='test')
    chosen=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],
                perception_memo_verify_ids=[],save_own_depth=False,types=['object_abs_distance'])
    dump(w/'settings.json',chosen)
    assert op.COUNTS==(0,0,0,580,0) and op.SCHEDULE==((0,3),)
    configs=op.prepare(conf);assert configs[0]['items']==str(target/'items/dist580.json')
    assert op.descriptors(str(target))[0]['expected']==580
    rehearsal=op.rehearsal(conf);assert rehearsal[0]['types']==['object_abs_distance'] and rehearsal[0]['expected']==580
    memory=op.memory_bound();assert memory['fits'] and memory['reads'][0]['captures']==98
    assert not op.memory_bound(allocation_bytes=1)['fits']
    summary=op.run(conf,100000,['0'],runner=lambda *a,**k:dict(completed=580,complete=True,failure=None),clock=lambda:0)
    assert summary['expected']==summary['completed']==580 and summary['complete']
    dump(w/'PLANNING.json',dict(rehearsal=rehearsal,memory=memory,summary=summary,mapped=len(mapped),captures=len(captures)))
    with (w/'score.log').open('w') as out:
        subprocess.run([sys.executable,'-B',str(HERE/'score_d.py'),str(target/'items/dist580.json'),'--src',str(target),
                        '--self-test',str(w/'synthetic_returns'),'--out',str(w/'scores.json')],stdout=out,check=True)
    assert read(w/'scores.json')['passed']
    result=dict(passed=True,source_member_bytes_verified=len(names),compile_files=len(paths),bindings=[200,544],
                synthetic_item_count=580,manifest_accepted=True,mapping_count=len(mapped),captures=len(captures),
                planning=True,scorer_self_test=True,negative_tests=['frame','pair','unit','room','hash','arm','export_step'],
                work=str(w),builds={k:{x:v[x] for x in ('token','delivery_dir','delivery_sha256','budget_gpu_seconds','walltime','budget_fits')} for k,v in reports.items()})
    dump(w/'TEST_RESULTS.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
