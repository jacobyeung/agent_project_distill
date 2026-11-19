from pathlib import Path
p = Path('work/round1/tools/lane_code_filter.py')
s = p.read_text()
a = s.index('                with deadline():\n                    for unused in range(100):')
b = s.index('                out.write(os.path.relpath', a)
s = s[:a] + '''                # The enclosing scan timeout bounds manifest construction/compression.
                # Log the temporary name BEFORE creation, including for SIGKILL/ENOSPC.
                tmp = None
                try:
                    for unused in range(100):
                        candidate = '.dedup-' + uuid.uuid4().hex
                        sys.stderr.write('MANIFEST_PENDING %s\\n' % os.path.join(mdir, candidate))
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
                            g.write(''.join(x + '\\n' for x in dups).encode('utf-8', 'surrogateescape'))
                    os.rename(tmp, name, src_dir_fd=dfd, dst_dir_fd=dfd)
                    tmp = None
                finally:
                    if tmp is not None:
                        sys.stderr.write('MANIFEST_LEFTOVER %s\\n' % os.path.join(mdir, tmp))
                        sys.stderr.flush()
''' + s[b:]
p.write_text(s)
