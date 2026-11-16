"""Exercise production worker code with local transport and model stand-ins."""
import json
import os
from pathlib import Path
import selectors
import sys
import threading
import traceback

# Standalone CPU rehearsals never read the production secret.
import tempfile
Path('/dev/shm/b07_n7').mkdir(exist_ok=True)
_secret_dir=Path(tempfile.mkdtemp(prefix='a',dir='/dev/shm/b07_n7'))
_secret_file=_secret_dir/'secret';_secret_file.write_text('37'*32);_secret_file.chmod(0o600)
os.environ['A0_BUILD_SECRET_FILE']=str(_secret_file)

ROOT=Path(__file__).resolve().parents[1]
key=sys.argv[1]
WORK=Path(sys.argv[2]).resolve()
package=ROOT/'kit'/key
# Bound the event-loop wait in this CPU-only test environment.
select=selectors.EpollSelector.select
def bounded(self,timeout=None):return select(self,0.1 if timeout is None else min(timeout,0.1))
selectors.EpollSelector.select=bounded
source=(package/'proof/run.py').read_text()
source=source.replace("ROOT=Path(__file__).resolve().parents[1]", "ROOT=Path("+repr(str(package))+")")
source=source.replace("mode='proof'", "mode='production'")
source=source.replace("root=work/('a_'+job+'_'+token)","root=work/('a_'+job+'_'+token)\n    import xnames; xnames.install(root)")
source=source.replace("config['proof_only']=True;config['bootstrap_parent']=str(work)","config['bootstrap_parent']=str(work)\n    config.update(x0='a'*64,x1=F.sha(ap),x2=0)")
source=source.replace("pool=ROOT/'launcher/test_runs'/token/'pool';pool.parent.mkdir(parents=True)", "pool=work/'pool'")
source=source.replace("synthetic=True,rate=", "synthetic=False,rate=")
source=source.replace("trace_source=ROOT/'proof/_bootstrap_current.py'", "trace_source=work/'_bootstrap_current.py'")
source=source.replace("                    chain.main()", "                    import gate\n                    gate.run(json.loads((root/'bootstrap/CONFIG.json').read_text()),root)")
# Preserve production item selection in CONFIG; the fixture data provider supplies a subset.
source=source.replace("    original_loader=data.official_rows", "    original_tasks=data.tasks_for\n    original_loader=data.official_rows")
if key=='revsi':
 source=source.replace("    original_score=O.score_run", "    original_tasks=data.tasks_for\n    original_score=O.score_run")
source=source.replace("    with ExitStack() as stack:","""    def fixture_tasks(spec,roots):
        rows=original_tasks(spec,roots)
        return [dict(r,answer='3',ground_truth='3',released_answer='3') for r in rows if r['example_id'] in chosen_ids]
    def fixture_membership(cfg):
        ts=A.tasks(cfg)
        assert {t['example_id'] for t in ts}==chosen_ids
        return ts
    import gate
    with ExitStack() as stack:
        stack.enter_context(patch.object(data,'tasks_for',fixture_tasks))
        stack.enter_context(patch.object(A,'membership',fixture_membership))
""")
# The real accepted parity script runs in a separate CPU process with a fixed template fixture.
source=source.replace("        raise ValueError('Unexpected fixture command: '+str(argv))", """        if any(str(x).endswith('prove_prompts.py') for x in argv):
            target=argv[argv.index('--output')+1]
            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
                return original_run([sys.executable,'-B',str(Path(__file__).resolve().parent/'parity_fixture.py'),str(ROOT),target],capture_output=True)
        raise ValueError('Unexpected fixture command: '+str(argv))""")
source=source.replace("        F.js(out/'PARITY.json',dict(processor_checked=False,fixture=True))", "        raise AssertionError('Production must use the bootstrap parity proof')")
# The copied payload is the active adapter source in both kits.
if key=='vsi':
 source=source.replace("(chain,'utility',utility),(A,'EXPORT_SHA'", "(chain,'utility',utility),(A,'HERE',package/'reader'),(A,'EXPORT_SHA'")
source=source.replace("    config.update(x0='a'*64,x1=F.sha(ap),x2=0)", '''    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'kit'))
    import rebind as B
    binding=B.bind('vsibench5130' if ROOT.name=='vsi' else 'revsi999t32','step544','direct', ledger=work/'official.jsonl')
    binding['export']=dict(kind='fixture',sha256=F.sha(ap),label='CPU fixture with synthetic answers')
    binding['binding_sha256']=B.binding_sha256(binding)
    config.update(x0=binding['binding_sha256'],x1=F.sha(ap),x2=0)''')
# Rehearsal provenance remains outside the submitted CONFIG.
source=source.replace("    F.js(work/'RESULT.json',result)","""    result['config_mode']=config['mode']
    result['phase_b_items']=0
    result['real_processor']=False
    result['boundaries']=['Local archive, media, namespace, GPU and process transports are stand-ins.',
        'The task provider supplies the fixed accepted proof subset with constant synthetic answers.',
        'The engine and tokenizer are fakes; the pre-decode parity proof uses a fixed chat-template stand-in.']
    result['config']=config
    packet=work/'packet';packet.mkdir()
    (packet/'BATCH.sh').write_text(script)
    B.dump(packet/'CONFIG.json',config)
    B.dump(packet/'BINDING.json',binding)
    B.dump(packet/'BATCH.pin.json',dict(sha256=B.sha256_file(packet/'BATCH.sh'),config_sha256=B.sha256_file(packet/'CONFIG.json')))
    from types import SimpleNamespace as NS
    result['fetch']=B.fetch(NS(destination=packet,return_dir=pool/token))
    result['reports']=B.report(NS(destination=packet,return_dir=None,accepted_return=False))
    result['fixture_packet']=str(packet)
    F.js(work/'RESULT.json',result)""")
if '--done' in sys.argv:
    source=source.replace("    artifact=physical(root,config['spec']['artifact']['path'])", """    config['spec']['step']=200
    config['spec']['artifact']['path']=str(J.FSW/'ap/8865619b/runs/359fcc3c/m200/artifact.json')
    artifact=physical(root,config['spec']['artifact']['path'])""")
    source=source.replace("    base,bm,export,ap=F.models(fixture,artifact,real_base)", """    base,bm,export,ap=F.models(fixture,artifact,real_base)
    avalue=json.loads(ap.read_text());avalue['step']=200;F.js(ap,avalue)
    (export/'heads.pt').write_bytes(b'fixture')""")
    source=source.replace("'m544/'+str(p.relative_to(export))", "'m200/'+str(p.relative_to(export))")
    source=source.replace("{'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes()}", "{'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes(), **{'sj/orch_cd/legs1_reads/out/'+n:(ROOT/'reader/out'/n).read_bytes() for n in ('common.py','export_check.py')}}")
    source=source.replace("binding['export']=dict(kind='fixture',sha256=F.sha(ap)", "binding['export']=dict(kind='fixture',sha256=export_tar['sha256']")
    source=source.replace("config.update(x0=binding['binding_sha256'],x1=F.sha(ap),x2=0)", "config.update(x0=binding['binding_sha256'],x1=export_tar['sha256'],x2=1,x3=export_tar['bytes'])")
    source=source.replace("        with (fixture/'e.tar').open('rb') as stream:yield stream", """        raw=(fixture/'e.tar').read_bytes();n=len(raw)//4
        idx=int(argv[-1].split('.part')[1][:2])
        yield io.BytesIO(raw[idx*n:(idx+1)*n] if idx<3 else raw[idx*n:])""")
    source=source.replace("        if any(str(x).endswith('prove_prompts.py')", """        if '--export' in argv:
            argv=list(argv);argv[2]=str(ROOT/'reader/out/export_check.py')
            argv[argv.index('--export')+1]=str(artifact)
            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
                return original_run([argv[0],'-B',str(Path(__file__).resolve().parent/'checker_fixture.py'),*argv[2:]],**kwargs)
        if any(str(x).endswith('prove_prompts.py')""")
    source=source.replace("    with ExitStack() as stack:", """    import export_stage as E,s1
    receipts=fixture/'receipt';receipts.mkdir()
    (receipts/'gcs_359fcc3c_m200.done').write_text('q8/8865619b/359fcc3c_m200.tar '+str(export_tar['bytes'])+' '+export_tar['sha256']+chr(10))
    def local_path(value):
        return receipts if str(value)=='/project/community/jjyeung/okh7/x_f5c353f7/o' else Path(value)
    with ExitStack() as stack:
        stack.enter_context(patch.object(E,'Path',local_path))
        stack.enter_context(patch.object(gate,'Path',local_path))
        stack.enter_context(patch.object(E,'writable',lambda v:Path(v).resolve()))
        stack.enter_context(patch.object(E.T,'writable',lambda v:Path(v).resolve()))
        stack.enter_context(patch.object(s1,'MIN_FREE',0))
        stack.enter_context(patch.object(s1,'stage_videos',S.stage_videos))
""")
    source=source.replace("    B.dump(packet/'CONFIG.json',config)", "    B.dump(packet/'CONFIG.json',json.loads(B.boot_files(packet/'BATCH.sh')['bootstrap/CONFIG.json']))")
if '--nonshm' in sys.argv:
    scratch=Path(os.environ['A0_FIXTURE_RAM'])
    scratch.mkdir(exist_ok=False)
    source=source.replace("work/'prepared'",repr(str(scratch/'prepared')))
    source=source.replace("work/'prepared/BATCH.sh'","Path("+repr(str(scratch/'prepared/BATCH.sh'))+")")
    source=source.replace("fixture=work/'f'", "fixture=Path("+repr(str(scratch/'f'))+")")
    source=source.replace("packet=work/'packet'","packet=Path("+repr(str(scratch/'packet'))+")")
    source=source.replace("work/'BATCH.sh'","Path("+repr(str(scratch/'BATCH.sh'))+")")
    source=source.replace("pool=work/'pool'", "pool=Path("+repr(str(scratch/'pool'))+")")
    source=source.replace("trace_source=work/'_bootstrap_current.py'", "trace_source=Path("+repr(str(scratch/'_bootstrap_current.py'))+")")
    source=source.replace("return original_run([sys.executable,'-B',str(Path(__file__).resolve().parent/'parity_fixture.py'),str(ROOT),target],capture_output=True)","""original_target=Path(target)
                target="""+repr(str(Path('/dev/shm/b07_n7')/'PLACEHOLDER'))+"""
                result=original_run([sys.executable,'-B',str(Path(__file__).resolve().parent/'parity_fixture.py'),str(ROOT),target],capture_output=True)
                original_target.parent.mkdir(parents=True,exist_ok=True)
                original_target.symlink_to(target,target_is_directory=True)
                Path("""+repr(str(scratch/'parity_debug.log'))+""").write_bytes(result.stdout+result.stderr)
                return result""")
    source=source.replace(repr(str(Path('/dev/shm/b07_n7')/'PLACEHOLDER')),repr(str(scratch/'p9')))
    source=source.replace("            kw['stdout'].write(log.getvalue().encode())", "            Path("+repr(str(scratch/'child_debug.txt'))+").write_text(log.getvalue())\n            kw['stdout'].write(log.getvalue().encode())")
    source="from pathlib import Path\n"+source
    source=source.replace('work=Path(work).resolve()', 'work=Path(work).absolute()')
    # Only the fixture adapts read-only source locations. Runtime logical roots
    # still use xnames' non-RAM mapping and the real namespace builder.
    source=source.replace("import xnames; xnames.install(root)","""import xnames
    descriptor=os.open(ROOT.parents[1],os.O_RDONLY|os.O_DIRECTORY)
    owner=ROOT.parents[1]
    roots=[owner/'kit',owner/'tests',owner/'out',Path('/scratch/jjyeung/orch_n30/b07_offread/kit/offkit')]
    held=[descriptor]
    xnames.media_alias(str(owner),'/proc/'+str(os.getpid())+'/fd/'+str(descriptor))
    for base in roots:
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY);held.append(fd)
        alias='/proc/'+str(os.getpid())+'/fd/'+str(fd)
        entries=[base]+list(base.rglob('*')) if base.name!='out' else [base]+list(base.glob('*.json'))
        for entry in entries:
            xnames.media_alias(str(entry),alias+'/'+str(entry.relative_to(base)))
    xnames.install(work)""")
    source=source.replace("    with ExitStack() as stack:","""    real_namespace=J.namespace
    namespace_checks=[]
    def checked_namespace(*args):
        argv=real_namespace(*args)
        with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
            mapped=original_run(['/bin/echo',*argv],capture_output=True,text=True,check=True).stdout.split()
        for arg in mapped:xnames.scan(arg)
        shell=(package/'vllm_isolated.sh').read_text()
        import shlex
        target=shlex.split(shell.splitlines()[1])[1]
        assert target.startswith(str(J.AP)+'/')
        assert str(J.AP) in mapped
        namespace_checks.append(dict(argv=mapped,exec_target=target,root=str(args[0]),passed=True))
        return argv
    with ExitStack() as stack:""")
    source=source.replace("(J,'namespace',lambda *a:[])","(J,'namespace',checked_namespace)")
    source=source.replace("    result['config_mode']=config['mode']", "    result['namespace_checks']=namespace_checks\n    result['config_mode']=config['mode']")
# The source is retained so the exact fixture changes can be audited.
WORK.parent.mkdir(parents=True,exist_ok=True)
((scratch if '--nonshm' in sys.argv else WORK.parent)/(WORK.name+'_source.py')).write_text(source)
lines={}
rootstr=str(ROOT)
def tracer(frame,event,arg):
    name=frame.f_code.co_filename
    if not name.startswith(rootstr) or not name.endswith('.py'):return None
    if event=='line':lines.setdefault(name,set()).add(frame.f_lineno)
    return tracer
sys.settrace(tracer);threading.settrace(tracer)
try:
    scope={'__name__':'fixture_module','__file__':str(Path(__file__).resolve())}
    exec(compile(source,str((scratch if '--nonshm' in sys.argv else WORK.parent)/(WORK.name+'_source.py')),'exec'),scope)
    result=scope['run'](WORK)
    print(json.dumps({k:v for k,v in result.items() if k!='config'},indent=2))
finally:
    sys.settrace(None);threading.settrace(None)
    ((scratch if '--nonshm' in sys.argv else WORK.parent)/('coverage_'+key+('_done' if '--done' in sys.argv else '')+'.json')).write_text(json.dumps({n:sorted(v) for n,v in sorted(lines.items())},indent=1)+'\n')
    import hashlib
    ((scratch if '--nonshm' in sys.argv else WORK.parent)/('coverage_'+key+('_done' if '--done' in sys.argv else '')+'_pins.json')).write_text(json.dumps({n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in lines if Path(n).is_file()},indent=1)+'\n')
