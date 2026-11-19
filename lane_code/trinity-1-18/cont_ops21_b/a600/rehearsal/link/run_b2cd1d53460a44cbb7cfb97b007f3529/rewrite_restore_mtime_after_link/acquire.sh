set -euo pipefail
MODE=$( /usr/bin/python3 -I -s -B - "$E" <<'REUSE_PY'
import hashlib
import os
import stat
import sys
from contextlib import ExitStack
from pathlib import Path

pin = {'archive_bytes': 1048576, 'archive_sha256': '362fc9457f902fbdcbc126e650dcb85ac23f5288bc2158714fc213beb5c1675a', 'object': 'q8/8865619b/6ed2c7aa_m600.tar'}

mutation = ('rewrite_restore_mtime', 'after_link')
real_link = os.link
def change(part):
    part = Path(part)
    if mutation[0] == 'replace':
        part.rename(str(part)+'.original')
        # Identical content still must not pass an inode-identity check.
        part.write_bytes(Path(str(part)+'.original').read_bytes())
    elif mutation[0] == 'symlink':
        part.rename(str(part)+'.original')
        part.symlink_to(str(part)+'.original')
    else:
        saved = part.stat()
        with part.open('r+b') as stream:
            stream.write(b'CHANGED')
        if mutation[0] == 'rewrite_restore_mtime':
            os.utime(str(part), ns=(saved.st_atime_ns, saved.st_mtime_ns))
def racing_link(src, dst, **kwargs):
    if mutation[1] == 'before_link' and Path(dst).name == '0':
        change(src)
    result = real_link(src, dst, **kwargs)
    if mutation[1] == 'after_link' and Path(dst).name == '3':
        change(Path(src).parent/'0')
    return result
os.link = racing_link

dest = Path(sys.argv[1])
fields = [pin['object'], str(pin['archive_bytes']), pin['archive_sha256']]
reuse = os.environ.get('REUSE_PARTS_FROM')
if reuse is None and os.environ.get('REUSE_SEARCH') == '1':
    root = Path('/scratch/jjyeung/orch_n30/cont_ops21_b/a600/rehearsal/link/run_b2cd1d53460a44cbb7cfb97b007f3529/rewrite_restore_mtime_after_link/KROOT')
    with os.scandir(str(root)) as entries:
        names = sorted(e.name for e in entries if e.name.startswith('a15_cot_ap')
                       and e.is_dir(follow_symlinks=False))
    for name in names:
        source = root/name/'a/e'
        if source.resolve() == dest.resolve():
            continue
        try:
            marker = (source/'5').read_text().split()
        except FileNotFoundError:
            continue
        if marker == fields:
            reuse = str(source)
            break
if reuse is None:
    print('pull')
else:
    if not reuse:
        raise ValueError('REUSE_PARTS_FROM is empty')
    source = Path(reuse)
    if (source/'5').read_text().split() != fields:
        raise ValueError('Reuse marker differs from m600 pin')
    parts = [source/str(i) for i in range(4)]
    for i in range(4):
        if os.path.lexists(str(dest/str(i))):
            raise ValueError('Reuse destination already exists: ' + str(dest/str(i)))

    def identity(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

    def open_regular(part, stack):
        fd = os.open(str(part), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != pin['archive_bytes'] // 4:
            raise ValueError('Reuse part is not a regular file of pinned size: ' + str(part))
        return fd, info

    with ExitStack() as stack:
        sources = [open_regular(part, stack) for part in parts]
        records = [identity(info) for fd, info in sources]
        linked = [dest/str(i) for i in range(4)]
        ctimes = []
        for part, target in zip(parts, linked):
            os.link(str(part), str(target), follow_symlinks=False)
            ctimes.append(target.lstat().st_ctime_ns)

        def require_unchanged(info, i, path):
            if (not stat.S_ISREG(info.st_mode) or identity(info) != records[i]
                    or info.st_ctime_ns != ctimes[i]):
                raise ValueError('Reuse identity or timestamps changed: ' + str(path))

        def verify_paths(i):
            require_unchanged(os.fstat(sources[i][0]), i, parts[i])
            require_unchanged(parts[i].lstat(), i, parts[i])
            require_unchanged(linked[i].lstat(), i, linked[i])

        streams = []
        for i, target in enumerate(linked):
            verify_paths(i)
            fd, info = open_regular(target, stack)
            require_unchanged(info, i, target)
            streams.append(fd)
        digest = hashlib.sha256()
        for i, fd in enumerate(streams):
            verify_paths(i)
            require_unchanged(os.fstat(fd), i, linked[i])
            for chunk in iter(lambda: os.read(fd, 1024 * 1024), b''):
                digest.update(chunk)
            require_unchanged(os.fstat(fd), i, linked[i])
            verify_paths(i)
        for i, fd in enumerate(streams):
            require_unchanged(os.fstat(fd), i, linked[i])
            verify_paths(i)
        if digest.hexdigest() != pin['archive_sha256']:
            raise ValueError('Reuse concatenated sha256 differs from m600 pin')
        print('linked from %s; part 0 link count %d' % (source, os.fstat(streams[0]).st_nlink))
REUSE_PY
)
if [ "$MODE" = pull ]; then
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"; echo "$(date -u +%TZ) part $i"
done
  echo "pulled; part 0 link count $(stat -c %h "$E/0")"
else
  echo "$MODE"
fi
echo ACQUISITION_COMPLETE
