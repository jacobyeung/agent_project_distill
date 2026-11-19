"""Audit only registered K1 training GT sources; never compute footprint scores."""
from common import *
import re
import resource
import zipfile

BUILD = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
RAW = Path('/scratch/jjyeung/orch_cd/toolprog/data/scannet_gt/raw')
COMMAND = 'bash scripts/cpu.sh scripts/s1k2_audit.py'


def selected_blocks(path, wanted):
    # Inspect identities in the shared index; decode only the registered train records.
    text = path.read_text().split('  "pilot":', 1)[0]
    blocks = re.findall(r'^    \{\n.*?^    \}(?:,|\n)', text, re.M | re.S)
    result = []
    for block in blocks:
        identity = re.search(r'"canonical": "([^"]+)"', block)
        if identity and identity[1] in wanted:
            result.append(json.loads(block.rstrip(',\n')))
    assert len(result) == len(wanted)
    assert {c['canonical'] for c in result} == wanted
    return result


def main():
    resource.setrlimit(resource.RLIMIT_AS, (39 << 30, 39 << 30))
    registration = W/'out/S1K_REGISTRATION.json'
    rule = W/'out/S1K2_RULE.md'
    wanted = set(read(registration)['captures'])
    assert len(wanted) == 110
    sources = [Path(__file__), W/'scripts/common.py', W/'scripts/cpu.sh', registration, rule, K1,
               BUILD/'out/CAPTURES.json', BUILD/'work/inventory.py', BUILD/'work/gt_set.py',
               BUILD/'native_kit/build_manifest.py',
               BUILD/'native_kit/vendor_sam/vendor/scene_gt.py',
               W/'vendor/harness.py', W/'evidence/k1_room_tables.py',
               W/'configs/KERNEL_PROVENANCE.json', W/'configs/KERNEL_FROZEN.json']
    inputs = {str(p): sha(p) for p in sources}
    captures = selected_blocks(K1, wanted)
    assert all(c['k1_split'] == 'train' for c in captures)
    inventory = selected_blocks(BUILD/'out/CAPTURES.json', wanted)
    by_id = {c['canonical']: c for c in inventory}
    metadata_path = W/'out/S1K2_TRAIN_METADATA.json'
    inventory_path = W/'out/S1K2_TRAIN_INVENTORY.json'
    write(metadata_path, dict(captures=captures, scope='K1 train only', command=COMMAND), inputs)
    write(inventory_path, dict(captures=inventory, scope='K1 train only', command=COMMAND), inputs)
    inputs.update({str(p): sha(p) for p in [metadata_path, inventory_path]})
    excluded = []
    source_records = {}
    known_raster_members = {'depth.npy', 'inst.npy', 'K.npy', 'K_frames.npy', 'c2w.npy',
                           'valid.npy', 'ids.npy', 'labels.npy', 'obb_centroid.npy',
                           'obb_lengths.npy', 'obb_axes.npy', 'frame_indices.npy'}
    for c in captures:
        expected = {g['path']: g['sha256'] for g in by_id[c['canonical']]['gt_sources']}
        assert expected[c['gt']['path']] == c['gt']['sha256']
        for path, expected_hash in expected.items():
            p = Path(path)
            assert p.is_relative_to('/scratch'), 'NFS reads are forbidden'
            if path not in source_records:
                if not p.is_file():
                    source_records[path] = dict(status='MISSING', expected_sha256=expected_hash)
                    continue
                actual = sha(p)
                assert actual == expected_hash, 'GT digest mismatch: '+path
                inputs[path] = actual
                with zipfile.ZipFile(p) as archive:
                    members = archive.namelist()
                # Unexpected fields need examination, never an automatic exclusion.
                assert set(members) == known_raster_members, (path, members)
                source_records[path] = dict(status='RASTER_ONLY', sha256=actual, members=members)
        mesh_checks = []
        if c['canonical'].startswith('scannet/'):
            scene = c['canonical'].split('/')[1]
            for suffix in ('_vh_clean_2.ply', '_vh_clean_2.0.010000.segs.json', '.aggregation.json'):
                p = RAW/scene/(scene+suffix)
                exists = p.is_file()
                mesh_checks.append(dict(path=str(p), status='PRESENT' if exists else 'MISSING'))
                assert not exists, 'Mesh exists; inspect its floor labels before excluding '+str(p)
        excluded.append(dict(capture=c['canonical'], room=c['room'], split='train',
                             status='EXCLUDED', label_status='MISSING', gt_sources=list(expected),
                             reason='Registered GT sources contain depth/instance rasters and object boxes, not independent room areas or segmented floor meshes.',
                             room_area_source_path='MISSING: no mesh/room-area annotation path registered',
                             source_code_mesh_checks=mesh_checks))
    audit_path = W/'out/S1K2_GT_AUDIT.json'
    write(audit_path, dict(status='BLOCKED', command=COMMAND, captures=len(captures),
                          rooms=len({c['room'] for c in captures}), eligible_captures=0,
                          excluded=excluded, gt_sources=source_records,
                          search_scope='Registered K1 training manifest, its capture inventory, all referenced training GT NPZs, and documented ScanNet raw-mesh paths; no NFS or unregistered broad search.',
                          data_access='Only registered train records were decoded from shared metadata indexes. No held-out payload, prediction, score, R0-dev, dev-S1 or official item was opened. GT NPZs were hashed and their ZIP member names inspected; arrays were not decompressed.'), inputs)
    (W/'BLOCKER.md').write_text(
        '# S1k2: independent room-area GT is MISSING\n\n'
        f'All {len(captures)} registered K1 training captures lack a qualifying independent room-area source in the kit inputs. '
        'The complete capture exclusions, exact GT paths and SHA256 values are in out/S1K2_GT_AUDIT.json.\n\n'
        'The required input is a scan-GT room-area annotation or segmented floor mesh, with metric units and an authenticated capture-to-room mapping. '
        f'The expected source binding belongs in {K1}, in each registered training capture\'s GT metadata. '
        'That metadata records only an NPZ path and SHA256; no independent area/mesh path is supplied, so an exact missing annotation filename cannot be asserted.\n\n'
        f'Checked {BUILD}/out/CAPTURES.json and its inventory/GT-selection/build-manifest source. '
        'Every registered training GT source resolves to /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/. '
        'All NPZs contain depth, instances, intrinsics, poses, validity, object identities/labels, object boxes and frame indices; none contains a room-area label or mesh topology. '
        'Object bounding boxes are not room footprints. evidence/k1_room_tables.py explicitly identifies the existing labels as room_v314 on GT geometry.\n\n'
        f'The documented ScanNet mesh templates under {RAW}/<scene>/ are <scene>_vh_clean_2.ply, '
        '<scene>_vh_clean_2.0.010000.segs.json and <scene>.aggregation.json. All three files are absent for each of the 41 registered ScanNet captures. '
        'The audit lists all exact paths. The kit supplies no corresponding independent ScanNet++ room-area/mesh binding.\n\n'
        'Family scores, bootstrap intervals, winner, deployment constants and independent-label validation remain MISSING. '
        'No S1k2 kernel was rebound or approved. Supply the authenticated GT source on local disk to unblock selection.\n\n'
        f'Command: `{COMMAND}`.\n')
    status('S1k2 is blocked: the 110 registered K1 training captures have no independent room-area annotation or segmented floor-mesh source among the audited kit inputs. All captures are excluded and listed in out/S1K2_GT_AUDIT.json. No scores, winner or kernel rebind exists. CPU-only validation and blocker packaging remain.')
    print('BLOCKED: 110 excluded captures;', len(source_records), 'GT rasters audited;',
          len({c['room'] for c in captures}), 'rooms; 0 independent labels')


if __name__ == '__main__':
    main()
