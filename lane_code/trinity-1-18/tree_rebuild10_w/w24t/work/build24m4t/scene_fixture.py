from pathlib import Path
import copy, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys, time

L=Path(__file__).resolve().parents[2];D=L/'work/build24m4t';T=L/'work/tree_r1c'
sys.path[:0]=[str(Path('/tmp/q_22c714e1/z/s') if len(sys.argv)>1 else T),str(L/'out/kit_qd/b')]
import z
from student_pilot.p3_provenance import file_pin, load, pinned
from student_pilot.s1_exclusions import Exclusions
from student_pilot import r2_scene_bindings as S

NS=Path('/tmp/q_22c714e1');Z=NS/'z'

def driver(mode):
    import sc
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
    spec=importlib.util.spec_from_file_location('rcj_fixture',L/'out/rcj/x.py')
    x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
    root=Path(sys.argv[3]);root.mkdir()
    (root/'g').mkdir();(root/'dr').mkdir();(root/'v').mkdir()
    for path in (root,L,Path(sys.prefix),Path(sys.base_prefix)):
        (root/'g'/path.relative_to('/scratch')).mkdir(parents=True,exist_ok=True)
    # Same host_root, scratch, namespace and read-only /tmp ordering as launch(r).
    cmd=[shutil.which('bwrap'),*x.host_root(),'--dev-bind','/dev','/dev','--proc','/proc',
         '--tmpfs','/project/community/jjyeung/c7d31ddd','--tmpfs','/tmp','--ro-bind',str(root/'g'),'/scratch',
         '--bind',str(root),str(root)]
    for path in (str(L),sys.prefix,sys.base_prefix):cmd+=['--ro-bind',path,path]
    cmd+=['--bind',str(root),str(root),'--bind',str(NS),str(NS),'--remount-ro','/tmp','--remount-ro','/project/community/jjyeung/c7d31ddd',
          '--setenv','PYTHONPATH',str(D/'instrument'),
          '--chdir',str(root),sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'driver',mode]
    p=subprocess.run(cmd,capture_output=True,text=True)
    z.write(root/'outer.json',dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
    if p.returncode:raise SystemExit(p.returncode)

def prepare():
    F=D/('real_'+str(time.time_ns()));F.mkdir()
    instrument=D/'instrument';instrument.mkdir(exist_ok=True)
    # Observe the real child without replacing its command or any native function.
    (instrument/'sitecustomize.py').write_text('''import atexit,errno,json,os,sys
from pathlib import Path
calls=[]
def profile(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='compare' and frame.f_code.co_filename.endswith('/s1_scene_census.py'):
  calls.append(dict(source=frame.f_locals['source'],result=arg))
sys.setprofile(profile)
def finish():
 sys.setprofile(None)
 q=Path('/tmp/q_22c714e1/z/q')
 tests={}
 for label,p in [('tree',Path('/tmp/q_22c714e1/z/s/a')),('input',Path('/tmp/q_22c714e1/z/i/a')),('output_alias',Path('/tmp/q_22c714e1/z/i/sc/a')),('other_tmp',Path('/tmp/q_22c714e1/u/a')),('root',Path('/a'))]:
  try:p.write_text('bad')
  except OSError as e:
   tests[label]=e.errno
   assert e.errno==errno.EROFS,(label,e)
  else:raise AssertionError(label)
 (q/'access.json').write_text(json.dumps(dict(compare_calls=calls,readonly=tests,dev=Path('/dev/null').exists(),proc=Path('/proc/self/maps').is_file())))
atexit.register(finish)
''')
    records=[]
    for mode in ('q','r'):
        base=F/mode;tmp=base/'tmp';physical=tmp/'q_22c714e1/z';inputs=physical/'i';inputs.mkdir(parents=True)
        (tmp/'q_22c714e1/u').mkdir()
        shutil.copytree(T,physical/'s',copy_function=os.link)
        paths={}
        def pin(rel,raw):
            p=tmp/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            h=z.sha(p);logical='/tmp/'+rel;paths[h]=logical;return dict(path=logical,sha256=h)
        def jp(name,v):return pin('q_22c714e1/z/i/'+name,(json.dumps(v,sort_keys=True)+'\n').encode())
        dev=pin('q_22c714e1/z/i/dev.json',(T/'student_pilot/r2_dev_merged.json').read_bytes())
        old=pin('q_22c714e1/z/i/old.json',(L/'work/build24m4n/inputs/969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986').read_bytes())
        bench=pin('q_22c714e1/u/b.json',(L/'work/build24m4n/inputs/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970').read_bytes())
        local=lambda p:dict(path=str(tmp/Path(p['path']).relative_to('/tmp')),sha256=p['sha256'])
        oldrule=Exclusions(local(old),local(bench));newrule=Exclusions(local(dev),local(bench))
        held=next(s for s in sorted(newrule.names['dev']-oldrule.names['dev']) if not oldrule.excluded(dict(scene=s)) and not newrule.matches(dict(scene=s))['benchmark'])
        sets=[];names=('T0_gaps','OTHER','U_Faithful')
        for j,name in enumerate(names):
            rows=[dict(qid=name+str(i),dataset=scene.split('/')[0],scene=scene.split('/')[1],question_type='route_planning',head_program=None,score_nomination_allowed=False,answer='A',target='<think>\nA.\n</think>\n\nA') for i,scene in enumerate(('d1/fixture_clean',held))]
            raw=gzip.compress(('\n'.join(json.dumps(r) for r in rows)+'\n').encode(),mtime=0)
            p=pin('q_22c714e1/z/i/'+str(j)+'.gz',raw)
            sets.append(dict(name=name,status='final',files=dict(rows=dict(p,rows=2,bytes=len(raw))),rows_per_type=dict(route_planning=2)))
        lists={}
        for j,name in enumerate(('dev_s1','eval_rooms','room_release_gate')):
            p=pin('q_22c714e1/z/i/'+str(j)+'.tsv',b'');lists[name]=dict(list=p['path'],list_sha256=p['sha256'],rows=0)
        lists['dev_s1'].update(withhold=old['path'],withhold_sha256=old['sha256']);lists['eval_rooms'].update(v2=bench['path'],v2_sha256=bench['sha256'])
        manifest=jp('manifest.json',dict(schema='dose-pool-s1-manifest-v2',sets=sets,exclusions=lists))
        receipts={}
        for j,name in enumerate(S.SOURCES):
            rows=[dict(qid=name+str(i),dataset=s.split('/')[0],scene=s.split('/')[1]) for i,s in enumerate(('d1/fixture_clean',held))]
            p=pin('q_22c714e1/z/i/s'+str(j)+'.jsonl',('\n'.join(json.dumps(r) for r in rows)+'\n').encode())
            receipts[name]=jp('s'+str(j)+'.json',dict(rows_metadata=p,count=2))
        pose=jp('pose.json',dict(sources=[dict(receipt=receipts['pose_a2v3']),dict(receipt=receipts['pose_a3v2'])]))
        pool=jp('pool.json',dict(manifest=manifest,tokenizer=None))
        cfg=dict(streams=dict(pose=pose,vqa=receipts['vqa'],routing=receipts['camera'],pointing=receipts['pointing']),s1_routing=dict(selection=pool),remove_files=[],dev_scene_exclusions=dev,benchmark_scene_exclusions=bench,r2_all_stream_exclusions=True)
        z.write(inputs/'value.json',dict(config=cfg,paths=paths,names=names,held=held))
        # This carrier only gives the fixture its exact /tmp names. Mode q has
        # no x.py outer view; mode r additionally enters that view in outer().
        cmd=[shutil.which('bwrap'),'--ro-bind','/','/','--bind',str(L),str(L),'--bind',str(tmp),'/tmp','--dev-bind','/dev','/dev','--proc','/proc',
             '--setenv','PYTHONPATH',str(instrument),sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'outer',mode,str(base/'node')]
        p=subprocess.run(cmd,capture_output=True,text=True)
        (base/'run.log').write_text(p.stdout+p.stderr)
        records.append(dict(mode=mode,command=cmd,returncode=p.returncode,log=str((base/'run.log').relative_to(L))))
        z.write(D/'REAL_BWRAP_RUNS.json',records)
        assert p.returncode==0,p.stdout+p.stderr
        result=load(inputs/'result.json');access=load(inputs/'sc/access.json')
        assert access['compare_calls'] and all(v['result']=='PASS' for v in access['compare_calls']),access
        assert access['dev'] and access['proc']
        records[-1].update(result=result,access=access,inner_commands=load(inputs/'commands.json'))
        print(mode,'PASS',len(access['compare_calls']),'real child census compares',flush=True)
    z.write(D/'REAL_BWRAP_TESTS.json',dict(status='PASS',binary=shutil.which('bwrap'),binary_sha256=z.sha(shutil.which('bwrap')),records=records,scope='Synthetic rows; unchanged native rebuild, verify and census comparison; actual sc.bind subprocess command; private /tmp carrier and mode-r host_root outer view.'))

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    elif sys.argv[1]=='driver':driver(sys.argv[2])
    elif sys.argv[1]=='compare':compare(sys.argv[2])
    elif sys.argv[1]=='outer':outer(sys.argv[2])
