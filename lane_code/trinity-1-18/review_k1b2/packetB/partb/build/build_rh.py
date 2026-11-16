"""Package the CPU interpreter and a complete, bounded rehearsal destination."""
import argparse
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import tarfile
import time

import job_support as H

ROOT = Path(__file__).resolve().parent
SCRIPT = '''#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
ROOT="$(pwd -P)"
mkdir -p jt/home jt/cache jt/temp
export SLURM_JOB_ID=424242
mkdir -p jt/job_tmp/$SLURM_JOB_ID
export HOME="$ROOT/jt/home" XDG_CACHE_HOME="$ROOT/jt/cache" TMPDIR="$ROOT/jt/temp"
export HF_HOME="$ROOT/jt/cache/hf" TORCH_HOME="$ROOT/jt/cache/torch" TRITON_CACHE_DIR="$ROOT/jt/cache/triton"
export TMP="$TMPDIR" TEMP="$TMPDIR" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
if [[ -e out ]]; then
    mv -- out "out_saved_$(date -u +%Y%m%dT%H%M%S)_$$"
fi
mkdir out
P="$ROOT/runtime/uv/bin/python3.12"
NP=/tmp/b7e31d84/runtime/uv/bin/python3.12
if [[ ! -x "$P" ]]; then
    P=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
    NP="$P"
fi
rc=0
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind "$ROOT/jt" /tmp \
    --bind "$ROOT" /tmp/b7e31d84 --chdir /tmp/b7e31d84 \
    --setenv HOME /tmp/home --setenv XDG_CACHE_HOME /tmp/cache \
    --setenv TMPDIR /tmp/temp --setenv TMP /tmp/temp --setenv TEMP /tmp/temp \
    --setenv HF_HOME /tmp/cache/hf --setenv TORCH_HOME /tmp/cache/torch \
    --setenv TRITON_CACHE_DIR /tmp/cache/triton --die-with-parent \
    "$NP" -I -s -B /tmp/b7e31d84/rh_prepare.py >out/outer.log 2>&1 || rc=$?
# Collection runs on the host even when the outer namespace never starts.
exec nice -n 19 "$P" -I -s -B rh_prepare.py --collect "$rc"
'''

class RateWriter:
    def __init__(self, stream, rate=8*1024**2):
        self.stream, self.rate, self.start, self.count = stream, rate, time.monotonic(), 0
        self.digest = hashlib.sha256()
    def write(self, data):
        self.count += len(data)
        if self.count >= 3_000_000_000:
            raise ValueError('RH archive reached its 3-GB cap')
        self.digest.update(data)
        result = self.stream.write(data)
        time.sleep(max(0, self.count / self.rate - (time.monotonic() - self.start)))
        return result
    def __getattr__(self, name):
        return getattr(self.stream, name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pack-env', action='store_true', help='Requires answered heavy-I/O permission')
    args = parser.parse_args()
    rh = ROOT / 'rh'
    rh.mkdir(exist_ok=True)
    (rh / 'run_rh.sh').write_text(SCRIPT)
    files = {}
    for name in ('rh_prepare.py','rehearse_v2.py','phase_worker.py','phase_support.py','job_support.py',
                 'batch_entry.py','stage_job.py','stage_fixture.py','rh_batch.py','rh_batch_fixture.py','rh_coverage.py'):
        files[name] = ROOT / name
    for sub in ('packet','manifest_v2'):
        for path in (ROOT / sub).iterdir():
            if path.is_file():
                files[str(path.relative_to(ROOT))] = path
    reference = ROOT / 'reference/sj/orch_cd/evalx/work/milestone'
    for relative in ('chain_save.py','orchard_stage.py','orchard_job.py','orchard_results.py',
                     'native_bootstrap.py','orchard_native/native_stage.py'):
        path = reference / relative
        files[str(path.relative_to(ROOT))] = path
    # The harness creates both stand-ins and its image fixture deterministically.
    files['reference/FAMILY.json'] = ROOT / 'reference/FAMILY.json'
    files['payload/a845b1789.tar'] = ROOT / 'payload/a845b1789.tar'
    model_archive = ROOT / 'inputs/model.tar'
    if model_archive.is_file():
        files['inputs/model.tar'] = model_archive
    metadata = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar')
    family = json.loads((ROOT / 'reference/FAMILY.json').read_text())
    pin = family['assets']['small_objects'][1]
    metadata_ready = metadata.is_file() and metadata.stat().st_size == pin['bytes']
    if metadata_ready:
        assert H.sha(metadata) == pin['sha256']
        files['inputs/a.tar'] = metadata
    H.dump(rh / 'CONTENTS.json', dict(files={name:str(p) for name,p in files.items()},
                                      metadata_ready=metadata_ready, environments_packed=args.pack_env))
    # A small local layout supports the requested same-script pre-bwrap probe.
    local = rh / 'local'
    local.mkdir(exist_ok=True)
    (local / 'run_rh.sh').write_text(SCRIPT)
    for name, path in files.items():
        target = local / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            if path.is_relative_to(ROOT):
                os.link(path, target)
            else:
                shutil.copyfile(path, target)
        elif H.sha(target) != H.sha(path):
            target.write_bytes(path.read_bytes())
    if not args.pack_env:
        print(json.dumps(dict(layout=str(local), archive_built=False, metadata_ready=metadata_ready)))
        return
    if shutil.disk_usage(ROOT).free < 203 * 1024**3:
        raise ValueError('Archive construction must leave at least 200 GiB free')
    archive_path = rh / 'RH_1_3.tar'
    if archive_path.exists():
        saved = rh / ('RH_1_3.saved_' + str(time.time_ns()) + '.tar')
        archive_path.rename(saved)
    with archive_path.open('xb') as raw:
        writer = RateWriter(raw)
        with tarfile.open(fileobj=writer, mode='w|', bufsize=1024**2) as archive:
            info = tarfile.TarInfo('run_rh.sh')
            content = SCRIPT.encode()
            info.size, info.mode = len(content), 0o755
            archive.addfile(info, io.BytesIO(content))
            for name, path in sorted(files.items()):
                archive.add(path, arcname=name, recursive=False)
            for path, name in ((Path('/scratch/jjyeung/envs/p1cpu'), 'runtime/p1cpu'),
                               (Path('/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu'), 'runtime/uv')):
                archive.add(path, arcname=name, recursive=True)
        result = dict(bytes=writer.count, sha256=writer.digest.hexdigest(), metadata_ready=metadata_ready,
                      environments_packed=True, archive=str(archive_path))
    H.dump(rh / 'ARCHIVE.json', result)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
