"""Read pinned local metadata and write a scope; never import or run generators."""
from pathlib import Path
import collections
import hashlib
import json
import re
import statistics

ROOT = Path(__file__).resolve().parent
M = Path('/scratch/jjyeung/n30_mirror')
O = Path('/scratch/jjyeung/orch_n30')
INPUTS = {}
COMMAND = 'PYTHONDONTWRITEBYTECODE=1 python scope.py'

def read(p):
    p = Path(p)
    b = p.read_bytes()
    INPUTS[str(p)] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
    return b

def load(p):
    return json.loads(read(p))

ref = load(O/'sb_rowB3/out/REFUSALS.json')
missing = load(O/'sb_rowD3/out/MISSING.json')
pool_path = M/'b01_d0guard/work/d0closure/x/runs/359fcc3c/inputs/prepare_35e47f02fbf74107ae910d52e99157e8/routing/pool/manifest.json'
pool = load(pool_path)
dev_manifest = load(M/'rows_r1/out/vsti_rel_dev_r0/MANIFEST.json')
dev_rasters = load(M/'rows_r1/out/vsti_rel_dev_r0/RASTERS.json')
vsti_manifest = load(M/'rows_a2/v4/vsti/out/vsti_rel_v4/MANIFEST.json')
raster_v2 = load(M/'rows_a2/a2_vqa_v2/RASTERS_v2.json')
raster_v3 = load(M/'rows_a2/a2_vqa_v3/RASTERS_v3.json')

# Hash the inspected code and reports without executing application code.
for p in [
    O/'sb_rowD3/out/REPORT.md', O/'sb_rowD2/out/REPORT.md',
    O/'sb_rowB3/build_rows.py', O/'sb_rowB3/verify_rows.py',
    O/'sb_rowD3/d2_support.py',
    M/'rows_r1/work/codeB/build_rasters.py', M/'rows_r1/work/codeB/common.py',
    M/'rows_r1/work/BRIEF_B_DEV.md',
    M/'rows_r1/work/codeA/build_away.py',
    M/'rows_r1/out/a2_vqa_v7/BUILD_MANIFEST.json',
    M/'rows_a2/v4/vsti/code/sources.py',
    M/'rows_a2/v4/vsti/code/geometry.py', M/'rows_a2/v4/vsti/code/generate.py',
    ROOT/'evidence/local_paths.txt', ROOT/'evidence/local_paths.list',
    ROOT/'evidence/generator_search.txt', ROOT/'evidence/raw_search.txt',
    ROOT/'evidence/provenance_search.txt', ROOT/'evidence/final_search.txt',
    ROOT/'evidence/native_search.txt', Path(__file__),
]:
    read(p)

provenance = collections.defaultdict(list)
sample_text = read(O/'sb_rowD3/out/READ30.md').decode()
for block in re.findall(r'```json\n(.*?)\n```', sample_text, re.S):
    r = json.loads(block)
    p = r.get('provenance', {})
    if p.get('source'):
        provenance[p['source']].append(p)

groups = collections.defaultdict(lambda: {'rows': 0, 'scenes': set(), 'unresolved': 0})
refused_path = O/'sb_rowD2/out/REFUSED.jsonl'
h = hashlib.sha256()
size = 0
with refused_path.open('rb') as f:
    for line in f:
        h.update(line)
        size += len(line)
        r = json.loads(line)
        g = groups[r['source']]
        g['rows'] += 1
        if r.get('canonical'):
            g['scenes'].add(r['canonical'])
        else:
            g['unresolved'] += 1
INPUTS[str(refused_path)] = {'sha256': h.hexdigest(), 'bytes': size}
assert sum(g['rows'] for g in groups.values()) == 93370
assert len(groups) == len(missing['sources']) == 11

receipts = [r for r in dev_rasters.values() if 'seconds' in r]
seconds = [r['seconds'] for r in receipts]
raw_bytes = [sum(v['bytes'] for p, v in r['inputs'].items() if '/r0gt/' in p) for r in receipts]
stat = lambda v: {'min': min(v), 'median': statistics.median(v), 'max': max(v)}
proxy = {
    'source': str(M/'rows_r1/out/vsti_rel_dev_r0/RASTERS.json'),
    'scope': 'R0 ScanNet++ receipts only; different scenes, not training measurements or dataset download sizes',
    'receipt_count': len(receipts), 'audit_pass_count': sum(r['audit']['passed'] for r in receipts),
    'raw_subset_GB_per_scene': stat([b/1e9 for b in raw_bytes]),
    'elapsed_worker_seconds_per_scene': stat(seconds),
    'CPU_hours': None,
    'CPU_hours_status': 'MISSING: receipts measure elapsed time, not process CPU time',
    'GPU_hours_known_adapter': 0,
    'includes': ['mesh_aligned_0.05.ply', 'segments.json', 'segments_anno.json',
                 'pose_intrinsic_pins.json', 'colmap/images.txt', 'colmap/cameras.txt'],
    'excludes': ['RGB/video', 'full source pose extraction', 'dataset archive download',
                 'missing-code recovery', 'independent downstream validation'],
    'formula': 'For N scenes: N * min/median/max(raw subset bytes) / 1e9; N * min/median/max(seconds) / 3600. A planning analogy, not an execution quote.',
}

raw_requirements = {
    'scannet': {
        'status': 'MISSING_EXACT_LOADER_CONTRACT',
        'required_types': ['instance-labelled mesh', 'mesh segmentation and instance aggregation JSON',
                           'alignment transform and stable object IDs/boxes',
                           'camera poses, intrinsics, exact frame-index mapping'],
        'candidate_native_names_not_verified_against_lost_loader': [
            '<scene>_vh_clean_2.ply', '<scene>_vh_clean_2.0.010000.segs.json',
            '<scene>.aggregation.json', '<scene>.txt',
            '<scene>.sens or pinned extracted pose/intrinsic files'],
        'raw_root': None, 'raw_root_status': 'MISSING: no training raw-data root recovered',
        'GB_per_scene': None, 'GB_total': None,
        'sizing_status': 'MISSING: no matching raw-file sizes; do not substitute full RGB-D scene estimates',
        'CPU_hours': None, 'GPU_hours': None,
        'compute_status': 'MISSING original loader/rasterizer and benchmark; available related adapter is CPU-only',
    },
    'scannetpp': {
        'status': 'PARTIAL_CONTRACT_FROM_RELATED_ADAPTER',
        'required_types': ['scans/mesh_aligned_0.05.ply', 'scans/segments.json', 'scans/segments_anno.json',
                           'iphone/pose_intrinsic_pins.json (derived; original pose source also required)',
                           'iphone/colmap/images.txt', 'iphone/colmap/cameras.txt',
                           'exact training frame indices and original instance IDs/OBBs'],
        'raw_root': None, 'raw_root_status': 'MISSING: R0 example root is not a training raw-data root',
        'GB_per_scene': None, 'GB_total': None,
        'planning_proxy': proxy['raw_subset_GB_per_scene'],
        'version_risk': 'Raster keys say scannetppv2; direction sets mix scannetppv2 and scannetpp. Canonical aliases alone do not establish mesh/annotation release.',
    },
    'arkitscenes': {
        'status': 'MISSING_EXACT_LOADER_CONTRACT',
        'required_types': ['3D object annotations with stable IDs and oriented boxes',
                           'registered mesh or depth+instance visibility source used by original loader',
                           'camera trajectory, per-frame intrinsics, timestamp-to-frame map',
                           'original Training split metadata and frame evidence'],
        'candidate_native_names_not_verified_against_lost_loader': [
            '<video_id>_3dod_annotation.json', '<video_id>_3dod_mesh.ply',
            'lowres_wide.traj', 'lowres_wide_intrinsics/*.pincam',
            'lowres_depth/* (only if consumed by recovered loader)'],
        'raw_root': None, 'raw_root_status': 'MISSING: no training raw-data root recovered',
        'GB_per_scene': None, 'GB_total': None, 'CPU_hours': None, 'GPU_hours': None,
        'sizing_status': 'MISSING: raw-file manifest, extraction policy, and timing benchmark',
    },
}

raster_groups = collections.defaultdict(list)
for entry in ref['missing_inputs']:
    e = dict(entry)
    key = Path(e['expected_mirror']).stem
    ds, scene = key.split('__', 1)
    e.update(dataset=ds, scene=scene)
    e['pin_matches_v2'] = raster_v2.get(key) == e['sha256']
    e['pin_matches_v3'] = raster_v3.get(key) == e['sha256']
    raster_groups[ds].append(e)
assert sum(map(len, raster_groups.values())) == 307
assert sum('MISSING_GT' in v for v in ref['rows'].values()) == 4420

builder_prefix = '/scratch/jjyeung/orch_n30/rows_a2/work/builder_cr/builder_cr/'
builder_pins = {p: v for p, v in dev_manifest['inputs'].items() if '/builder_cr/' in p}
adapter = str(M/'rows_r1/work/codeB/build_rasters.py')
generators = {
    'raster': {'original_training_entrypoint': None, 'original_training_commit': None,
               'status': 'MISSING: original entrypoint and run manifest; build_t1_cr.py is a candidate, not a proven 307-file producer',
               'candidate_builder_pins_from_R0_manifest': builder_pins,
               'available_related_adapter': {'path': adapter, **INPUTS[adapter]},
               'adapter_scope': 'R0-dev only; do not substitute its scenes, poses, or annotations for training inputs',
               'dependencies_missing': [builder_prefix+'build_t1_cr.py', builder_prefix+'raycast_cr.py',
                                        '/scratch/jjyeung/orch_n30/rows_r1/work/r0/code/r0lib.py'],
               'adapter_numeric_contract': '32 frames, 240x320, +0.5 pixel centres, camera-z depth, face majority instance with first-vertex tie-break; OpenCV/OpenGL checked against COLMAP; OBB length/layout verified.'},
    'VSTI_row_consumer': {
        'files': {str(M/'rows_a2/v4/vsti/code'/name): INPUTS[str(M/'rows_a2/v4/vsti/code'/name)]
                  for name in ['generate.py', 'geometry.py', 'sources.py']},
        'commit': None,
        'role': 'Consumes rasters; does not regenerate them. Fixed seed 20261116 plus hash-derived per-alias seeds; sorted alias traversal and exact frame-index equality.',
        'environment_from_manifest': vsti_manifest['runtime'],
        'additional_inputs': ['/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json',
                              '/scratch/jjyeung/orch_n30/b12_cntapp/work/si_by_alias.json',
                              '/scratch/jjyeung/orch_n30/b12_cntapp/work/si_ext_by_alias.json',
                              '/scratch/jjyeung/orch_n30/b12_cntapp/work/d3_token_map.json'],
        'additional_input_status': 'MISSING at checked staging roots; exact originals must be restored, not inferred',
    },
    'weak_data': {'commit': '73934511aff5dac8af4b3b12490a88762105dc24',
                  'script': None, 'script_status': 'MISSING: script name not recovered; provenance source root /scratch/jjyeung/orch_cd/weak_data',
                  'frame_map_sha256': '17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3',
                  'frame_map_path': None, 'frame_map_status': 'MISSING: hash known, original filename not recovered',
                  'source': str(O/'sb_rowD3/out/READ30.md')},
}

packs = []
for source in missing['sources']:
    expected = source['expected_path']
    g = groups[expected]
    assert g['rows'] == source['rows'], expected
    scenes = sorted(g['scenes'])
    ds = dict(sorted(collections.Counter(s.split('/')[0] for s in scenes).items()))
    candidates = [s for s in pool['sets'] if any(
        v.get('sha256', '').startswith(Path(expected).name.split('.')[0]) for v in s.get('files', {}).values())]
    entry = dict(expected_path=expected, status='MISSING', affected_rows=g['rows'],
                 affected_scene_count=len(scenes), affected_scenes=scenes, dataset_scene_counts=ds,
                 unresolved_canonical_rows=g['unresolved'], checked_paths_from_D3=source['checked_paths'],
                 exact_full_pack_scene_list=None, full_pack_scene_list_status='MISSING: affected scenes are not a complete raw-input manifest',
                 raw_input_status='MISSING: exact loader, raw paths, raw hashes, and source-qid/instance-role binding',
                 raw_requirements_refs=list(ds), raw_GB_per_scene=None, raw_GB_total=None,
                 CPU_hours=None, GPU_hours=None,
                 runtime_status='MISSING: no matching original pipeline benchmark; a CPU-only implementation is plausible, not verified',
                 sample_provenance=provenance[expected])
    if candidates:
        assert len(candidates) == 1
        s = candidates[0]
        f = s['files']['admitted']
        assert f['sha256'].startswith(Path(expected).name.split('.')[0])
        entry.update(name=s['name'], pinned_sha256=f['sha256'], pack_bytes=f['bytes'],
                     full_pack_rows=f['rows'], reported_full_pack_scenes=s['scenes'],
                     reported_scanned_dirs=s['scan_dirs'], dataset_release_labels=sorted({k.split('|')[-1] for k in s['rows_per_type_dataset']}),
                     generator_root=s['generator_root'], generator_file_pins=s['generator_state'],
                     original_admitted_path=f['path'], generator_status='MISSING locally; manifest records exact script hashes',
                     check_status='SHA256 comparison available; deterministic serialization/compression and exact input closure unproven',
                     manifest_source=str(pool_path))
    else:
        assert '/weak_data/' in expected
        entry.update(name=Path(expected).name, pinned_sha256=None, pack_bytes=None,
                     pin_status='MISSING: no full pack sha256 recovered; commit/frame-map hash are not pack hashes',
                     generator_ref='weak_data', reported_full_pack_scenes=None,
                     check_status='No pack SHA256 target recovered; exact retained-row and independent GT proof would be required')
    packs.append(entry)

all_direction_scenes = sorted(set().union(*(g['scenes'] for g in groups.values())))
availability_log = (ROOT/'evidence/local_paths.txt').read_text()
availability = []
for p in (ROOT/'evidence/local_paths.list').read_text().splitlines():
    absent = f"cannot access '{p}'" in availability_log
    availability.append({'path': p, 'status': 'MISSING' if absent else 'PRESENT',
                         'kind': 'named directory check; presence does not certify raw dataset contents'})

report = {
    'status': 'SCOPE_COMPLETE_REGENERATION_BLOCKED', 'recommendation': 'PARTIAL',
    'recommendation_text': 'Recover pinned generators, original raw-input manifests and frame/instance bindings first; do not start a bulk dataset fetch or certify raw-only regeneration.',
    'host': 'trinity-1-18', 'command': COMMAND,
    'number_methods': {
        'raster_counts': "len(REFUSALS.missing_inputs), grouped by basename before '__'; count rows containing MISSING_GT",
        'direction_counts_and_lists': 'Stream D2 REFUSED.jsonl; group by source and deduplicate recorded canonical; assert counts match D3 MISSING.json',
        'full_pack_numbers': 'Read matched sets[].files.admitted, scenes and scan_dirs from the pinned pool manifest; never sum overlapping scene counts',
        'storage_and_runtime_proxy': proxy['formula'],
        'local_availability': 'Exact ls -ld command and output in evidence/local_paths.txt; no raw directory found to size with du -s',
        'hashes': 'hashlib.sha256 over full bytes of each input; embedded upstream pins are attributed, not revalidated',
    },
    'input_sha256': INPUTS,
    'rasters': {'count': 307, 'affected_sources': 4420, 'groups': dict(raster_groups),
                'original_raw_input_manifest': 'MISSING', 'generators_ref': 'raster',
                'raw_requirements_refs': ['scannet', 'scannetpp'],
                'training_CPU_hours': None, 'training_GPU_hours': None,
                'scannetpp_227_raw_subset_GB_proxy': {k:v*227 for k,v in proxy['raw_subset_GB_per_scene'].items()},
                'scannetpp_227_worker_hours_proxy': {k:v*227/3600 for k,v in proxy['elapsed_worker_seconds_per_scene'].items()},
                'all_307_raw_GB_total': None, 'all_307_sizing_status': 'MISSING: ScanNet raw sizes and exact training input contracts',
                'check': 'All target file hashes known. Byte identity can be checked directly. Reproducibility requires matching arrays, dtypes, serialization order, NumPy/ZIP/zlib versions and ray-casting conventions; not established.',
                'equivalence': 'Without original arrays/member hashes, a container hash mismatch cannot be waived. An independently reviewed per-source proof must bind IDs, frames, poses, boxes, visibility, operands, margins and answers to pinned raw data. Aggregate/statistical agreement is insufficient.'},
    'direction_packs': packs,
    'direction_unique_affected_scenes': all_direction_scenes,
    'direction_unique_affected_scene_count': len(all_direction_scenes),
    'direction_unique_affected_dataset_counts': dict(collections.Counter(s.split('/')[0] for s in all_direction_scenes)),
    'generators': generators, 'raw_requirements': raw_requirements, 'R0_proxy': proxy,
    'local_availability': availability,
    'availability_scope': 'Known staging roots and explicit conventional dataset-root probes only. No whole-node scan, NFS inventory, remote paths, archives, or network checked. Raw data are not established locally; fetch/restore only after exact manifests are recovered.',
    'proof_requirements': [
        'Restore exact dataset releases, raw hashes, original frame sampling, per-frame intrinsics and pose conventions.',
        'Recover source-qid to instance-role mappings; names and old answers do not identify instances or prove geometry.',
        'Recover selection seeds, ordering, exclusions, scene aliases, qid construction and template/formatter versions.',
        'For gzip packs, match mtime/header/name, compression library/level, JSON ordering and float formatting to target bytes.',
        'Compare complete SHA256 where pinned. A mismatch needs independently reviewed exhaustive semantic proof, not statistical answer agreement.',
        'For retained rows, validate signed-up, facing transforms, angular boundary policy, exact frame evidence and all numeric operands.',
        'Reproduce the downstream direct-VQA transform and opposite-direction selection; its available build_away.py is not a raw GT generator.',
    ],
    'risks': ['Dataset release drift; absent meshes, segment/instance annotation files or pose extraction metadata',
              'Canonical capture aliases do not establish dataset release or full-pack membership',
              'Original training raster entrypoint and 3 weak-data pack hashes not recovered',
              'R0 proxy has failed camera-convention/geometry checks and cannot be treated as guaranteed training throughput',
              'Byte-level gzip/NPZ drift; numeric boundary changes; missing deterministic selection manifests'],
    'actions_performed': 'Local metadata/code reads, scoped filename searches, named-directory ls, and scope writing only; no generator execution, regeneration, fetch, Git, SSH, GPU use or remote-path probing.',
}

md = []
def line(s=''): md.append(s)
line('Regeneration needs missing pinned generators and complete input manifests; raw datasets alone do not establish either byte identity or equivalent GT.')
line('Command for every count, list, hash and proxy below: `PYTHONDONTWRITEBYTECODE=1 python scope.py`; methods, exact scenes, paths and full hashes are in `REGEN_SCOPE.json`. GB means decimal GB.')
line()
line('**(a) Missing GT rasters**')
line()
line('| Item | Exact scene list / output pins | Generator | Raw inputs and local state | Raw GB; compute |')
line('|---|---|---|---|---|')
line('| ScanNet: 80 | JSON `rasters.groups.scannet`; all NPZ SHA256 known | Original entrypoint/commit MISSING; candidate below | Instance mesh, segments/aggregation, boxes/alignment, poses/K and frame pins; loader contract/raw root MISSING | GB/scene, total and CPU/GPU-hours MISSING |')
pbytes = report['rasters']['scannetpp_227_raw_subset_GB_proxy']
ptime = report['rasters']['scannetpp_227_worker_hours_proxy']
line(f'| ScanNet++ v2: 227 | JSON `rasters.groups.scannetppv2`; all NPZ SHA256 known | Candidate `build_t1_cr.py`, SHA `eef52cfe…`; related adapter `66772ccb…` | Mesh + segment/OBB JSON + aligned poses/per-frame K + COLMAP + exact pins; training inputs MISSING | Proxy {pbytes["min"]:.2f}–{pbytes["max"]:.2f} GB total (median-scenario {pbytes["median"]:.2f}); {ptime["min"]:.2f}–{ptime["max"]:.2f} worker-h (median {ptime["median"]:.2f}); related adapter uses 0 GPU-h |')
line()
line('These 307 files affect 4,420 sources; no ARKit raster occurs in this missing list. Full 307-file GB and measured CPU-hours remain MISSING.')
line('Candidate files expected at `/scratch/jjyeung/orch_n30/rows_a2/work/builder_cr/builder_cr/{build_t1_cr.py,raycast_cr.py}` are MISSING. Their recorded SHA256s are `eef52cfe0f1dcdb4e428a172bf3d0cd2cb59c8dc73c5cbce1f21b25fde5b09f8` and `80b2a1521c8215bf8a65ecea51eaec340a5d9887ae7f96fd3fb6a91cfbc4688b`. Neither is proven to be the original 307-file entrypoint.')
line(f'Available adapter: `n30_mirror/rows_r1/work/codeB/build_rasters.py`, SHA256 `{INPUTS[adapter]["sha256"]}`; it builds R0-dev, not these training scenes. Commit MISSING. Its `r0lib.py` dependency is also MISSING locally.')
line('The adapter specifies 32 × 240 × 320 samples, pixel centres +0.5, camera-z depth, majority face-instance assignment, first-vertex tie breaking, COLMAP convention checks and verified OBB extents. Recover the training version before adopting these choices.')
line(f'Proxy basis: {len(receipts)} R0 receipts ({proxy["audit_pass_count"]} pass), {min(raw_bytes)/1e9:.3f}–{max(raw_bytes)/1e9:.3f} GB/scene, median {statistics.median(raw_bytes)/1e9:.3f}; {min(seconds):.1f}–{max(seconds):.1f} elapsed seconds/scene, median {statistics.median(seconds):.1f}. Multiply by 227; these are worker elapsed hours, not measured CPU-hours or a training forecast.')
line('The proxy includes `scans/{mesh_aligned_0.05.ply,segments.json,segments_anno.json}`, sliced `iphone/pose_intrinsic_pins.json`, and `iphone/colmap/{images.txt,cameras.txt}`. It excludes RGB, full pose extraction, downloads and proof work. Its R0 scene inputs cannot replace training inputs.')
line('Available raster consumer: `n30_mirror/rows_a2/v4/vsti/code/generate.py`, SHA `fceb45e6bee7aff7d8c4b388cdf0caf269c1141b42d06c24c6833d23afabcb88`; it uses fixed/hash-derived seeds. Row replay also needs the original alias/frame manifests and exclusions. All 307 target raster pins match `RASTERS_v3.json`; full hashes for consumer dependencies are in JSON.')
line()
line('**(b) Missing direction packs**')
line()
line('Each row lists retained direction rows, exact affected-scene counts by dataset (S=ScanNet, P=ScanNet++, A=ARKitScenes), and the full pack scene count reported upstream. Exact affected lists are in JSON; complete pack scene manifests are MISSING.')
line()
line('| Pack / SHA256 prefix | Retained rows | Affected scenes S/P/A | Full-pack scenes | Generator | Raw GB / CPU / GPU |')
line('|---|---:|---|---:|---|---|')
for p in packs:
    d = p['dataset_scene_counts']
    label = p['name'].replace('PACK_object_rel_direction_', 'weak_data ').replace('.jsonl.gz', '')
    pin = p.get('pinned_sha256')
    gen = ('r3' if p['name'].endswith('gaps') else 'r2') if pin else 'commit 73934511…; script MISSING'
    line(f'| {label} / {pin[:16] if pin else "pin MISSING"} | {p["affected_rows"]:,} | {d.get("scannet",0)}/{d.get("scannetpp",0)}/{d.get("arkitscenes",0)} | {p.get("reported_full_pack_scenes") or "MISSING"} | {gen} | MISSING / MISSING / MISSING |')
line()
line(f'The packs affect 93,370 rows across {len(all_direction_scenes):,} distinct recorded canonical captures. Do not sum overlapping per-pack scenes or treat retained scene lists as complete pack inputs.')
line('r2: `/scratch/jjyeung/orch_cd/dose_pool/work/v314r2/dose_t0.py` SHA `58d03b0488bfad58e270ded1f0e594d9bca70de9ca87d3a912c34c58cb69fce8`; renderer `ground_rows_out/render_full.py` SHA `584d6e031f1970a522a8f9c476c07ed3cd2d1c1107fe10cf10cac6b5e39d102d`.')
line('r3: corresponding `work/v314r3/dose_t0.py` SHA `dd73f017703417e11b022e5b2def31c3c0c41d73bd477c0bf961f4387edca1d0`; renderer SHA `63a7cbc068de174730b9e0030082ed5107e22a17ee19a39a34b4800f5a315344`. These are manifest pins; executable copies and commit IDs are MISSING in the inspected mirror.')
line('The three weak-data packs record commit `73934511aff5dac8af4b3b12490a88762105dc24` and frame-map SHA `17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3`; their generator filename, frame-map filename and pack SHA256 are MISSING. Their exact expected pack paths remain in JSON; no remote path was probed.')
line('ScanNet/ScanNet++ packs require the native geometry/annotation/camera inputs above plus original qid→instance roles, scene release, sampled-frame evidence, selection seeds, exclusions, templates and packing rules. T0 records `scannetppv2`; T1 records `scannetpp`. Do not infer release equality from canonical aliases.')
line('ARKit packs additionally need stable annotated OBB IDs, the original mesh/depth visibility source, trajectory, per-frame intrinsics, timestamp/frame mapping and Training metadata. Native candidate filenames are listed separately in JSON; the exact loader and raw root are MISSING, so no fetch list is asserted.')
line('All direction GB/scene, total GB and CPU/GPU-hours are MISSING: the full raw manifests, loaders and matching timing logs were not recovered. The R0 raster proxy does not price pack selection, role reconstruction or validation. Retained-row reconstruction may cost less than full-pack byte replay but cannot inherit its file hash.')
line()
line('**Local availability and verification**')
line()
line('`evidence/local_paths.txt` records the exact `ls -ld` command: training staging roots `orch_n30/{rows_a2,b12_cntapp}/work`, their checked mirrors, R0 raw roots, and explicit conventional dataset-root probes are absent. Only the checked R0 receipt directory exists; it does not establish raw-data availability. No raw directory was available to size with `du -s`.')
line('This is a bounded path check, not proof that the entire node has no datasets. Fetch or restore is required for these expected paths unless an owner supplies another pinned local root; the training raw roots and exact raw-file hashes remain MISSING. No NFS or unreachable `orch_cd` path was searched.')
line('Rasters: all target hashes permit exact checking, but deterministic byte replay is unproven. Pin raycaster/mesh versions, poses, float dtypes, ordering, NumPy and NPZ/ZIP/zlib behavior. A container mismatch cannot be dismissed without original member hashes/arrays or an independently accepted per-source GT proof.')
line('Packs: eight full SHA256 targets are recovered; three are MISSING. Exact replay also needs JSON/float ordering, gzip headers/mtime and compression versions. Source-row hashes, a commit or a frame-map hash are not pack hashes.')
line('Equivalent GT requires exhaustive source-bound checks of instance roles, frame visibility, signed-up/frame conventions, facing transforms, boundary margins, numeric operands and answers. Old labels or statistical agreement cannot certify equivalence. Available `build_away.py` is a downstream text/selection transform, not a raw-GT generator.')
line('Before execution: recover the missing code/input closure; size only the named raw files; validate one pinned scene per dataset and one pack against hashes or an explicit equivalence contract; then estimate CPU time from that pilot. No pilot, regeneration or fetch ran for this scope.')
line('Recommendation: **PARTIAL** — recover pinned builders and raw/frame/instance manifests first; do not bulk-fetch datasets or claim bit-for-bit/equivalent regeneration yet.')
assert len(md) <= 60, len(md)
(ROOT/'out/REGEN_SCOPE.md').write_text('\n'.join(md)+'\n')
report['report_sha256'] = hashlib.sha256((ROOT/'out/REGEN_SCOPE.md').read_bytes()).hexdigest()
report['report_lines'] = len(md)
(ROOT/'out/REGEN_SCOPE.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n')
print(json.dumps({'report_lines': len(md), 'rasters': 307, 'packs': len(packs),
                  'direction_unique_affected_scenes': len(all_direction_scenes),
                  'input_files_hashed': len(INPUTS), 'report_sha256': report['report_sha256']}))
