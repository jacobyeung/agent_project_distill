"""Build the K5 kit: config, fixed-input plane, pins, placement transport and lane scripts (local only)."""
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent/'work'
OLD0 = WORK/'old0'
R1 = Path('/scratch/jjyeung/orch_n30/lever1_c/r1')
DUMP = R1/'returned/0.gz'
DUMP_SHA = '5839d0ba8206ebbf50a5284eec6d6b434e193f50c792d672266765fcb64219c7'
ROWS = R1/'inspect/g_0.json'
DENSE = OLD0/'b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
FRAMES = OLD0/'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
DENSE_SHA = '4fef3415587c918f422515c0cf74565b77a1f90f4ef63d77c73718364e7fbc10'
FRAMES_SHA = 'c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439'
CAM52 = WORK/'cam52.txt'
OLD = '/project/community/jjyeung/a883c5c365aee'
OLD_PAYLOAD_SHA = 'e94006f6f7fc7830ffadf6ca38a33f37aa586a7570db1b162f0ff2dfc32e4de0'
OLD_INPUTS_SHA = '025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207'
NS = '/scratch/jjyeung/b01ec87a6f29b'
SMALL = ['0.py', '1.json', '2.py', '9.py']
# Served sources the worker imports, pinned by digest (paths relative to the staged code root p/).
SOURCES = ['tree/student_pilot/tower_read.py', 'tree/student_pilot/_tower_native.py',
           'tree/student_pilot/camera_targets.py', 'tree/student_pilot/geometry_profiles.py',
           'tree/student_pilot/scene_state.py', 'b/e2e_reader/real.py', 'b/e2e_reader/geometry.py',
           'b/e2e_reader/stage1.py']
# Measured inputs for the forecast (seconds).
EST = dict(
    staging=300.0,        # 173701 staged the same old package in 289.9 s
    verify=20.0,          # plane extraction and frame hashing on job-local disk
    publish=30.0,
    startup=20.0,         # interpreter, imports, pins per arm
    first_load=18.2,      # first-call weight load: 25.55 - 7.32 (rank 1 capture 0)
    reload=13.1,          # rebuild on a frame-count switch: 20.44 - 7.32 (rank 1 capture 55)
    t64=7.32, t32=4.31,   # rank 1 mean tower seconds after the first call (29 and 27 captures)
    t64_max=9.27, t32_max=4.73,
    bind=0.3,             # PNG open and convert per capture
    det_factor=1.25,      # unmeasured allowance for the deterministic arms
    relaunch=60.0,        # one strict-to-warn relaunch of a deterministic arm
    cpu64=985.0, cpu32=325.0,  # CPU tower, 16 threads (rank 1 CPU_TOWER_BENCH)
    cpu_decode=90.0, cpu_load=60.0,
    limit=3000.0, factor=1.5)
# Arms: (reverse order?, deterministic?)
ARMS = [[0, 0], [1, 0], [0, 1], [1, 1]]        # A1, A2, D1, D2
GROUPS = [[2, 0], [3, 1]]                       # job 0: D1 then A1; job 1: D2 then A2
DATASET = {'d1': 0, 'd2': 1, 'd3': 2}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def hx(value):
    return value.encode().hex()


def load_dump():
    assert sha(DUMP) == DUMP_SHA
    rows = []
    with gzip.open(DUMP, 'rt') as f:
        for line in f:
            rows.append(json.loads(bytes.fromhex(json.loads(line)['a0'])))
    assert len(rows) == 60
    return rows


def digest_binding(value):
    sys.path.insert(0, str(OLD0))
    from h1eval.items import digest
    return digest(value)


def captures():
    assert sha(DENSE) == DENSE_SHA and sha(FRAMES) == FRAMES_SHA
    dense = json.loads(DENSE.read_text())['captures']
    frames = json.loads(FRAMES.read_text())['captures']
    frames = {c['native']: c for c in frames} if isinstance(frames, list) else frames
    items = {x['item_id']: x for x in json.loads(ROWS.read_text())['items']}
    dump = load_dump()
    out = []
    for i, r in enumerate(dump):
        meta = r['metadata']
        native = items[meta['item_id']]['task']['native']
        d, c = dense[native], frames[native]
        assert digest_binding(dict(anchors=c, dense=d)) == meta['frame_binding_sha256']
        assert [f['index'] for f in d['frames']] == meta['dense_indices']
        assert d['anchor_slots'] == meta['anchor_slots'] and c['anchor_indices'] == meta['geometry']['source_indices']
        assert c['scene'] == meta['capture'] and meta['source_hw'] == c['hw']
        raw = base64.b64decode(r['arrays'])
        with np.load(io.BytesIO(raw), allow_pickle=False) as z:
            half = z['depth'].astype('<f2')
        geo = meta['geometry']
        out.append(dict(native=native, capture=meta['capture'], item_id=meta['item_id'], dense=d, frames=c,
                        dump=dict(K=geo['K'], c2w_metric=geo['camera_to_world_metric'],
                                  c2w_unscaled=geo['camera_to_world_unscaled'], scale=geo['scale'],
                                  depth_sha256=r['depth_sha256'], source_indices=geo['source_indices']),
                        gravity=[float(v) for v in np.asarray(geo['camera_to_world_unscaled'])[0][2][:3]],
                        plane=half, position=i))
    seen = {x['capture'] for x in out}
    wanted = {l.strip() for l in CAM52.read_text().splitlines() if l.strip()}
    assert len(wanted) == 52
    scene_to_native = {}
    for native, c in frames.items():
        scene_to_native.setdefault(c['scene'], []).append(native)
    assert all(len(scene_to_native[s]) == 1 for s in wanted)
    # New captures follow the 60 in the dense manifest's order.
    for native in dense:
        c = frames.get(native)
        if c is None or c['scene'] not in wanted or c['scene'] in seen:
            continue
        d = dense[native]
        slots = d['anchor_slots']
        assert [d['frames'][s]['index'] for s in slots] == c['anchor_indices']
        assert [d['frames'][s]['sha256'] for s in slots] == [f['sha256'] for f in c['frames']]
        assert len(d['frames']) in (32, 64)
        out.append(dict(native=native, capture=c['scene'], item_id=None, dense=d, frames=c, dump=None,
                        gravity=[0.0, -1.0, 0.0], plane=None, position=len(out)))
    assert len(out) == 84 and len({x['capture'] for x in out}) == 84
    assert len({x['capture'] for x in out} & wanted) == 52
    return out


def positions(n, reverse):
    order = list(range(n))
    if reverse:
        order.reverse()
    return order+[0]


def arm_seconds(counts, arm):
    reverse, det = ARMS[arm]
    total, last = EST['startup'], None
    for x in positions(len(counts), reverse):
        k = counts[x]
        total += EST['bind']+(EST['t64'] if k == 64 else EST['t32'])
        if last is None:
            total += EST['first_load']
        elif k != last:
            total += EST['reload']
        last = k
    return total*(EST['det_factor'] if det else 1.0)


def group_seconds(counts, group):
    arms = [arm_seconds(counts, a) for a in group]
    extra = EST['relaunch'] if any(ARMS[a][1] for a in group) else 0.0
    return EST['staging']+EST['verify']+sum(arms)+extra+EST['publish'], arms


def token():
    path = ROOT/'TOKEN'
    if not path.exists():
        value = 'a'+os.urandom(6).hex()
        path.write_text(value+'\n')
    value = path.read_text().strip()
    assert len(value) == 13 and value[0] in 'abcdef'
    return value


def payload(caps, tok):
    remote = '/project/community/jjyeung/'+tok
    planes = np.stack([c['plane'] for c in caps if c['plane'] is not None])
    assert planes.shape == (60, 32, 51, 51)
    raw = planes.astype('<f2').tobytes()
    gz = gzip.compress(raw, 9, mtime=0)
    (ROOT/'8.gz').write_bytes(gz)
    counts = [len(c['dense']['frames']) for c in caps]
    rows = []
    plane = 0
    for c in caps:
        d = c['dense']
        rows.append(dict(
            k=hashlib.sha256(c['native'].encode()).hexdigest()[:16],
            n=len(d['frames']), h=[f['sha256'] for f in d['frames']], i=[f['index'] for f in d['frames']],
            s=d['anchor_slots'], a=c['frames']['anchor_indices'], w=c['frames']['hw'],
            g=c['gravity'], c=None if c['dump'] is None else c['dump']['scale'],
            o=plane if c['plane'] is not None else -1))
        if c['plane'] is not None:
            plane += 1
    groups = [group_seconds(counts, g) for g in GROUPS]
    single = group_seconds(counts, [0, 1, 2, 3])
    cfg = dict(
        x0=tok, xg=OLD, xh=OLD_PAYLOAD_SHA, xi=OLD_INPUTS_SHA,
        xf=[hx(v) for v in ('orchard_h10.common', 'read_config', 'template', 'storage_proof', 'orchard_h10.job',
                            'stage', 'environment', 'namespace', 'opaque', 'physical')],
        xj=NS+'/d/v/py',
        x8=[hx(NS+'/p/tree'), hx(NS+'/p/b'), hx(NS+'/d/v/site')],
        x9=[[hx(NS+'/p/'+s), sha(OLD0/s)] for s in SOURCES],
        xa=[hx(v) for v in ('e2e_reader.real', 'TowerG3T', 'e2e_reader.geometry', 'from_tower',
                            'e2e_reader.stage1', 'median_ratio', 'g3t', 'H100')],
        xk=[hx(v) for v in ('native_frames', 'dense_indices', 'anchor_slots', 'anchor_indices',
                            'raw_pose9', 'frame_indices', 'depth_grid', 'depth_conf_grid', 'points_grid',
                            'grid_uv', 'source_hw', 'contract', 'camera_to_world', 'scale', 'model')],
        xb=[hx(NS+'/d/g/model.safetensors'), hx(NS+'/d/g/config.json')],
        xc=NS+'/d/f',
        x3=rows, xr=ARMS, xq=GROUPS,
        xp=dict(name='8.gz', sha256=sha(ROOT/'8.gz'), raw_sha256=hashlib.sha256(raw).hexdigest(),
                bytes=len(raw), shape=[60, 32, 51, 51]),
        x7=EST, xt=[g[0] for g in groups], xw=remote)
    for g in groups:
        assert g[0]*EST['factor'] <= EST['limit'], g
    (ROOT/'1.json').write_text(json.dumps(cfg, separators=(',', ':'))+'\n')
    forecast = dict(
        groups=[dict(arms=[['A1', 'A2', 'D1', 'D2'][a] for a in GROUPS[i]], seconds=g[0], minutes=g[0]/60,
                     times_1_5_minutes=g[0]*1.5/60, arm_seconds=g[1]) for i, g in enumerate(groups)],
        single_job=dict(seconds=single[0], minutes=single[0]/60, times_1_5_minutes=single[0]*1.5/60,
                        over_cap_minutes=single[0]/60-EST['limit']/EST['factor']/60),
        cpu=dict(seconds=EST['staging']+EST['verify']+EST['cpu_decode']+EST['cpu_load']+EST['cpu64']+EST['publish']),
        estimates=EST, captures=len(caps), frames64=counts.count(64), frames32=counts.count(32),
        measured_from='rank 1 dump tower seconds (H100) and the 173701 staging time; deterministic factor unmeasured')
    forecast['cpu']['times_1_5_minutes'] = forecast['cpu']['seconds']*1.5/60
    (ROOT/'FORECAST.json').write_text(json.dumps(forecast, indent=1)+'\n')
    return cfg


def reference(caps):
    out = []
    for c in caps:
        out.append(dict(k=hashlib.sha256(c['native'].encode()).hexdigest()[:16], capture=c['capture'],
                        dataset=['ScanNet', 'ScanNet++', 'ARKit'][DATASET[c['native'].split('/')[0]]],
                        native=c['native'], item_id=c['item_id'], frames=len(c['dense']['frames']),
                        rank1=c['dump'] is not None, position=c['position'], dump=c['dump']))
    (ROOT/'REFERENCE_K5.json').write_text(json.dumps(dict(schema=1, dump_sha256=DUMP_SHA, captures=out),
                                                      separators=(',', ':'))+'\n')


EXCLUDE = '--exclude=orchard-community-4'


def flags(gpu):
    return ('--parsable --account=mt01 --partition=general '+EXCLUDE+' --nodes=1 --ntasks=1 '
            '--job-name=a15_cot_ap{t} '+('--gres=gpu:1 ' if gpu else '')+
            '--cpus-per-task=16 --mem=200G --time=00:50:00 --no-requeue --export=NONE --chdir=/tmp')


def scripts(tok, cfg):
    p = '/project/community/jjyeung/'+tok
    head = '#!/bin/bash\nset -euo pipefail\numask 077\nP='+p+'\n'
    guard = 'q=$(squeue -u jjyeung -p general -h)\ntest -z "$q"\n'
    cpu = (head+'test ! -e "$P/6.txt"\ntest ! -e "$P/4.json"\n'+guard+
           'reply=$(CUDA_VISIBLE_DEVICES= sbatch '+flags(False).format(t=tok)+
           ' --output="$P/4.out" --error="$P/4.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 0 $P")\n'
           'job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]\n(set -C; printf \'%s\\n\' "$job" > "$P/6.txt")\nprintf \'%s\\n\' "$job"\n')
    (ROOT/'o_cpu.sh').write_text(cpu)
    for g in range(len(GROUPS)):
        pin = ''
        pinflag = ''
        if g:
            pin = ('first=$(cat "$P/70.txt"); [[ "$first" =~ ^[0-9]+$ ]]\n'
                   'node=$(TZ=UTC sacct -j "$first" -X -n -P -o NodeList | sed -n 1p)\n'
                   '[[ "$node" =~ ^[A-Za-z0-9-]+$ ]]\n')
            pinflag = ' --nodelist="$node"'
        sub = (head+'test ! -e "$P/7%d.txt"\n' % g+pin+
               '/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P" %d\n' % g+guard+
               'reply=$(sbatch '+flags(True).format(t=tok)+pinflag+
               ' --output="$P/5%d.out" --error="$P/5%d.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 1 $P %d")\n' % (g, g, g)+
               'job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]\n(set -C; printf \'%s\\n\' "$job" > "$P/7'+str(g)+'.txt")\nprintf \'%s\\n\' "$job"\n')
        (ROOT/('o_sub%d.sh' % g)).write_text(sub)
        names = ['5%d.json' % g, '5%d.1.json' % g, '5%d.err' % g, '5%d.out' % g, '5%d.stderr' % g, '6%d.err' % g, '12%d.txt' % g]
        fetch = (head+'job=$(cat "$P/7%d.txt"); [[ "$job" =~ ^[0-9]+$ ]]\n' % g+
                 'q=$(squeue -j "$job" -h -o \'%i\')\ntest -z "$q"\n'
                 'st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)\n'
                 'case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac\n'
                 'printf \'%s %s\\n\' "$job" "$st" > "$P/12'+str(g)+'.txt"\n'
                 '/usr/bin/python3 -I -s -B - "$P" "$job" '+str(g)+' <<\'PY\'\n'
                 'import hashlib,json,sys,tarfile\nfrom pathlib import Path\n'
                 'p=Path(sys.argv[1]);g=sys.argv[3]\n'
                 'try:\n'
                 '    r=json.loads((p/("5"+g+".1.json")).read_text());b=(p/("5"+g+".json")).read_bytes()\n'
                 '    ok=r["job"]==sys.argv[2] and r["sha256"]==hashlib.sha256(b).hexdigest() and r["bytes"]==len(b)\n'
                 'except Exception:\n    ok=False\n'
                 'print("ok" if ok else "E42",file=sys.stderr)\n'
                 'with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:\n'
                 '    for n in '+json.dumps(names)+':\n'
                 '        if (p/n).is_file() and (p/n).stat().st_size<=8000000:t.add(p/n,arcname=n,recursive=False)\n'
                 'PY\n')
        (ROOT/('o_fetch%d.sh' % g)).write_text(fetch)
    cfetch = (head+'job=$(cat "$P/6.txt"); [[ "$job" =~ ^[0-9]+$ ]]\n'
              'q=$(squeue -j "$job" -h -o \'%i\')\ntest -z "$q"\n'
              'st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)\n'
              'case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac\n'
              'printf \'%s %s\\n\' "$job" "$st" > "$P/11.txt"\n'
              '/usr/bin/python3 -I -s -B - "$P" <<\'PY\'\n'
              'import sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1])\n'
              'with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:\n'
              '    for n in ["11.txt","4.json","4.1.json","4.err","4.out","4.stderr"]:\n'
              '        if (p/n).is_file() and (p/n).stat().st_size<=2000000:t.add(p/n,arcname=n,recursive=False)\n'
              'PY\n')
    (ROOT/'o_cfetch.sh').write_text(cfetch)


def place(tok, cfg):
    remote = '/project/community/jjyeung/'+tok
    files = SMALL+['8.gz']
    pins = {n: sha(ROOT/n) for n in files}
    (ROOT/'3.json').write_text(json.dumps(pins, indent=1)+'\n')
    members = files+['3.json']
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz', format=tarfile.USTAR_FORMAT, compresslevel=9) as archive:
        for name in members:
            raw = (ROOT/name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o600, 0
            archive.addfile(info, io.BytesIO(raw))
    blob = buffer.getvalue()
    pin = hashlib.sha256(blob).hexdigest()
    total = sum((ROOT/n).stat().st_size for n in members)
    body = ('import base64,hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path\n'
            'def install():\n'
            '    p=Path(%r)\n' % remote+
            '    blob=base64.b64decode(ASSETS,validate=True)\n'
            '    if hashlib.sha256(blob).hexdigest()!=%r:raise ValueError("E40")\n' % pin+
            '    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as t:\n'
            '        members=t.getmembers()\n'
            '        if sorted(m.name for m in members)!=%r or any(not m.isfile() for m in members):raise ValueError("E41")\n' % sorted(members)+
            '        data={m.name:t.extractfile(m).read() for m in members}\n'
            '    pins=json.loads(data["3.json"])\n'
            '    if sorted(pins)!=%r:raise ValueError("E43")\n' % sorted(files)+
            '    for n in pins:\n'
            '        if hashlib.sha256(data[n]).hexdigest()!=pins[n]:raise ValueError("E43")\n'
            '    if sum(map(len,data.values()))!=%d:raise ValueError("E45")\n' % total+
            '    if p.exists():raise ValueError("E44")\n'
            '    p.mkdir(mode=0o700)\n'
            '    for n,b in data.items():\n'
            '        with (p/n).open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())\n'
            '    for n,b in data.items():\n'
            '        if hashlib.sha256((p/n).read_bytes()).hexdigest()!=hashlib.sha256(b).hexdigest():raise ValueError("E47")\n'
            '    print(sum(map(len,data.values())))\n'
            'try:\n    install()\n'
            'except Exception as e:\n'
            '    code=e.args[0] if e.args and isinstance(e.args[0],str) and e.args[0] in ("E40","E41","E43","E44","E45","E47") else "E49"\n'
            '    print(code,file=sys.stderr)\n    raise SystemExit(1)\n')
    script = ('#!/bin/bash\nset -euo pipefail\numask 077\n/usr/bin/python3 -I -s -B - <<\'PY\'\n'
              'ASSETS=%r\n' % base64.b64encode(blob).decode()+body+'PY\n')
    (ROOT/'o_place.sh').write_text(script)
    return dict(files=members, file_bytes=total, transport_bytes=len(script.encode()),
                transport_sha256=hashlib.sha256(script.encode()).hexdigest(), archive_sha256=pin)


def main():
    tok = token()
    caps = captures()
    reference(caps)
    cfg = payload(caps, tok)
    scripts(tok, cfg)
    placed = place(tok, cfg)
    build = dict(token=tok, path='/project/community/jjyeung/'+tok, small_files=SMALL+['3.json'],
                 placed=placed, old_package=OLD, captures=len(caps), groups=GROUPS, arms=ARMS,
                 lane_scripts=['o_place.sh', 'o_cpu.sh', 'o_cfetch.sh', 'o_sub0.sh', 'o_fetch0.sh',
                               'o_sub1.sh', 'o_fetch1.sh'])
    (ROOT/'BUILD.json').write_text(json.dumps(build, indent=1)+'\n')
    print(json.dumps(dict(token=tok, placed=placed, forecast=json.loads((ROOT/'FORECAST.json').read_text())['groups']), indent=1))


if __name__ == '__main__':
    main()
