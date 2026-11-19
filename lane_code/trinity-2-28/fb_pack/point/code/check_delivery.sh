#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/fb_pack/point/out
sha256sum -c rows_pointing_locate.sqlite.sha256 receipt_pointing_locate.json.sha256 receipt_pointing_locate_staged.json.sha256 TRANSFORM.json.sha256 CHECKS.json.sha256 STAGING_PROPOSAL.json.sha256 fbp_point.tar.sha256
env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import hashlib,json,pathlib,tarfile
root=pathlib.Path.cwd().parent
checks=json.loads((root/'out/CHECKS.json').read_text())
assert checks['rows']==25020 and checks['strict_no_digits_except_frame']['fail_rows']==7
assert len((root/'out/REPORT.md').read_text().splitlines())<=80
with tarfile.open(root/'out/fbp_point.tar') as tf:
    names=tf.getnames()
    assert len(names)==len(set(names)) and 'out/rows_pointing_locate.sqlite' in names
    for member in tf:
        assert member.isfile() and not pathlib.PurePosixPath(member.name).is_absolute() and '..' not in pathlib.PurePosixPath(member.name).parts
        h=hashlib.sha256()
        with tf.extractfile(member) as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        g=hashlib.sha256()
        with (root/member.name).open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):g.update(block)
        assert h.digest()==g.digest(),member.name
print('Archive members match delivered files; report is within 80 lines; digit conflict remains disclosed.')
PY
