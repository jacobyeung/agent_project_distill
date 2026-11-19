set -euo pipefail
MODE=$( /usr/bin/python3 -I -s -B - "$E" <<'REUSE_PY'
import hashlib
import os
import stat
import sys
from pathlib import Path

pin = {'archive_bytes': 1048576, 'archive_sha256': '362fc9457f902fbdcbc126e650dcb85ac23f5288bc2158714fc213beb5c1675a', 'object': 'q8/8865619b/6ed2c7aa_m600.tar'}
dest = Path(sys.argv[1])
fields = [pin['object'], str(pin['archive_bytes']), pin['archive_sha256']]
reuse = os.environ.get('REUSE_PARTS_FROM')
if reuse is None and os.environ.get('REUSE_SEARCH') == '1':
    root = Path('/scratch/jjyeung/orch_n30/cont_ops21_b/a600/rehearsal/link/run_5382bfda0d4d45a68ada4a0b7e9c992d/missing_part/KROOT')
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
    for part in parts:
        info = part.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size != pin['archive_bytes'] // 4:
            raise ValueError('Reuse part is not a regular file of pinned size: ' + str(part))
    digest = hashlib.sha256()
    for part in parts:
        with part.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
    if digest.hexdigest() != pin['archive_sha256']:
        raise ValueError('Reuse concatenated sha256 differs from m600 pin')
    for i in range(4):
        if os.path.lexists(str(dest/str(i))):
            raise ValueError('Reuse destination already exists: ' + str(dest/str(i)))
    for i, part in enumerate(parts):
        os.link(str(part), str(dest/str(i)), follow_symlinks=False)
    print('linked from %s; part 0 link count %d' % (source, (dest/'0').stat().st_nlink))
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
