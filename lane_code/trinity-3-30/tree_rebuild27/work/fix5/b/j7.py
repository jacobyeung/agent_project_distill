import os,re,socket,stat,sys,time
from pathlib import Path
# jn7 helper for the batch shell: traceback copy (tb), node hold record (hold), release poll (poll), hold end (end).
# Every call runs under a KILL timeout in the wrapper; failures return non-zero and never raise into it.
TB_CAP=204800
mode=sys.argv[1]
def utc(t=None):return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(t))
def target(xr,job):
    t=Path(xr)/'o'/job
    if not re.fullmatch('[0-9]+',job):raise ValueError('E71')
    if any(p.is_symlink() for p in (t,*t.parents)):raise ValueError('E72')
    return t
def put(t,name,raw):
    t.mkdir(parents=True,exist_ok=True,mode=0o700)
    dest=t/name;temp=t/(name+'.part')
    if dest.is_symlink() or temp.is_symlink():raise ValueError('E73')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)
    os.replace(temp,dest)
def regular(p):
    try:s=os.lstat(p)
    except OSError:return None
    return s.st_size if stat.S_ISREG(s.st_mode) else -1
def tb(node,xr,job,status):
    # The kit's raw traceback file (fix4 contract: $Q_ROOT/tb.txt), unscreened, bounded at 200 KB; URLs replaced.
    src=Path(node)/'tb.txt';t=target(xr,job);size=regular(src)
    if size is None:raw=('no traceback file at %s; status=%s; utc %s\n'%(src,status,utc())).encode()
    elif size<0:raw=('%s is not a regular file; status=%s\n'%(src,status)).encode()
    else:
        fd=os.open(src,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as f:
            if size<=TB_CAP:raw=f.read(TB_CAP)
            else:
                head=f.read(TB_CAP//2-200);f.seek(size-(TB_CAP//2-200));tail=f.read()
                raw=head+('\n[jn7: %d bytes of %d omitted]\n'%(size-len(head)-len(tail),size)).encode()+tail
        raw=re.sub(rb'https?://[^\s\'"]+',b'[URL]',raw)[:TB_CAP]
    put(t,'tb.txt',raw)
def hold(node,xr,job,status,step,start,deadline):
    node=Path(node);t=target(xr,job);start=int(start);deadline=int(deadline)
    def row(label,p):
        size=regular(p)
        return '%-22s %s  %s\n'%(label,p,'absent' if size is None else ('dir' if p.is_dir() else ('not regular' if size<0 else '%d bytes'%size)))
    slog=Path('/tmp')/('q_22c714e1_%s'%job)
    text=('HOLD job=%s node=%s status=%s step=%s\n'%(job,socket.gethostname(),status,step)+
        'start_utc %s deadline_utc %s hold_seconds %d\n'%(utc(start),utc(deadline),deadline-start)+
        'The job failed before training; the wrapper keeps the node and the node directory until the deadline,\n'
        'until %s exists, or until TERM/USR1 (scancel). It then exits with status %s.\n'%(t/'RELEASE',status)+
        'release: touch %s (seen within about 25 s)\n'%(t/'RELEASE')+
        'enter:   srun --overlap --jobid %s --pty bash\n'%job+
        'sandbox: /tmp/q_22c714e1 inside the job sandbox is the node directory below\n'
        'node-local paths:\n'+
        row('node directory',node)+row('prepared root p',node/'p')+row('prepared q p/q',node/'p'/'q')+
        row('proof result',node/'p'/'q'/'RESULT.json')+row('traceback tb.txt',node/'tb.txt')+
        row('kit shell j.sh',node/'j.sh')+row('request r.json',node/'r.json')+
        ''.join(row('log '+n,node/n) for n in ('j2.log','j2.err','q.log','rooms.log','h.log','rv.log',job+'.steps'))+
        row('slurm log',Path(str(slog)+'.log'))+row('slurm err',Path(str(slog)+'.err'))+
        'training markers (absent, else no hold): %s %s\n'%(node/'t.log',node/'p'/'rv.json'))
    raw=text.encode()
    try:put(node,'HOLD.txt',raw)
    except OSError:pass
    put(t,'HOLD.txt',raw)
def poll(xr,job):
    return 0 if os.path.lexists(target(xr,job)/'RELEASE') else 1
def end(xr,job,status,reason,start):
    put(target(xr,job),'HOLD_END.txt',('HOLD_END job=%s reason=%s status=%s start_utc %s end_utc %s held_seconds %d\n'%(
        job,reason,status,utc(int(start)),utc(),int(time.time())-int(start))).encode())
try:
    if mode=='tb':tb(*sys.argv[2:6])
    elif mode=='hold':hold(*sys.argv[2:9])
    elif mode=='poll':raise SystemExit(poll(*sys.argv[2:4]))
    elif mode=='end':end(*sys.argv[2:7])
    else:raise SystemExit(2)
except SystemExit:raise
except Exception:raise SystemExit(3)
