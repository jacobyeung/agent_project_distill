#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
S=/fixture/stage; PA=/fixture/package; E=$PA/a/e
OBJECT=q8/8865619b/6ed2c7aa_m600.tar; DONE=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m600.done
test -f "$DONE"; test ! -e "$E"; mkdir -m 700 "$E"
cp "$DONE" "$E/5"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json "$E/7"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json "$E/8"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/data_receipt.json "$E/9"
f=($(cat "$E/5")); test "${f[0]}" = "$OBJECT" && test "${f[1]}" = 21583032320 && test "${f[2]}" = 673c147c46bd5a64a991e023307b6e2676f1c2cb96c564ca236ab7c914e2c430
for n in 7:b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad 8:a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda 9:03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47; do test "$(sha256sum "$E/${n%%:*}" | cut -d' ' -f1)" = "${n#*:}"; done
MODE=$( /usr/bin/python3 -I -s -B - "$E" <<'REUSE_PY'
import hashlib
import os
import stat
import sys
from contextlib import ExitStack
from pathlib import Path

pin = {'object': 'q8/8865619b/6ed2c7aa_m600.tar', 'archive_bytes': 21583032320, 'archive_sha256': '673c147c46bd5a64a991e023307b6e2676f1c2cb96c564ca236ab7c914e2c430'}
dest = Path(sys.argv[1])
fields = [pin['object'], str(pin['archive_bytes']), pin['archive_sha256']]
reuse = os.environ.get('REUSE_PARTS_FROM')
if reuse is None and os.environ.get('REUSE_SEARCH') == '1':
    root = Path('/project/community/jjyeung/okh7')
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
for X in A; do
  P=$PA; T=03:00:00; D2=d2.py
  /usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
  PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
  if ! /usr/bin/python3 -I -s -B $S/d.py "$P/a/1.json" "$P/a/0.json" "$PREP" > "$S/dry_$X.out" 2>&1; then echo "$X DRY FAILED"; exit 1; fi
  (cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time $T)
  if ! /usr/bin/python3 -I -s -B $S/$D2 "$P" $S/w2$X > "$S/dry2_$X.out" 2>&1; then echo "$X DRY2 FAILED"; exit 1; fi
  printf '%s\n' 0 > "$P/a/1.txt"; echo "$(date -u +%TZ) $X filled, dry pass"
done
