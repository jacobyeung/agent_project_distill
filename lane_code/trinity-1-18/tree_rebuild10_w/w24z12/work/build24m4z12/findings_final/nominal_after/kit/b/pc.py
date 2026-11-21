"""Batch-shell publication of small evidence and immutable native states."""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import re
import io
import runpy
import http.client
import concurrent.futures
import stat
from urllib.parse import urlsplit
import subprocess
import sys
import tarfile
import time

CAP = 50_000_000
LOG_CAP = 40_000_000
RESERVE = 50 * 1024**3


def read(p):
    v = json.loads(Path(p).read_text())
    return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def put(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.part')
    atomic(p, (json.dumps(v, sort_keys=True) + '\n').encode())


def atomic(p, raw):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.part')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        os.fchmod(f.fileno(), 0o600); f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def masked(value):
    return re.sub(r'https?://[^\s\"\'<>]+', '[URL]', str(value))


def deadline():
    if os.environ.get('TK_COPY_DEADLINE'):
        return float(os.environ['TK_COPY_DEADLINE'])
    end = os.environ.get('SLURM_JOB_END_TIME')
    if end and end.isdigit(): return float(end)-15
    start = float(os.environ.get('TK_JOB_START', time.time()))
    return start+float(os.environ.get('TK_TIME_LIMIT_SECONDS', '86400'))-15


# 50 MB / 1 MB/s, with factor three; also bounds stalled requests.
ARCHIVE_SECONDS = 150


def priority_version(train, state, nominal):
    train, state = Path(train), Path(state)
    request = state.parent/'stop.request'
    markers = sorted([*train.glob('checkpoint_*/complete.json'), *train.glob('m*/artifact.json')])
    return dict(stop=request.stat().st_mtime_ns if request.exists() else None,
                nominal=time.time() >= nominal,
                markers={str(p):sha(p) for p in markers})


def priority_settled(train, state, nominal):
    marker = Path(state)/'priority_settled.json'
    return marker.is_file() and read(marker) == priority_version(train, state, nominal)


def upload(uri, path, offset, length, name):
    started = time.time(); url = urlsplit(uri)
    chunk=int(os.environ.get('TK_UPLOAD_CHUNK_BYTES',8<<20))
    if chunk<256<<10 or chunk%(256<<10):raise ValueError('E107 chunk alignment')
    limit = float(os.environ.get('TK_UPLOAD_DEADLINE', deadline()))
    log = Path(os.environ['TK_UPLOAD_LOG'])
    def event(code=None, ran=None, error=None):
        raw = json.dumps(dict(time=time.time(), name=name, http=code, range=masked(ran) if ran else None,
                             error=masked(error) if error else None))+'\n'
        fd=os.open(log, os.O_WRONLY|os.O_CREAT|os.O_APPEND, 0o600)
        try: os.write(fd,raw.encode())
        finally: os.close(fd)
    def request(raw, cr):
        code=ran=None; conn=None
        try:
            train=os.environ.get('TK_PRIORITY_TRAIN')
            if train and not priority_settled(train, os.environ['TK_PRIORITY_STATE'], float(os.environ.get('TK_NOMINAL_STOP', 'inf'))):
                state=Path(os.environ['TK_PRIORITY_STATE'])
                if any(not (state/('gcs_'+p.parent.name+'.done')).exists() for p in Path(train).glob('m*/artifact.json')):
                    raise InterruptedError('E105 export ready')
                if (state.parent/'stop.request').exists() or (os.environ.get('TK_NOMINAL_STOP') and time.time()>=float(os.environ['TK_NOMINAL_STOP'])):
                    raise InterruptedError('E105 stop ready')
            remaining=limit-time.time()
            if remaining<=0: raise TimeoutError('E104 reserved publication window')
            conn=http.client.HTTPSConnection(url.netloc,timeout=min(10,max(.1,remaining)))
            conn.putrequest('PUT',url.path+('?' + url.query if url.query else ''))
            conn.putheader('Content-Length',str(len(raw)))
            conn.putheader('Content-Type','application/octet-stream')
            conn.putheader('Content-Range',cr);conn.endheaders()
            if raw:conn.send(raw)
            r=conn.getresponse();code=r.status;ran=r.getheader('Range');body=r.read()
            event(code,ran)
            if code not in (200,201,308):raise IOError('HTTP '+str(code))
            return code,ran,body
        except Exception as e:
            event(code,ran,repr(e));raise
        finally:
            if conn is not None:conn.close()
    md5=hashlib.md5(); digest=hashlib.sha256()
    with open(path,'rb') as f:
        f.seek(offset);left=length
        while left:
            b=f.read(min(1<<20,left))
            if not b:raise IOError('short read')
            md5.update(b);digest.update(b);left-=len(b)
    code,ran,body=request(b'', 'bytes */'+str(length))
    cursor=int(ran.split('-')[-1])+1 if ran else 0
    if not 0<=cursor<=length:raise IOError('invalid Range')
    with open(path,'rb') as f:
        while code==308:
            if cursor==length:
                if length:raise IOError('incomplete final response')
                raw=b'';cr='bytes */0'
            else:
                f.seek(offset+cursor);raw=f.read(min(chunk,length-cursor))
                cr=f'bytes {cursor}-{cursor+len(raw)-1}/{length}'
            code,ran,body=request(raw,cr)
            if code==308:
                next_cursor=int(ran.split('-')[-1])+1 if ran else 0
                if next_cursor<=cursor:raise IOError('no progress')
                cursor=next_cursor
    meta=json.loads(body)
    expected=base64.b64encode(md5.digest()).decode()
    if int(meta['size'])!=length or meta.get('md5Hash')!=expected or meta.get('name')!=name or not meta.get('generation'):
        raise IOError('GCS size/md5/name/generation mismatch')
    return dict(name=name,bytes=length,offset=offset,md5=expected,sha256=digest.hexdigest(),
                generation=meta['generation'],crc32c=meta.get('crc32c'),seconds=time.time()-started,started_at=started,finished_at=time.time())


def writer_main(argv):
    # Keep gc.py's split, prior-receipt and result semantics; use resumable transport.
    module=runpy.run_path(argv[0],run_name='gc_runtime')
    g=module['main'].__globals__
    def logged_upload(*args):
        try:return upload(*args)
        except Exception as error:
            raw=json.dumps(dict(time=time.time(),name=args[-1],http=None,range=None,error=masked(repr(error))))+'\n'
            fd=os.open(os.environ['TK_UPLOAD_LOG'],os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
            try:os.write(fd,raw.encode())
            finally:os.close(fd)
            raise
    g['upload']=logged_upload
    if os.environ.get('TK_DIAGNOSTIC_PREFIX')=='1':
        names=g['part_names'];g['part_names']=lambda name,count:names(name,count)[:1]
    g['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor
    receipt=argv[2]+'.receipts.jsonl'
    builtin_open=open
    class Append(io.StringIO):
        def close(self):
            if not self.closed:
                p=Path(receipt);atomic(p,(p.read_bytes() if p.exists() else b'')+self.getvalue().encode())
            super().close()
    def opened(path,mode='r',*a,**kw):
        if str(path)==receipt and mode=='a':return Append()
        return builtin_open(path,mode,*a,**kw)
    g['open']=opened
    return module['main'](argv[1:])


def beneath(path, root):
    return path == root or root in path.parents


class Copier:
    def __init__(self, kit, root, job, target=None, train=None, home=None, writer=None, sessions=None):
        self.kit, self.root = Path(kit).resolve(), Path(root).resolve()
        spec = read(self.kit/'k/p.json')
        self.cfg = read(self.kit/'k/n.json')
        if not Path(spec['n_root']).is_absolute():
            raise ValueError('R1_COPY_N_ROOT_NOT_ABSOLUTE')
        self.target = Path(spec['n_root']).absolute()
        self.job = str(job)
        if not self.job.replace('_', '').isalnum():
            raise ValueError('E91')
        self.live = self.target/'o'/self.job/'live'
        self.claims = self.root/'live_spool/claims'
        self.checkpoint = self.target/'n_ck'/self.job
        self.spool = self.root/'live_spool'
        self.train = Path(train) if train else self.root/'p/q/r'
        self.sessions = Path(sessions) if sessions is not None else (Path(home)/'sess.json' if home is not None else self.target/'n_s'/('sess_'+self.job+'.json'))
        self.home = self.sessions.parent
        self.writer = Path(writer) if writer else self.kit/'b/gc.py'
        self.names = read(self.kit/'k/y.json')
        if target is not None and Path(target).absolute() != self.target:
            raise ValueError('R1_COPY_TARGET_OUTSIDE_N_ROOT')
        self.paths()
        self.spool.mkdir(parents=True, exist_ok=True)
        self.claims.mkdir(parents=True, exist_ok=True)
        self.state = self.spool/'state'
        self.state.mkdir(exist_ok=True)
        self.final_pass = False
        self.exit_status = None
        self.logs_complete = False
        private = self.spool/'private'
        private.mkdir(exist_ok=True, mode=0o700)
        cached = private/'sess.json'
        self.deadline = deadline()
        self.data_deadline = self.deadline-min(10,max(0,(self.deadline-time.time())/10))
        policy=self.names.get('publication',{})
        reserve=ARCHIVE_SECONDS if ARCHIVE_SECONDS!=150 else policy.get('archive_rate_factor',3)*CAP/policy.get('archive_bytes_per_second',1_000_000)
        self.archive_due = self.deadline-reserve
        self.upload_until = self.archive_due
        if not cached.exists():
            raw = self.session_bytes()
            self.validate_sessions(raw)
            atomic(cached, raw)
        self.cached_sessions()

    def validate_sessions(self, raw):
        values = json.loads(raw)
        expected = {key+'.j'+self.job+f'.part{i:02d}-of-04'
                    for key in self.names['objects'].values() for i in range(4)}
        if not isinstance(values, dict) or set(values) != expected: raise ValueError('E101')
        for value in values.values():
            if not isinstance(value,str) or urlsplit(value).scheme not in ('https','http') or not urlsplit(value).netloc:
                raise ValueError('invalid URL')
        return raw

    def cached_sessions(self):
        original=self.sessions
        try:
            self.sessions=self.spool/'private/sess.json'
            return self.validate_sessions(self.session_bytes())
        finally:self.sessions=original


    def paths(self):
        # Validate before the first mkdir and every pass. Reject symlink ancestors.
        forbidden = (self.kit, self.root/'kit', self.root/'h')
        for name, path, expected in (
            ('LIVE', self.live, self.target/'o'/self.job/'live'),
            ('N_CK', self.checkpoint, self.target/'n_ck'/self.job),
            ('SESSIONS', self.sessions, self.target/'n_s'/self.sessions.name)):
            absolute = path.absolute()
            resolved = path.resolve()
            if any(resolved == p.resolve() or beneath(resolved, p.resolve()) for p in forbidden):
                raise ValueError('R1_COPY_'+name+'_INSIDE_KIT')
            if absolute != expected or not beneath(absolute, self.target) or '..' in path.parts:
                raise ValueError('R1_COPY_'+name+'_OUTSIDE_N_ROOT')
            # The session leaf is checked by session_bytes for its named status.
            probe = absolute.parent if name == 'SESSIONS' else absolute
            if any(p.is_symlink() for p in (probe, *probe.parents)):
                raise ValueError('R1_COPY_'+name+'_PATH_SYMLINK')
        if self.root == self.kit or beneath(self.root, self.kit):
            raise ValueError('R1_COPY_ROOT_INSIDE_KIT')
        if self.spool.is_symlink() or beneath(self.spool.resolve(), self.kit):
            raise ValueError('R1_COPY_SPOOL_INSIDE_KIT')

    def note(self, label, error):
        with (self.spool/'retry.log').open('a') as stream:
            stream.write(json.dumps(dict(time=int(time.time()), action=label,
                error=masked(repr(error)), errno=getattr(error,'errno',None)))+'\n')

    def attempt(self, label, action):
        try:
            return action()
        except Exception as error:
            self.note(label, error)

    def small(self):
        self.paths()
        with (self.spool/'small.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._small()

    def _small(self):
        # Each publication has one shared byte budget, including its manifest.
        self.live.mkdir(parents=True, exist_ok=True)
        rows, pending = [], []
        markers = []
        for pattern in ('checkpoint_*/complete.json', 'm*/artifact.json'):
            for p in sorted(self.train.glob(pattern)):
                if p.is_file() and not p.is_symlink():
                    markers.append(dict(name=str(p.relative_to(self.train)), bytes=p.stat().st_size, sha256=sha(p)))
        listing = (json.dumps(markers, sort_keys=True) + '\n').encode()
        if len(listing) > 1_000_000:
            raise ValueError('E92')
        pending.append(('markers.json', listing))
        metadata_budget = CAP - LOG_CAP - 1_000_000 - len(listing)
        candidates = []
        for pattern in ('metrics_*.jsonl', 'attempt_*.json', 'run_*.json'):
            candidates.extend(self.train.glob(pattern))
        candidates.extend(self.root.glob('*.steps'))
        candidates.extend((self.root/'h/o').glob('*.steps'))
        for p in sorted(candidates):
            if not p.is_file() or p.is_symlink():
                continue
            n = p.stat().st_size
            if n > metadata_budget:
                rows.append(dict(name=p.name, omitted='copy byte cap', source_bytes=n))
                continue
            raw = p.read_bytes()
            if len(raw) > metadata_budget:
                rows.append(dict(name=p.name, omitted='copy byte cap'))
                continue
            pending.append((p.name, raw))
            metadata_budget -= len(raw)
        logs = [self.root/n for n in ('t.log', 'q.log', 'h.log', 'rooms.log', 'j2.log', 'j2.err') if (self.root/n).is_file()]
        logs += [self.spool/'upload.log'] if (self.spool/'upload.log').is_file() else []
        # Share 40 MB fairly; every retained byte is from a log's tail.
        remaining = LOG_CAP
        screen = runpy.run_path(str(self.kit/'b/z.py'))['screen']
        words, hashes = read(self.kit/'k/g.json'), read(self.kit/'b/wh.json')
        for i, p in enumerate(logs):
            allowance = remaining // (len(logs) - i)
            with p.open('rb') as f:
                f.seek(max(0, p.stat().st_size - allowance))
                raw = f.read(allowance)
            raw = screen(masked(raw.decode('utf-8', 'replace')), words, hashes).encode()[-allowance:] if allowance else b''
            pending.append((p.name, raw))
            remaining -= len(raw)
        for p in sorted(self.state.glob('*')):
            if p.is_file() and p.stat().st_size <= metadata_budget:
                raw = p.read_bytes(); pending.append((p.name, raw)); metadata_budget -= len(raw)
        total = 0
        for name, raw in pending:
            dest = self.live/name
            atomic(dest,raw)
            total += len(raw)
            rows.append(dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        record = dict(time=int(time.time()), files=rows, payload_bytes=total, cap_bytes=CAP)
        raw = (json.dumps(record, sort_keys=True)+'\n').encode()
        assert total + len(raw) <= CAP
        atomic(self.live/'copy.json',raw)
        self.copy_exit()
        return total + len(raw)

    def copy_exit(self):
        local = self.root/'o'
        for name in ('o.tar', 'RESULT.json'):
            source = local/name
            if source.is_file():
                destination = self.target/'o'/self.job/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                partial = destination.with_name(name+'.part')
                shutil.copyfile(source, partial)
                with partial.open('rb') as f:os.fsync(f.fileno())
                os.replace(partial, destination)
        if (local/'o.tar').is_file() and (local/'RESULT.json').is_file():
            put(self.state/'o_copy.done', dict(sha256=sha(local/'o.tar')))

    def exit_archive(self):
        if not self.final_pass: return
        if self.priority_pending() and time.time()<self.archive_due and not getattr(self,'stop_settled',False): return
        archive = self.root/'o/o.tar'
        frozen = self.state/'o_frozen.json'
        if not frozen.exists() and self.exit_status is not None:
            subprocess.run([sys.executable, '-I', '-s', '-B', str(self.kit/'b/o.py'),
                str(self.root), str(self.exit_status), '0', '--local', '--final'],
                env={**os.environ, 'SLURM_JOB_ID':self.job}, check=True)
            put(frozen, dict(sha256=sha(archive)))
        if archive.is_file():
            if archive.stat().st_size > CAP:
                raise ValueError('E103')
            # The marker is the immutable archive itself; send verifies every part.
            self.send(archive.parent, archive, ['o'], archive=archive)
            self.attempt('o_copy', self.copy_exit)

    def archive(self, directory, marker):
        directory, marker = Path(directory), Path(marker)
        identity = sha(marker)
        # Persistence has already authenticated and archived this state when its receipt exists.
        for suffix in ('.local.json', '.json'):
            p = self.train/'persist'/(identity+suffix)
            if p.exists():
                receipt = read(p)
                archive = Path(receipt['archive']['path'])
                # Translate paths written inside the view into their node-local host path.
                if not archive.is_file():
                    archive = self.train/'persist'/archive.name
                if archive.is_file() and receipt['source']['sha256'] == identity and sha(archive) == receipt['archive']['sha256']:
                    return archive
        # Native persistence publishes its receipt after closing the archive.
        # Do not make a second weight-sized tar while that writer is active.
        if not self.final_pass and any((self.train/'persist'/(identity+s)).exists() for s in ('.local.claim','.claim','.tar')):
            raise ValueError('E100')
        target = self.spool/(identity+'.tar')
        ready = self.spool/(identity+'.ready.json')
        if ready.exists():
            v = read(ready)
            if target.is_file() and sha(target) == v['sha256']:
                return target
            raise ValueError('E93')
        files = sorted(p for p in directory.rglob('*') if p.is_file())
        if any(p.is_symlink() for p in directory.rglob('*')):
            raise ValueError('E94')
        size = sum(p.stat().st_size+1024 for p in files)+10240
        if shutil.disk_usage(self.spool).free < size+RESERVE:
            raise ValueError('E95')
        with tarfile.open(target, 'w') as t:
            for p in files:
                t.add(p, arcname=str(p.relative_to(directory)), recursive=False)
        if sha(marker) != identity:
            raise ValueError('E96')
        put(ready, dict(sha256=sha(target), bytes=target.stat().st_size))
        return target

    def claim(self, labels, identity):
        # Allocation-specific object keys and a local lock serialize this allocation.
        with (self.claims/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for label in labels:
                key = self.names['objects'][label] + '.j' + self.job
                p = self.claims/(hashlib.sha256(key.encode()).hexdigest()+'.json')
                if p.exists():
                    if read(p)['identity'] == identity:
                        return label, key
                else:
                    put(p, dict(identity=identity, object=key, job=self.job))
                    return label, key
        raise ValueError('E97')

    def session_bytes(self):
        # Pin both opened objects; never follow a replaced directory or file link.
        directory = None
        try:
            try:
                directory = os.open(self.sessions.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            except FileNotFoundError:
                raise ValueError('directory missing') from None
            except OSError:
                raise ValueError('directory inaccessible') from None
            info = os.fstat(directory)
            if info.st_uid != os.getuid():
                raise ValueError('directory owner')
            if stat.S_IMODE(info.st_mode) != 0o700:
                raise ValueError('directory mode')
            try:
                info = os.stat(self.sessions.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                raise ValueError('file missing') from None
            if stat.S_ISLNK(info.st_mode):
                raise ValueError('file symlink')
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('file not regular')
            fd = os.open(self.sessions.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, 'rb') as stream:
                current = os.fstat(stream.fileno())
                if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                    raise ValueError('file changed')
                if current.st_uid != os.getuid(): raise ValueError('file owner')
                if stat.S_IMODE(current.st_mode) != 0o600:
                    raise ValueError('file mode')
                raw = stream.read()
            try:
                values = json.loads(raw)
            except (ValueError, UnicodeError):
                raise ValueError('invalid JSON') from None
            if not isinstance(values, dict):
                raise ValueError('not an object')
            for name, value in values.items():
                if not isinstance(name, str) or not name or not isinstance(value, str):
                    raise ValueError('invalid mapping')
                try:
                    url = urlsplit(value)
                    valid = url.scheme in ('http', 'https') and bool(url.netloc)
                except ValueError:
                    valid = False
                if not valid:
                    raise ValueError('invalid URL')
            return raw
        except OSError:
            raise ValueError('file inaccessible') from None
        finally:
            if directory is not None:
                os.close(directory)

    def send(self, directory, marker, labels, archive=None):
        remaining=self.upload_until-time.time()
        if remaining<=0:return
        old=signal.getsignal(signal.SIGALRM)
        def expired(*_):raise TimeoutError('E104 reserved publication window')
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,remaining)
        try:return self._send(directory,marker,labels,archive=archive)
        except TimeoutError as error:
            self.note('upload',error)
            with (self.spool/'upload.log').open('a') as f:
                f.write(json.dumps(dict(time=time.time(),name=directory.name,http=None,range=None,error=masked(repr(error))))+'\n')
            put(self.state/('gcs_'+directory.name+'.json'),dict(status='upload pending retry',returncode=124))
            receipts=self.spool/'private/sess.json.receipts.jsonl'
            if not receipts.exists() or not receipts.stat().st_size:
                put(self.state/'UPLOAD_NO_RECEIPTS.json',dict(status='FAIL',object=directory.name,returncode=124))
                print('UPLOAD_NO_RECEIPTS '+directory.name+' rc=124',file=sys.stderr,flush=True)
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)

    def _send(self, directory, marker, labels, archive=None):
        if self.upload_until<=time.time():return
        identity = sha(marker)
        done = self.state/('gcs_'+directory.name+('_stop' if labels == ['ckstop'] else '')+'.done')
        if done.exists():
            if read(done)['marker_sha256'] != identity:
                raise ValueError('E98')
            return
        archive = self.archive(directory, marker) if archive is None else Path(archive)
        raw = self.cached_sessions()
        label, key = self.claim(labels, identity)
        local = self.spool/'private/sess.json'
        command = [sys.executable, '-I', '-s', '-B', str(Path(__file__).resolve()), '--writer',
                   str(self.writer), 'split', str(local), key, str(archive), '4', '4']
        # Test writers retain the same interface; production always uses the sealed gc.py.
        if self.writer.name != 'gc.py': command=[sys.executable,'-I','-s','-B',str(self.writer),'split',str(local),key,str(archive),'4','4']
        remaining=self.upload_until-time.time()
        if remaining<=0: return
        try:
            result=subprocess.run(command,capture_output=True,text=True,
                timeout=max(.1,remaining),env={**os.environ,'TK_UPLOAD_DEADLINE':str(self.upload_until),
                'TK_UPLOAD_LOG':str(self.spool/'upload.log'),
                'TK_PRIORITY_TRAIN':str(self.train) if label.startswith('ck') and label!='ckstop' else '',
                'TK_PRIORITY_STATE':str(self.state),
                'TK_NOMINAL_STOP':str(self.nominal_stop()),
                'TK_DIAGNOSTIC_PREFIX':'1' if getattr(self,'diagnostic_prefix',False) else '0'})
            rc=result.returncode
            with (self.spool/'upload.log').open('a') as f:
                f.write(masked((result.stdout or '')+(result.stderr or '')))
                f.write(json.dumps(dict(time=time.time(),name=key,http=None,range=None,returncode=rc,error=masked(result.stderr) if rc else None))+'\n')
        except subprocess.TimeoutExpired as error:
            rc=124;self.note('upload',error)
        receipts=Path(str(local)+'.receipts.jsonl')
        if not receipts.exists() or not receipts.stat().st_size:
            put(self.state/'UPLOAD_NO_RECEIPTS.json',dict(status='FAIL',object=key,returncode=rc))
            print('UPLOAD_NO_RECEIPTS '+key+' rc='+str(rc),file=sys.stderr,flush=True)
            self.attempt('logs',self.small)
        if rc:
            put(self.state/('gcs_'+directory.name+'.json'), dict(status='upload pending retry', object=key, returncode=rc))
            return
        if getattr(self,'diagnostic_prefix',False):return
        receipts = Path(str(local)+'.receipts.jsonl')
        parts = {v['name']:v for v in (json.loads(line) for line in receipts.read_text().splitlines())}
        cursor = 0
        with archive.open('rb') as f:
            for i in range(4):
                v = parts[key+f'.part{i:02d}-of-04']
                if v['offset'] != cursor or not v.get('generation'):
                    raise ValueError('E99')
                h, left = hashlib.sha256(), v['bytes']
                while left:
                    b = f.read(min(left, 1 << 20))
                    if not b:
                        raise ValueError('E99')
                    h.update(b); left -= len(b)
                if h.hexdigest() != v['sha256']:
                    raise ValueError('E99')
                cursor += v['bytes']
        if cursor != archive.stat().st_size:
            raise ValueError('E99')
        put(done, dict(object=key, bytes=cursor, sha256=sha(archive), marker_sha256=identity, generation=label))

    def exports(self):
        markers=list(self.train.glob('m*/artifact.json'))
        stop_step=max([read(p).get('step',-1) for p in self.train.glob('checkpoint_*/complete.json')]+[-1]) if self.stop_ready() else -1
        markers.sort(key=lambda p: (p.parent.name!='m'+str(stop_step), p.parent.name in self.names['objects'], -int(p.parent.name[1:]) if p.parent.name[1:].isdigit() else 0))
        for marker in markers:
            if not marker.parent.name[1:].isdigit():
                continue
            step = int(marker.parent.name[1:])
            labels = ['m'+str(step)] if 'm'+str(step) in self.names['objects'] else ['mstop','mstopB','mstopC']
            try:
                self.send(marker.parent, marker, labels)
            except Exception as error:
                put(self.state/('gcs_'+marker.parent.name+'.json'),
                    dict(status='pending retry', error=type(error).__name__))

    def nominal_stop(self):
        recipe=self.cfg.get('recipe',{})
        if not os.environ.get('TK_JOB_START'):return float('inf')
        return float(os.environ['TK_JOB_START'])+recipe['wall_seconds']-recipe['stop_before_seconds']

    def stop_marker(self):
        markers=list(self.train.glob('checkpoint_*/complete.json'))
        if not markers:return None
        latest=lambda rows:max(rows,key=lambda p:(read(p).get('step',-1),p.stat().st_mtime_ns))
        if self.final_pass or list(self.train.glob('run_*.json')):return latest(markers)
        threshold=self.nominal_stop()
        request=self.spool/'stop.request'
        if request.exists():threshold=min(threshold,request.stat().st_mtime)
        eligible=[p for p in markers if p.stat().st_mtime>=threshold]
        return latest(eligible) if eligible else None

    def stop_checkpoint(self):
        marker=self.stop_marker()
        if marker is None:
            put(self.state/'ckstop.json',dict(status='no completed checkpoint'))
            return
        identity=sha(marker);directory=marker.parent
        ordinary=self.state/('gcs_'+directory.name+'.done')
        stop=self.state/('gcs_'+directory.name+'_stop.done')
        if ordinary.exists() and read(ordinary).get('marker_sha256')==identity:
            receipt=read(ordinary)
            put(stop,{**receipt,'reused_ordinary':True})
            put(self.state/'ckstop.json',dict(status='gcs',marker_sha256=identity,
                reused_ordinary=True,object=receipt['object'],receipt=str(stop)))
            return
        self.send(directory,marker,['ckstop'])
        put(self.state/'ckstop.json',dict(status='gcs' if stop.exists() else 'left node-local',marker_sha256=identity))

    def checkpoints(self):
        settled = priority_settled(self.train, self.state, self.nominal_stop())
        if (self.stop_requested() or self.priority_pending()) and not settled:return
        stop = self.stop_marker()
        markers = sorted(self.train.glob('checkpoint_*/complete.json'),
                         key=lambda p:(read(p).get('step',-1),p.stat().st_mtime_ns), reverse=True)
        for marker in markers:
            if time.time() >= min(self.upload_until, self.archive_due):break
            if marker == stop or (self.state/('gcs_'+marker.parent.name+'_stop.done')).exists():continue
            self.attempt('checkpoint',lambda marker=marker:self.send(
                marker.parent,marker,['ck%02d'%i for i in range(16)]))

    def stop_ready(self):
        return self.final_pass or self.stop_marker() is not None

    def stop_requested(self):
        return self.stop_ready() or (self.spool/'stop.request').exists() or time.time()>=self.nominal_stop()

    def diagnostics(self, final=False):
        # Four fixed 512 KiB parts. Part 0 is durable after the archive settles;
        # unsubmitted parts 1-3 hold the final tail. Completed parts never change.
        if 'u' not in self.names['objects']:return
        folder=self.spool/'u';folder.mkdir(exist_ok=True)
        marker=folder/'complete.json';payload=folder/'u.log'
        block=512*1024
        def tail(cap):
            source=self.spool/'upload.log'
            if not source.exists():return b'\n'
            with source.open('rb') as f:
                f.seek(max(0,source.stat().st_size-cap));raw=f.read(cap)
            raw=masked(raw.decode('utf-8','replace')).encode()[-cap:]
            if len(raw)==cap:raw=raw.partition(b'\n')[2]
            return raw+b'\n'
        def padded(raw,size):return raw[:size].ljust(size,b'\n')
        if not marker.exists():
            atomic(payload,padded(tail(block-1),block)+b'\n'*(3*block))
            put(marker,dict(kind='u'))
        if final and not (folder/'frozen.json').exists():
            atomic(payload,payload.read_bytes()[:block]+padded(tail(3*block-1),3*block))
            put(folder/'frozen.json',dict(sha256=sha(payload)))
        self.diagnostic_prefix=not final
        try:self.send(folder,marker,['u'],archive=payload)
        finally:self.diagnostic_prefix=False

    def priority_pending(self):
        if self.stop_requested() and not self.stop_ready():return True
        markers=list(self.train.glob('checkpoint_*/complete.json'))
        if markers and self.stop_ready():
            marker=max(markers,key=lambda p:(read(p).get('step',-1),p.stat().st_mtime_ns))
            if not (self.state/('gcs_'+marker.parent.name+'_stop.done')).exists():return True
        for marker in self.train.glob('m*/artifact.json'):
            if not (self.state/('gcs_'+marker.parent.name+'.done')).exists():return True
        return False

    def incomplete(self):
        if self.priority_pending():return True
        for marker in self.train.glob('checkpoint_*/complete.json'):
            if not any((self.state/('gcs_'+marker.parent.name+suffix+'.done')).exists() for suffix in ('','_stop')):return True
        if not self.logs_complete:return True
        if not all((self.state/n).is_file() for n in ('gcs_o.done','o_copy.done')):return True
        return read(self.state/'gcs_o.done').get('sha256')!=read(self.state/'o_copy.done').get('sha256')

    def pass_once(self, final=False, small=True):
        self.paths(); self.cached_sessions()
        with (self.spool/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.final_pass = final
            frozen=(self.state/'gcs_o.done').exists()
            self.upload_until=self.deadline if frozen else self.archive_due
            for label, action in [('stop',self.stop_checkpoint),('exports',self.exports),
                                  ('logs',self.small),('o',self.exit_archive),('u',self.diagnostics),('checkpoints',self.checkpoints)]:
                if time.time()>=self.deadline:break
                if label=='u' and (not final or not (self.state/'o_frozen.json').exists()):continue
                if label=='stop' and not self.stop_ready():continue
                if label=='checkpoints' and (self.stop_requested() or self.priority_pending()) and not priority_settled(self.train,self.state,self.nominal_stop()):continue
                if label=='o' and not final:continue
                if label=='logs' and not small:continue
                if label in ('logs','o'):self.upload_until=self.deadline
                if label=='checkpoints':self.upload_until=min(self.archive_due,self.data_deadline)
                if final:self.upload_until=min(self.upload_until,self.data_deadline)
                with (self.spool/'final_order.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(phase=label,time=time.time(),final=final))+'\n')
                result=self.attempt(action.__name__,action)
                if label=='u':
                    # The durable log prefix settles before ordinary data; its final
                    # tail remains reserved for diagnostics of subsequent retries.
                    put(self.state/'priority_settled.json',priority_version(self.train,self.state,self.nominal_stop()))
                if label=='stop':self.stop_settled=True
                if label=='logs':
                    self.logs_complete=result is not None
                    if self.logs_complete:put(self.state/'logs.done',dict(time=time.time()))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('kit');p.add_argument('root');p.add_argument('job')
    p.add_argument('--loop', action='store_true');p.add_argument('--final', action='store_true')
    p.add_argument('--small', action='store_true')
    p.add_argument('--loop-small', action='store_true')
    p.add_argument('--sessions')
    p.add_argument('--prepare', action='store_true')
    p.add_argument('--status', type=int, default=0)
    args = p.parse_args()
    c = Copier(args.kit,args.root,args.job,sessions=args.sessions)
    c.exit_status = args.status if args.final else None
    if args.prepare:
        return
    if args.small:
        c.attempt('small', c.small)
        return
    stop = [False]
    for sig in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT):
        signal.signal(sig, lambda *_:stop.__setitem__(0,True))
    if args.loop_small:
        while not stop[0]:
            c.attempt('small', c.small)
            for _ in range(600):
                if stop[0]:break
                time.sleep(1)
        c.attempt('small', c.small)
        return
    last = 0.
    final_end = c.data_deadline
    while True:
        now = time.monotonic()
        c.attempt('pass', lambda: c.pass_once(final=args.final, small=not args.loop))
        if now-last>=600:
            last=now
        if not args.loop:
            if args.final and time.time() < final_end and c.incomplete():
                time.sleep(2)
                continue
            if args.final:
                c.upload_until=c.deadline
                while time.time()<c.deadline and not (c.state/'gcs_u.done').exists():
                    c.attempt('u_final',lambda:c.diagnostics(final=True))
                    if not (c.state/'gcs_u.done').exists():time.sleep(.2)
            return
        for _ in range(10):
            if stop[0]:
                return
            time.sleep(1)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--seconds':
        print(max(1,int(deadline()-time.time())));sys.exit(0)
    if len(sys.argv)>1 and sys.argv[1]=='--writer':sys.exit(writer_main(sys.argv[2:]))
    main()
