"""Build the K4 kit: 7 arms per capture, the C-only frame archive, the transport and lane scripts."""
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
GB = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
K3D, K3C, K2 = GB/'orchard_tower2x_c', GB/'orchard_tower2x_b', GB/'orchard_tower2x'
INPUTS = Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/out/INPUTS_K3.json')
SERVED = Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames')
SITE = '/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages'
SOURCE = '/project/community/jjyeung/ac794e028b16f/8.tgz'
REUSED_BYTES = 44374984
REUSED_SHA = 'e8072d952b78f6eb3317d8214821ded02cebfa9a4349e81f317961fd146813ff'
LABELS = ['A', 'A2', "A'", "B'", "C'", 'Bm', 'Cm']
ORDER = [0, 1, 2, 5, 6, 3, 4]
GPU_LIMIT, CPU_LIMIT = 2700, 3600
GPU_TIME, CPU_TIME = '00:45:00', '01:00:00'
CPU_UNIT_ALLOW = 2400.0
SHIPPED = ['0.py', '1.json', '2.py', '9.py', 'BATCH.sh', '10.tgz', '3.json']
FLOOR = 'F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); [ "$F" -ge 5 ] || { echo E48 >&2; exit 3; }\n'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def put(path, obj):
    path.write_text(json.dumps(obj, indent=2)+'\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def token():
    p = ROOT/'TOKEN'
    if not p.exists():
        p.write_text('a'+secrets.token_hex(6)+'\n')
    return p.read_text().strip()


def frames_dir(inputs):
    d = ROOT/'work_frames'
    d.mkdir(exist_ok=True)
    for cap in inputs['captures']:
        for f in cap['frames']:
            link = d/(f['sha256']+'.png')
            if not link.is_symlink():
                link.symlink_to(f['path'])
    return d


def build_rows(base, inputs, k2, worker):
    by_capture = {c['capture']: c for c in inputs['captures']}
    k3 = json.loads((K3D/'1.json').read_text())
    rows = []
    for row, served_row, old in zip(base['x3'], k2['x3'], k3['x3']):
        assert row['x0'] == served_row['x0'] == old['x0']
        cap = by_capture[row['x3']]
        anchors = cap['anchors']
        assert anchors == old['x4'][0]['x0'] == served_row['x4'][0]['x0']
        low = {f['index']: f['sha256'] for f in cap['frames']}
        served = dict(zip(anchors, served_row['x4'][0]['x1']))
        def arm(ids, code):
            slots = [ids.index(i) for i in anchors]
            flags = [code == 2 or (code == 1 and k not in slots) for k in range(len(ids))]
            hashes = [low[i] if f else served[i] for i, f in zip(ids, flags)]
            return dict(x0=ids, x1=hashes, x2=slots, x5=flags, x6=['0'*64]*len(ids))
        arms = [arm(anchors, 0), None, arm(anchors, 2), arm(cap['B'], 2), arm(cap['C'], 2),
                arm(cap['B'], 1), arm(cap['C'], 1)]
        new = dict(x0=row['x0'], x1=row['x1'], x2=row['x2'], x4=arms, x5=row['x5'], x6=row['x6'])
        cfg = dict(base, xl=str(ROOT/'work_frames'), xc=str(SERVED))
        for a in (0, 2, 3, 4, 5, 6):
            _, raw, _, _, _ = worker.images(cfg, new, a, keep=False)
            arms[a]['x6'] = raw
        arms[1] = copy.deepcopy(arms[0])
        # The recipe hashes must equal the K3d plan wherever both decode the same frame.
        for a, k in ((2, 0), (3, 1)):
            assert arms[a]['x6'] == old['x4'][k]['x6'] and arms[a]['x1'] == old['x4'][k]['x1']
        for a in range(7):
            worker.binding(new, a)
        rows.append(new)
    return rows


def archive_c(rows, inputs):
    with tarfile.open(K3C/'8.tgz') as t:
        held = set(t.getnames())
    paths = {f['sha256']: f['path'] for c in inputs['captures'] for f in c['frames']}
    need = sorted({h+'.png' for r in rows for a in r['x4'] for h, f in zip(a['x1'], a['x5']) if f} - held)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0, compresslevel=6) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name in need:
                raw = Path(paths[name[:-4]]).read_bytes()
                assert hashlib.sha256(raw).hexdigest()+'.png' == name
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(raw), 0o600, 0
                archive.addfile(info, io.BytesIO(raw))
    (ROOT/'10.tgz').write_bytes(buffer.getvalue())
    return need, held


def transport(remote, names):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name in names:
            raw = (ROOT/name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o600, 0
            archive.addfile(info, io.BytesIO(raw))
    blob = buffer.getvalue()
    code = '''import hashlib,io,json,os,sys,tarfile
from pathlib import Path
os.umask(0o077)
P=Path(REMOTE)
S=Path(SOURCE)
N=NAMES
def install():
    b=sys.stdin.buffer.read(LENGTH+1)
    if len(b)!=LENGTH or hashlib.sha256(b).hexdigest()!=PIN:raise ValueError("E40")
    with tarfile.open(fileobj=io.BytesIO(b),mode="r:") as t:
        members=t.getmembers()
        if sorted(m.name for m in members)!=sorted(N) or any(not m.isfile() for m in members):raise ValueError("E41")
        data={m.name:t.extractfile(m).read() for m in members}
    pins=json.loads(data["3.json"])
    if set(pins)!=(set(N)-{"3.json"})|{"8.tgz"}:raise ValueError("E43")
    for n in N:
        if n!="3.json" and hashlib.sha256(data[n]).hexdigest()!=pins[n]:raise ValueError("E43")
    if P.exists():raise ValueError("E44")
    if S.stat().st_size!=REUSED:raise ValueError("E45")
    with S.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=pins["8.tgz"]:raise ValueError("E46")
    P.mkdir(mode=0o700)
    os.link(S,P/"8.tgz")
    if not os.path.samefile(S,P/"8.tgz"):raise ValueError("E47")
    for n,v in data.items():
        with (P/n).open("xb") as f:f.write(v)
    print(sum(map(len,data.values())))
try:
    install()
except Exception as e:
    code=e.args[0] if e.args and isinstance(e.args[0],str) and e.args[0] in ("E40","E41","E43","E44","E45","E46","E47") else "E49"
    print(code,file=sys.stderr)
    raise SystemExit(1)
'''
    for key, value in [('REMOTE', json.dumps(remote)), ('SOURCE', json.dumps(SOURCE)), ('NAMES', json.dumps(names)),
                       ('LENGTH', str(len(blob))), ('PIN', json.dumps(hashlib.sha256(blob).hexdigest())),
                       ('REUSED', str(REUSED_BYTES))]:
        code = code.replace(key, value)
    assert "'" not in code
    prelude = '#!/bin/bash\nset -euo pipefail\numask 077\n'+FLOOR+"exec /usr/bin/python3 -I -s -B -c '"+code+"'\n"
    (ROOT/'place.tar').write_bytes(blob)
    (ROOT/'o_place.sh').write_bytes(prelude.encode()+blob)
    return blob, prelude


def scripts(tok, remote):
    name = 'a15_cot_ap'+tok
    common = '#!/bin/bash\nset -euo pipefail\numask 077\n'+FLOOR+'P='+remote+'\n'
    cpu = (common+'test ! -e "$P/6.txt"\ntest ! -e "$P/4.json"\nq=$(squeue -u jjyeung -p general -h)\ntest -z "$q"\n'
           'reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 '
           '--nodes=1 --ntasks=1 --job-name='+name+' --cpus-per-task=8 --mem=200G --time='+CPU_TIME+' --no-requeue '
           '--export=NONE --chdir=/tmp --output="$P/4.out" --error="$P/4.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 0 $P")\n'
           'job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]\n(set -C; printf \'%s\\n\' "$job" > "$P/6.txt")\nprintf \'%s\\n\' "$job"\n')
    sub = (common+'test ! -e "$P/7.txt"\n/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P"\nq=$(squeue -u jjyeung -p general -h)\ntest -z "$q"\n'
           'reply=$(sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 '
           '--job-name='+name+' --gres=gpu:1 --cpus-per-task=8 --mem=200G --time='+GPU_TIME+' --no-requeue --export=NONE '
           '--chdir=/tmp --output="$P/5.out" --error="$P/5.stderr" "$P/BATCH.sh")\n'
           'job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]\n(set -C; printf \'%s\\n\' "$job" > "$P/7.txt")\nprintf \'%s\\n\' "$job"\n')
    def fetch(marker, state, names, check):
        return ('#!/bin/bash\nset -euo pipefail\numask 077\nP='+remote+'\n'
                'job=$(cat "$P/'+marker+'"); [[ "$job" =~ ^[0-9]+$ ]]\n'
                "st=$(TZ=UTC sacct -j \"$job\" -X -n -P -o State | head -1 | cut -d' ' -f1)\n"
                'case "$st" in COMPLETED|FAILED|TIMEOUT|CANCELLED|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac\n'
                'printf \'%s %s\\n\' "$job" "$st" > "$P/'+state+'"\n'
                '/usr/bin/python3 -I -s -B - "$P" "$job" <<\'PY\'\n'
                'import hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1])\n'+check+
                'with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:\n'
                '    for n in '+json.dumps(names)+':\n'
                '        if (p/n).is_file():t.add(p/n,arcname=n,recursive=False)\nPY\n')
    gpu_check = ('r=json.loads((p/"5.1.json").read_text());b=(p/"5.json").read_bytes()\n'
                 'if r["job"]!=sys.argv[2] or r["sha256"]!=hashlib.sha256(b).hexdigest() or r["bytes"]!=len(b):raise ValueError("E42")\n')
    files = {
        'o_cpu.sh': cpu,
        'o_check_sub.sh': sub,
        'o_cfetch.sh': fetch('6.txt', '11.txt', ['11.txt', '4.json', '4.1.json', '4.err', '4.out', '4.stderr'], ''),
        'o_fetch.sh': fetch('7.txt', '12.txt', ['12.txt', '5.json', '5.1.json', '4.json', '4.err', '4.out', '4.stderr',
                                                 '5.err', '5.out', '5.stderr', '6.err'], gpu_check),
    }
    for n, text in files.items():
        (ROOT/n).write_text(text)
    (ROOT/'BATCH.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexec /usr/bin/python3 -I -s -B '+remote+'/9.py 1 '+remote+'\n')


def forecast_file(cfg, worker):
    ret = json.loads((K3D/'returned/5.json').read_text())
    arms = [a for r in ret['rows'] for a in r['arms']]
    t32 = max(a['seconds'] for a in arms if len(a['ids']) == 32)
    t63 = max(a['seconds'] for a in arms if len(a['ids']) == 63)
    t94 = t63*94/63*1.03
    counts = [worker.SPEC[a][0] for _, a in worker.tasks(cfg)]
    measured = {32: t32, 63: t63, 94: t94}
    infer = sum(measured[n] for n in counts)
    scaled = ret['staging_seconds']+ret['load_seconds']+infer+30
    return dict(measured_k3d=dict(job=173701, staging_seconds=ret['staging_seconds'], load_seconds=ret['load_seconds'],
                                  total_seconds=ret['total_seconds'], max_32_seconds=t32, max_63_seconds=t63,
                                  arm_runs=len(arms), frames=sum(len(a['ids']) for a in arms)),
                k4_frames=sum(counts), k4_arm_runs=len(counts), est_94_seconds=t94,
                forecast_seconds=scaled, forecast_minutes=scaled/60, forecast_x1_5_minutes=1.5*scaled/60,
                guard_seconds=worker.forecast(cfg), guard_minutes=worker.forecast(cfg)/60,
                gpu_limit=GPU_TIME, cpu_limit=CPU_TIME,
                formula='K3d measured staging + load + sum over 70 arm runs of K3d max arm seconds by frame count '
                        '(94 frames = 63-frame max x 94/63 x 1.03) + 30 s IO; guard = 600 + 78.2 + sum(1.5 x arm + 3) + 120')


def main():
    sys.path.append(SITE)
    tok = token()
    remote = '/project/community/jjyeung/'+tok
    worker = module('worker_k4', ROOT/'2.py')
    inputs = json.loads(INPUTS.read_text())
    base = json.loads((K3D/'1.json').read_text())
    k2 = json.loads((K2/'1.json').read_text())
    frames_dir(inputs)
    with (K3C/'8.tgz').open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == REUSED_SHA
    rows = build_rows(base, inputs, k2, worker)
    cfg = dict(base, x0=tok, x3=rows, xl=remote+'/8', xr=ORDER, xq=70, xs=3.0,
               xv=[GPU_LIMIT, GPU_LIMIT-300, CPU_LIMIT, CPU_UNIT_ALLOW])
    t32, t63 = 4.95, 9.73
    cfg['x7'] = [600.0, base['x7'][1], 1.5, t32, t63, round(t63*94/63*1.03, 2), 120.0]
    assert cfg['xq'] == len(worker.tasks(cfg)) and worker.forecast(cfg) <= cfg['xv'][1]
    (ROOT/'1.json').write_text(json.dumps(cfg, separators=(',', ':'))+'\n')
    need, held = archive_c(rows, inputs)
    scripts(tok, remote)
    pins = {n: sha(ROOT/n) for n in SHIPPED if n != '3.json'}
    pins['8.tgz'] = REUSED_SHA
    put(ROOT/'3.json', pins)
    blob, prelude = transport(remote, SHIPPED)
    ref = json.loads((K3D/'REFERENCE.json').read_text())
    caps = []
    for r, old in zip(rows, ref['captures']):
        assert r['x0'] == old['key']
        caps.append(dict(key=old['key'], capture=old['capture'], group=old['group'], gt=old['gt'], t1=old['t1'],
                         scale=old['scale'], gravity=old['gravity'],
                         arms=[dict(ids=a['x0'], sha256=a['x1'], slots=a['x2'], raw_sha256=a['x6'], served=[not f for f in a['x5']])
                               for a in r['x4']]))
    put(ROOT/'REFERENCE_K4.json', dict(token=tok, input_sha256=sha(ROOT/'1.json'), labels=LABELS,
        t1_receipt=ref['t1_receipt'], gt_sha256=ref['gt_sha256'], t1_extract_sha256=ref['t1_extract_sha256'],
        k3d_reference_sha256=sha(K3D/'REFERENCE.json'), captures=caps))
    fc = forecast_file(cfg, worker)
    put(ROOT/'FORECAST.json', fc)
    added = sum((ROOT/n).stat().st_size for n in SHIPPED)
    per = {}
    for r in rows:
        per[r['x0']] = len({h for a in r['x4'] for h, f in zip(a['x1'], a['x5']) if f and h+'.png' not in held})
    build = dict(token=tok, path=remote, job_name='a15_cot_ap'+tok, source=SOURCE, shipped=SHIPPED,
                 bound_files=SHIPPED+['8.tgz'], added_bytes=added, new_png_count=len(need), new_png_per_capture=per,
                 new_png_bytes=sum(Path(p).stat().st_size for p in [ROOT/'work_frames'/n for n in need]),
                 archive_10_bytes=(ROOT/'10.tgz').stat().st_size, archive_10_sha256=sha(ROOT/'10.tgz'),
                 reused_bytes=REUSED_BYTES, reused_sha256=REUSED_SHA, reused_png_count=len(held),
                 transport_file='o_place.sh', transport_bytes=(ROOT/'o_place.sh').stat().st_size,
                 transport_sha256=sha(ROOT/'o_place.sh'), transport_prelude_bytes=len(prelude.encode()),
                 place_tar_bytes=len(blob), place_tar_sha256=hashlib.sha256(blob).hexdigest(),
                 return_reserve_bytes=3_000_000, cpu_return_reserve_bytes=1_000_000,
                 project_budget_bytes=50_000_000, labels=LABELS, order=ORDER,
                 forecast_minutes=fc['forecast_minutes'], guard_minutes=fc['guard_minutes'],
                 meaning='K4 tower coverage kit, 10 captures x 7 arms (A, A2, A\', B\', C\', Bm, Cm)')
    assert build['added_bytes']+build['return_reserve_bytes']+build['cpu_return_reserve_bytes'] < build['project_budget_bytes']
    put(ROOT/'BUILD.json', build)
    print(json.dumps({k: v for k, v in build.items() if k not in ('new_png_per_capture',)}, indent=1))


if __name__ == '__main__':
    main()
