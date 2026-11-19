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

    def walk_error(error):
        skips['io'] += 1

    try:
        # fwalk protects traversal against a directory being replaced by a link.
        for d, dirs, files, dfd in os.fwalk('.', follow_symlinks=False, onerror=walk_error):
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
                import tempfile
                with deadline():
                    for unused in range(100):
                        tmp = '.dedup-' + next(tempfile._get_candidate_names())
                        try:
                            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                         0o600, dir_fd=dfd)
                            break
                        except FileExistsError:
                            continue
                    else:
                        raise OSError('cannot allocate manifest file')
                    with os.fdopen(fd, 'wb') as raw:
                        with gzip.GzipFile(filename=name, mode='wb', fileobj=raw) as g:
                            g.write(''.join(x + '\n' for x in dups).encode('utf-8', 'surrogateescape'))
                    os.rename(tmp, name, src_dir_fd=dfd, dst_dir_fd=dfd)
                out.write(os.path.join(mdir, name).encode('utf-8', 'surrogateescape') + b'\0')
            finally:
                os.close(dfd)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        sys.stderr.write('STATS %s files=%d bytes=%d dups=%d skipped_oversize=%d skipped_bigdirs=%d %s %s\n'
                         % (label, n, tot, len(dups), big, len(bigdirs), ' '.join(bigdirs[:20]),
                            ' '.join('skipped_%s=%d' % (k, skips[k]) for k in sorted(skips))))


if os.environ.get('LCS_ROBUST_SYNC', '0') == '1':
    robust_scan()
    sys.exit(0)

