"""Build the code-only kit from the authenticated local package mirrors."""
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
OUT = BASE.parent/'cap/score_tower2x'
TOKEN = 'ae27b6409c13f'
REMOTE = '/project/community/jjyeung/'+TOKEN
IDS = ['41069054', '41291643', '42899535', '45663051', '47332598',
       '41159782', '45261332', '43828368', '43649603', '44358634']
DENSE = 'b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
FRAMES = 'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def build():
    pay = BASE/'work/payload'
    dm = json.loads((pay/DENSE).read_text())
    fm = {x['scene']:x for x in json.loads((pay/FRAMES).read_text())['captures']}
    t1 = json.loads((OUT/'T1_EXTRACT.json').read_text())
    gt = json.loads((BASE/'out2/GT.json').read_text())
    parity = json.loads((BASE.parent/'cap/t1ret/PARITY.json').read_text())
    assert parity['trusted'] and parity['discrete_matches'] == 150
    timing = {}
    with tarfile.open(BASE.parent/'cap/dret/0.tgz') as t:
        for n in (32, 64):
            timing[str(n)] = json.load(t.extractfile(f'metadata/8_{n}.json'))
    rows, refs, availability = [], [], []
    for i, id_ in enumerate(IDS):
        capture = 'arkitscenes/'+id_
        key = hashlib.sha256(capture.encode()).hexdigest()[:16]
        source = fm[capture]
        dense = dm['captures']['d3/'+id_]
        old = t1['captures'][capture]
        assert old['source_indices'] == source['anchor_indices'] == gt[capture]['source_indices']
        assert [dense['frames'][s]['sha256'] for s in dense['anchor_slots']] == [f['sha256'] for f in source['frames']]
        a = dict(x0=source['anchor_indices'], x1=[f['sha256'] for f in source['frames']], x2=list(range(32)))
        arms = [a, None, None]
        if len(dense['frames']) == 64:
            arms[1] = dict(x0=[f['index'] for f in dense['frames']], x1=[f['sha256'] for f in dense['frames']], x2=dense['anchor_slots'])
        # The geometry contract stores world-up, so recover camera-zero up from its rotation.
        gravity = old['c2w'][0][2][:3]
        rows.append(dict(x0=key, x1=old['scale'], x2=gravity, x3=capture, x4=arms, x5=source['hw']))
        refs.append(dict(key=key, capture=capture, group='failing' if i<5 else 'reference',
            gt=gt[capture]['c2w'], t1=old['c2w'], scale=old['scale'], gravity=gravity,
            arms=[None if a is None else dict(ids=a['x0'], sha256=a['x1'], slots=a['x2']) for a in arms]))
        availability.append(dict(capture=capture, native='d3/'+id_, anchors=32,
            dense_frames=len(dense['frames']), B_available=arms[1] is not None, C_available=False,
            reason='No non-anchor frames in the registered manifest; no registered 64-frame base for nesting 96.'))
    logical = '/scratch/jjyeung/b01ec87a6f29b'
    settings = dict(weights_path=logical+'/d/g/model.safetensors', config_path=logical+'/d/g/config.json',
                    device='cuda:0', dense_frames=32, depth_chunk_size=8, dtype='bf16')
    source_files = ['tree/student_pilot/'+n for n in ['tower_read.py', '_tower_native.py', 'camera_targets.py', 'tower_errors.py', 'c1r_ref.py', 'g3t_online.py']]
    cfg = dict(x0=TOKEN, x3=rows,
        x7=[600., timing['32']['initial_load_seconds'], 1.5, timing['32']['timings']['g3t_s'],
            timing['64']['timings']['g3t_s'], timing['64']['timings']['g3t_s']*2.25, 120.],
        x8=[logical+'/p/tree', logical+'/d/v/site'],
        x9=[[logical+'/p/'+n, sha(pay/n)] for n in source_files],
        xa=['student_pilot.tower_read', 'NATIVE_INPUT', 'native_square_pad_bicubic_1024_bilinear_518_v1',
            'FrozenG3TTower', 'student_pilot.camera_targets', 'to_gravity_reference_frame'],
        xb=settings, xc=logical+'/d/f',
        xd=['dense_frames', 'tower_native_frames', 'tower_frame_indices', 'tower_anchor_slots', 'frame_indices', 'raw_pose9'],
        xf=['orchard_h10.common', 'read_config', 'template', 'storage_proof', 'orchard_h10.job', 'stage', 'environment', 'namespace', 'opaque'],
        xg='/project/community/jjyeung/a883c5c365aee',
        xh=json.loads((BASE/'out3/dense/BUILD.json').read_text())['payload_sha256'],
        xi=sha(BASE/'parent/a/1.json'), xj=logical+'/d/v/py')
    write(ROOT/'1.json', cfg)
    write(OUT/'REFERENCE.json', dict(token=TOKEN, input_sha256=sha(ROOT/'1.json'), captures=refs,
          t1_receipt=t1['receipt'], gt_sha256=sha(BASE/'out2/GT.json')))
    inventory = []
    # Inspect the three package mirrors actually named by the handoff, without remote IO.
    for kit in ('orchard_t1', 'orchard_dense', 'orchard_dense_r3'):
        script = (BASE/kit/'o_place.sh').read_text()
        data = base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'\)", script)[1])
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            with tarfile.open(fileobj=io.BytesIO(t.extractfile('0.tgz').read())) as inner:
                raw = inner.extractfile(DENSE).read()
                d = json.loads(raw)
                inventory.append(dict(kit=kit, package=re.search(r'^P=(.+)$', script, re.M)[1],
                    manifest_sha256=hashlib.sha256(raw).hexdigest(),
                    counts={id_:len(d['captures']['d3/'+id_]['frames']) for id_ in IDS}))
    write(ROOT/'AVAILABILITY.json', dict(captures=availability, package_mirrors=inventory,
        optional_manifest=dict(path='work/payload/inputs/r0dev/FRAMES_MANIFEST.json',
          sha256=sha(pay/'inputs/r0dev/FRAMES_MANIFEST.json'),
          note='ScanNet++ only; no requested ARKit captures. Its independent 32/64 layouts are not a 96-frame nested manifest.'),
        remote_inventory_live=False, substitution=False, native_decode_verified=False,
        provenance=dict(dense_manifest_sha256=sha(pay/DENSE), frames_sha256=sha(pay/FRAMES)),
        source=dm['producer_plan']))
    estimate = cfg['x7'][0]+cfg['x7'][1]+cfg['x7'][2]*sum(cfg['x7'][3+i] for r in rows for i,a in enumerate(r['x4']) if a is not None)+cfg['x7'][6]
    write(ROOT/'FORECAST.json', dict(estimate_seconds=estimate, estimate_minutes=estimate/60,
        inference_and_load_seconds=estimate-600, stage_allowance_seconds=600,
        formula='600 staging + 78.2098 observed full-reader load allowance + 1.5 * sum(observed tower seconds) + 120 IO/return allowance',
        measured_dense=timing, assumptions=['Staging is an unmeasured allowance, enforced at 600 seconds.',
            'The inherited stage unpacks existing archives into job-local /tmp; no environment is installed.',
            'The worker loads only the frozen tower, with T1 scale and gravity held fixed.',
            'A forecast over 1500 seconds refuses before staging/loading. Total allocation is 1800 seconds.'],
        runnable_arms=dict(A=10, B=sum(r['x4'][1] is not None for r in rows), C=0)))
    batch = '#!/bin/bash\nset -euo pipefail\numask 077\nexec /usr/bin/python3 -I -s -B '+REMOTE+'/0.py 1 '+REMOTE+'\n'
    (ROOT/'BATCH.sh').write_text(batch)
    bound = ['0.py', '1.json', '2.py', 'BATCH.sh']
    write(ROOT/'3.json', {n:sha(ROOT/n) for n in bound})
    bound.append('3.json')
    payload = {n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in bound}
    body = '''#!/bin/bash
set -euo pipefail
umask 077
/usr/bin/python3 -I -s -B - <<'PY'
import base64,hashlib,json
from pathlib import Path
p=Path('REMOTE')
assets=ASSETS
data={k:base64.b64decode(v) for k,v in assets.items()}
if sum(map(len,data.values()))>=2_000_000:raise ValueError('E40')
pins=json.loads(data['3.json'])
for n,h in pins.items():
    if hashlib.sha256(data[n]).hexdigest()!=h:raise ValueError('E41')
p.mkdir(mode=0o700)
for n,b in data.items():
    with (p/n).open('xb') as f:f.write(b)
print(sum(map(len,data.values())))
PY
'''.replace('REMOTE', REMOTE).replace('ASSETS', repr(payload))
    (ROOT/'o_place.sh').write_text(body)
    common = '#!/bin/bash\nset -euo pipefail\numask 077\nP='+REMOTE+'\n'
    submit = "sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_ap"+TOKEN
    (ROOT/'o_cpu.sh').write_text(common+'''test ! -e "$P/6.txt"
test ! -e "$P/4.json"
reply=$(CUDA_VISIBLE_DEVICES= '''+submit+''' --cpus-per-task=1 --mem=2G --time=00:05:00 --no-requeue --export=NONE --chdir=/tmp --output=/dev/null --error=/dev/null --wrap="exec /usr/bin/python3 -I -s -B $P/0.py 0 $P")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\\n' "$job" > "$P/6.txt")
printf '%s\\n' "$job"
''')
    (ROOT/'o_check_sub.sh').write_text(common+'''test ! -e "$P/7.txt"
/usr/bin/python3 -I -s -B "$P/0.py" 2 "$P"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=('''+submit+''')
'''.replace('reply=('+submit+')\n','')+'''reply=$('''+submit+''' --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:30:00 --no-requeue --export=NONE --chdir=/tmp --output=/dev/null --error=/dev/null "$P/BATCH.sh")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\\n' "$job" > "$P/7.txt")
printf '%s\\n' "$job"
''')
    (ROOT/'SUBMIT.cmd').write_text((ROOT/'o_check_sub.sh').read_text())
    (ROOT/'o_fetch.sh').write_text(common+'''job=$(cat "$P/7.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i')
test -z "$q"
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads((p/'5.1.json').read_text());b=(p/'5.json').read_bytes()
if r['job']!=sys.argv[2] or r['sha256']!=hashlib.sha256(b).hexdigest() or r['bytes']!=len(b):raise ValueError('E42')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
    for n in ('5.json','5.1.json'):t.add(p/n,arcname=n,recursive=False)
PY
''')
    write(ROOT/'BUILD.json', dict(token=TOKEN, path=REMOTE, bound_files=bound,
        placement_bytes=sum((ROOT/n).stat().st_size for n in bound), estimate_minutes=estimate/60,
        return_reserve_bytes=500_000, project_budget_bytes=2_000_000))
    print(json.dumps(dict(estimate_minutes=estimate/60, placement_bytes=sum((ROOT/n).stat().st_size for n in bound))))


if __name__ == '__main__':
    build()
