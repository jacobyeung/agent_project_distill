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
import stat
from urllib.parse import urlsplit
import subprocess
import sys
import tarfile
import time
import datetime
import runpy
import http.client
from concurrent.futures import ThreadPoolExecutor, as_completed

CAP = 50_000_000
LOG_CAP = 40_000_000
RESERVE = 50 * 1024**3
HASH_CACHE = {}


def read(p):
    v = json.loads(Path(p).read_text())
    return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v


def sha(p):
    p = Path(p)
    st = p.stat()
    key = (str(p),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    if key in HASH_CACHE: return HASH_CACHE[key]
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    HASH_CACHE[key] = h.hexdigest()
    return HASH_CACHE[key]


def atomic_bytes(p, raw, mode=0o600):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.part')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, p)
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def put(p, v):
    atomic_bytes(p, (json.dumps(v, sort_keys=True) + '\n').encode())


def allocation_end(cfg=None):
    value = os.environ.get('SLURM_JOB_END_TIME', '')
    if value:
        try: return float(value)
        except ValueError:
            try: return datetime.datetime.fromisoformat(value).timestamp()
            except ValueError: pass
    if os.environ.get('TK_JOB_START'):
        recipe = (cfg or {}).get('recipe', {})
        seconds = float(recipe.get('wall_seconds', 86400))
        return float(os.environ['TK_JOB_START']) + seconds
    return time.time() + 150


def deadlines(cfg=None):
    end = allocation_end(cfg)
    # Finish bulk data before TERM@600, with another 180 s for evidence.
    if os.environ.get('TK_JOB_START') or os.environ.get('SLURM_JOB_END_TIME'):
        return end - 780, end - 600
    return end - 20, end - 10


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
        private = self.spool/'private'
        private.mkdir(exist_ok=True, mode=0o700)
        cached = private/'sess.json'
        if not cached.exists():
            raw = self.session_bytes()
            atomic_bytes(cached, raw)
        self.session_bytes(cached)
        self.bulk_end, self.final_end = deadlines(self.cfg)



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
                error=type(error).__name__, errno=getattr(error,'errno',None)))+'\n')

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
        logs = [self.root/n for n in ('t.log', 'q.log', 'h.log', 'rooms.log') if (self.root/n).is_file()]
        # Share 40 MB fairly; every retained byte is from a log's tail.
        remaining = LOG_CAP
        for i, p in enumerate(logs):
            allowance = remaining // (len(logs) - i)
            with p.open('rb') as f:
                f.seek(max(0, p.stat().st_size - allowance))
                raw = f.read(allowance)
            pending.append((p.name, raw))
            remaining -= len(raw)
        for p in sorted(self.state.glob('*')):
            if p.is_file() and p.stat().st_size <= metadata_budget:
                raw = p.read_bytes(); pending.append((p.name, raw)); metadata_budget -= len(raw)
        total = 0
        for name, raw in pending:
            dest = self.live/name
            tmp = dest.with_name(dest.name + '.part')
            tmp.write_bytes(raw)
            os.replace(tmp, dest)
            total += len(raw)
            rows.append(dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        record = dict(time=int(time.time()), files=rows, payload_bytes=total, cap_bytes=CAP)
        raw = (json.dumps(record, sort_keys=True)+'\n').encode()
        assert total + len(raw) <= CAP
        (self.live/'copy.json').write_bytes(raw)
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
                os.replace(partial, destination)
        if (local/'o.tar').is_file() and (local/'RESULT.json').is_file():
            put(self.state/'o_copy.done', dict(sha256=sha(local/'o.tar')))

    def exit_archive(self):
        # The embedded shell can make a provisional archive while logs still grow.
        if not self.final_pass or self.priority_pending() or self.exports_pending():
            return
        archive = self.root/'o/o.tar'
        frozen = self.root/'o/frozen.json'
        if not frozen.is_file():
            with open('/dev/null', 'wb') as quiet:
                subprocess.run([sys.executable, '-I', '-s', '-B', str(self.kit/'b/o.py'),
                    str(self.root), str(self.exit_status or 0), '0', '--local', '--freeze'],
                    env={**os.environ, 'SLURM_JOB_ID':self.job},
                    stdout=quiet, stderr=quiet, check=True)
        if archive.is_file():
            if archive.stat().st_size > CAP:
                raise ValueError('E103')
            self.send(archive.parent, archive, ['o'], archive=archive)
            self.attempt('o_copy', self.copy_exit)

    def stop_marker(self):
        markers = list(self.train.glob('checkpoint_*/complete.json'))
        if not markers:
            return None
        latest = max(markers, key=lambda p:(read(p).get('step', -1),p.stat().st_mtime_ns))
        if self.final_pass:
            return latest
        # Native completion markers contain no stop bit. A completed run report
        # is the first unambiguous evidence available without changing the trainer.
        for report in self.train.glob('run_*.json'):
            value = read(report)
            step = value.get('last_step', value.get('step', value.get('end_step')))
            if value.get('stop_reason') and step == read(latest).get('step'):
                return latest
        return None

    def stop_export(self):
        marker = self.stop_marker()
        if marker is None:
            return None
        p = self.train/('m'+str(read(marker)['step']))/'artifact.json'
        return p if p.is_file() else None

    def priority_pending(self):
        marker = self.stop_marker()
        if marker is not None and not (self.state/('gcs_'+marker.parent.name+'_stop.done')).is_file():
            return True
        export = self.stop_export()
        return export is not None and not (self.state/('gcs_'+export.parent.name+'.done')).is_file()

    def exports_pending(self):
        return any(not (self.state/('gcs_'+p.parent.name+'.done')).is_file()
                   for p in self.train.glob('m*/artifact.json') if p.parent.name[1:].isdigit())

    def incomplete(self):
        pending = []
        if self.priority_pending(): pending.append('stop')
        if self.exports_pending(): pending.append('exports')
        for p in self.train.glob('checkpoint_*/complete.json'):
            if not (self.state/('gcs_'+p.parent.name+'.done')).is_file(): pending.append(p.parent.name)
        for label in ('logs.done','gcs_o.done','o_copy.done'):
            if not (self.state/label).is_file(): pending.append(label)
        return pending

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

    def session_bytes(self, path=None):
        path = Path(path) if path is not None else self.sessions
        # Pin both opened objects; never follow a replaced directory or file link.
        directory = None
        try:
            try:
                directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
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
                info = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                raise ValueError('file missing') from None
            if stat.S_ISLNK(info.st_mode):
                raise ValueError('file symlink')
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('file not regular')
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, 'rb') as stream:
                current = os.fstat(stream.fileno())
                if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                    raise ValueError('file changed')
                if current.st_uid != os.getuid():
                    raise ValueError('file owner')
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
            expected = {key+'.j'+self.job+f'.part{i:02d}-of-04'
                        for key in self.names['objects'].values() for i in range(4)}
            if set(values) != expected or len(expected) != 108:
                raise ValueError('E101')
            return raw
        except OSError:
            raise ValueError('file inaccessible') from None
        finally:
            if directory is not None:
                os.close(directory)

    def send(self, directory, marker, labels, archive=None):
        identity = sha(marker)
        done = self.state/('gcs_'+directory.name+('_stop' if labels == ['ckstop'] else '')+'.done')
        if done.exists():
            if read(done)['marker_sha256'] != identity:
                raise ValueError('E98')
            return
        archive = self.archive(directory, marker) if archive is None else Path(archive)
        local = self.spool/'private/sess.json'
        self.session_bytes(local)
        label, key = self.claim(labels, identity)
        command = [sys.executable, '-B', str(self.writer), 'split', str(local), key, str(archive), '4', '4']
        if self.writer == self.kit/'b/gc.py':
            command = [sys.executable, '-I', '-s', '-B', str(self.kit/'b/pc.py'), '--writer', *command[2:]]
        limit = self.final_end if labels == ['o'] else self.bulk_end
        if time.time() >= limit:
            return
        with open('/dev/null', 'wb') as quiet:
            rc = subprocess.run(command, stdout=quiet, stderr=quiet,
                env={**os.environ, 'TK_COPY_DEADLINE':str(limit)}).returncode
        if rc:
            put(self.state/('gcs_'+directory.name+'.json'), dict(status='upload pending retry', object=key, returncode=rc))
            return
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
        stop = self.stop_export()
        for marker in sorted(self.train.glob('m*/artifact.json'), key=lambda p:(p != stop, str(p))):
            if not marker.parent.name[1:].isdigit():
                continue
            step = int(marker.parent.name[1:])
            labels = ['m'+str(step)] if 'm'+str(step) in self.names['objects'] else ['mstop','mstopB','mstopC']
            try:
                self.send(marker.parent, marker, labels)
            except Exception as error:
                put(self.state/('gcs_'+marker.parent.name+'.json'),
                    dict(status='pending retry', error=type(error).__name__))

    def stop_checkpoint(self):
        # Select only a checkpoint at the reported final step. A signal may arrive
        # before run_*.json is written, in which case the latest completed state wins.
        marker = self.stop_marker()
        if marker is None:
            put(self.state/'ckstop.json', dict(status='no completed checkpoint'))
            return
        identity = sha(marker)
        directory = marker.parent
        size = sum(p.stat().st_size+1024 for p in directory.rglob('*') if p.is_file())
        self.send(directory, marker, ['ckstop'])
        put(self.state/'ckstop.json', dict(status='gcs' if
            (self.state/('gcs_'+directory.name+'_stop.done')).exists() else 'left node-local',
            marker_sha256=identity))

    def checkpoints(self):
        if not self.final_pass or self.priority_pending() or self.exports_pending():
            return
        for marker in sorted(self.train.glob('checkpoint_*/complete.json')):
            self.attempt('checkpoint', lambda marker=marker: self.send(
                marker.parent, marker, ['ck%02d'%i for i in range(16)]))

    def pass_once(self, final=False, small=True):
        self.paths()
        with (self.spool/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.final_pass = final
            phases = [('stop', [self.stop_checkpoint]),
                      ('exports', [self.exports]),
                      ('logs', [self.small] if small else []),
                      ('o', [self.exit_archive]),
                      ('checkpoints', [self.checkpoints])]
            for label, actions in phases:
                if final:
                    with (self.spool/'final_order.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(phase=label, time=time.time()))+'\n')
                for action in actions:
                    try:
                        action()
                        if final and label == 'logs': put(self.state/'logs.done', dict(complete=True))
                    except Exception as error:
                        self.note(action.__name__, error)


def upload_range(uri, path, offset, length, name, chunk, deadline):
    """Resume a part from the server's acknowledged offset, never from a guess."""
    started = time.monotonic()
    url = urlsplit(uri)
    route = url.path + ('?' + url.query if url.query else '?')

    def request(data, content_range):
        left = deadline-time.time()
        if left <= 0: raise TimeoutError('E104')
        conn = http.client.HTTPSConnection(url.netloc, timeout=max(.1, min(10, left)))
        try:
            conn.putrequest('PUT', route)
            conn.putheader('Content-Length', str(len(data)))
            conn.putheader('Content-Type', 'application/octet-stream')
            conn.putheader('Content-Range', content_range)
            conn.endheaders()
            if data: conn.send(data)
            reply = conn.getresponse(); raw = reply.read()
            if reply.status in (200, 201): return json.loads(raw), length
            if reply.status != 308: raise IOError('E105')
            accepted = reply.getheader('Range')
            cursor = int(accepted.rsplit('-', 1)[1])+1 if accepted else 0
            if not 0 <= cursor <= length: raise ValueError('E106')
            return None, cursor
        finally: conn.close()

    meta, cursor = request(b'', 'bytes */'+str(length))
    with open(path, 'rb') as stream:
        while meta is None and time.monotonic()-started < 4:
            if cursor >= length: raise IOError('E107')
            stream.seek(offset+cursor); data = stream.read(min(chunk, length-cursor))
            if not data: raise IOError('E108')
            before = cursor
            meta, cursor = request(data, f'bytes {cursor}-{cursor+len(data)-1}/{length}')
            if cursor != before+len(data): raise IOError('E109')
    if meta is None: return None
    md5, digest = hashlib.md5(), hashlib.sha256()
    with open(path, 'rb') as stream:
        stream.seek(offset); left = length
        while left:
            data = stream.read(min(chunk, left))
            if not data: raise IOError('E108')
            md5.update(data); digest.update(data); left -= len(data)
    if (int(meta['size']) != length or meta.get('name', name) != name
            or meta.get('md5Hash') != base64.b64encode(md5.digest()).decode()
            or not meta.get('generation')):
        raise ValueError('E110')
    return dict(name=name, bytes=length, offset=offset, md5=meta['md5Hash'],
                sha256=digest.hexdigest(), generation=meta['generation'],
                seconds=time.monotonic()-started, file=str(Path(path).resolve()))


def writer_main(args):
    helper, mode, local, key, path, count, parallel = args
    if mode != 'split' or count != '4': raise ValueError('E111')
    gc = runpy.run_path(helper, run_name='q_gc')
    sessions = read(local)
    receipts = Path(local+'.receipts.jsonl')
    rows = [json.loads(line) for line in receipts.read_text().splitlines()] if receipts.exists() else []
    prior = {r['name']:r for r in rows}
    timing_path = Path(local+'.timing.json')
    timing = read(timing_path) if timing_path.exists() else {}
    size = Path(path).stat().st_size; step = -(-size//4)
    deadline = float(os.environ['TK_COPY_DEADLINE'])
    jobs = [(name, i*step, max(0,min(step,size-i*step)))
            for i,name in enumerate(gc['part_names'](key,4))]
    todo = [j for j in jobs if not (j[0] in prior and prior[j[0]]['offset']==j[1]
                                   and prior[j[0]]['bytes']==j[2])]
    for name, _, _ in todo: timing.setdefault(name,time.time())
    put(timing_path,timing)
    pending = False
    with ThreadPoolExecutor(max_workers=min(4,int(parallel))) as pool:
        futures = [pool.submit(upload_range,sessions[n],path,o,l,n,gc['CHUNK'],deadline)
                   for n,o,l in todo]
        for future in as_completed(futures):
            try: row = future.result()
            except Exception: pending = True; continue
            if row is None: pending = True; continue
            row['seconds'] = time.time()-timing[row['name']]
            prior[row['name']] = row
            raw = ''.join(json.dumps(r,sort_keys=True)+'\n' for r in prior.values()).encode()
            atomic_bytes(receipts, raw)
    return int(pending)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--writer':
        return writer_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == '--seconds':
        print(max(1, int(deadlines()[1] - time.time()))); return
    p = argparse.ArgumentParser()
    p.add_argument('kit');p.add_argument('root');p.add_argument('job')
    p.add_argument('--loop', action='store_true');p.add_argument('--final', action='store_true')
    p.add_argument('--small', action='store_true')
    p.add_argument('--loop-small', action='store_true')
    p.add_argument('--sessions')
    p.add_argument('--prepare', action='store_true')
    p.add_argument('--status', type=int, default=0)
    p.add_argument('--payload')
    args = p.parse_args()
    c = Copier(args.kit,args.root,args.job,sessions=args.sessions)
    c.exit_status = args.status if args.final else None
    if args.prepare:
        return
    if args.payload:
        payload = Path(args.payload)
        while time.time() < c.bulk_end:
            c.send(payload.parent,payload,['ck01'],archive=payload)
            if (c.state/('gcs_'+payload.parent.name+'.done')).exists(): return 0
            time.sleep(1)
        return 1
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
    final_end = time.monotonic()+max(0, c.final_end-time.time())
    while True:
        now = time.monotonic()
        c.attempt('pass', lambda: c.pass_once(final=args.final, small=not args.loop))
        if now-last>=600:
            last=now
        if not args.loop:
            if args.final and time.monotonic() < final_end and c.incomplete():
                time.sleep(2)
                continue
            return
        for _ in range(1):
            if stop[0]:
                return
            time.sleep(1)


if __name__ == '__main__':
    raise SystemExit(main())
