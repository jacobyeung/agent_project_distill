#!/usr/bin/env python3
"""Isolated local probes of the exact delivered helper bytes. Python 3.6."""
from __future__ import print_function
import ast
import builtins
import io
import json
import math
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tarfile
import time

# This imports the wrapper, not a package worker or one of its sibling modules.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack as P


def materialize(package, work):
    files,pay,pub,plan = P.structure(package)
    src = work/'a'; src.mkdir(mode=0o700)
    for n,d in pay.items():
        p=src/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
    return files,pay,pub,plan,src


def module(path):
    return runpy.run_path(str(path),run_name='pack_probe')


def metadata(package, work, config):
    f,pay,pub,plan,src=materialize(package,work)
    helper=module(src/'8.py')
    cfg=helper['load_helpers'](package)
    from orchard_h10.common import submit_argv,valid_token,opaque
    from orchard_h10.job import verify_config
    verify_config(cfg);valid_token(pub['token'])
    wall=config.get('remote',{}).get('walltime','02:30:00')
    argv=submit_argv(pub['token'],1,wall);opaque(argv)
    for n in ('3.py','a/4.py','a/5.py','a/6.py'):
        # Python 3.12 parser can check 3.6 grammar; this does not attest APIs.
        if sys.version_info >= (3,8):
            ast.parse(f[n].decode(),filename=n,feature_version=(3,6))
    public_guards=[]
    if 'items/dist580.json' in pay:
        cases=[(['--gpus','2','--time',wall],b'D requires --gpus 1'),
               (['--gpus','1','--time','99:00:00'],b'D requires --time ')]
        for i,(flags,expected) in enumerate(cases):
            # check never submits. If a guard is absent, the native login
            # checker also rejects this local placement before any job call.
            r=subprocess.run(['nice','-n','10',sys.executable,'-I','-s','-B',
                str(package/'3.py'),'check']+flags,cwd=str(work),env=P.clean_env(work),
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
            (work/('public_guard%d.log'%i)).write_bytes(r.stdout+r.stderr)
            P.require(r.returncode!=0 and expected in r.stderr,
                      'D public resource guard did not reject before placement')
            public_guards.append(dict(flags=flags,rejected=True))
    P.write(work/'result.json',dict(passed=True,native_load_helpers=True,
        native_verify_config=True,submit_argv=argv,grammar_only_python36=True,
        public_resource_guards=public_guards))


def guard(package,work,config):
    f,pay,pub,plan,src=materialize(package,work)
    sys.path.insert(0,str(src))
    helper=module(package/'a/5.py')
    from orchard_h10.common import install_process_guard
    root=work/('a'+os.urandom(6).hex());root.mkdir(mode=0o700)
    install_process_guard(root)
    proof=helper['check_bundle_guard'](package,root)
    # Dispatch uses the genuine bundled bootstrap. The recording launcher makes
    # no model claim; guard and its 4 MiB write run as actual subprocesses.
    dispatch=root/'a';dispatch.mkdir()
    P.write(dispatch/'1.json',dict(action=1,config={}))
    argv=[sys.executable,'-I','-s','-B',str(dispatch/'5.py'),str(dispatch/'1.json')]
    calls=[]
    result=helper['dispatch_operator'](root,proof,argv,lambda a,**k:calls.append(a))
    P.require(len(calls)==1 and result['entry_sequence_passed'] is True,'Dispatch proof failed')
    P.write(work/'result.json',dict(passed=True,guard=result,
        scope='real process guard/write; recorded operator dispatch'))


def check_rows(src, rows, layout='duplicate'):
    # Import native code, including its actual dependency modules.
    sys.path[:0]=[str(src/'tree'),str(src/'b'),str(src)]
    import torch
    # Installed torch/_torch_docs.py:9815-9823; called before tensor operations.
    torch.set_num_threads(8)
    from student_pilot.carrier_c1_data import layout_inputs
    count=0
    for row in rows:
        if not isinstance(row,dict) or 'student_input' not in row:
            continue
        layout_inputs(row,layout=layout)
        count+=1
    return count


def rows_in(value):
    if isinstance(value,dict):
        if 'student_input' in value:
            yield value
        else:
            for item in value.values():
                for row in rows_in(item):yield row
    elif isinstance(value,list):
        for item in value:
            for row in rows_in(item):yield row


def isolated_entry(python, script, roots, cwd, log):
    code=('import runpy,sys; import torch; torch.set_num_threads(8); '
          'sys.path[:0]=sys.argv[2:]; sys.argv=[sys.argv[1]]; '
          'runpy.run_path(sys.argv[0],run_name="pack_import")')
    # The script directory is deliberately absent unless its own code inserts it.
    return P.run([python,'-I','-s','-B','-c',code,str(script)]+list(map(str,roots)),
                 cwd,log,timeout=120)


def logic(package,work,config):
    f,pay,pub,plan,src=materialize(package,work)
    sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
    rows=[]
    for n,d in pay.items():
        if n.endswith('.json'):
            rows.extend(rows_in(json.loads(d)))
        elif n.endswith('.jsonl'):
            for line in d.decode().splitlines():
                if line.strip():rows.extend(rows_in(json.loads(line)))
    for spec in config.get('row_files',[]):
        p=Path(spec['path']);P.require(P.file_sha(p)==spec['sha256'],'Rows SHA differs')
        for line in p.read_text().splitlines():
            if line.strip():rows.extend(rows_in(json.loads(line)))
    count=check_rows(src,rows,plan.get('export_binding',{}).get('frame_layout','duplicate'))
    # A read package need not carry training rows. Its native read mappers and
    # the staged restore are checked separately; report the actual row count.
    entries=set(config.get('isolated_entries',[]))
    entries.add('h1eval/h10/launch.py')
    for n in pay:
        if Path(n).name=='worker.py' or Path(n).name.endswith('_worker.py'):
            if '/tests/' not in '/'+n and not n.startswith('tree/'):
                entries.add(n)
    for i,n in enumerate(sorted(entries)):
        P.safe_name(n);P.require(n in pay,'Missing isolated entry: '+n)
        isolated_entry(config.get('python',sys.executable),src/n,
                       [src/'b',src/'tree',src],work,work/('import%d.log'%i))
    op=module(package/'a/6.py')
    desc=op['descriptors'](str(src));memory=op['memory_bound']()
    P.require(memory['fits'] is True and memory['basis']=='fixed_g3t_shapes'
              and memory['sam_measurement_required'] is False,'Operator memory contract failed')
    P.require(desc and all(d['stage1_select_rule']==plan['stage1_select_rule']
              and d['perception_memo']==plan['perception_memo']
              and d['perception_memo_modules']==plan['perception_memo_modules'] for d in desc),
              'Operator settings differ from plan')
    from orchard_h10.common import ORDER
    expected=P.read(package/'a/0.json').get('types',list(ORDER))
    actual=[ORDER[t] for d in desc for t in d['types']]
    P.require(set(actual)==set(expected),'Operator type selection differs from inputs')
    settings=dict(stage1_select_rule=plan['stage1_select_rule'],
        perception_memo=plan['perception_memo'],perception_memo_modules=plan['perception_memo_modules'],
        perception_memo_verify_ids=plan.get('perception_memo_verify_ids',[]),save_own_depth=False,types=expected)
    P.write(work/'settings.json',settings)
    cfg=dict(package=str(src),output=str(work/'r'),settings=str(work/'settings.json'),
        plan_sha256=pub['plan_sha256'],inputs_sha256='0'*64,
        operator_sha256=P.file_sha(package/'a/6.py'),python=sys.executable,
        export=str(work/'e'),binding=str(work/'b.json'),export_pin=str(work/'p.json'),
        device='cpu',prefix=[])
    # The native rehearsal uses tiny CPU model stubs. measure_memory stays off:
    # full-reader evidence requires the real staged restore and RGBs on Orchard.
    rehearsal=op['rehearsal'](cfg)
    P.require(rehearsal and all(r['expected']==desc[i]['expected']
              for i,r in enumerate(rehearsal)),'Operator rehearsal differs')
    P.require(op['memory_bound'](allocation_bytes=1)['fits'] is False,
              'Memory bound accepted an insufficient allocation')
    from h1eval.items import load_manifest,read_contract
    manifests=[]
    for n,d in pay.items():
        if n.startswith('items/') and n.endswith('.json'):
            value=json.loads(d)
            if isinstance(value,dict) and value.get('schema')=='h1-items-v1':
                load_manifest(src/n);manifests.append(n)
    contracts=[]
    for r in rehearsal:
        args=r['args'];path=Path(args[args.index('--items')+1])
        manifest=load_manifest(path)
        arms=args[args.index('--arms')+1].split(',')
        modes=args[args.index('--modes')+1].split(',')
        read_contract(manifest,arms,[{'name':name} for name in modes],','.join(r['types']))
        contracts.append(dict(manifest=manifest['name'],arms=arms,modes=modes,types=r['types']))
    P.write(work/'result.json',dict(passed=True,rows_checked=count,
        isolated_entries=sorted(entries),memory=memory,descriptors=desc,
        manifests=manifests,rehearsal=rehearsal,read_contracts=contracts,
        scope='imports/layout/native stub rehearsal/planning; no full staged reader or restore'))


def make_trap_fixture(batch, package, work, child, label):
    """Same transformation as o_traptest: replace only Python body and I/O sites."""
    marker="<<'A' &\n"
    P.require(batch.count(marker)==1 and batch.count('trap fin EXIT')==1,
              'Missing/ambiguous batch EXIT trap')
    head,rest=batch.split(marker,1);body,tail=rest.rsplit('\nA\n',1)
    lines=[]
    for line in head.splitlines():
        if line.startswith('P='):
            line='P='+str(package)
        elif line.startswith('L='):
            line='L='+str(work/(label+'.log'))
        elif line.startswith('R='):
            line='R='+str(work/(label+'.capture'))
        elif line.startswith('echo "node '):
            line='echo "node fixture" > "$L"'
        elif line.startswith('/usr/bin/python3 '):
            line=line.replace('/usr/bin/python3',sys.executable,1)
        lines.append(line)
    # No GPU query, real pool write, or package bootstrap is executed here.
    fixture='\n'.join(lines)+marker+child+'\nA\n'+tail
    path=work/(label+'.sh');path.write_text(fixture)
    return path


def trap_probe(batch, package, work, ignore_signal=False):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    fail=make_trap_fixture(batch,package,work,
            "raise RuntimeError('pack planted early failure')",'a0')
    env=P.clean_env(work)
    r=subprocess.run(['nice','-n','10','bash',str(fail)],cwd=str(work),env=env,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
    capture=work/'a0.capture'
    P.require(r.returncode!=0 and capture.exists(),'EXIT trap lost early failure')
    text=capture.read_text()
    P.require('node fixture' in text and 'exit 1' in text
              and 'pack planted early failure' in text,'EXIT trap lost diagnostic tail')
    ready=work/'a1.ready';stop=work/'a1.stop';end=work/'a1.end'
    child=("import signal,time\nfrom pathlib import Path\n"
           "ready=Path(%r);stop=Path(%r);end=Path(%r)\n" % (str(ready),str(stop),str(end))
           +("signal.signal(signal.SIGUSR1,signal.SIG_IGN)\n" if ignore_signal else
             "signal.signal(signal.SIGUSR1,lambda *a:stop.write_text('stop\\n'))\n")
           +"ready.write_text('ready\\n')\n"
           "deadline=time.time()+1.5\n"
           "while time.time()<deadline and not stop.exists():time.sleep(0.01)\n"
           "if stop.exists():end.write_text('slot\\n')\n"
           "raise SystemExit(0 if end.exists() else 7)\n")
    path=make_trap_fixture(batch,package,work,child,'a1')
    with (work/'a1.outer').open('wb') as outer:
        proc=subprocess.Popen(['nice','-n','10','bash',str(path)],cwd=str(work),env=env,
                              stdout=outer,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+5
        while not ready.exists() and proc.poll() is None and time.monotonic()<deadline:
            time.sleep(0.01)
        P.require(ready.exists(),'Signal fixture did not start')
        proc.send_signal(signal.SIGUSR1)
        rc=proc.wait(timeout=5)
    P.require(rc==0 and stop.exists() and end.exists(),
              'USR1 did not drain child to a stop/end slot')
    P.require('exit 0' in (work/'a1.capture').read_text(),'Trap changed clean stop exit')
    return dict(passed=True,early_exit=r.returncode,signal_exit=rc,end_slot=str(end),
                scope='batch wrapper and cooperative CPU child, not training ranks')


def trap(package,work,config):
    P.write(work/'result.json',trap_probe((package/'BATCH.sh').read_text(),package,work/'a'))


def native_stop(package,work,config):
    """Signal the genuine read runner with a tiny cooperative child.

    The native commands(), worker_args(), handler, wait, journal summary and
    return path run unchanged. Only the decoder process is a tiny CPU fixture.
    """
    f,pay,pub,plan,src=materialize(package,work)
    child=work/'1.py';ready=work/'0.ready';end=work/'0.end'
    child.write_text("import sys,time\nfrom pathlib import Path\n"
        "stop=Path(sys.argv[1]);ready=Path(sys.argv[2]);end=Path(sys.argv[3])\n"
        "ready.write_text('ready\\n');deadline=time.time()+2\n"
        "while time.time()<deadline and not stop.exists():time.sleep(0.01)\n"
        "if stop.exists():end.write_text('slot\\n')\n"
        "raise SystemExit(0 if end.exists() else 7)\n")
    supervisor=work/'0.py'
    # Keep supervisor paths numeric: the real native argv guard remains active.
    code='''import json,subprocess,sys,time
from pathlib import Path
src=Path(%r);sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
from orchard_h10 import runner
from orchard_h10.common import ORDER
config=dict(package=str(src),output=%r,python=sys.executable,plan_sha256=%r,
            inputs_sha256='0'*64,device='cpu',types=%r,
            arms=['tower'],modes=['none'],stop_margin=0,return_margin=0,
            perception_memo='on',perception_memo_modules=['g3t'],
            perception_memo_verify_ids=[],stage1_select_rule='candidates_argmax')
config.update(export=str(src/'e'),binding=str(src/'b.json'),export_pin=str(src/'p.json'))
op=__import__('runpy').run_path(%r,run_name='pack_probe')
spec=op['descriptors'](str(src))[0]
config['types']=[ORDER[t] for t in spec['types']]
# prepare() identifies the real item input without loading any weights.
settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
              perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
Path(%r).write_text(json.dumps(settings));config.update(settings=%r,operator_sha256=%r)
prepared=op['prepare'](config)[0];config=prepared
config.update(stop_margin=0,return_margin=0)
def launcher(argv,**kw):
    cfg=json.loads((Path(kw['cwd'])/argv[-1]).read_text())
    actual=runner.worker_args(cfg);marker=actual[actual.index('--stop-file')+1]
    return subprocess.Popen([sys.executable,'-I','-s','-B',%r,marker,%r,%r],**kw)
summary=runner.run(config,[''],time.time()+60,launcher=launcher)
Path(%r).write_text(json.dumps(summary))
if summary.get('failure') or not summary.get('stopped') or not Path(%r).exists():
    raise ValueError('Native runner stop/end proof failed')
print('NATIVE_STOP_PASS')
''' % (str(src),str(work/'r'),pub['plan_sha256'],[],str(package/'a/6.py'),
       str(work/'settings.json'),str(work/'settings.json'),P.file_sha(package/'a/6.py'),
       str(child),str(ready),str(end),str(work/'summary.json'),str(end))
    supervisor.write_text(code)
    with (work/'stop.log').open('wb') as out:
        proc=subprocess.Popen(['nice','-n','10',sys.executable,'-I','-s','-B',str(supervisor)],
            cwd=str(work),env=P.clean_env(work),stdout=out,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+15
        while not ready.exists() and proc.poll() is None and time.monotonic()<deadline:
            time.sleep(0.01)
        if not ready.exists():
            # The tiny fixture has its own deadline; do not leave it running.
            rc=proc.wait(timeout=15)
            raise P.GateError('Native runner did not start CPU child; see '+str(work/'stop.log'))
        proc.send_signal(signal.SIGUSR1)
        rc=proc.wait(timeout=15)
    P.require(rc==0 and end.exists() and (work/'r/metadata/STOP').exists(),
              'Native runner stop/end proof failed; see '+str(work/'stop.log'))
    P.write(work/'result.json',dict(passed=True,end_slot=str(end),
        source_sha256=P.sha(pay['orchard_h10/runner.py']),
        summary=P.read(work/'summary.json'),
        scope='native read runner and worker arguments with tiny CPU decoder; no training export'))


class Mirrors:
    """Map declared remote file access to authenticated local bytes, preserving paths.

    This is a dry filesystem adapter, not a security sandbox. Builders and
    package helpers are trusted code. Input mirrors are read-only; only the
    package prefix maps to a writable local copy. No package source changes.
    """
    def __init__(self, mirrors, remote_package, local_package):
        self.mirrors=mirrors;self.remote=remote_package.rstrip('/');self.local=str(local_package)

    def translate(self,path,writing=False):
        if isinstance(path,int):return path
        s=os.fspath(path) if hasattr(os,'fspath') else str(path)
        if isinstance(s,bytes):s=s.decode()
        if s==self.remote or s.startswith(self.remote+'/'):
            return self.local+s[len(self.remote):]
        if s in self.mirrors:
            P.require(not writing,'Attempted write to input mirror')
            return self.mirrors[s]['local']
        return path

    def __enter__(self):
        self.saved=(builtins.open,io.open,os.stat,os.mkdir,os.chmod,Path.resolve,tarfile.bltn_open,
                    getattr(io,'open_code',None))
        op,iop,stat,mkdir,chmod,resolve,tarop,open_code=self.saved
        def mapped_open(path,mode='r',*a,**k):
            return op(self.translate(path,any(c in mode for c in 'wax+')),mode,*a,**k)
        def mapped_io(path,mode='r',*a,**k):
            return iop(self.translate(path,any(c in mode for c in 'wax+')),mode,*a,**k)
        def mapped_resolve(path,*a,**k):
            s=str(path)
            if s==self.remote or s.startswith(self.remote+'/') or s in self.mirrors:
                return Path(s)
            return resolve(path,*a,**k)
        builtins.open=mapped_open;io.open=mapped_io;tarfile.bltn_open=mapped_open
        if open_code is not None:
            io.open_code=lambda p:open_code(self.translate(p))
        os.stat=lambda p,*a,**k:stat(self.translate(p),*a,**k)
        os.mkdir=lambda p,*a,**k:mkdir(self.translate(p,True),*a,**k)
        os.chmod=lambda p,*a,**k:chmod(self.translate(p,True),*a,**k)
        Path.resolve=mapped_resolve
        return self

    def __exit__(self,*args):
        builtins.open,io.open,os.stat,os.mkdir,os.chmod,Path.resolve,tarfile.bltn_open,open_code=self.saved
        if open_code is not None:io.open_code=open_code


def real_fill(package,work,config):
    files,pay,pub,plan=P.structure(package)
    root=work/('a'+os.urandom(5).hex());root.mkdir()
    local=root/(P.PREFIX+pub['token']);local.mkdir(mode=0o700)
    for n,d in files.items():
        p=local/n;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(d)
    (local/'a').chmod(0o700)
    remote=config.get('remote',{}).get('root',P.REMOTE_ROOT)+'/'+local.name
    # Mutable templates remain in the release; dry-fill outputs are separate.
    # Existing a/1.json and export.json may be placeholders and are overwritten
    # only in this new dry copy, by the exact production fill helper.
    args=P.fill_argv(config,remote)[4:]
    saved=sys.argv[:]
    with Mirrors(config['mirrors'],remote,local):
        sys.argv=[remote+'/a/4.py']+args[1:]
        runpy.run_path(remote+'/a/4.py',run_name='__main__')
        base=P.read(local/'a/0.json');filled=P.read(local/'a/1.json')
        P.preserved(base,filled,P.file_sha(local/'a/6'))
        # Run exact public entrypoint, including real path/permission assertions.
        sys.argv=[remote+'/3.py','check','--gpus','1','--time',config['remote']['walltime']]
        try:runpy.run_path(remote+'/3.py',run_name='__main__')
        except SystemExit as e:P.require(e.code in (None,0),'Native entrypoint check failed')
        # Native load/check_inputs do not hash all dependency members; the
        # independent resolver below verifies them before this gate passes.
        from orchard_h10.job import check_inputs
        cfg=module_payload_helpers(local)
        check_inputs(filled,cfg,package=Path(remote))
    sys.argv=saved
    resolved=resolve_archives(base,filled,config['mirrors'],remote,local)
    # Filled metadata and preparation bytes are outbound package surfaces too.
    P.privacy(P.package_files(local),pay,pub,config.get('old_identities',[]),
              config.get('forbidden_extra',[]))
    P.write(work/'result.json',dict(passed=True,inputs=P.file_sha(local/'a/1.json'),
        prep=P.file_sha(local/'a/6'),resolved=resolved,
        scope='exact fill and login checks through authenticated path mirrors'))


def module_payload_helpers(package):
    with tarfile.open(str(package/'0.tgz')) as tar:
        raw=tar.extractfile('8.py').read()
    ns={'__name__':'pack_helper','__file__':str(package/'8.py')}
    exec(compile(raw,ns['__file__'],'exec'),ns)
    return ns['load_helpers'](package)


def resolve_archives(base,filled,mirrors,remote,local):
    """Hash all members needed by files/policy/env; reject ambiguous ownership."""
    P.preserved(base,filled,P.file_sha(local/'a/6'))
    owners={};resolved={};total=0;small={}
    wanted={filled['files'][filled[k]]['path'] for k in ('policy_receipt','environment_receipt')}
    wanted.update(filled['policy'].values())
    for i,a in enumerate(filled['archives']):
        # Streaming concatenation uses exact production Parts implementation.
        helper=module(local/'a/4.py');paths=[]
        for pin in a['parts']:
            path=pin['path']
            if path.startswith(remote+'/'):
                actual=local/path[len(remote)+1:]
            else:
                P.require(path in mirrors,'Missing archive mirror: '+path)
                actual=Path(mirrors[path]['local'])
            P.require(actual.stat().st_size==pin['bytes'] and P.file_sha(actual)==pin['sha256'],
                      'Archive part differs: '+path)
            paths.append(str(actual))
        stream=helper['Parts'](paths)
        try:
            with tarfile.open(fileobj=stream,mode='r|*') as archive:
                for m in archive:
                    n=m.name
                    while n.startswith('./'):n=n[2:]
                    P.safe_name(n.rstrip('/'))
                    dest=Path('/scratch/jjyeung')/Path(a['destination']).relative_to('sj')/n
                    key=str(dest)
                    if m.isdir():continue
                    P.require(m.isfile(),'Dependency archive nonregular member: '+n)
                    P.require(key not in owners,'Ambiguous archive member: '+key)
                    import hashlib
                    h=hashlib.sha256();size=0;pieces=[]
                    with archive.extractfile(m) as source:
                        for chunk in iter(lambda:source.read(1024*1024),b''):
                            h.update(chunk);size+=len(chunk)
                            if key in wanted:
                                P.require(size<=4*1024**2,'Oversized policy/environment member')
                                pieces.append(chunk)
                    owners[key]=dict(slot=i,bytes=size,sha256=h.hexdigest())
                    if key in wanted:small[key]=b''.join(pieces)
            while stream.read(1024*1024):pass
            P.require(stream.digest.hexdigest()==a['sha256'],'Whole archive differs')
        finally:
            if stream.stream is not None:stream.stream.close()
        total+=stream.size
    for name,pin in filled['files'].items():
        P.require(pin['path'] in owners,'Missing resolved file: '+name)
        actual=owners[pin['path']]
        P.require(actual['bytes']==pin['bytes'] and actual['sha256']==pin['sha256'],
                  'Resolved file pin differs: '+name)
        resolved[name]=actual['slot']
    for name in ('vnice','terminator'):
        P.require(filled['policy'][name] in owners,'Missing policy script: '+name)
    policy=json.loads(small[filled['files'][filled['policy_receipt']]['path']])
    P.require(policy.get('authorized') is True and all(policy.get(n)==filled['policy'][n]
              for n in ('vnice','terminator')),'Policy receipt does not authorize scripts')
    pay=P.unpack((local/'0.tgz').read_bytes())
    assets=json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    for n in ('vnice','terminator'):
        P.require(P.sha(small[filled['policy'][n]])==assets[n+'_sha256'],
                  'Policy script hash differs: '+n)
    env=json.loads(small[filled['files'][filled['environment_receipt']]['path']])
    P.require(isinstance(env.get('versions'),dict),'Environment receipt versions missing')
    return dict(files=resolved,read_bytes_measured=total)


def main():
    P.limit_resources()
    mode=sys.argv[1];package=Path(sys.argv[2]).resolve();work=Path(sys.argv[3]).resolve()
    config=P.read(sys.argv[4]) if len(sys.argv)>4 else {}
    work.mkdir(parents=True,exist_ok=True)
    env=P.clean_env(work);os.environ.clear();os.environ.update(env)
    funcs={'metadata':metadata,'guard':guard,'logic':logic,'trap':trap,'stop':native_stop,'fill':real_fill}
    funcs[mode](package,work,config)
    print('PROBE_PASS '+mode)


if __name__=='__main__':
    main()
