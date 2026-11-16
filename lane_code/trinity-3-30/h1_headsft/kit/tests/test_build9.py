"""Build 9 coverage, score provenance, opacity, reserve, and repin gates."""
import copy
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from orchard_h10.common import ORDER, FORBIDDEN, opaque, sha, write, read_config

K=Path(__file__).resolve().parents[1]
OLD=K/'tmp/b8/rehearsal/a6e2bacffbbd5'


@pytest.mark.parametrize('fault',[None,'missing','duplicate','foreign','binding','identity'])
def test_type_merge(tmp_path,monkeypatch,fault):
    import h1eval.h10.merge as m
    source=OLD/'r/metadata';dest=tmp_path/'metadata'
    # Only small journal records and binding receipts; never copy a tree or kit.
    write(dest/'IDENTITY.json',json.loads((source/'IDENTITY.json').read_text()))
    roots=[]
    for t in range(5):
        for i in range(2):
            root=dest/'journals'/str(t)/str(i);roots.append(root)
            for name in ('environment.json','items.jsonl'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((source/'journals'/str(t)/str(i)/name).read_bytes())
    b=json.loads((roots[0]/'environment.json').read_text())['binding']
    monkeypatch.setattr(m,'code_hash',lambda *a:b['evaluator_code_sha256'])
    if fault=='missing':roots.pop()
    elif fault in ('duplicate','foreign'):
        p=roots[0]/'items.jsonl';rows=p.read_text().splitlines();r=json.loads(rows[0])
        if fault=='foreign':r['id']='not_in_plan'
        p.write_text('\n'.join(rows+[json.dumps(r)])+'\n')
    elif fault=='binding':
        p=roots[-1]/'environment.json';v=json.loads(p.read_text());v['binding']['export_sha256']='bad';write(p,v)
    elif fault=='identity':
        p=dest/'IDENTITY.json';v=json.loads(p.read_text());v['cards']=4;write(p,v)
    if fault:
        with pytest.raises(ValueError):m.merge_types(roots,tmp_path/'out',OLD/'items.json')
        assert not (tmp_path/'out').exists()
    else:
        assert m.merge_types(roots,tmp_path/'out',OLD/'items.json')['records']==110
        curve=json.loads((tmp_path/'out/curve.json').read_text())
        assert 'task_accuracy' in curve['per_type'][ORDER[0]]['own']['none']['M2']


def test_journal_score_and_separate_call_rates():
    from h1eval.scorers import accuracy
    from h1eval.runner import measure,table
    from h1eval.statistics import aggregate
    item=dict(question_type='camera_displacement',question='How far in meters from frame 1 to frame 2?',ground_truth='1')
    output=dict(text='</think><answer>1</answer>',finish='eos',calls=[
        dict(call='<move from=1 to=2>',response='error: no pose',served=False)])
    assert accuracy(output,item)['task_accuracy']==1.
    output['scores']={'answer':.3}
    v=accuracy(output,item)
    assert v['task_accuracy']==.3 and v['unserved_rate']==v['error_rate']==1.
    row=dict(id='a',room_key='a',type=item['question_type'],arm='own',mode='none',output=output,measurements=measure(output,item))
    stats=aggregate([row])[item['question_type']]['own']['none']['M2']
    assert stats['task_accuracy']['value']==.3 and stats['error_rate']['value']==1.
    text=table([row]);assert 'Unserved calls' in text and 'Error calls' in text and '0.3000' in text


def test_opaque_package_and_worker(tmp_path):
    from orchard_h10.runner import commands
    for word in ('g3t','camera','benchmark','parity','devs1','r0','scannetpp','displacement','rotation','distance','room','direction','own','split'):
        assert word in FORBIDDEN
        with pytest.raises(ValueError):opaque(['/tmp/'+word.upper()])
    package=K/'orchard_h10/package'
    for p in package.iterdir():
        if p.is_file() and p.suffix!='.tgz':opaque([p.name,p.read_text()])
    cfg=dict(package='/scratch/jjyeung/ab12cd34ef56/p',output=str(tmp_path),python='/usr/bin/python3',device='cpu')
    for kind in ORDER:
        argv=commands(cfg,kind,0,['0'],10,20);opaque(argv)
        assert argv[1:]==['-B','-I','5.py',str(ORDER.index(kind))+'0.json']
        c=json.loads((tmp_path/'metadata/a'/argv[-1]).read_text())
        assert type(c['type']) is int
    assert (tmp_path/'metadata/a').stat().st_mode & 0o777==0o700
    cfg=read_config(package)
    assert cfg['order']==list(ORDER)
    assert cfg['payload_pins']['b/e2e_reader/grounding.py']['sha256'].startswith('47ab8435')


def test_process_guard(monkeypatch,tmp_path):
    import subprocess
    from orchard_h10.common import install_process_guard
    seen=[]
    monkeypatch.setattr(subprocess,'Popen',lambda a,*x,**k:seen.append((a,k)))
    install_process_guard(tmp_path)
    subprocess.Popen(['/usr/bin/python3','-I','5.py','0.json'],env={'A':'1'})
    assert len(seen)==1
    for argv,env in [(['python','-m','h1eval.h10.launch'],{}),(['python','5.py'],{'A':'own'})]:
        with pytest.raises(ValueError):subprocess.Popen(argv,env=env)
    assert len(seen)==1


def test_reserve_set_and_guards(tmp_path):
    from h1eval.items import load_manifest,build_r0dev,manifest,read_contract,encoded
    m=load_manifest(K/'items/r0dev.json');assert m==build_r0dev()
    assert m['name']=='r0dev_f32' and m['development_only']
    assert m['count']==2169 and m['r0_check']['found']==2169
    assert len({r['room_key'] for r in m['items']})==98
    assert m['per_type']=={k:v['n_dev'] for k,v in m['constants'].items()}
    assert len({r['id'] for r in m['items']})==2169
    assert len({r['qid'] for r in m['items']})==2167
    assert all(len(r['frame_indices'])==32 for r in m['items'])
    read_contract(m,['own'],[{'name':'none'}])
    for arms,modes,types in [(['tower'],[],None),(['own'],[{'name':'scale_scene'}],None),(['own'],[],ORDER[0])]:
        with pytest.raises(ValueError):read_contract(m,arms,modes,types)
    with pytest.raises(ValueError,match='overlap R0'):manifest('devs1_routed',m['items'][:1],K/'items/r0dev.json')
    bad=copy.deepcopy(m);bad['development_only']=False
    p=tmp_path/'0.json';p.write_bytes(encoded(bad))
    with pytest.raises(ValueError,match='development only'):load_manifest(p)


def test_optional_phase_skip_and_standin(tmp_path,monkeypatch):
    from orchard_h10 import runner as r
    from h1eval import items as I
    from h1eval.modes import plan
    from h1eval.cli import modes
    from h1eval.modes import DEFAULT_MODES
    raw=I.load_manifest(K/'items/devs1_routed.json')
    base=[v for t in ORDER for v in [x for x in raw['items'] if x['question_type']==t][:2]]
    extra=I.load_manifest(K/'items/r0dev.json')
    reserve=[next(v for v in extra['items'] if v['question_type']==t) for t in extra['per_type']]
    def load(path):return dict(items=reserve if str(path).endswith('8.json') else base)
    monkeypatch.setattr(I,'load_manifest',load)
    cfg=dict(package=str(K),output=str(tmp_path/'r'),python='/usr/bin/python3',device='cpu',plan_sha256='a'*64,
             export='x',settings='x',binding='x')
    seen=[]
    def launch(argv,**kw):
        opaque(argv);seen.append(argv)
        c=json.loads((Path(kw['cwd'])/argv[-1]).read_text());t=c['type'];i=c['index'];n=c['cards']
        chosen=[v for v in base[i::n] if v['question_type']==ORDER[t]] if t<5 else reserve[i::n]
        wanted=plan(chosen,['own'],[{'name':'none'},*modes(DEFAULT_MODES)] if t<5 else [{'name':'none'}])
        root=Path(cfg['output'])/'metadata/journals'/str(t)/str(i);root.mkdir(parents=True,exist_ok=True)
        (root/'items.jsonl').write_text(''.join(json.dumps(dict(id=a,arm=b,mode=d,complete=True,seconds=.001,output={'text':'stand-in'}))+'\n' for a,b,d in sorted(wanted)))
        return type('Done',(),{'wait':lambda self:0})()
    no=r.run(cfg,['0','1'],time.time()+3600,launcher=launch)
    assert no['complete'] and len(seen)==10
    receipt=tmp_path/'8.json';write(receipt,dict(verified=True,archive_sha256='f'*64))
    cfg=dict(cfg,output=str(tmp_path/'s'),optional=dict(items='8.json',receipt=str(receipt),sha256=sha(receipt)))
    seen.clear();yes=r.run(cfg,['0','1'],time.time()+3600,launcher=launch)
    assert yes['complete'] and len(seen)==12 and yes['expected']==no['expected']+9
    opaque([(Path(cfg['output'])/'STEPS.jsonl').read_text()])
    cfg=dict(cfg,output=str(tmp_path/'guard'));seen.clear()
    assert r.run(cfg,['0','1'],time.time(),launcher=launch)['stopped'] and not seen
    cfg['optional']['sha256']='0'*64
    with pytest.raises(ValueError):r.optional_ready(cfg)


def test_repin_inventory_and_hashes(tmp_path):
    from orchard_h10.build import repin_reader
    p=tmp_path/'grounding.py';p.write_text('value=2\n')
    spec=dict(source=str(tmp_path),sha256={p.name:sha(p)})
    assert repin_reader(spec,{p.name:b'value=1\n'})[p.name]==p.read_bytes()
    spec['sha256'][p.name]='0'*64
    with pytest.raises(ValueError,match='hash'):repin_reader(spec,{p.name:b''})
    spec['sha256'][p.name]=sha(p);(tmp_path/'foreign.py').write_text('')
    with pytest.raises(ValueError,match='inventory'):repin_reader(spec,{p.name:b''})


def test_allocation_export_cache(tmp_path,monkeypatch):
    import h1eval.cli as c
    root=tmp_path/'e';root.mkdir();p=root/'0.bin';p.write_bytes(b'1')
    cache=tmp_path/'a/7.json';calls=[];original=c.sha
    monkeypatch.setattr(c,'sha',lambda p:(calls.append(str(p)),original(p))[1])
    first=c.export_hash(root,cache,'1');assert len(calls)==1
    assert c.export_hash(root,cache,'1')==first and len(calls)==1
    p.write_bytes(b'2')
    assert c.export_hash(root,cache,'1')!=first and len(calls)==2
    c.export_hash(root,cache,'2');assert len(calls)==3
