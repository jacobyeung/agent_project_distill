import os, sys, time, json, hashlib, shutil, subprocess, signal, resource, difflib
from pathlib import Path

PYTHON = '/scratch/jjyeung/envs/p1cpu/bin/python'
J = Path(__file__).resolve().parents[2]
W = J/'work/build24m4z13'/os.environ.get('T_RUN_ID','a2')
SOURCE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n')

def event(tag, **kw):
    line = json.dumps(dict(event=tag, **kw), sort_keys=True)+'\n'
    fd = os.open(os.environ['T_EVENTS'], os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try: os.write(fd, line.encode())
    finally: os.close(fd)

def await_path(path, timeout=15):
    deadline=time.monotonic()+timeout
    while not Path(path).exists():
        if time.monotonic()>deadline: raise RuntimeError('timeout: '+str(path))
        time.sleep(.02)

def shim(kind, args):
    case=Path(os.environ['T_CASE'])
    if kind=='--gpu':
        await_path(case/'initial.done')
        event('gpu', args=args)
        count=int(os.environ['T_GPUS'])
        if args==['-L']:
            for n in range(count): print(f'GPU {n}: H100 (UUID: {n})')
        else:
            for n in range(count): print('H100, 81920')
        return 0
    if kind=='--bg':
        # Run the actual screened publisher once before permitting GPU checks.
        # Hold the periodic worker without a second tick during these short tests.
        par=int(args[-1])
        event('publish.initial', args=args[1:])
        rc=subprocess.run([PYTHON]+args[1:]+['600','once']).returncode
        if rc: raise RuntimeError('initial publisher rc='+str(rc))
        (case/'initial.done').write_text('0\n')
        def stop(*_): raise SystemExit(0)
        signal.signal(signal.SIGTERM,stop)
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                try: os.kill(par,0)
                except ProcessLookupError: break
                time.sleep(.02)
            else: raise RuntimeError('background worker timeout')
        finally: (case/'background.done').write_text('0\n')
        return 0
    assert kind=='--py'
    scripts=[a for a in args if a.endswith('.py')]
    name=Path(scripts[0]).name if scripts else '-c'
    event('python', name=name, args=args)
    if name=='j2.py':
        assert args[-1]=='once'
        event('publish.once')
        if os.environ.get('T_PFAIL')=='1':
            print('P79',file=sys.stderr)
            return 79
    if name=='resolve.py' and os.environ['T_MODE']=='child':
        # Only the normal-child tests substitute the resolver, which would need a pool.
        Path(args[args.index('--output')+1]).write_text('{}\n')
        print('R00')
        return 0
    return subprocess.run([PYTHON]+args).returncode

def digest_tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

def run_one(label, version, root, gpu, mode, expected, token, sig=None, pfail=False):
    case=W/(label+'_'+version);case.mkdir()
    local=case/'tmp';local.mkdir()
    script=J/('inputs/jn3.sh' if version=='3' else 'out/jn4.sh')
    raw=script.read_text()
    x=root.parent
    raw=raw.replace('X="/project/community/jjyeung/okh7/x_22c714e1"', 'X="'+str(x)+'"')
    raw=raw.replace('--pool "/project/community/jjyeung/okh7"','--pool "'+str(J/'work/pool')+'"')
    (case/'run.sh').write_text(raw)
    job='9'+str(len(RESULTS)+1).zfill(4)
    env=dict(os.environ, PATH=str(W/'bin')+':/usr/bin:/bin', SLURM_JOB_ID=job,
             SLURM_TMPDIR=str(local), TMPDIR=str(J/'work/tmp'),
             T_CASE=str(case), T_EVENTS=str(case/'events.jsonl'), T_GPUS=str(gpu),
             T_MODE=mode, T_PFAIL=str(int(pfail)), T_SIGNAL=sig or '',
             OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
             NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
             XDG_CACHE_HOME=str(J/'work/tmp/cache'), HF_HOME=str(J/'work/tmp/hf'),
             PYTHONDONTWRITEBYTECODE='1')
    started=time.monotonic()
    with (case/'console.log').open('wb') as log:
        p=subprocess.Popen(['bash',str(case/'run.sh')],env=env,stdout=log,stderr=log)
        if sig:
            await_path(case/'child.ready')
            p.send_signal(getattr(signal,'SIG'+sig))
        rc=p.wait(timeout=25)
    await_path(case/'background.done')
    node=local/('q_22c714e1_'+job)
    published=x/'o'/job
    events=[json.loads(l) for l in (case/'events.jsonl').read_text().splitlines()]
    once=sum(e['event']=='publish.once' for e in events)
    initial=sum(e['event']=='publish.initial' for e in events)
    files={n:(published/n).read_text() for n in ('j2.log','j2.err')}
    local_text='\n'.join((node/n).read_text() for n in ('j2.log','j2.err'))
    tail='\n'.join(files.values())
    assert rc==expected,(label,version,rc,expected,local_text)
    assert token in local_text,(label,version,'local token absent',local_text)
    want_once=0 if version=='3' and mode!='child' else 1
    assert once==want_once,(label,version,'once',once)
    assert initial==1,(label,version,'initial',initial)
    if pfail: assert token not in tail and 'P79' in local_text
    elif version=='3' and mode!='child': assert token not in tail,(label,'before unexpectedly published',tail)
    else: assert token in tail,(label,'after token absent',tail)
    if gpu<4:
        assert not any(e['event']=='python' and e['name'] in ('v.py','resolve.py','l.py') for e in events)
        assert not (case/'child.ready').exists()
        assert not (node/'r0.json').exists()
    if mode=='seal':
        assert not any(e['event']=='python' and e['name']=='resolve.py' for e in events)
    if mode!='child': assert not (case/'child.ready').exists()
    if sig: assert (case/('signal.'+sig)).read_text().strip()==sig
    result=dict(case=label,version=version,status=rc,initial=initial,once=once,
                token=token,published=token in tail,live_exists=(published/'live').exists(),
                log=str(case.relative_to(J)),tail=str(published.relative_to(J)),
                seconds=round(time.monotonic()-started,3),PASS=True)
    (case/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    RESULTS.append(result)
    print(json.dumps(result),flush=True)
    return result

RESULTS=[]

def main():
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    assert os.nice(0)>=10
    assert subprocess.check_output(['hostname','-s'],text=True).strip()=='trinity-1-18'
    W.mkdir(parents=True,exist_ok=True)
    before=digest_tree(SOURCE)
    (W/'source.before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n')
    x=J/'work/x'/os.environ.get('T_RUN_ID','a2');x.mkdir(parents=True);(J/'work/pool').mkdir(exist_ok=True)
    root=x/'n';shutil.copytree(SOURCE,root)
    bad=x/'s/n';shutil.copytree(root,bad)
    altered=bad/'b/w.py';blob=bytearray(altered.read_bytes());blob[0]^=1;altered.write_bytes(blob)
    assert sum(a!=b for a,b in zip((root/'b/w.py').read_bytes(),altered.read_bytes()))==1
    assert {k for k,v in digest_tree(bad).items() if before[k]!=v}=={'b/w.py'}
    good=x/'c/n';shutil.copytree(root,good)
    (good/'job.sh').write_text('''#!/bin/bash
set -euo pipefail
printf 'C00\\n'
trap 'printf "TERM\\n" > "$T_CASE/signal.TERM"; echo C37; exit 37' TERM
trap 'printf "USR1\\n" > "$T_CASE/signal.USR1"; echo C38; exit 38' USR1
printf 'ready\\n' > "$T_CASE/child.ready"
if [[ -n "$T_SIGNAL" ]]; then
    while true; do sleep 0.05; done
fi
echo C23
exit 23
''')
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(good))+'\n'
                 for p in sorted(good.rglob('*')) if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json'))
    (good/'SHA256SUMS.txt').write_text(sums)
    bindir=W/'bin';bindir.mkdir()
    for name,kind in [('python3','--py'),('setsid','--bg'),('nvidia-smi','--gpu')]:
        p=bindir/name
        p.write_text('#!/bin/bash\nexec '+PYTHON+' -I -s -B '+str(Path(__file__).resolve())+' '+kind+' "$@"\n')
        p.chmod(0o700)
    for file in ('out/jn4.sh','out/t_jn4.sh','inputs/jn3.sh'):
        subprocess.run(['bash','-n',str(J/file)],check=True)
    src=(J/'inputs/jn3.sh').read_text();dst=(J/'out/jn4.sh').read_text()
    call='python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" 600 once || true'
    trap='trap \'status=$?; '+call+'; exit "$status"\' EXIT\n'
    assert dst==src.replace('PYJ2\n','PYJ2\n'+trap,1).replace('\n'+call+'\n','\n')
    assert (J/'out/t_jn4.sh').read_bytes()==(J/'out/jn4.sh').read_bytes()
    assert dst.index(trap)<dst.index('setsid')<dst.index('fewer than 4 H100')<dst.index('"$ROOT/b/v.py"')
    assert dst.count("' EXIT")==1 and dst.count(call)==1
    for version in ('3','4'):
        run_one('g0',version,root,0,'gpu',3,'fewer than 4 H100; stop before staging')
        run_one('g2',version,root,2,'gpu',3,'fewer than 4 H100; stop before staging')
        run_one('s',version,bad,4,'seal',1,'ValueError: E13')
        run_one('r',version,root,4,'resolve',1,'ValueError: E10')
        run_one('c',version,good,4,'child',23,'C23')
        run_one('t',version,good,4,'child',37,'C37',sig='TERM')
        run_one('u',version,good,4,'child',38,'C38',sig='USR1')
    run_one('p', '4',root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail=True)
    after=digest_tree(SOURCE)
    assert before==after and digest_tree(root)==before
    (W/'source.after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n')
    (W/'results.json').write_text(json.dumps(RESULTS,indent=2)+'\n')
    (W/'checks.log').write_text('PASS: bash -n; exact two-line change; one EXIT trap immediately after PYJ2; identical t_jn4; original header and ROOT; TERM/USR1; zero GPU guard precedes v/resolve/job; source kit unchanged; pristine fixture identical; one-byte seal fixture; normal fixture resealed; failed publisher preserves status.\n')
    print('PASS: '+str(len(RESULTS))+' cases',flush=True)

if __name__=='__main__':
    if len(sys.argv)>1: sys.exit(shim(sys.argv[1],sys.argv[2:]))
    main()
