from pathlib import Path
import copy, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys, time

L=Path(__file__).resolve().parents[2];D=L/'work/build24m4s';T=Path(os.environ.get('FIX_SOURCE',str(L/'work/tree_r1c')))
sys.path[:0]=[str(T),str(L/'out/kit_qd/b')]
import z
from student_pilot.p3_provenance import file_pin, load, pinned
from student_pilot.s1_exclusions import Exclusions
from student_pilot import r2_scene_bindings as S

NS=Path('/tmp/q_22c714e1');Z=NS/('p' if os.environ.get('FIX_MODE')=='q' else 'z')

def driver(mode):
    import sc
    import student_pilot
    assert Path(student_pilot.__file__).resolve().parent.parent == T.resolve()
    if mode=='r':assert not (Z/'s').exists()
    from student_pilot.r1_persisted import scope
    from student_pilot.s1_pool import selected_rows
    value=load(Z/'i/value.json');cfg=value['config'];sources=value['paths']
    commands=[];real_run=subprocess.run
    def record(command,**kwargs):
        commands.append(command)
        return real_run(command,**kwargs)
    sc.subprocess.run=record
    result=sc.bind(cfg,sources,Z/'i',Z/'q',L/'out/kit_qd')
    assert result==Z/'i/sc/sc'
    (Z/'q').mkdir()
    # Open the same output under its future logical name for native consumers.
    cmd=[shutil.which('bwrap'),'--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(Z/'i'),str(Z/'i'),'--bind',str(Z/'i/sc'),str(Z/'q'),
         sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'compare',mode]
    z.write(Z/'i/config.json',cfg)
    p=real_run(cmd,capture_output=True,text=True)
    print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
    if p.returncode:raise RuntimeError(p.stderr)
    z.write(Z/'i/commands.json',commands)

def compare(mode):
    from student_pilot.r1_persisted import scope
    from student_pilot.s1_pool import selected_rows
    from student_pilot.s1_scene_census import SceneCoverageError, compare as native_compare
    value=load(Z/'i/value.json');cfg=load(Z/'i/config.json')
    with scope(value['paths']):
        S.verify(cfg)
        result=load(Z/'q/sc/2.json');pool=load(pinned(result['pool_selection']))
        report=pool['source_scene_exclusions']
        checks={n:native_compare(report['expected'][n],report['sources'][n],report['files'],n) for n in value['names']}
        assert checks=={n:'PASS' for n in value['names']}
        selected={n:[r['qid'] for r in selected_rows(result['pool_selection'],n)] for n in value['names']}
        assert all(len(v)==1 for v in selected.values()),selected
        # Native compare must still reject a deliberately reintroduced held row.
        rule=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
        for name in value['names']:
            source='pool/'+name;rule.counts(source)
            rule.expected[source]=dict(schema='s1-scene-census-v1',method='subset-of-independently-checked-pool-selection',files=rule.files,rows=None,counts=dict(dev_matches=0,benchmark_matches=0,overlap_matches=0))
            for row in selected_rows(result['pool_selection'],name):rule.keep(row,source)
        rule.report()
        ds,scene=value['held'].split('/',1)
        rule.keep(dict(qid='bad',dataset=ds,scene=scene),'pool/'+value['names'][0])
        try:rule.report()
        except SceneCoverageError as e:
            assert 'dev_matches' in str(e);refusal=str(e)
        else:raise AssertionError('census accepted leaked row')
        # Reports of all other streams still match direct native regeneration.
        spec=load(Z/'i/sc.json')['spec'];other={}
        for name,part in spec['sources'].items():
            pin=S.rebuild_receipt(dict(part,source=name),cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'],Z/'i'/('direct_'+name))
            a=load(pinned(pin))['source_scene_exclusions']
            b=load(pinned(result['receipts'][name]))['source_scene_exclusions']
            assert json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
            other[name]='PASS'
    z.write(Z/'i/result.json',dict(status='PASS',mode=mode,pool_compare=checks,selected=selected,other_streams_byte_identical=other,negative_refusal=refusal,compare_sha256=z.sha(T/'student_pilot/s1_scene_census.py')))
    print('CENSUS_COMPARE_PASS '+mode,flush=True)

def outer(mode):
    if mode=='q':
        driver(mode);return
    from unittest.mock import patch
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('rcj_fixture',L/'out/rcj/x.py')
    x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
    root=Path(os.environ['FIX_ROOT'])
    import pl
    def payload(kit,resolved,planned,**kwargs):
        assert planned==Z and planned.is_dir() and not (planned/'s').exists()
        shutil.copytree(root/'seed/i',planned/'i')
        z.write(root/'state.json',dict(z_exists=Z.is_dir(),z_s_exists=(Z/'s').exists(),trainer=str(T),R1_TRAINER=os.environ['R1_TRAINER'],TRAINER=os.environ['TRAINER']))
        driver(mode)
        z.write(planned/'plan.json',dict(entries={},generated={}))
        return {},{},SimpleNamespace(close=lambda:None)
    inputs=SimpleNamespace(spec=dict(namespace=str(NS)),records=[],sources={},archives={})
    with patch.object(x,'Inputs',return_value=inputs),patch.object(pl,'plan_payload',side_effect=payload):
        x.plan_r(L/'out/kit_qd',root,'123')

def launch(root,instrument):
    from unittest.mock import patch
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('rcj_capture',L/'out/rcj/x.py')
    x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
    z.write(root/'mode.json',dict(mode='r'))
    z.write(root/'resolved.json',dict(parts=[]))
    z.write(root/'env.json',dict(venv=str(root/'v'),scratch=str(root/'g'),paths=[str(L/'out/kit_qd/b'),str(root/'cl'),str(root/'cl/site_alias')],record=str(root/'e.json')))
    class Pins:
        load=staticmethod(z.load)
        checked=staticmethod(lambda p,h:Path('/project/community/jjyeung/cp4tk_rt/kit/bwrap'))
    with patch.object(x,'attach',return_value=Pins),patch.object(x.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
        x.launch(L/'out/kit_qd',root,'123',action='plan')
    original=run.call_args.args[0];env=run.call_args.kwargs['env']
    cmd=list(original);cmd[0]=shutil.which('bwrap')
    # Local runtime adapters expose the fixture and Trinity interpreter.
    ix=cmd.index('--bind')
    adapters=[]
    for path in dict.fromkeys((str(L),sys.prefix,sys.base_prefix)):
        adapters+=['--ro-bind',path,path]
    cmd[ix:ix]=adapters
    tail=cmd.index('--chdir')+2
    cmd[tail:]=[sys.executable,'-s','-B',str(Path(__file__).resolve()),'outer','r']
    env.update(FIX_MODE='r',FIX_ROOT=str(root),FIX_SOURCE=str(root/'c'))
    z.write(root/'launch.json',dict(original=original,command=cmd,env={k:v for k,v in env.items() if k in ('PATH','FIX_ROOT','FIX_MODE','FIX_SOURCE')},adapters=adapters))
    return cmd,env

def prepare():
    F=D/('real_'+str(time.time_ns()));F.mkdir()
    instrument=D/'instrument_path';instrument.mkdir(exist_ok=True)
    # Observe the real child without replacing its command or any native function.
    (instrument/'sitecustomize.py').write_text("""import atexit,errno,json,os,sys
from pathlib import Path
calls=[]
def profile(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='compare' and frame.f_code.co_filename.endswith('/s1_scene_census.py'):
  calls.append(dict(source=frame.f_locals['source'],result=arg))
sys.setprofile(profile)
def finish():
 sys.setprofile(None)
 if not calls:return
 z=Path('/tmp/q_22c714e1')/('p' if os.environ.get('FIX_MODE')=='q' else 'z')
 tests={}
 paths=[('tree',Path(os.environ['FIX_SOURCE'])/'a'),('input',z/'i/a'),('output_alias',z/'i/sc/a'),('root',Path('/a')),('kit',Path(os.environ['FIX_KIT'])/'a'),('cl',Path(os.environ['ANYHOST_JOBS'])/'a'),('alias',Path(os.environ['ANYHOST_JOBS'])/'site_alias/a')]
 value=json.loads((z/'i/value.json').read_text())
 paths.extend(('source'+str(i),Path(p)) for i,p in enumerate(sorted(set(value['paths'].values()))))
 for label,p in paths:
  try:
   with p.open('ab'):pass
  except OSError as e:
   tests[label]=e.errno
   assert e.errno==errno.EROFS,(label,e)
  else:raise AssertionError(label)
 import student_pilot
 assert Path(student_pilot.__file__).resolve().parent.parent==Path(os.environ['FIX_SOURCE']).resolve()
 (z/'q/access.json').write_text(json.dumps(dict(compare_calls=calls,readonly=tests,dev=Path('/dev/null').exists(),proc=Path('/proc/self/maps').is_file(),trainer=student_pilot.__file__)))
atexit.register(finish)
""")
    records=[]
    for mode in (('r',) if os.environ.get('FIX_BEFORE')=='1' else ('r','q')):
        base=F/mode;tmp=base/'tmp';segment='p' if mode=='q' else 'z';physical=tmp/('q_22c714e1/'+segment);inputs=physical/'i';inputs.mkdir(parents=True)
        (tmp/'q_22c714e1/u').mkdir()
        paths={}
        def pin(rel,raw):
            p=tmp/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            h=z.sha(p);logical='/tmp/'+rel;paths[h]=logical;return dict(path=logical,sha256=h)
        def jp(name,v):return pin('q_22c714e1/'+segment+'/i/'+name,(json.dumps(v,sort_keys=True)+'\n').encode())
        dev=pin('q_22c714e1/'+segment+'/i/dev.json',(T/'student_pilot/r2_dev_merged.json').read_bytes())
        old=pin('q_22c714e1/'+segment+'/i/old.json',(L/'work/build24m4n/inputs/969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986').read_bytes())
        bench=pin('q_22c714e1/u/b.json',(L/'work/build24m4n/inputs/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970').read_bytes())
        local=lambda p:dict(path=str(tmp/Path(p['path']).relative_to('/tmp')),sha256=p['sha256'])
        oldrule=Exclusions(local(old),local(bench));newrule=Exclusions(local(dev),local(bench))
        held=next(s for s in sorted(newrule.names['dev']-oldrule.names['dev']) if not oldrule.excluded(dict(scene=s)) and not newrule.matches(dict(scene=s))['benchmark'])
        sets=[];names=('T0_gaps','OTHER','U_Faithful')
        for j,name in enumerate(names):
            rows=[dict(qid=name+str(i),dataset=scene.split('/')[0],scene=scene.split('/')[1],question_type='route_planning',head_program=None,score_nomination_allowed=False,answer='A',target='<think>\nA.\n</think>\n\nA') for i,scene in enumerate(('d1/fixture_clean',held))]
            raw=gzip.compress(('\n'.join(json.dumps(r) for r in rows)+'\n').encode(),mtime=0)
            p=pin('q_22c714e1/'+segment+'/i/'+str(j)+'.gz',raw)
            sets.append(dict(name=name,status='final',files=dict(rows=dict(p,rows=2,bytes=len(raw))),rows_per_type=dict(route_planning=2)))
        lists={}
        for j,name in enumerate(('dev_s1','eval_rooms','room_release_gate')):
            p=pin('q_22c714e1/'+segment+'/i/'+str(j)+'.tsv',b'');lists[name]=dict(list=p['path'],list_sha256=p['sha256'],rows=0)
        lists['dev_s1'].update(withhold=old['path'],withhold_sha256=old['sha256']);lists['eval_rooms'].update(v2=bench['path'],v2_sha256=bench['sha256'])
        manifest=jp('manifest.json',dict(schema='dose-pool-s1-manifest-v2',sets=sets,exclusions=lists))
        receipts={}
        for j,name in enumerate(S.SOURCES):
            rows=[dict(qid=name+str(i),dataset=s.split('/')[0],scene=s.split('/')[1]) for i,s in enumerate(('d1/fixture_clean',held))]
            p=pin('q_22c714e1/'+segment+'/i/s'+str(j)+'.jsonl',('\n'.join(json.dumps(r) for r in rows)+'\n').encode())
            receipts[name]=jp('s'+str(j)+'.json',dict(rows_metadata=p,count=2))
        pose=jp('pose.json',dict(sources=[dict(receipt=receipts['pose_a2v3']),dict(receipt=receipts['pose_a3v2'])]))
        pool=jp('pool.json',dict(manifest=manifest,tokenizer=None))
        cfg=dict(streams=dict(pose=pose,vqa=receipts['vqa'],routing=receipts['camera'],pointing=receipts['pointing']),s1_routing=dict(selection=pool),remove_files=[],dev_scene_exclusions=dev,benchmark_scene_exclusions=bench,r2_all_stream_exclusions=True)
        z.write(inputs/'value.json',dict(config=cfg,paths=paths,names=names,held=held))
        root=base/'node';root.mkdir();(root/'g').mkdir();(root/'v').mkdir()
        for path in (root,L,Path(sys.prefix),Path(sys.base_prefix)):
            (root/'g'/path.relative_to('/scratch')).mkdir(parents=True,exist_ok=True)
        (root/'cl/site_alias').mkdir(parents=True)
        shutil.copyfile(instrument/'sitecustomize.py',root/'cl/site_alias/sitecustomize.py')
        env={**os.environ,'FIX_MODE':mode,'FIX_ROOT':str(root),'FIX_KIT':str(L/'out/kit_qd'),'ANYHOST_JOBS':str(root/'cl')}
        import tarfile
        archive=z.load(L/'out/kit_qd/k/a.json')['source']
        if mode=='r':
            (tmp/'q_22c714e1').rename(root/'dr');(root/'dr/z').rename(root/'seed')
            source=root/'c'
        else:
            source=physical/'s'
        with tarfile.open(L/'out/kit_qd'/archive['path']) as t:t.extractall(source,filter='data')
        if mode=='r':
            cmd,launch_env=launch(root,instrument);env.update(launch_env)
            inputs=root/'dr/z/i'
        else:
            # a.py:29-30 extracts and imports Q_NS/p/s before plan_payload.
            env.update(FIX_SOURCE='/tmp/q_22c714e1/p/s',R1_TRAINER='/home/jjyeung/6d00e578/fixture',TRAINER='/home/jjyeung/6d00e578/fixture',PYTHONPATH=str(root/'cl/site_alias'))
            cmd=[shutil.which('bwrap'),'--ro-bind','/','/','--bind',str(L),str(L),'--bind',str(tmp),'/tmp','--dev-bind','/dev','/dev','--proc','/proc',sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'outer',mode]
        p=subprocess.run(cmd,capture_output=True,text=True,env=env)
        (base/'run.log').write_text(p.stdout+p.stderr)
        records.append(dict(mode=mode,command=cmd,returncode=p.returncode,log=str((base/'run.log').relative_to(L))))
        z.write(D/('BEFORE_RUNS.json' if os.environ.get('FIX_BEFORE')=='1' else 'REAL_PATH_RUNS.json'),records)
        if os.environ.get('FIX_BEFORE')=='1':
            assert p.returncode!=0 and "Can't find source path /tmp/q_22c714e1/z/s" in p.stderr,p.stdout+p.stderr
            z.write(D/'BEFORE.json',dict(status='EXPECTED_FAILURE',records=records,stdout=p.stdout,stderr=p.stderr,state=load(root/'state.json'),launch=load(root/'launch.json'),sc_sha256=z.sha(L/'out/kit_qd/b/sc.py')))
            print(p.stdout+p.stderr);return
        assert p.returncode==0,p.stdout+p.stderr
        result=load(inputs/'result.json');access=load(inputs/'sc/access.json')
        assert access['compare_calls'] and all(v['result']=='PASS' for v in access['compare_calls']),access
        assert access['dev'] and access['proc']
        records[-1].update(result=result,access=access,inner_commands=load(inputs/'commands.json'))
        print(mode,'PASS',len(access['compare_calls']),'real child census compares',flush=True)
    z.write(D/'REAL_PATH_TESTS.json',dict(status='PASS',binary=shutil.which('bwrap'),binary_sha256=z.sha(shutil.which('bwrap')),records=records,scope='Synthetic rows; unchanged native rebuild, verify and census comparison; actual sc.bind subprocess command; private /tmp carrier and mode-r host_root outer view.'))

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    elif sys.argv[1]=='driver':driver(sys.argv[2])
    elif sys.argv[1]=='compare':compare(sys.argv[2])
    elif sys.argv[1]=='outer':outer(sys.argv[2])
