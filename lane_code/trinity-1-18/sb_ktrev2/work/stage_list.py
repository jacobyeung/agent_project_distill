"""Exact run-time read set of the sb_ktfix kit, per part, for staging on another node with the same /scratch paths.
Parts: A, B, C = GPU passes plus their CPU pricing; H = the later held-out one-look CPU report.
Enumerates from the kit's own manifest, rowsets, frame joins and code paths (cross-checked by work/trace/*.json),
then stats and hashes. Files under 2 GB get a computed sha256; larger files get their kit pin, re-verified here.
Directories get a sha256sum-format manifest in out/manifests/ and the manifest's sha256. Reads only; writes only here."""
import hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/sb_ktfix')
W = Path('/scratch/jjyeung/orch_n30/sb_ktrev2')
OUT = W / 'out'; MAN = OUT / 'manifests'; MAN.mkdir(parents=True, exist_ok=True)
S = '/scratch/jjyeung'
TWO_GB = 2 * 1024 ** 3

def digest(x): return hashlib.sha256(json.dumps(x, sort_keys=True, allow_nan=False).encode()).hexdigest()
def capdir(c, root): return Path(root) / digest(c['canonical'])[:16]
def jl(p): return json.loads(Path(p).read_text())

m = jl(K / 'inputs/K1_MANIFEST.arkit_timing.json')
v2 = jl(K / 'inputs/V2_SOURCES.json')['input_sha256']
def rowset(name):
    p = K / 'inputs/K1_ROWSETS' / name
    assert hashlib.sha256(p.read_bytes()).hexdigest() == v2[str(p)]
    return set(p.read_text().splitlines())
train_ids, held_ids = rowset('K1_CAPTURES_TRAIN_239.txt'), rowset('K1_CAPTURES_HELDOUT_57.txt')
caps = [c for c in m['captures'] if c['canonical'] in train_ids | held_ids]
assert len(caps) == 296 and {c['canonical'] for c in caps} == train_ids | held_ids

rows = {}  # path -> dict(kind, parts:set, note)
def add(path, parts, kind='file', note=''):
    path = str(path)
    r = rows.setdefault(path, dict(kind=kind, parts=set(), note=note))
    r['parts'] |= set(parts)
    if note and note not in r['note']: r['note'] = (r['note'] + '; ' + note).strip('; ')

ABC = 'ABC'
# Kit folder: everything code_pins() hashes, plus preflight/binding inputs.
add(K / 'code', ABC, 'dir', 'kit code; code_pins hashes every .py/.json/.md; vendor imported')
add(K / 'configs', ABC, 'dir', 'kit configs; code_pins + kit.json/KBOX rule reads')
add(K / 'inputs/K1_ROWSETS', ABC + 'H', 'dir', 'pinned rowsets')
for n in ('cpu.sh', 'gpu_environment.sh', 'run_A.sh', 'run_B.sh', 'run_C.sh', 'finalize_v3.py', 'bind_camera.py'):
    add(K / 'scripts' / n, ABC, note='launcher or code_pins member')
for n in ('K1_MANIFEST.arkit_timing.json', 'V2_SOURCES.json', 'CAMERA_FRAME_JOINS.json', 'TASK_RULINGS.txt', 'KIT_SPEC_tower_frames_v2.md', 'pose_k1.py', 'MANIFEST.sha256'):
    add(K / 'inputs' / n, ABC + 'H', note='kit input (manifest/code_pins/common INPUTS)')
add(K / 'inputs/ROUTED_FULL_544_devS1_camera.jsonl.gz', 'C', note='staged step-544 camera records (pinned 8855c81e)')
add(K / 'out/DRYRUN.json', ABC, note='preflight requires PASS bound to code 53ea9d60')
for n, parts, note in [('GPU_GO.json', ABC, 'orchestrator GO bound to code_sha256'), ('SHARED_GPU_RESERVATION.json', ABC, 'names the shared ledger (ledger_path must resolve under /scratch on the run node)'), ('DA3_GO.txt', 'C', 'standalone GO line')]:
    add(K / 'inbox' / n, parts, 'create', 'CREATE AT LAUNCH: ' + note)

# Python: interpreter, venv, PYTHONPATH roots, and the reachable part of the .pth overlay.
add(f'{S}/uv-python/cpython-3.12.13-linux-x86_64-gnu', ABC, 'dir', 'base interpreter + stdlib of the venv')
add(f'{S}/envs/sam3_scipy_ovl', ABC, 'dir', 'venv (bin/python symlinks into uv-python); zz_evalx_sam3_overlay.pth adds the overlay below')
add(f'{S}/geo_bakeoff_kit/runtime/site', ABC, 'dir', 'PYTHONPATH[0]: torch 2.10+cu128, numpy, PIL, scipy, safetensors, timm, triton, nvidia libs')
cap = Path(f'{S}/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
site_names = set(os.listdir(f'{S}/geo_bakeoff_kit/runtime/site'))
def modname(n): return n[:-3] if n.endswith('.py') else n.split('.')[0] if '.cpython' in n else n
site_mods = {modname(n) for n in site_names}
for n in sorted(os.listdir(cap)):
    p = cap / n
    if n.endswith('.dist-info'):
        add(p, ABC, 'dir', 'overlay metadata read by importlib.metadata scans')
    elif n in ('ftfy', 'iopath', 'portalocker', 'psutil', 'pycocotools', 'regex', 'wcwidth'):
        assert modname(n) not in site_mods
        add(p, 'B', 'dir', 'SAM 3 dependency not shadowed by runtime/site')
    elif n in ('__editable__.sam3-0.1.0.pth', '__editable___sam3_0_1_0_finder.py', '_cuda_bindings_redirector.pth', 'distutils-precedence.pth', '__pycache__'):
        add(p, ABC, 'dir' if p.is_dir() else 'file', 'processed at interpreter start via the overlay .pth')
# PYTHONPATH[1] and DA3/geo_bakeoff code (imported only by Part C).
add(f'{S}/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src', 'C', 'dir', 'PYTHONPATH[1]: depth_anything_3 package + yaml configs')
add(f'{S}/geo_bakeoff_kit/work/geo_bakeoff', 'C', 'dir', 'geo_bakeoff.backends (DA3 adapter, validate_device)')
add(f'{S}/geo_bakeoff_kit/assets/da3/model.safetensors', 'C', note='DA3 nested giant-large weights')
add(f'{S}/geo_bakeoff_kit/assets/downloads.jsonl', 'C', note='weight_file() size/receipt check')

# Models and shared CPU inputs.
g = m['gpu']
add(g['tower_weights']['path'], ABC, note='G3T weights (pin d460957b)')
add(g['tower_config']['path'], ABC, note='G3T config (pin 5aeb2acd)')
add(g['sam_checkpoint']['path'], 'B', note='SAM 3 checkpoint (pin 9999e234)')
add(g['sam_receipt']['path'], 'B', note='SAM 3 receipt (pin 979e2f77)')
add(g['sam_source'], 'B', 'dir', 'SAM 3 source root (sys.path[0] at load; bpe vocab in sam3/assets)')
sel = f'{S}/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso'
add(f'{sel}/selector_head.json', 'AB' + 'H', note='selector head (CPU pricing)')
add(f'{sel}/selector_head.safetensors', 'AB' + 'H', note='selector head (CPU pricing)')
add(f'{S}/orch_n30/sb_kbox2/train_labels.json', 'AB', note='corrected train labels')
add(f'{S}/orch_n30/sb_kbox2/heldout_labels.json', 'H', note='corrected held-out labels read by labels("heldout")')

# Per-capture K1 inputs.
for c in caps:
    tr = c['canonical'] in train_ids
    for f in c['dense_frames']:
        add(f['path'], 'AB', note='K1 dense frame (all 64 hashed by binding; A feeds 32 anchors, B all 64)')
    T, CV, OWN = capdir(c, f'{S}/k1/run_tower_sam_2'), capdir(c, f'{S}/k1/run_convert_2'), capdir(c, f'{S}/k1/own_170235/native/probe')
    add(T / 'tower.npz', 'AB' + ('' if tr else 'H'), note='stored C64 tower; GPU pass skips the capture if absent')
    add(T / 'PHASE_COMPLETE.json', 'AB' if tr else 'H', note='stored tower receipt')
    add(CV / 'candidates.json', 'AB' if tr else 'BH', note='stored 32-frame SAM cache (B binding + anchors on all 296)')
    add(OWN / 'own.npz', 'AB' if tr else 'H', note='own depth/gravity')
    add(c['gt']['path'], 'AB' if tr else 'H', note='GT raster')
    gp = CV / 'geometry.npz'
    if gp.exists(): add(gp, 'A' if tr else 'H', note='convert export scale check')
    elif tr: add(gp, 'A', 'absent', 'ABSENT: NO_CONVERT_EXPORT (expected for 2 train captures)')

# Part C camera inputs, replicating camera_binding.camera_items().
joins = jl(K / 'inputs/CAMERA_FRAME_JOINS.json')
req = Path(f'{S}/devs1_r2/REQUEST.json'); add(req, 'C', note='dev-S1 staging request')
for p in joins['input_sha256']:
    if p.startswith(str(req.parent / 'anchors')): add(p, 'C', note='anchor/dense manifest hashed by camera_items')
c_frames = set()
for e in joins['items']:
    for f in e['frames']: c_frames.add(f['path'])
    dense, slots = e.get('dense_frames', []), e.get('anchor_slots', [])
    if len(dense) == 64 and len(slots) == 32 and all(Path(f['path']).is_file() for f in dense):
        for f in dense: c_frames.add(f['path'])
for p in c_frames: add(p, 'C', note='dev-S1 frame (32 bound; 64 dense when available)')

# Cross-check per-capture data paths against the CPU traces.
check = {}
for P in 'ABC':
    t = jl(W / 'work/trace' / f'trace_{P}.json')
    data = [p for p in t['opens'] if p.startswith((f'{S}/k1', f'{S}/devs1', f'{S}/orch_cd/dose_pool', f'{S}/orch_n30/sb_kbox2', sel, f'{S}/geo_bakeoff_kit/assets/da3/', f'{S}/geo_bakeoff_kit/assets/downloads', f'{S}/orch_cd/ttower', f'{S}/orch_n30/k1_ops3'))]
    unlisted = [p for p in data if not (p in rows and P in rows[p]['parts']) and not any(p.startswith(d + '/') for d, r in rows.items() if r['kind'] == 'dir')]
    check[P] = dict(traced_data_files=len(data), unlisted=unlisted)
    if P == 'C':
        traced = {p for p in t['opens'] if p.startswith(f'{S}/devs1_frames/')}
        check[P].update(devs1_traced=len(traced), devs1_listed=len(c_frames), devs1_equal=traced == c_frames)
print('trace cross-check', json.dumps(check)[:2000], flush=True)

# Stat and hash.
def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()
pins = {g['tower_weights']['path']: g['tower_weights']['sha256'], g['sam_checkpoint']['path']: g['sam_checkpoint']['sha256'], f'{S}/geo_bakeoff_kit/assets/da3/model.safetensors': '8899faf998dedbc230261ab736fa57015280727399429122d44d4f9e7aac2ddd'}
def walk(d):
    out = []
    for r, ds, fs in os.walk(d):
        ds.sort()
        for n in sorted(fs) + sorted(x for x in ds if os.path.islink(os.path.join(r, x))):
            out.append(os.path.join(r, n))
    return out
def do_file(p):
    st = os.lstat(p)
    return dict(bytes=st.st_size, sha256=sha_file(p))
def do_dir(d):
    lines = []; links = []; total = 0; n = 0
    for p in walk(d):
        rel = os.path.relpath(p, d)
        if os.path.islink(p):
            links.append(f'{os.readlink(p)}\t{rel}'); continue
        total += os.path.getsize(p); n += 1
        lines.append(f'{sha_file(p)}  {rel}')
    slug = d.strip('/').replace('/', '__')
    text = '\n'.join(lines) + '\n'
    (MAN / f'{slug}.sha256').write_text(text)
    res = dict(bytes=total, sha256=hashlib.sha256(text.encode()).hexdigest(), files=n, manifest=f'out/manifests/{slug}.sha256')
    if links:
        lt = '\n'.join(links) + '\n'; (MAN / f'{slug}.symlinks').write_text(lt)
        res['links'] = f'{len(links)} symlinks (target<TAB>path) in out/manifests/{slug}.symlinks sha256 {hashlib.sha256(lt.encode()).hexdigest()}'
    return res
t0 = time.time(); results = {}
def work(item):
    p, r = item
    if r['kind'] in ('create', 'absent'): return p, dict(bytes=None, sha256=None)
    if not os.path.lexists(p): return p, dict(bytes=None, sha256=None, missing=True)
    if r['kind'] == 'dir': return p, do_dir(p)
    res = do_file(p)
    if p in pins: assert res['sha256'] == pins[p], p
    return p, res
with ThreadPoolExecutor(4) as ex:
    for i, (p, res) in enumerate(ex.map(work, sorted(rows.items(), key=lambda kv: -1 if kv[1]['kind'] == 'dir' else 0))):
        results[p] = res
        if i % 2000 == 0: print(i, len(rows), round(time.time() - t0), flush=True)

missing = sorted(p for p, r in results.items() if r.get('missing'))
order = {'create': 0, 'dir': 1, 'file': 2, 'absent': 3}
with (OUT / 'STAGE_LIST.tsv').open('w') as f:
    f.write('path\tkind\tbytes\tsha256\thash_source\tparts\tnote\n')
    for p in sorted(rows, key=lambda x: (order[rows[x]['kind']], x)):
        r, res = rows[p], results[p]
        kind = r['kind'] + ('_MISSING' if res.get('missing') else '')
        src = 'n/a' if res['sha256'] is None else (f"manifest:{res['manifest']} ({res['files']} files)" if r['kind'] == 'dir' else 'computed; equals kit pin' if p in pins else 'computed')
        note = r['note'] + ('; ' + res['links'] if 'links' in res else '')
        f.write(f"{p}\t{kind}\t{'' if res['bytes'] is None else res['bytes']}\t{res['sha256'] or ''}\t{src}\t{','.join(sorted(r['parts']))}\t{note}\n")

totals = {}
for P in 'ABCH':
    sel_rows = [p for p in rows if P in rows[p]['parts'] and results[p]['bytes'] is not None]
    totals[P] = dict(bytes=sum(results[p]['bytes'] for p in sel_rows), entries=len(sel_rows))
allp = [p for p in rows if results[p]['bytes'] is not None]
totals['union'] = dict(bytes=sum(results[p]['bytes'] for p in allp), entries=len(allp))
groups = {}
for p in allp:
    k = ('k1_frames' if p.startswith(f'{S}/k1_frames/') else 'devs1_frames' if p.startswith(f'{S}/devs1_frames/') else 'k1_per_capture' if p.startswith((f'{S}/k1/run_', f'{S}/k1/own_')) else 'gt_rasters' if '/dose_pool/' in p else 'python_env' if p.startswith((f'{S}/uv-python', f'{S}/envs/', f'{S}/geo_bakeoff_kit/runtime')) else 'weights' if p.endswith(('model.safetensors', 'sam3.pt')) else 'kit_folder' if p.startswith(str(K)) else 'other')
    for P in sorted(rows[p]['parts']):
        groups.setdefault(P, {}).setdefault(k, 0); groups[P][k] += results[p]['bytes']
summary = dict(totals=totals, by_group=groups, missing=missing, trace_check=check, seconds=time.time() - t0, rows=len(rows))
(OUT / 'STAGE_TOTALS.json').write_text(json.dumps(summary, indent=1, sort_keys=True))
print(json.dumps(dict(totals=totals, missing=missing[:20], n_missing=len(missing)), indent=1))
