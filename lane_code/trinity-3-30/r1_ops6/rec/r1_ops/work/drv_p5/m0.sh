#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC CUDA_VISIBLE_DEVICES=''
python3 -I -B - <<'PYCODE'
"""Preflight every collision before no-replace, same-filesystem renames."""
import ctypes
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

O = Path('/project/community/jjyeung/okh7')
B = O/'i_69d2930d'
K = O/'x_69d2930d'
JOB = '170956'
NAME = 'a15_cot_ap673bc60f'
OLD_SHA = 'a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589'
OLD_SUMS = '036d6738c9c79fc9dfda2beb24e5fc7bcaeec2baeb943ad07e4d671644be9708'

def refuse(message):
    raise SystemExit('REFUSED: '+message)

def private(p):
    s = p.lstat()
    if not stat.S_ISDIR(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o700 or s.st_uid != os.geteuid():
        refuse('private owned directory required: '+str(p))

def sha(p):
    if p.is_symlink() or not p.is_file():
        refuse('regular unlinked file required: '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()

def query(argv):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=60,
                       env=dict(os.environ, TZ='UTC'))
    if r.returncode:
        refuse(argv[0]+' failed')
    return r.stdout

def queue_clear():
    for line in query(['squeue', '-h', '-o', '%i|%j|%P|%T']).splitlines():
        if not line.strip():
            continue
        fields = line.strip().split('|')
        if len(fields) != 4:
            refuse('malformed squeue row')
        if fields[1].strip() == NAME:
            refuse('job name still queued: '+NAME)

def main(staging):
    for p in (O, B, K):
        private(p)
    # Existing proof lock serializes against a driver already entering submission.
    lock = B/'p0.lock'
    if lock.is_symlink() or not lock.is_file():
        refuse('old proof lock is missing or linked')
    with lock.open('r') as held:
        try:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            refuse('proof submission lock is busy')
        queue_clear()
        rows = [line.strip().split('|') for line in query([
            'sacct', '-X', '-n', '-P', '-j', JOB,
            '--format=JobIDRaw,JobName%128,State,End']).splitlines() if line.strip()]
        rows = [r for r in rows if r[0] == JOB]
        if len(rows) != 1 or len(rows[0]) < 4:
            refuse('missing or ambiguous accounting for '+JOB)
        _, name, state, end = rows[0][:4]
        terminal = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY',
                    'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}
        if name != NAME or state.split()[0].rstrip('+') not in terminal:
            refuse('old proof has not ended')
        try:
            ended = datetime.datetime.fromisoformat(end).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            refuse('accounting End is not a timestamp')
        if ended > datetime.datetime.now(datetime.timezone.utc):
            refuse('accounting End is in the future')
        if (B/'job.id').read_text().strip() != JOB:
            refuse('old bundle job.id differs')
        for tag in ('e0', 'd0'):
            if (B/tag/'rc').read_text().strip() != '0':
                refuse('old worker has no successful completion: '+tag)
        if sha(B/'p.tar') != OLD_SHA or sha(B/'sums.txt') != OLD_SUMS:
            refuse('old archive or sums does not identify p_69d2930d')
        for line in (B/'sums.txt').read_text().splitlines():
            digest, name = line.split('  ', 1)
            rel = Path(name)
            if rel.is_absolute() or '..' in rel.parts or sha(B/rel) != digest:
                refuse('old sealed member differs: '+name)
        receipt = K/'o'/f'{JOB}.proof.json'
        record = json.loads(receipt.read_text())
        if record.get('job') != JOB or record.get('status') not in ('FAIL', 'FAILED'):
            refuse('failed proof receipt differs')
        if record.get('config_identity') != 'fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f':
            refuse('failed receipt identity differs')
        # Staging inputs are immutable and can only be reused after SHA equality.
        for name, digest in staging.items():
            p = Path(name)
            if p.exists() or p.is_symlink():
                if sha(p) != digest:
                    refuse('staging collision differs: '+name)
                print('REUSE SHA256', digest, name)
        optional = [O/'r/673bc60f', Path('/tmp/jjyeung/a_673bc60f'),
                    Path('/tmp/jjyeung/p_673bc60f_170956')]
        moves = [(p, p.with_name(p.name+'.f170956')) for p in (B, K)]
        for p in optional:
            target = p.with_name(p.name+'.f170956')
            if target.exists() or target.is_symlink():
                refuse('move-aside target exists: '+str(target))
            if p.exists() or p.is_symlink():
                private(p)
                moves.append((p, target))
        before = {}
        for src, dst in moves:
            if dst.exists() or dst.is_symlink():
                refuse('move-aside target exists: '+str(dst))
            if src.stat().st_dev != dst.parent.stat().st_dev:
                refuse('move must stay on one filesystem: '+str(src))
            before[str(src)] = (src.stat().st_dev, src.stat().st_ino)
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        queue_clear()
        for src, dst in moves:
            # RENAME_NOREPLACE refuses races instead of replacing any destination.
            if rename(-100, os.fsencode(src), -100, os.fsencode(dst), 1):
                error = ctypes.get_errno()
                # The project filesystem rejects renameat2 flags (EINVAL); fall back to a plain rename after a fresh absence check under the held lock.
                if error != 22 or dst.exists() or dst.is_symlink():
                    refuse(f'rename {src} failed ({os.strerror(error)}); inspect partial state, never retry automatically')
                os.rename(src, dst)
                print(f'FALLBACK plain rename (renameat2 EINVAL) {src}')
            s = dst.stat()
            if (s.st_dev, s.st_ino) != before[str(src)]:
                refuse('inode changed during rename')
            print(f'MOVED {src} -> {dst}; dev={s.st_dev} inode={s.st_ino} mode={stat.S_IMODE(s.st_mode):04o}')
            # Directory-entry listing only; never display sessions or other contents.
            print('LIST', str(dst), json.dumps(sorted(p.name for p in dst.iterdir())))
        print('PASS moved aside; bundle and kit inode/listing summaries above; nothing deleted')

STAGING_PINS = {'/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/d.db': '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/c.json': '0bc9414250b2ce082a5a1a74fb9421da991f0b794b6ed6c362ab96e92c11dea6', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/d.json': 'aaecc9c42cd549ebdf4da6483ffa6de6f580dc1039a2b53457e975cfe5082ebb', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/d_8091154cd499c474.json': '8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/j.json': 'aa7eb225074ac55bd0f0f2df80a21bb4ccd9e9622aa04fe5903995bbf64498d6', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json': '02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/r.json': '35f4a364304f24ed3683413952b3591d7427e787ad5cba056e4acc62d513263b', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/v.json': '3b3cc53285d5a92449e6b133c2f47dd4ea6b9df1eb83dd8ac60353f859f079fb', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/s.json': '5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/u_d7c3206c079b8397/i.json': '5e4ae8a89de8efcad68346e09ae1a42d4828163dc7e498e113df78bebdd4b6be', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/u_d7c3206c079b8397/m.json': '0d83e1372e7f4e7b499c424e868248990faf1b6ea8cccb6b7207f560554856dc', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/u_d7c3206c079b8397/u.gz': '14439f0c658d5afbfbd6b4fed67230b9a6f93aca9ad52c195c74f6a546dcb4a8'}

if __name__ == '__main__':
    try:
        main(STAGING_PINS)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        refuse(str(error))

PYCODE
