import json, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
f = json.loads((HERE/'facts_raw.json').read_text())
J = '/scratch/jjyeung/orch_n30/lever7/nfa/ref/ret/metadata/reads'
f['fit_set'] = dict(rule='K5 captures outside the 38 with GT cameras bound at the 32 anchors; 41254810 left out as rank 5 excluded it',
    captures=40, by_dataset={'ScanNet': 21, 'ScanNet++': 13, 'ARKit': 6},
    sources={'rank5_nogt_npz': dict(count=22, usable=21, tars={'/scratch/jjyeung/orch_n30/lever1_c/arch5/nogt_gt15_20261120.tar': '9287ce416ae353db4d7d31ab60e310f0c2e2906d4c11b8dcf9456b2224594dd0',
                                                     '/scratch/jjyeung/orch_n30/lever1_c/arch6/nogt_arkit7_20261120.tar': '84098c02f033026c778bf9e3fb7191c77b5ad1a6b33a43405b09dce5effa03cc'},
                                  binding='frame_indices equal K5 dump source_indices and item frames on 22/22', scale='metric (rank 1 served plane)'),
             'camera_t1_gt_npz': dict(count=19, dir='/scratch/jjyeung/orch_n30/cont_ops25_c/cam/gt/t1_gt/gt', binding='frame_indices equal item frames on 19/19',
                                     scale='K5 unit-plane stand-in: rotation and gross class valid, metric translation needs the served scale')},
    no_gt_file=f['outside38_gt']['none_list'])
f['arms'] = {
 'iii_baseline_tower': dict(job=171253, package='b9ef552934627', return_sha256='c82cb20ff9d194b9b9ccc50fbbdba14545332861cad3b0a6f6360a8e76decfc0',
    return_paths=['/scratch/jjyeung/orch_n30/lever7/nfa/ref/parent/a/f/0.tgz', 'orchard:/project/community/jjyeung/okh7/ae71c903/b9ef55293462700029cf5/result.tar.gz',
                  'gs://cmu-gpucloud-jjyeung/q8/ae71c903/b9ef55293462700029cf5/result.tar.gz'],
    journals={J+'/0/metadata/journals/0/0/items.jsonl': ['camera_displacement', 150, '621b8503d78d956c6502bd402566daed01fd7e95c4703fa6e9bd69ba88232f81'],
              J+'/0/metadata/journals/1/0/items.jsonl': ['camera_rotation', 150, '9c181501231e3d460131d7ebc9b95b67354111c0a7a19034123c372bb1945b02'],
              J+'/0/metadata/journals/2/0/items.jsonl': ['camera_movement_direction', 150, 'dfd3cbba12623e6b98c524c4cac0113f74c16d795be7673fc27f2d2bdff04e06'],
              J+'/0/metadata/journals/3/0/items.jsonl': ['object_abs_distance null_argmax', 150, '78a2781a06814516f836339fdde089e588d4299323de0025cc5bb5ebea1bd562'],
              J+'/1/metadata/journals/3/0/items.jsonl': ['object_abs_distance candidates_argmax (pinned)', 150, 'd30aa74917ee66d0e023a7c7a2e5925386e9ae615a6fee775409610545f87bd5']},
    ids_join_devs1_routed='636/636 ids in devs1_routed.json (sha 2849206e...)'),
 'ii_own_heads': dict(camera=dict(job=170631, package='b01ec87a6f29b', path='orchard:/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub_b01ec87a6f29b00029a87/items.jsonl',
                                  bytes=12272848, sha256='9a74924a89badccbc30b8a9e59cae3d99ebedda3069a430a45b991ef1e25a81a', rows=1050, baseline_rows='450 (mode none); 600 are perturbations',
                                  return_sha256_prefix='a2bc039a (pool copy purged; GCS q8/ae71c903/b01ec87a6f29b00029a87 unverified)'),
                      distance=dict(job=170706, path='orchard:/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl',
                                    bytes=5529114, sha256='826385c63cd9f44e131733f83609c9e712714ac4a0f4513b37161cd7bf3a7a2a', rows=369, baseline_rows='150 (mode none), null_argmax, 6-call cap'),
                      paired='own vs tower joined by item key with 0 missing keys (READER_R1_20261117.md Status; tower_pair.py)'),
 'i_direct_unserved': dict(job=169526, packet='e193c2a3c', note='step 544 direct reader: tool calls left unserved; camera answers 9.8/24.7/6.5 vs constant 16.7/25.3/10.1; 96 of 450 camera answers fail to parse',
                           compact='trinity-1-13:/scratch/jjyeung/orch_n30/native_r2/work/direct/DIRECT_B2048_COMPACT.json', compact_bytes=770752,
                           compact_sha256='0ece1ea5e9f04c50fad3060ee94b9867fc789dfcbf765d2f6040cff24ce98428',
                           full='orchard:/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz', full_bytes=39743652,
                           full_sha256='ea97204a8fcd319f4a62b884988b704cdb9ccb22b8c288eaebb97c3fe4dbfaeb',
                           paired='paired with native read 170056 on 636 keys (NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md); key join to 171253 and frame equality unchecked'),
}
f['serving_cost'] = dict(source='SCORE_K5.json cost (H100 s per capture, rebuilds excluded)', A={'ScanNet': 7.32, 'ScanNet++': 7.32, 'ARKit': 4.28},
                         D={'ScanNet': 8.55, 'ScanNet++': 8.54, 'ARKit': 4.76}, check_over_tower=2.15,
                         devs1_extra_seconds_per_full_read=round(54*8.55+30*4.76), devs1_full_read_hours_171253=3.69)
f['coverage'] = dict(devs1_tower_arm_items=786, on_k5=786, uncovered_captures=0, gpu_minutes_to_complete_devs1=0,
                     r0dev_distance=dict(items=290, captures=98, dataset='ScanNet++', two_path_tower_gpu_min=round(98*(7.32+8.54)/60, 1),
                                         orchard_overhead_min='staging 6.3, load 1.7, warmup 2.1 per job (171253, FORECAST_NFA.json); CPU check about 25 (K5)',
                                         arm_reads='tower and own arm each about 2 H100-h (290 x about 25 s); direct exists (171197)'),
                     camera_items_beyond_devs1=0)
(HERE.parent/'FACTS_STAB.json').write_text(json.dumps(f, indent=1)+'\n')
print(hashlib.sha256((HERE.parent/'FACTS_STAB.json').read_bytes()).hexdigest())
