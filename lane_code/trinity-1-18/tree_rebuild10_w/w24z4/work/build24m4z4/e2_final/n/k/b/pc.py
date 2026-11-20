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
    tmp.write_text(json.dumps(v, sort_keys=True) + '\n')
    os.replace(tmp, p)


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
            values = json.loads(raw)
            expected = {key+'.j'+self.job+f'.part{i:02d}-of-04'
                        for key in self.names['objects'].values() for i in range(4)}
            if not expected.issubset(values):
                raise ValueError('E101')
            fd = os.open(cached, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream: stream.write(raw)


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

    def exit_archive(self):
        archive = self.root/'o/o.tar'
        if not archive.is_file() and self.exit_status is not None:
            # The final pass reaches this only after the stop, exports and logs.
            with open('/dev/null', 'wb') as quiet:
                subprocess.run([sys.executable, '-I', '-s', '-B', str(self.kit/'b/o.py'),
                    str(self.root), str(self.exit_status), '0', '--local'],
                    env={**os.environ, 'SLURM_JOB_ID':self.job},
                    stdout=quiet, stderr=quiet, check=True)
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
        identity = sha(marker)
        done = self.state/('gcs_'+directory.name+('_stop' if labels == ['ckstop'] else '')+'.done')
        if done.exists():
            if read(done)['marker_sha256'] != identity:
                raise ValueError('E98')
            return
        archive = self.archive(directory, marker) if archive is None else Path(archive)
        try:
            raw = (self.spool/'private/sess.json').read_bytes()
        except ValueError as error:
            put(self.state/('gcs_'+directory.name+'.json'), dict(status='export not uploaded: sessions unusable ('+str(error)+')', archive=str(archive), marker_sha256=identity))
            return
        label, key = self.claim(labels, identity)
        # Session capabilities and their writer sidecars stay in node-local runtime storage.
        private = self.spool/'private'
        private.mkdir(exist_ok=True, mode=0o700)
        local = private/'sess.json'
        os.chmod(private, 0o700)
        fd = os.open(local, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
        # Never forward writer diagnostics: a transport exception may contain a capability URL.
        with open('/dev/null', 'wb') as quiet:
            rc = subprocess.run([sys.executable, '-B', str(self.writer), 'split', str(local), key, str(archive), '4', '4'], stdout=quiet, stderr=quiet).returncode
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
        for marker in sorted(self.train.glob('m*/artifact.json')):
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
        markers = list(self.train.glob('checkpoint_*/complete.json'))
        if not markers:
            put(self.state/'ckstop.json', dict(status='no completed checkpoint'))
            return
        marker = max(markers, key=lambda p:(read(p).get('step', -1),p.stat().st_mtime_ns))
        identity = sha(marker)
        directory = marker.parent
        size = sum(p.stat().st_size+1024 for p in directory.rglob('*') if p.is_file())
        self.send(directory, marker, ['ckstop'])
        put(self.state/'ckstop.json', dict(status='gcs' if
            (self.state/('gcs_'+directory.name+'_stop.done')).exists() else 'left node-local',
            marker_sha256=identity))

    def checkpoints(self):
        for marker in sorted(self.train.glob('checkpoint_*/complete.json')):
            self.attempt('checkpoint', lambda marker=marker: self.send(
                marker.parent, marker, ['ck%02d'%i for i in range(16)]))

    def pass_once(self, final=False, small=True):
        self.paths()
        with (self.spool/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.final_pass = final
            if final:
                phases = [('stop', [self.stop_checkpoint]),
                          ('exports', [self.exports, self.checkpoints]),
                          ('logs', [self.small] if small else []),
                          ('o', [self.exit_archive])]
                for label, actions in phases:
                    with (self.spool/'final_order.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(phase=label, time=time.time()))+'\n')
                    for action in actions:
                        self.attempt(action.__name__, action)
            else:
                if small:
                    self.attempt('small', self.small)
                for action in (self.checkpoints, self.exports, self.exit_archive):
                    self.attempt(action.__name__, action)


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
    while True:
        now = time.monotonic()
        c.attempt('pass', lambda: c.pass_once(final=args.final, small=not args.loop))
        if now-last>=600:
            last=now
        if not args.loop:
            if args.final and not (c.state/'gcs_o.done').is_file():
                time.sleep(2)
                continue
            return
        for _ in range(10):
            if stop[0]:
                return
            time.sleep(1)


if __name__ == '__main__':
    main()
