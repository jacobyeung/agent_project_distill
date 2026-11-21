import os, sys, time, json, hashlib, shutil, subprocess, signal, resource, difflib
from pathlib import Path
PYTHON='/scratch/jjyeung/envs/p1cpu/bin/python'
J=Path(__file__).resolve().parents[2]
W=J/'work/build27'
SOURCE=J/'work/x/a2/n'
RESULTS=[]

def event(tag, **kw):
    data=(json.dumps(dict(event=tag,pid=os.getpid(),t=time.monotonic(),**kw),sort_keys=True)+'\n').encode()
    fd=os.open(os.environ['T_EVENTS'],os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o600)
    try: os.write(fd,data)
    finally: os.close(fd)

def await_true(fn, timeout=15):
    end=time.monotonic()+timeout
    while not fn():
        if time.monotonic()>end: raise RuntimeError('timeout waiting for '+repr(fn))
        time.sleep(.01)

def read_events(case):
    p=case/'events.jsonl'
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

def shim(kind,args):
    case=Path(os.environ['T_CASE']); job=os.environ['SLURM_JOB_ID']; x=Path(os.environ['T_X'])
    if kind=='--gpu':
        await_true(lambda:(x/'o'/job/'j2.err').exists())
        event('gpu',args=args)
        for n in range(int(os.environ['T_GPUS'])):
            print(f'GPU {n}: H100 (UUID: {n})' if args==['-L'] else 'H100, 81920')
        return 0
    if kind=='--timeout':
        event('timeout',args=args)
        os.execv('/usr/bin/timeout',['timeout']+args)
    assert kind=='--py'
    scripts=[a for a in args if a.endswith('.py')]
    name=Path(scripts[0]).name if scripts else '-c'
    event('python',name=name,args=args)
    if name=='j2.py':
        if args[-1]=='once':
            event('publish.once')
            mode=os.environ['T_PFAIL']
            if mode=='fail': print('P79',file=sys.stderr);return 79
            if mode=='iofail':
                # The real publisher catches this failed replace().
                target=x/'o'/job/'j2.log'
                if target.exists(): target.rename(case/'initial.j2.log')
                target.mkdir()
            if mode=='hang':
                # The real publisher blocks opening a FIFO as its local log.
                node=Path(scripts[0]).parent; log=node/'j2.log'
                log.rename(node/'j2.saved.log');os.mkfifo(log,0o600)
            if os.environ['T_FINAL_SIGNAL']: time.sleep(1.0)
        else:
            event('publish.periodic')
            if os.environ['T_TICKS']=='1': args=args+['0.05']
        os.execv(PYTHON,[PYTHON]+args)
    if name=='resolve.py' and os.environ['T_MODE'] in ('child','logger'):
        Path(args[args.index('--output')+1]).write_text('{}\n')
        print('R00');return 0
    if name=='l.py' and os.environ['T_MODE']=='logger':
        # Fail the actual l.py: make only its stdout read-only. Its input is valid.
        fd=os.open('/dev/null',os.O_RDONLY);os.dup2(fd,1);os.close(fd)
    os.execv(PYTHON,[PYTHON]+args)

def digest_tree(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

def alive(pid):
    try:
        state=Path('/proc')/str(pid)/'stat'
        return state.exists() and state.read_text().split()[2]!='Z'
    except FileNotFoundError: return False

def cleanup(p,case):
    # Only processes launched by this test; no other lane's processes.
    if p.poll() is None:
        os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
    for e in read_events(case):
        if e['event']=='publish.periodic':
            try: os.killpg(e['pid'],signal.SIGKILL)
            except ProcessLookupError: pass

def run_one(label,version,root,gpu,mode,expected,token,pfail='',sig='',finalsig='',setup='',ticks=False):
    case=W/(label+'_'+version);case.mkdir();local=case/'tmp';local.mkdir()
    x=root.parent;raw=(J/f'out/jn{version}.sh').read_text()
    raw=raw.replace('X="/project/community/jjyeung/okh7/x_22c714e1"','X="'+str(x)+'"')
    raw=raw.replace('--pool "/project/community/jjyeung/okh7"','--pool "'+str(W/'pool')+'"')
    (case/'run.sh').write_text(raw)
    job='8'+str(len(RESULTS)+1).zfill(4);node=local/('q_22c714e1_'+job)
    if version=='7':(x/'o'/job).mkdir(parents=True,exist_ok=True);(x/'o'/job/'RELEASE').write_text('')
    if setup=='node':local.chmod(0o500)
    if setup in ('log','publisher'):
        node.mkdir();(node/('j2.log' if setup=='log' else 'j2.py')).mkdir()
    env=dict(os.environ,PATH=str(W/'bin')+':/usr/bin:/bin',SLURM_JOB_ID=job,
             SLURM_TMPDIR=str(local),TMPDIR=str(W/'tmp'),T_CASE=str(case),T_EVENTS=str(case/'events.jsonl'),
             T_X=str(x),T_GPUS=str(gpu),T_MODE=mode,T_PFAIL=pfail,T_SIGNAL=sig,T_FINAL_SIGNAL=finalsig,
             T_TICKS=str(int(ticks)),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
             NUMEXPR_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',
             XDG_CACHE_HOME=str(W/'tmp/cache'),HF_HOME=str(W/'tmp/hf'))
    start=time.monotonic();watchdog=False;tick_count=0
    with (case/'console.log').open('wb') as log:
        p=subprocess.Popen(['bash',str(case/'run.sh')],env=env,stdout=log,stderr=log,start_new_session=True)
        try:
            if sig:
                await_true(lambda:(case/'tree.ready').exists())
                tree=json.loads((case/'tree.ready').read_text())
                assert len(set(tree.values()))==3 and all(alive(pid) for pid in tree.values()),tree
                event_file=case/'sent.signal';event_file.write_text(sig+'\n')
                p.send_signal(getattr(signal,'SIG'+sig))
            if ticks:
                stamps=set();until=time.monotonic()+.7
                while time.monotonic()<until:
                    f=x/'o'/job/'j2.log'
                    if f.exists(): stamps.add(f.stat().st_mtime_ns)
                    time.sleep(.01)
                tick_count=len(stamps);assert tick_count>=3,tick_count
                (case/'release').write_text('1\n')
            if finalsig:
                await_true(lambda:any(e['event']=='publish.once' for e in read_events(case)))
                time.sleep(.1)
                p.send_signal(getattr(signal,'SIG'+finalsig))
                (case/'sent.final.signal').write_text(finalsig+'\n')
            try: rc=p.wait(timeout=(160 if version=='6' else 170) if pfail=='hang' else 20)
            except subprocess.TimeoutExpired:
                watchdog=True;cleanup(p,case);rc=p.returncode
        finally:
            # Record whether the wrapper itself stopped the real periodic worker.
            periodic=[e['pid'] for e in read_events(case) if e['event']=='publish.periodic']
            time.sleep(.03)
            worker_stopped=all(not alive(pid) for pid in periodic)
            cleanup(p,case)
    elapsed=time.monotonic()-start
    events=read_events(case);once=sum(e['event']=='publish.once' for e in events)
    pub=x/'o'/job
    files={f.name:f.read_text() for f in pub.glob('*') if f.is_file() and f.name in ('j2.log','j2.err','j2.fallback.log')}
    tail='\n'.join(files.values());present=token in tail
    local_text='\n'.join(f.read_text() for f in node.glob('*') if f.name in ('j2.log','j2.err','j2.saved.log') and f.is_file() and not f.is_fifo())
    (case/'published.json').write_text(json.dumps(files,indent=2)+'\n')
    (case/'local.txt').write_text(local_text)
    assert rc==expected or (pfail=='hang' and version=='4' and watchdog),(label,version,rc,expected,local_text)
    assert once==(0 if setup and version=='4' else 1),(label,version,once)
    if version in ('6','7'):
        assert not watchdog,(label,version,'watchdog')
        assert present,(label,version,'missing token',token,tail)
        assert worker_stopped,(label,version,'periodic worker survived')
        timeouts=[e['args'] for e in events if e['event']=='timeout']
        # jn6: the live mirror's own bounded calls are not publication attempts.
        mirror=[a for a in timeouts if any(str(v).endswith('j6.py') for v in a)]
        # jn7: the traceback copy and the hold's own bounded calls are not publication attempts either.
        held=[a for a in timeouts if any(str(v).endswith('j7.py') for v in a)]
        timeouts=[a for a in timeouts if a not in mirror and a not in held]
        hold=version=='7' and expected!=0 and not sig and not setup
        hx=x/'o'/job
        assert (hx/'HOLD.txt').is_file()==hold,(label,version,'hold',hold)
        if hold:
            end=(hx/'HOLD_END.txt').read_text()
            assert 'reason=release status=%d '%expected in end,(label,end)
            assert ('status=%d '%expected) in (hx/'HOLD.txt').read_text().splitlines()[0]
        assert (hx/'tb.txt').is_file()==(version=='7' and not setup),(label,version,'tb')
        if version=='7' and not setup: assert (hx/'tb.txt').stat().st_size<=204800
        if version=='6': assert not held
        if version in ('6','7') and not setup:
            live=x/'o'/(job+'_live')/'live.json'
            assert live.is_file() and json.loads(live.read_text())['phase']=='final',(label,'no final live snapshot')
            assert any(a[:2]==['--signal=KILL','30s'] for a in mirror),(label,'final snapshot not bounded',mirror)
            assert sum(f.stat().st_size for f in live.parent.iterdir())<2_000_000
        assert timeouts[0][:2]==['--signal=KILL','120s'],timeouts
        if pfail or setup: assert timeouts[-1][:2]==['--signal=KILL','15s'],timeouts
        assert len(timeouts)==(2 if pfail or setup else 1),timeouts
        fallback=files.get('j2.fallback.log','')
        assert len(fallback.splitlines())==(1 if pfail or setup else 0),fallback
        if fallback: assert 'status='+str(expected) in fallback and len(fallback)<120,fallback
    elif setup or pfail:
        assert not present,(label,version,'baseline unexpectedly repaired',tail)
    else: assert present,(label,version,'regression control missing token',tail)
    if gpu<4 or setup:
        assert not any(e['event']=='python' and e['name'] in ('v.py','resolve.py','l.py') for e in events)
        assert not (case/'tree.ready').exists()
    if mode=='seal': assert not any(e['event']=='python' and e['name']=='resolve.py' for e in events)
    if mode=='logger': assert 'OSError: [Errno 9] Bad file descriptor' in local_text,local_text
    if mode=='resolve': assert 'ValueError: E10' in local_text,local_text
    if sig:
        assert (case/'signal.parent').read_text().strip()==sig
        assert (case/'signal.child').read_text().strip()==sig
        assert (case/'signal.grandchild').read_text().strip()==sig
        assert all(not alive(pid) for pid in tree.values()),tree
    if pfail=='hang' and version=='5': assert 119<elapsed<124,elapsed
    # jn6 adds at most the 30 s final snapshot after the 120 s publish and 15 s fallback.
    if pfail=='hang' and version=='6': assert 119<elapsed<124+31,elapsed
    # jn7 adds the bounded tb copy and a hold released at its first poll.
    if pfail=='hang' and version=='7': assert 119<elapsed<124+31+10,elapsed
    result=dict(case=label,version=version,status=rc,expected=expected,once=once,published=present,
                periodic=len(periodic),periodic_stopped=worker_stopped,ticks=tick_count,
                watchdog=watchdog,seconds=round(elapsed,3),token=token,log=str(case.relative_to(J)),PASS=True)
    (case/'result.json').write_text(json.dumps(result,indent=2)+'\n');RESULTS.append(result)
    (W/'results.json').write_text(json.dumps(RESULTS,indent=2)+'\n')
    print(json.dumps(result),flush=True)

TREE=r"""import os,sys,time,signal,subprocess,json
from pathlib import Path
c=Path(os.environ['T_CASE']);level=int(sys.argv[1]);child=None
code={'TERM':37,'USR1':38}
def stop(s,_):
    name=signal.Signals(s).name.removeprefix('SIG')
    (c/('signal.'+['parent','child','grandchild'][level])).write_text(name+'\n')
    if child:
        child.send_signal(s);rc=child.wait(timeout=5)
        assert rc==code[name],rc
    print('C'+str(code[name]),flush=True)
    raise SystemExit(code[name])
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGUSR1,stop)
(c/('pid'+str(level))).write_text(str(os.getpid()))
if level<2: child=subprocess.Popen([sys.executable,'-I','-s','-B',__file__,str(level+1)])
if level==2:
    (c/'tree.ready').write_text(json.dumps({str(i):int((c/('pid'+str(i))).read_text()) for i in range(3)}))
if not os.environ['T_SIGNAL']:
    if os.environ['T_TICKS']=='1':
        while not (c/'release').exists():time.sleep(.02)
    if child: assert child.wait(timeout=5)==23
    print('C23',flush=True);sys.exit(23)
while True:time.sleep(.02)
"""

def main():
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    assert os.nice(0)>=10
    assert subprocess.check_output(['hostname','-s'],text=True).strip()=='trinity-1-18'
    before=digest_tree(SOURCE);(W/'source.before.json').write_text(json.dumps(before,indent=2)+'\n')
    x=W/'x';x.mkdir();(W/'pool').mkdir()
    root=x/'n';shutil.copytree(SOURCE,root)
    bad=x/'s/n';shutil.copytree(root,bad)
    altered=bad/'b/w.py';blob=bytearray(altered.read_bytes());blob[0]^=1;altered.write_bytes(blob)
    good=x/'c/n';shutil.copytree(root,good)
    (W/'tree.py').write_text(TREE)
    (good/'job.sh').write_text('#!/bin/bash\nexec '+PYTHON+' -I -s -B '+str(W/'tree.py')+' 0\n')
    (good/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(good))+'\n' for p in sorted(good.rglob('*')) if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')))
    bindir=W/'bin';bindir.mkdir()
    for name,kind in [('python3','--py'),('nvidia-smi','--gpu'),('timeout','--timeout')]:
        p=bindir/name;p.write_text('#!/bin/bash\nexec '+PYTHON+' -I -s -B '+str(Path(__file__).resolve())+' '+kind+' "$@"\n');p.chmod(0o700)
    for v in ('6','7'):subprocess.run(['bash','-n',str(J/f'out/jn{v}.sh')],check=True)
    for v in ('6','7'):
        run_one('g0',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging')
        run_one('g2',v,root,2,'gpu',3,'fewer than 4 H100; stop before staging')
        run_one('seal',v,bad,4,'seal',1,'ValueError: E13')
        run_one('resolve',v,root,4,'resolve',1,'ValueError: E10')
        run_one('logger',v,root,4,'logger',120,'OSError: [Errno 9] Bad file descriptor')
        run_one('normal',v,good,4,'child',23,'C23')
        run_one('term',v,good,4,'child',37,'C37',sig='TERM')
        run_one('usr1',v,good,4,'child',38,'C38',sig='USR1')
        run_one('ticks',v,good,4,'child',23,'C23',ticks=True)
        run_one('node',v,root,0,'gpu',1,'node directory failed',setup='node')
        run_one('log',v,root,0,'gpu',1,'j2.log redirect failed',setup='log')
        run_one('create',v,root,0,'gpu',1,'j2.py creation failed',setup='publisher')
        run_one('pfail',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail='fail')
        run_one('iofail',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail='iofail')
        run_one('resolve_pfail',v,root,4,'resolve',1,'resolve.py refusal',pfail='fail')
        run_one('logger_pfail',v,root,4,'logger',120,'l.py refusal',pfail='fail')
        run_one('term_final',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',finalsig='TERM')
        run_one('usr1_final',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',finalsig='USR1')
    for v in ('6','7'):
        run_one('hang',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail='hang',finalsig='TERM')
    after=digest_tree(SOURCE);assert before==after==digest_tree(root)
    (W/'source.after.json').write_text(json.dumps(after,indent=2)+'\n')
    assert digest_tree(bad).keys()==before.keys()
    assert {k for k,h in digest_tree(bad).items() if h!=before[k]}=={'b/w.py'}
    print('PASS: '+str(len(RESULTS))+' cases; pristine source and kit unchanged',flush=True)

if __name__=='__main__':
    if len(sys.argv)>1:sys.exit(shim(sys.argv[1],sys.argv[2:]))
    main()
