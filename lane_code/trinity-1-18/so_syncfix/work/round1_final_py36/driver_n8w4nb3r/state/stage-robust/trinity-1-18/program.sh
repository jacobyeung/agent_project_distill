set -u
cd /scratch/jjyeung/orch_n30/so_syncfix/work/round1_final_py36/driver_n8w4nb3r/sources/trinity-3-30 2>/dev/null || { echo SKIP\ trinity-1-18\ no\ orch_n30/source; exit 66; }
timeout --kill-after=0.15 0.9 env LCS_ROBUST_SYNC=1 LCS_FILE_SECONDS=30 python3 - trinity-1-18 code_sync/meta > /dev/null <<'LCS_FILTER_EOF'
# lane_code_filter.py <label> [manifest_dir]: run with cwd = the tree to sync.
# Prints NUL-separated relative paths of whitelisted agent-written files, one copy per distinct content;
# later identical copies are listed in <manifest_dir>/DEDUP_<label>.tsv.gz ("dup_path<TAB>kept_path") and
# that manifest path is printed last. Stats go to stderr.
import gzip, hashlib, os, re, stat, sys
EXT = ('.py', '.sh', '.md', '.json', '.jsonl', '.yaml', '.yml', '.toml', '.cfg', '.txt', '.patch', '.diff', '.tpl', '.ini', '.tsv')
MAXB = 512 * 1024
DATA_MAXB = 256 * 1024  # .json/.jsonl above this are data rows or result dumps
MAXDIR = 2000
SUBSTR = ('out/devin_traces', '/dl/', '/root/', '/envs/', 'site-packages', '__pycache__', '.cache', 'node_modules')
# Scratch copies, test/mutation outputs, caches, vendored libraries, data rows and result dumps.
DIRRE = re.compile(r'^(tmp.*|retained_.*|rows_.*|slices_v\d+|.*proofs?|.*_proof|artifacts|r2_[a-z0-9_]{8}|rec_v\d.*'
                   r'|.*_stale|.*_prev|cmp_.*|test_products|results|clone|mutation.*|mut|mut_.*|.*_mut|round_.*'
                   r'|.*cache.*|scipy|numpy|torch|.*\.dist-info|.*\.egg-info|runs|evidence|transactions|env\d*|venv|\.venv)$')
def robust_scan():
    """Linux/Python 3.6: anchor traversal to directory fds and bound each read."""
    import contextlib
    import errno
    import signal

    class ReadDeadline(Exception):
        pass

    def alarm(signum, frame):
        raise ReadDeadline()

    seconds = float(os.environ.get('LCS_FILE_SECONDS', '3'))
    if not 0 < seconds <= 30:
        raise ValueError('LCS_FILE_SECONDS must be in (0, 30]')

    @contextlib.contextmanager
    def deadline():
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    previous = signal.signal(signal.SIGALRM, alarm)
    label = sys.argv[1] if len(sys.argv) > 1 else '?'
    mdir = sys.argv[2] if len(sys.argv) > 2 else None
    n = tot = big = 0
    bigdirs, dups, seen = [], [], {}
    skips = dict(nonregular=0, symlink=0, timeout=0, io=0, changed=0)
    out = sys.stdout.buffer
    flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW

    def safe_walk(path, dfd):
        # Python 3.6 fwalk opens child directories without O_NOFOLLOW/O_NONBLOCK.
        # Keep these flags on directory opens as well as on file opens.
        try:
            with deadline():
                names = os.listdir(dfd)
        except ReadDeadline:
            skips['timeout'] += 1
            return
        except OSError:
            skips['io'] += 1
            return
        dirs, files = [], []
        for name in names:
            try:
                with deadline():
                    mode = os.lstat(name, dir_fd=dfd).st_mode
                if stat.S_ISDIR(mode):
                    dirs.append(name)
                elif stat.S_ISLNK(mode):
                    skips['symlink'] += 1
                else:
                    files.append(name)
            except ReadDeadline:
                skips['timeout'] += 1
            except OSError:
                skips['io'] += 1
        yield path, dirs, files, dfd
        # The caller prunes and sorts dirs before recursion resumes.
        for name in dirs:
            child = None
            try:
                with deadline():
                    mode = os.lstat(name, dir_fd=dfd).st_mode
                    if not stat.S_ISDIR(mode):
                        skips['symlink' if stat.S_ISLNK(mode) else 'nonregular'] += 1
                        continue
                    child = os.open(name, flags | os.O_DIRECTORY, dir_fd=dfd)
                yield from safe_walk(os.path.join(path, name), child)
            except ReadDeadline:
                skips['timeout'] += 1
            except OSError as error:
                skips['changed' if error.errno == errno.ENOTDIR else 'io'] += 1
            finally:
                if child is not None:
                    os.close(child)

    rootfd = None
    try:
        rootfd = os.open('.', flags | os.O_DIRECTORY)
        for d, dirs, files, dfd in safe_walk('.', rootfd):
            p = '/' + d[2:] + '/' if d != '.' else '/'
            keep = []
            for x in dirs:
                q = p + x + '/'
                if x == '.git' or 'frames' in x or DIRRE.match(x) or any(s in q for s in SUBSTR):
                    continue
                fd = None
                try:
                    with deadline():
                        st = os.lstat(x, dir_fd=dfd)
                        if stat.S_ISLNK(st.st_mode):
                            skips['symlink'] += 1
                            continue
                        if not stat.S_ISDIR(st.st_mode):
                            skips['nonregular'] += 1
                            continue
                        fd = os.open(x, flags | os.O_DIRECTORY, dir_fd=dfd)
                        if len(os.listdir(fd)) > MAXDIR:
                            bigdirs.append(q[1:])
                            continue
                        keep.append(x)
                except ReadDeadline:
                    skips['timeout'] += 1
                except OSError:
                    skips['io'] += 1
                finally:
                    if fd is not None:
                        os.close(fd)
            dirs[:] = sorted(keep)
            for f in sorted(files):
                if not f.endswith(EXT) or f.endswith('.sqlite') or any(s in p + f for s in SUBSTR):
                    continue
                fd = None
                try:
                    with deadline():
                        st = os.lstat(f, dir_fd=dfd)
                        if not stat.S_ISREG(st.st_mode):
                            skips['symlink' if stat.S_ISLNK(st.st_mode) else 'nonregular'] += 1
                            continue
                        limit = DATA_MAXB if f.endswith(('.json', '.jsonl')) else MAXB
                        if st.st_size > limit:
                            big += 1
                            continue
                        fd = os.open(f, flags, dir_fd=dfd)
                        opened = os.fstat(fd)
                        if not stat.S_ISREG(opened.st_mode):
                            skips['nonregular'] += 1
                            continue
                        if (st.st_dev, st.st_ino) != (opened.st_dev, opened.st_ino):
                            skips['changed'] += 1
                            continue
                        data = bytearray()
                        while len(data) <= limit:
                            chunk = os.read(fd, min(65536, limit + 1 - len(data)))
                            if not chunk:
                                break
                            data.extend(chunk)
                        if len(data) > limit:
                            big += 1
                            continue
                        after = os.fstat(fd)
                        if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
                                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                            skips['changed'] += 1
                            continue
                        h = hashlib.sha1(data).hexdigest()
                        sz = opened.st_size
                except ReadDeadline:
                    skips['timeout'] += 1
                    continue
                except OSError as error:
                    skips['symlink' if error.errno == errno.ELOOP else 'io'] += 1
                    continue
                finally:
                    if fd is not None:
                        os.close(fd)
                rel = os.path.join(d, f)[2:]
                if h in seen:
                    dups.append(rel + '\t' + seen[h])
                    continue
                seen[h] = rel
                n += 1
                tot += sz
                out.write(rel.encode('utf-8', 'surrogateescape') + b'\0')
        if mdir:
            # Refuse absolute/parent paths and links in the manifest destination.
            parts = mdir.split('/')
            if os.path.isabs(mdir) or '..' in parts:
                raise ValueError('manifest directory must stay within the scan root')
            dfd = os.open('.', flags | os.O_DIRECTORY)
            try:
                for part in parts:
                    if part in ('', '.'):
                        continue
                    try:
                        os.mkdir(part, dir_fd=dfd)
                    except FileExistsError:
                        pass
                    nextfd = os.open(part, flags | os.O_DIRECTORY, dir_fd=dfd)
                    os.close(dfd)
                    dfd = nextfd
                name = 'DEDUP_%s.tsv.gz' % label.replace('/', '_')
                # O_EXCL prevents opening a pre-existing special file or hard link.
                # Replace by rename from a unique regular file, never by following it.
                import uuid
                # The enclosing scan timeout bounds manifest construction/compression.
                # Log the temporary name BEFORE creation, including for SIGKILL/ENOSPC.
                tmp = None
                try:
                    for unused in range(100):
                        candidate = '.dedup-' + uuid.uuid4().hex
                        sys.stderr.write('MANIFEST_PENDING %s\n' % os.path.join(mdir, candidate))
                        sys.stderr.flush()
                        try:
                            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                         0o600, dir_fd=dfd)
                            tmp = candidate
                            break
                        except FileExistsError:
                            continue
                    else:
                        raise OSError('cannot allocate manifest file')
                    with os.fdopen(fd, 'wb') as raw:
                        with gzip.GzipFile(filename=name, mode='wb', fileobj=raw) as g:
                            g.write(''.join(x + '\n' for x in dups).encode('utf-8', 'surrogateescape'))
                    os.rename(tmp, name, src_dir_fd=dfd, dst_dir_fd=dfd)
                    tmp = None
                finally:
                    if tmp is not None:
                        sys.stderr.write('MANIFEST_LEFTOVER %s\n' % os.path.join(mdir, tmp))
                        sys.stderr.flush()
                out.write(os.path.relpath(os.path.join(mdir, name)).encode('utf-8', 'surrogateescape') + b'\0')
            finally:
                os.close(dfd)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if rootfd is not None:
            os.close(rootfd)
        signal.signal(signal.SIGALRM, previous)
        sys.stderr.write('STATS %s files=%d bytes=%d dups=%d skipped_oversize=%d skipped_bigdirs=%d %s %s\n'
                         % (label, n, tot, len(dups), big, len(bigdirs), ' '.join(bigdirs[:20]),
                            ' '.join('skipped_%s=%d' % (k, skips[k]) for k in sorted(skips))))


if os.environ.get('LCS_ROBUST_SYNC', '0') == '1':
    robust_scan()
    sys.exit(0)


label = sys.argv[1] if len(sys.argv) > 1 else '?'
mdir = sys.argv[2] if len(sys.argv) > 2 else None
n = 0; tot = 0; big = 0; bigdirs = []; dups = []; seen = {}; out = sys.stdout.buffer
for d, dirs, files in os.walk('.', followlinks=False):
    p = '/' + d[2:] + '/' if d != '.' else '/'
    keep = []
    for x in dirs:
        q = p + x + '/'
        if x == '.git' or 'frames' in x or DIRRE.match(x) or any(s in q for s in SUBSTR):
            continue
        try:
            if len(os.listdir(os.path.join(d, x))) > MAXDIR:
                bigdirs.append(q[1:]); continue
        except OSError:
            continue
        keep.append(x)
    dirs[:] = sorted(keep)
    for f in sorted(files):
        if not f.endswith(EXT) or f.endswith('.sqlite'):
            continue
        fp = os.path.join(d, f)
        if any(s in p + f for s in SUBSTR):
            continue
        try:
            st = os.lstat(fp)
            if not stat.S_ISREG(st.st_mode):
                continue
            sz = st.st_size
            if sz > MAXB or (sz > DATA_MAXB and f.endswith(('.json', '.jsonl'))):
                big += 1; continue
            h = hashlib.sha1(open(fp, 'rb').read()).hexdigest()
        except OSError:
            continue
        rel = fp[2:]
        if h in seen:
            dups.append(rel + '\t' + seen[h]); continue
        seen[h] = rel; n += 1; tot += sz
        out.write(rel.encode('utf-8', 'surrogateescape') + b'\0')
if mdir:
    os.makedirs(mdir, exist_ok=True)
    mp = os.path.join(mdir, 'DEDUP_%s.tsv.gz' % label.replace('/', '_'))
    with gzip.open(mp, 'wt', encoding='utf-8', errors='surrogateescape') as g:
        g.write(''.join(x + '\n' for x in dups))
    out.write(os.path.relpath(mp).encode() + b'\0')
sys.stderr.write('STATS %s files=%d bytes=%d dups=%d skipped_oversize=%d skipped_bigdirs=%d %s\n'
                 % (label, n, tot, len(dups), big, len(bigdirs), ' '.join(bigdirs[:20])))
LCS_FILTER_EOF
rc=("${PIPESTATUS[@]}"); echo "PIPE ${rc[*]}"; for r in "${rc[@]}"; do [ "$r" = 0 ] || exit 4; done
