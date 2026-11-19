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


class Copier:
    def __init__(self, kit, root, job, target=None, train=None, home=None, writer=None, sessions=None):
        self.kit, self.root = Path(kit).resolve(), Path(root).resolve()
        spec = read(self.kit/'k/p.json')
        self.cfg = read(self.kit/'k/n.json')
        self.target = Path(target or spec['n_root'])
        self.job = str(job)
        if not self.job.replace('_', '').isalnum():
            raise ValueError('E91')
        self.live = self.target/'o'/self.job/'live'
        self.live.mkdir(parents=True, exist_ok=True)
        self.spool = self.root/'live_spool'
        self.spool.mkdir(parents=True, exist_ok=True)
        # z.py resolve()/resolve600() bind the final cfg.output to namespace/r.
        self.train = Path(train) if train else self.root/'r'
        self.sessions = Path(sessions) if sessions is not None else (Path(home)/'sess.json' if home is not None else Path(spec['n_root'])/'n_s/sess.json')
        self.home = self.sessions.parent
        self.writer = Path(writer) if writer else self.kit/'b/gc.py'
        self.names = read(self.kit/'k/y.json')
        self.claims = self.target/'o'/'gcs_claims'
        self.claims.mkdir(parents=True, exist_ok=True)
        self.final_pass = False

    def small(self):
        with (self.spool/'small.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._small()

    def _small(self):
        # Each publication has one shared byte budget, including its manifest.
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
        return total + len(raw)

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
        # A global project-side lock serializes generations across allocations.
        with (self.claims/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for label in labels:
                key = self.names['objects'][label]
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

    def send(self, directory, marker, labels):
        identity = sha(marker)
        done = self.live/('gcs_'+directory.name+'.done')
        if done.exists():
            if read(done)['marker_sha256'] != identity:
                raise ValueError('E98')
            return
        archive = self.archive(directory, marker)
        try:
            raw = self.session_bytes()
        except ValueError as error:
            put(self.live/('gcs_'+directory.name+'.json'), dict(status='export not uploaded: sessions unusable ('+str(error)+')', archive=str(archive), marker_sha256=identity))
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
            put(self.live/('gcs_'+directory.name+'.json'), dict(status='upload pending retry', object=key, returncode=rc))
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
            self.send(marker.parent, marker, labels)

    def stop_checkpoint(self):
        # Select only a checkpoint at the reported final step. A signal may arrive
        # before run_*.json is written, in which case the latest completed state wins.
        markers = list(self.train.glob('checkpoint_*/complete.json'))
        if not markers:
            put(self.live/'ckstop.json', dict(status='no completed checkpoint'))
            return
        marker = max(markers, key=lambda p:(read(p).get('step', -1),p.stat().st_mtime_ns))
        identity = sha(marker)
        directory = marker.parent
        size = sum(p.stat().st_size+1024 for p in directory.rglob('*') if p.is_file())
        destination = self.target/'n_ck'/self.job
        if shutil.disk_usage(self.target).free >= size+RESERVE+10240:
            destination.mkdir(parents=True, exist_ok=True)
            done = destination/'complete.json'
            if done.exists():
                if read(done)['marker_sha256'] != identity:
                    raise ValueError('E98')
                return
            target = destination/(directory.name+'.tar')
            partial = target.with_name(target.name+'.part')
            # Stream directly to the project, without a second node-local copy.
            with tarfile.open(partial, 'w') as t:
                for p in sorted(directory.rglob('*')):
                    if p.is_symlink():
                        raise ValueError('E94')
                    if p.is_file():
                        t.add(p, arcname=str(p.relative_to(directory)), recursive=False)
            if sha(marker) != identity:
                raise ValueError('E96')
            os.replace(partial, target)
            result = dict(status='project', path=str(target), bytes=target.stat().st_size, sha256=sha(target), marker_sha256=identity)
            put(done, result); put(self.live/'ckstop.json', result)
        else:
            self.send(directory, marker, ['ckstop'])
            put(self.live/'ckstop.json', dict(status='gcs' if (self.live/('gcs_'+directory.name+'.done')).exists() else 'left node-local', marker_sha256=identity, reason='project free space below size plus 50 GiB'))

    def pass_once(self, final=False, small=True):
        with (self.spool/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.final_pass = final
            if small:
                self.small()
            for action in [self.exports] + ([self.stop_checkpoint] if final else []):
                try:
                    action()
                except Exception as e:
                    put(self.live/(action.__name__+'.json'), dict(status='pending retry', error=type(e).__name__))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('kit');p.add_argument('root');p.add_argument('job')
    p.add_argument('--loop', action='store_true');p.add_argument('--final', action='store_true')
    p.add_argument('--small', action='store_true')
    p.add_argument('--loop-small', action='store_true')
    p.add_argument('--sessions')
    args = p.parse_args()
    c = Copier(args.kit,args.root,args.job,sessions=args.sessions)
    if args.small:
        c.small()
        return
    stop = [False]
    for sig in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT):
        signal.signal(sig, lambda *_:stop.__setitem__(0,True))
    if args.loop_small:
        while not stop[0]:
            c.small()
            for _ in range(600):
                if stop[0]:break
                time.sleep(1)
        c.small()
        return
    last = 0.
    while True:
        now = time.monotonic()
        c.pass_once(final=args.final, small=not args.loop)
        if now-last>=600:
            last=now
        if not args.loop:
            return
        for _ in range(10):
            if stop[0]:
                c.pass_once(final=True,small=False)
                return
            time.sleep(1)


if __name__ == '__main__':
    main()
