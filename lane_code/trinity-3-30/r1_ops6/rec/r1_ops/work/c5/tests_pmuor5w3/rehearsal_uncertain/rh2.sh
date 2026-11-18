#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/rehearsal_uncertain/i_7f1589c1
KH=/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/rehearsal_uncertain/x_7f1589c1
[[ $# == 0 ]] || exit 2
for p in "${BUN%/*}" "$BUN" "$KH" "$KH/o"; do
 [[ -d "$p" && ! -L "$p" && $(stat -c %a "$p") == 700 ]] || { echo 'REFUSED: private directory required'; exit 3; }
done
printf '%s  %s\n' 'd7b862d96e335437389ec6eae2503599c37487d9b78ac822f8a2f37e0cc6d4fa' "$BUN/p.tar" | sha256sum -c --quiet
cd "$BUN"
sha256sum -c --quiet sums.txt
exec 9> "$BUN/rehearsal.lock"
flock -n 9 || { echo 'REFUSED: concurrent rehearsal'; exit 4; }
exec 8> "$BUN/p0.lock"
flock -n 8 || { echo 'REFUSED: concurrent proof'; exit 4; }
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\n' "$Q"
[[ "$Q" != *a15_cot_ap05b8ac6a* && "$Q" != *a15_cot_ap05b8ac69* ]] || { echo 'REFUSED: C proof or rehearsal queued'; exit 4; }
python3 -I -B - "$KH" "$BUN" <<'CHECK'
from pathlib import Path
import json,re,sys
k,b=map(Path,sys.argv[1:])
for entry in k.iterdir():
 if entry.is_symlink() or entry.name not in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'}:raise SystemExit('REFUSED: unexpected kit top-level entry: '+entry.name)
for name in ('submission.started','job.id','a.json'):
 p=b/name
 if p.exists() or p.is_symlink():raise SystemExit('REFUSED: proof attempt exists')
for name in ('rehearsal.started','rehearsal.job.id','rehearsal.sbatch.out','rehearsal.json'):
 p=b/name;target=b/(name+'.r172467')
 if not p.is_file() or p.is_symlink() or target.exists() or target.is_symlink():raise SystemExit('REFUSED: rehearsal marker state differs')
if (b/'rehearsal.job.id').read_text().strip()!='172467':raise SystemExit('REFUSED: rehearsal ID differs')
if (b/'rehearsal.sbatch.out').read_text().strip()!='Submitted batch job 172467':raise SystemExit('REFUSED: rehearsal submission differs')
r=json.loads((b/'rehearsal.json').read_text())
if r.get('job')!='172467' or r.get('kind')!='REHEARSAL' or r.get('partition')!='general' or r.get('proof') is not False:raise SystemExit('REFUSED: rehearsal ledger differs')
p=k/'o/172467.rehearsal.json'
if not p.is_file() or p.is_symlink():raise SystemExit('REFUSED: failed receipt unavailable')
r=json.loads(p.read_text())
if r.get('job')!='172467' or r.get('status')!='REHEARSAL_FAIL' or r.get('rc')!=1 or r.get('admission_executed') is not False:raise SystemExit('REFUSED: failed receipt differs')
for p in (b/'a4.json.r172467',k/'o/rh2.a4.check.json',k/'o/rh2_08f3a7b2.sh'):
 if p.exists() or p.is_symlink():raise SystemExit('REFUSED: retained or new output already exists')
p=b/'a4.json'
if p.is_symlink() or (p.exists() and not p.is_file()):raise SystemExit('REFUSED: linked authority')
CHECK
/scratch/jjyeung/envs/p1cpu/bin/python -I -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition general --out "$KH/o/rh2.a4.check.json"
python3 -I -B - "$KH" "$BUN" <<'ROTATE'
import ctypes,json,os,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:]);candidate=k/'o/rh2.a4.check.json'
libc=ctypes.CDLL(None,use_errno=True)
rename=libc.renameat2
rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
rename.restype=ctypes.c_int
def move(p,q):
 if q.exists() or q.is_symlink():raise SystemExit('REFUSED: rename destination exists')
 if rename(-100,os.fsencode(p),-100,os.fsencode(q),1):raise OSError(ctypes.get_errno(),'No-replace rename failed')
p=b/'a4.json';valid=False
if p.exists():
 try:valid=json.loads(p.read_text())==json.loads(candidate.read_text())
 except (ValueError,UnicodeError):pass
if valid:print('PASS retained valid general a4.json')
else:
 if p.exists():move(p,b/'a4.json.r172467')
 move(candidate,p)
 print('PASS installed fresh general a4.json')
for name in ('rehearsal.started','rehearsal.job.id','rehearsal.sbatch.out','rehearsal.json'):
 move(b/name,b/(name+'.r172467'))
print('PASS retained rehearsal 172467 markers')
ROTATE
(set -o noclobber; cat > "$KH/o/rh2_08f3a7b2.sh" <<'JOB'
#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export PATH=/usr/local/bin:/usr/bin:/bin TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/rehearsal_uncertain/i_7f1589c1
KH=/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/rehearsal_uncertain/x_7f1589c1
[[ ${SLURM_JOB_ID:-} =~ ^[1-9][0-9]*$ ]] || exit 3
ROOT=/tmp/jjyeung/rh2_08f3a7b2_${SLURM_JOB_ID}/root
if /scratch/jjyeung/envs/p1cpu/bin/python -I -B - "$KH" "$BUN" "$ROOT" "$SLURM_JOB_ID" <<'STAGE'
"""Prepare the pinned CPU startup inputs in this allocation's private storage."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def regular(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), 'Missing or linked input: '+str(p))
    return p

def private(path):
    p = Path(path)
    require(not p.is_symlink() and p.is_dir() and
            stat.S_IMODE(p.stat().st_mode) == 0o700 and p.stat().st_uid == os.geteuid(),
            'Private directory required: '+str(p))

def main(k, b, root, job):
    os.umask(0o077)
    require(re.fullmatch('[1-9][0-9]*', job), 'Numeric allocation required')
    require(os.environ.get('SLURM_JOB_NAME') == 'a15_cot_ap05b8ac6a' and
            os.environ.get('SLURM_JOB_PARTITION') == 'general' and
            os.environ.get('SLURM_JOB_NUM_NODES') == '1' and
            os.environ.get('SLURM_GPUS_ON_NODE', '0') in ('', '0') and
            os.environ.get('CUDA_VISIBLE_DEVICES', '') == '', 'Allocation differs')
    for p in (k.parent, k, b, k/'o'):
        private(p)
    require(root == Path('/tmp/jjyeung')/('rh2_08f3a7b2_'+job)/'root', 'Stage location differs')
    manifest = regular(k/'SHA256SUMS.txt')
    cert = json.loads(regular(k/'ANON_OK.json').read_text())
    require(cert.get('status') == 'CLEAN' and cert.get('hits') == 0 and
            cert.get('manifest_sha256') == sha(manifest), 'Certificate differs')
    pins = {}
    for line in manifest.read_text().strip().rsplit('\n'):
        digest, sep, name = line.partition('  ')
        require(sep and re.fullmatch('[0-9a-f]{64}', digest) and name not in pins and
                not Path(name).is_absolute() and '..' not in Path(name).parts, 'Invalid inventory')
        pins[name] = digest

    def kitfile(name):
        p = regular(k/name)
        require(p.resolve().is_relative_to(k.resolve()) and sha(p) == pins.get(name),
                'Kit pin differs: '+name)
        return p

    cur = json.loads(kitfile('k/0.json').read_text())
    launch = json.loads(kitfile('k/launch.json').read_text())
    cfgpath = kitfile(launch['config']['file'])
    require(sha(cfgpath) == launch['config']['sha256'], 'Config pin differs')
    cfg = json.loads(cfgpath.read_text())
    kitx = kitfile('b/kitx.py')
    # The sealed tail supplies b/ and k/ through tk_nx, outside this root.
    asroot = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
    alroot = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
    x = asroot+'ap/8865619b/'

    def hostfile(pin):
        name = pin['file']
        if name.startswith(x):
            p = kitfile(name[len(x):])
        else:
            p = regular(name)
        return p

    def localpath(name):
        for prefix in (asroot, alroot):
            if name.startswith(prefix):
                tail = name[len(prefix):]
                require('..' not in Path(tail).parts, 'Invalid logical path')
                return root/'aws/u'/tail
        raise ValueError('Unmapped logical path')

    extras = {}
    for item in cur['extra']:
        require(item['dest'] not in extras, 'Duplicate input destination')
        extras[item['dest']] = item
    descriptor = cfg['streams']['vqa']
    source = extras[descriptor['path']]
    require(source['sha256'] == descriptor['sha256'] and len(source['parts']) == 1,
            'Descriptor staging differs')
    descfile = regular(source['parts'][0])
    require(sha(descfile) == descriptor['sha256'], 'Descriptor pin differs')
    store = json.loads(descfile.read_text())
    database = store['database']
    dbsource = extras[database['path']]
    require(dbsource['sha256'] == database['sha256'], 'Store staging differs')
    record = hostfile(cur['record'])
    require(sha(record) == cur['record']['sha256'], 'Runtime record differs')
    archives = [(name, hostfile(cur[name]), cur[name]['sha256'])
                for name in ('venv', 'closure', 'trainer', 'np') if name in cur]
    dbparts = [regular(p) for p in dbsource['parts']]
    total = sum(p.stat().st_size for _, p, _ in archives) + sum(p.stat().st_size for p in dbparts)
    total += record.stat().st_size + descfile.stat().st_size
    # Keep enough room for the runtime and store; refuse before reading archives.
    require(total < 24_000_000_000, 'Startup input size exceeds 24 GB')
    free = os.statvfs('/tmp')
    require(free.f_bavail * free.f_frsize >= total*3 + 2_000_000_000, 'Insufficient temporary space')
    parent = root.parent.parent
    parent.mkdir(mode=0o700, exist_ok=True)
    private(parent)
    root.parent.mkdir(mode=0o700)
    root.mkdir(mode=0o700)
    for rel in ('aws/u/ap/8865619b/u', 'epochs', 'c7d31ddd/anyhost',
                'c7d31ddd/data2root', 'c7d31ddd/runs/aws128p_20261025/models'):
        (root/rel).mkdir(parents=True, exist_ok=True, mode=0o700)
    rows = []
    started = time.time()
    destinations = dict(venv=root/'c7d31ddd/venvs',
                        closure=root/'c7d31ddd/_jobs'/('cp4tk_'+cur['closure']['sha256'][:12]),
                        trainer=root/'epochs'/cur['commit'], np=root/'np226')
    for key, path, digest in archives:
        dst = destinations[key]
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # The sealed extractor hashes every archive byte while streaming it once.
        subprocess.run([sys.executable, '-I', '-B', str(kitx), str(path), digest, str(dst)], check=True)
        rows.append(dict(kind=key, source=str(path), sha256=digest, bytes=path.stat().st_size))

    def copy_checked(parts, dst, digest):
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        h = hashlib.sha256()
        count = 0
        with dst.open('xb') as out:
            for part in parts:
                with regular(part).open('rb') as inp:
                    for block in iter(lambda: inp.read(1 << 20), b''):
                        out.write(block); h.update(block); count += len(block)
        require(h.hexdigest() == digest and sha(dst) == digest, 'Copied input pin differs')
        dst.chmod(0o400)
        rows.append(dict(source=[str(p) for p in parts], destination=str(dst.relative_to(root)),
                         sha256=digest, bytes=count))

    # Admission installs these two sealed files over the closure's site_alias.
    alias = destinations['closure']/'site_alias'
    if alias.exists() or alias.is_symlink():
        retained = destinations['closure']/'site_alias.r172467'
        require(not retained.exists() and not retained.is_symlink(), 'Retained alias exists')
        alias.rename(retained)
    alias.mkdir(mode=0o700)
    for name in ('sitecustomize.py', 'prestage_hooks.py'):
        copy_checked([kitfile('b/sa/'+name)], alias/name, pins['b/sa/'+name])
    copy_checked([record], root/'c7d31ddd/anyhost'/(cur['record']['sha256']+'.json'), cur['record']['sha256'])
    copy_checked([descfile], localpath(descriptor['path']), descriptor['sha256'])
    copy_checked(dbparts, localpath(database['path']), database['sha256'])
    # Direct Python invocation needs no rewritten console-script shebangs.
    for directory, children, files in os.walk(root):
        p = Path(directory)
        if not p.is_symlink():
            p.chmod(0o700)
    report = dict(status='STAGED', job=job, bytes=total, inputs=rows,
                  elapsed_seconds=time.time()-started, admission_executed=False)
    with (k/'o'/(job+'.rh2.stage.json')).open('x') as f:
        json.dump(report, f, sort_keys=True); f.write('\n')
    print('STAGED bytes='+str(total), flush=True)

if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
STAGE
then
    /bin/bash "$BUN/p_05b8ac69.sh" "$BUN/a4.json" --rehearsal "$ROOT"
else
    rc=$?
    /scratch/jjyeung/envs/p1cpu/bin/python -I -B - "$KH" "$SLURM_JOB_ID" "$rc" <<'FAILED'
import json,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2];rc=int(sys.argv[3])
with (k/'o'/(job+'.rehearsal.json')).open('x') as f:
 json.dump(dict(status='REHEARSAL_FAIL',job=job,rc=rc,rehearsal=True,
                steps=dict(self_stage='FAIL'),admission_executed=False,
                production_authorized=False),f,sort_keys=True);f.write('\n')
FAILED
    exit "$rc"
fi
JOB
)
chmod 500 "$KH/o/rh2_08f3a7b2.sh"
(set -o noclobber; date -u +%FT%TZ > "$BUN/rehearsal.started")
sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:45:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output="$KH/o/%j.rehearsal.out" --error="$KH/o/%j.rehearsal.err" "$KH/o/rh2_08f3a7b2.sh" > "$BUN/rehearsal.sbatch.out"
python3 -I -B - "$BUN" "$KH" <<'END'
import hashlib,json,re,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:]);s=(b/'rehearsal.sbatch.out').read_text().strip()
m=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',s)
if not m:raise SystemExit('UNCERTAIN: no rehearsal ID; inspect; never resubmit')
job=m[1]
if job in ('172180','172467'):raise SystemExit('UNCERTAIN: stale allocation ID')
with (b/'rehearsal.job.id').open('x') as f:f.write(job+'\n')
with (b/'rehearsal.json').open('x') as f:
 json.dump(dict(job=job,kind='REHEARSAL',partition='general',gpus=0,authority='a4.json',proof=False,
                wrapper=str(k/'o/rh2_08f3a7b2.sh'),wrapper_sha256=hashlib.sha256((k/'o/rh2_08f3a7b2.sh').read_bytes()).hexdigest(),
                predecessor='172467'),f,sort_keys=True);f.write('\n')
print('SUBMITTED rehearsal_job='+job+'; never a PASS proof')
END
