from pathlib import Path
import ast,base64,difflib,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,time,traceback
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4z11';sys.path.insert(0,str(L/'out'))
import arm_launch as launch
A=launch.arm;J=A.J
T=Path(tempfile.mkdtemp(prefix='.t_',dir=L));os.chmod(T,0o700)
attic=L/'attic/build24m4z11';attic.mkdir(parents=True,exist_ok=True)
results=[];runs=[]
def write(p,v):launch.write(p,v)
def record(case,fn):
    start=time.monotonic()
    try:
        value=fn();results.append(dict(case=case,status='OK',seconds=round(time.monotonic()-start,3),details=value))
        print(case,'OK',flush=True)
    except BaseException:
        error=traceback.format_exc();(D/(case+'.failure.log')).write_text(error)
        results.append(dict(case=case,status='ERROR',output=error));print(error,flush=True);raise

def checked_run(args,label):
    p=subprocess.run(args,cwd=L,capture_output=True,text=True)
    (D/(label+'.log')).write_text(p.stdout+p.stderr)
    if p.returncode:raise AssertionError((p.returncode,p.stdout,p.stderr))
    return json.loads(p.stdout.splitlines()[-1])

protected=[L/'work/tree_r1',L/'work/tree_r1c',L/'work/tree_r1_base',L/'out/kit_qd',L/'out/rcj',L/'out/kit_n',L/'out/kit_n_go',L/'work/build24/kits/q']
before={str(p.relative_to(L)):launch.inventory(p) for p in protected if p.exists()}
verdict=T/'v.txt';verdict.write_text('Synthetic offline fixture only: '+'P'+'ASS\n'+launch.SELECTION+'\n'+launch.GENERATED+'\n')
try:
    for stop in ('3600','6000'):
        def full(stop=stop):
            v=checked_run(['nice','-n','10','bash',str(L/'out/arm_launch.sh'),str(verdict),stop],'full_'+stop)
            runs.append(Path(v['output']));write(D/('FULL_'+stop+'.json'),v);return v
        record('full_'+stop,full)
    def refuses(label,expected,fn):
        try:fn()
        except Exception as e:
            output=traceback.format_exc();(D/(label+'.log')).write_text(output)
            assert expected in str(e),(label,expected,str(e))
            return dict(refusal=str(e),log=str((D/(label+'.log')).relative_to(L)))
        raise AssertionError('accepted '+label)
    def launch_call(v=verdict,seconds='3600',evidence=launch.E):return launch.prepare(v,seconds,evidence=evidence,parent=T)
    record('missing_verdict',lambda:refuses('missing_verdict','R1_REVIEW_VERDICT_MISSING',lambda:launch_call(T/'missing.txt')))
    no=T/'no.txt';no.write_text('HOLD\n'+launch.SELECTION+'\n'+launch.GENERATED+'\n')
    record('without_pass',lambda:refuses('without_pass','R1_REVIEW_VERDICT_NOT_PASS',lambda:launch_call(no)))
    wrong_s=T/'wrong_s.txt';wrong_s.write_text('P'+'ASS\n'+'e'*64+'\n'+launch.GENERATED+'\n')
    record('wrong_selection',lambda:refuses('wrong_selection','R1_REVIEWED_SELECTION_DIFFERS',lambda:launch_call(wrong_s)))
    wrong_r=T/'wrong_r.txt';wrong_r.write_text('P'+'ASS\n'+launch.SELECTION+'\n'+'e'*64+'\n')
    record('wrong_regenerated',lambda:refuses('wrong_regenerated','R1_REVIEWED_REGENERATED_DIFFERS',lambda:launch_call(wrong_r)))
    for filename,code,label in [('receipt.json','R1_RECEIPT_BYTES_DIFFERS','altered_receipt'),('db_bytes.json','R1_DB_BYTES_DIFFERS','altered_db_bytes')]:
        e=T/label;e.mkdir()
        for n in ('receipt.json','routing_selection.json','db_bytes.json'):shutil.copyfile(launch.E/n,e/n)
        with (e/filename).open('ab') as f:f.write(b' ')
        record(label,lambda e=e,code=code,label=label:refuses(label,code,lambda:launch_call(evidence=e)))
    for i,s in enumerate(('3599','3601','11100','-6000','6000.0','６０００')):
        record('invalid_stop_'+str(i),lambda s=s,i=i:refuses('invalid_stop_'+str(i),'expected ',lambda:launch_call(seconds=s)))
    # Exercise native failures directly as well as the wrapper's byte pins.
    kwargs=dict(reviewed_selection_sha256=launch.SELECTION,reviewed_regenerated_sha256=launch.GENERATED,review_verdict=verdict,regenerated_receipt_path=launch.E/'receipt.json',base_path=L/'work/build24m4m/inputs'/launch.BASE,kit_layout=runs[0]/'layout.json')
    def direct(label,code,changes=None,metadata=None):
        args=dict(kwargs);args.update(changes or {})
        return refuses(label,code,lambda:A.apply(launch.E/'routing_selection.json',metadata or launch.E/'db_bytes.json',T/label,**args))
    record('native_wrong_selection',lambda:direct('native_wrong_selection','R1_REVIEWED_SELECTION_DIFFERS',dict(reviewed_selection_sha256='e'*64,review_verdict=wrong_s)))
    record('native_wrong_regenerated',lambda:direct('native_wrong_regenerated','R1_REVIEWED_REGENERATED_DIFFERS',dict(reviewed_regenerated_sha256='e'*64,review_verdict=wrong_r)))
    record('native_altered_receipt',lambda:direct('native_altered_receipt','E10:',dict(regenerated_receipt_path=T/'altered_receipt/receipt.json')))
    bad=T/'bad_db.json';obj=json.loads((launch.E/'db_bytes.json').read_bytes());obj['files'][0]['size']=0;write(bad,obj)
    record('native_altered_db_bytes',lambda:direct('native_altered_db_bytes','R1_DATABASE_METADATA_SIZE_INVALID',metadata=bad))
    def replay():
        report=[]
        Y=L.parent/'w24y2';baseline={'q':Y/'work/build24/kits/q','n':Y/'work/build24/kits/n','n_go':Y/'out/kit_n_go'}
        for run in runs:
            inventories={n:launch.inventory(p) for n,p in baseline.items()}
            for name in ('UPLOADS_ARMED','UPLOADS_ARMED_GO'):
                m=json.loads((run/(name+'.json')).read_text());listed=(run/(name+'.list')).read_text().splitlines()
                assert listed==[r['name'] for r in m['files']]
                assert name!='UPLOADS_ARMED' or not any(n.startswith('n_go/') for n in listed)
                assert name!='UPLOADS_ARMED_GO' or all(n.startswith('n_go/') for n in listed)
                for row in m['files']:
                    p=Path(row['local_path']);assert J.sha(p)==row['sha256'];assert p.stat().st_size==row['bytes'];assert format(p.stat().st_mode&511,'04o')==row['mode']
                    n,rel=row['name'].split('/',1)
                    if n=='u':assert row['sha256']==launch.SELECTION;continue
                    old=inventories[n].get(rel);assert row['baseline_sha256']==(old['sha256'] if old else None)
                    inventories[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
            for n,inv in inventories.items():assert inv==launch.inventory(run/'armed/kits'/n),(run,n)
            report.append(dict(run=str(run),complete_bytes_and_modes=True,ordinary_go_separate=True))
        return report
    record('overlay_replay',replay)
    def planner():
        reports=[]
        for index,run in enumerate(runs):
            for name in ('q','n_go'):
                root=T/('planner_'+str(index)+'_'+name);root.mkdir();kit=root/'k';shutil.copytree(run/'armed/kits'/name,kit)
                pool=root/'pool';(pool/'u').mkdir(parents=True);shutil.copyfile(launch.E/'routing_selection.json',pool/'u'/launch.SELECTION)
                spec=J.load(kit/'k/p.json');spec['n_root']=str(pool);A.cap(kit/'k/p.json',spec);A.reseal(kit)
                # Run the delivered planner in an isolated interpreter. Only n_root
                # in this private test copy changes; selection_pin is unmodified.
                code="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from pl import selection_pin;import json;pin,source=selection_pin(Path(sys.argv[2]));print(json.dumps(dict(pin=pin,source=str(source))))"
                label='planner_'+str(index)+'_'+name
                value=checked_run([sys.executable,'-I','-s','-B','-c',code,str(kit/'b'),str(kit)],label)
                assert value['pin']['sha256']==launch.SELECTION
                assert J.sha(Path(value['source']))==launch.SELECTION
                reports.append(dict(case=label,authenticated=True,log=str((D/(label+'.log')).relative_to(L))))
        return reports
    record('planner_selection_pin',planner)
    def discovery():
        qp=L.parent/'w24z8b/out/kit_qdp';launch.verify(qp,'1138611744d623dce116a7a104a5682ae7a6e889e3155059a92d20adc364ba83')
        q=runs[0]/'armed/kits/q';diffs={}
        for rel in ('k/h.json','k/r.json','k/p.json','k/a.json'):
            a,b=J.load(q/rel),J.load(qp/rel)
            diffs[rel]={k:dict(armed=a.get(k),discovery=b.get(k)) for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)}
        assert J.load(q/'k/h.json')['routing_selection']==J.load(qp/'k/h.json')['routing_selection']
        write(D/'DISCOVERY_DIFF.json',diffs)
        return dict(routing_selection_equal=True,differing_keys={r:list(v) for r,v in diffs.items()},log='work/build24m4z11/DISCOVERY_DIFF.json')
    record('discovery_comparison',discovery)
    def code_path():
        old=(attic/'arm_routing.py').read_text();new=(L/'out/arm_routing.py').read_text()
        start='    selection_hash=';end='    origins='
        assert old[old.index(start):old.index(end)]==new[new.index(start):new.index('    layout=')]
        old_tree=ast.parse(old);new_tree=ast.parse(new)
        def body(tree):
            f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='apply')
            out=[]
            for n in f.body:
                if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'layout','origins','baseline_files','baseline_seals','baseline_label','baseline','manifest'}:continue
                out.append(ast.dump(n,include_attributes=False))
            return out
        assert body(old_tree)==body(new_tree)
        return dict(verdict_and_validation_block_byte_identical=True,remaining_apply_statements_ast_identical=True,diff='work/build24m4z11/ARM_ROUTING.diff')
    record('helper_code_path',code_path)
    def protection():
        after={str(p.relative_to(L)):launch.inventory(p) for p in protected if p.exists()};assert before==after
        return dict(files=sum(map(len,before.values())),roots=list(before),bytes_and_modes_unchanged=True)
    record('protected_files',protection)
finally:
    # Keep synthetic verdicts and all helper manifests out of out/ and work/.
    for run in runs:
        if run.exists():run.rename(attic/run.name)
    T.rename(attic/T.name)
    write(D/'TEST_RESULTS.json',dict(status='OK' if results and all(r['status']=='OK' for r in results) else 'ERROR',tests=results,fixture_attic=str(attic/T.name),run_attic=[str(attic/r.name) for r in runs]))
