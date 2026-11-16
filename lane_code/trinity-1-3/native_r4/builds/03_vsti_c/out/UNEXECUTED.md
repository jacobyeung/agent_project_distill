The census combines an AST call graph with fresh test and rehearsal coverage. `out/UNEXECUTED.json` records roots, dynamic edges, source hashes and coverage pins.
V1/V1b/V1c unexplained reachable lines: 0. Inherited unexplained reachable lines: 318. GPU, venue and error counts: {'venue staging (Trinity or Orchard)': 579, 'error branch (with condition)': 402, 'GPU decode': 209, 'UNEXPLAINED': 318}.

A classified line has not passed a GPU or venue check. Dormant inherited entry points are outside this read and listed separately.

| File | Unexecuted lines | Class | Evidence or condition |
|---|---|---|---|
| `code/a.py` | 2-8,11,17,51,55 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: <module> |
| `code/a.py` | 12-14 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: phase |
| `code/a.py` | 18-22,39-42,44-45,47-48 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: run |
| `code/a.py` | 23-24,26-27,29-31,33-38 | error branch (with condition) | command == 'prepare' |
| `code/a.py` | 28 | error branch (with condition) | fresh != load(root / 'i/BOUND.json') |
| `code/a.py` | 32 | error branch (with condition) | len(bound['keys']) != 450 or len(load(checked(bound['inputs']['FRAMES.json']))['captures']) != 311 |
| `code/a.py` | 52-54 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: main |
| `code/adapter.py` | 36 | error branch (with condition) | sha(p['path']) != p['sha256'] |
| `code/adapter.py` | 54 | error branch (with condition) | len(group) < n |
| `code/adapter.py` | 65 | error branch (with condition) | k != 0 |
| `code/adapter.py` | 66 | error branch (with condition) | canary_only |
| `code/adapter.py` | 85 | error branch (with condition) | len(items) != 450 or len({str(x['id']) for x in items}) != 450 |
| `code/adapter.py` | 88 | error branch (with condition) | sorted(Counter((x['question_type'] for x in items)).values()) != [50] * 9 |
| `code/adapter.py` | 101 | error branch (with condition) | sel['schema'] != 'rgb32-selection-v1' or sel['cache_id'] != cache or len(sel['frames']) != 32 or (indices != [k * (sel['total_num_frames'] - 1) // 31 for k in range(32)]) or (sel['fps'] != 24) |
| `code/adapter.py` | 106 | error branch (with condition) | source.stat().st_size != f['png']['size_bytes'] or sha(source) != h |
| `code/adapter.py` | 149 | error branch (with condition) | len(set(b['keys'])) != len(b['keys']) or b['keys'] != b['canary'] + b['post_canary'] |
| `code/adapter.py` | 155 | error branch (with condition) | (b['canary'], b['post_canary']) != (canary, post) or len(tasks) != 450 |
| `code/engine.py` | 20 | error branch (with condition) | sys.version_info[:2] != (3, 12) or numpy.__version__ != '2.2.6' |
| `code/engine.py` | 31-34,36-37 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: NativeBoundary.__init__ |
| `code/engine.py` | 35 | error branch (with condition) | load(checked(spec['artifact'])).get('step') != 544 |
| `code/engine.py` | 39-43 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: NativeBoundary.batch |
| `code/engine.py` | 45-49 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: NativeBoundary.prefill |
| `code/engine.py` | 51-53 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: NativeBoundary.generate |
| `code/engine.py` | 110-112,114,117-119 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: tower |
| `code/engine.py` | 113 | error branch (with condition) | not receipt.is_file() or weights.stat().st_size != 5627166200 |
| `code/engine.py` | 142 | error branch (with condition) | not boundary.synthetic |
| `code/engine.py` | 223 | error branch (with condition) | g.get('binding') != bound['binding'] or g.get('config') != spec['config'] or bool(g.get('synthetic')) != boundary.synthetic |
| `code/engine.py` | 234-235 | GPU decode | The real boundary invokes prompt/cache/head parity before scoring. |
| `code/engine.py` | 247 | error branch (with condition) | set(bound['canary']) <= set(prior_keys) and (not canary_check(canary, bound['canary'], request, truth)['pass_']) |
| `code/engine.py` | 321 | error branch (with condition) | r['bound'] != bound['binding'] or digest({k: v for k, v in r.items() if k != 'binding'}) != r['binding'] |
| `code/engine.py` | 326 | error branch (with condition) | c['request_binding'] != r['binding'] or c['geometry'] != r['geometry'] or c['config'] != r['config'] |
| `code/entry.py` | 6 | venue staging (Trinity or Orchard) | READ_OVERLAY is set by the production namespace before numerical imports. |
| `code/entry.py` | 42-45,50,61,65 | error branch (with condition) | a.command in ('geometry', 'run', 'job') |
| `code/entry.py` | 58-59 | error branch (with condition) | remaining <= 0 |
| `code/entry.py` | 62-64 | error branch (with condition) | a.command == 'geometry' |
| `code/entry.py` | 73-74 | error branch (with condition) | a.command == 'proof' |
| `code/o.py` | 63,65,67,70-71 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: staged_addition |
| `code/o.py` | 69 | error branch (with condition) | receipt['bytes'] != record['bytes'] |
| `code/o.py` | 81 | error branch (with condition) | p.suffix not in ('.json', '.jsonl', '.npz', '.md', '.log') |
| `code/o.py` | 96,98-99,101,103,105,107,109-116,118-123,125,127-128,130-137,139-146,148-149,151-152,156-159,161-167,169-172,174-177,186-192,194 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: run |
| `code/o.py` | 97 | error branch (with condition) | digest({k: v for k, v in config.items() if k != 'binding'}) != config['binding'] |
| `code/o.py` | 100 | error branch (with condition) | not job.isdigit() or os.environ.get('SLURM_JOB_PARTITION') != 'general' |
| `code/o.py` | 104 | error branch (with condition) | source.stat().st_size != code_record['bytes'] or sha(source) != code_record['sha256'] |
| `code/o.py` | 106 | error branch (with condition) | sha(__file__) != sha(root / 'c/o.py') |
| `code/o.py` | 108 | error branch (with condition) | sha(sys.modules[n].__file__) != sha(root / 'c' / (n + '.py')) |
| `code/o.py` | 126 | error branch (with condition) | sha(root / 'a' / name) != h |
| `code/o.py` | 138 | error branch (with condition) | prior.get('failure') |
| `code/o.py` | 173 | error branch (with condition) | remaining <= 0 |
| `code/o.py` | 178-182 | error branch (with condition) | exception BaseException |
| `code/o.py` | 203-204 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: run_phase |
| `code/o.py` | 205 | error branch (with condition) | proof.get('synthetic') is not False or proof.get('items') != 10 or (not all((k in proof for k in ('identical_count', 'equal_token_share', 'records', 'proven')))) |
| `code/o.py` | 215-220,222 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: main |
| `code/o.py` | 221 | error branch (with condition) | a.command == 'packet' |
| `code/p.py` | 2-7,9,13 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: <module> |
| `code/p.py` | 10-12 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: main |
| `code/pixels.py` | 14 | error branch (with condition) | not av.__version__.startswith(required_av + '.') and av.__version__ != required_av |
| `code/policy.py` | 52 | error branch (with condition) | refused and (c['response'] != RESPONSE or c.get('original_kind', c.get('kind')) != 'error') |
| `code/proof.py` | 52-63,66-72 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: preparation_check |
| `code/proof.py` | 76-78,80-84,86-97,99-105,108,110-112,115-121 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: run |
| `code/proof.py` | 79 | error branch (with condition) | 'proof_core' not in spec |
| `code/proof.py` | 85 | error branch (with condition) | request['adapter_sources'] != N.adapter_sources() |
| `code/proof.py` | 98 | error branch (with condition) | Counter((r['question_type'] for r in references)) != {'camera_displacement': 3, 'camera_movement_direction': 3, 'camera_rotation': 4} |
| `code/proof.py` | 106-107 | error branch (with condition) | not budget.allows(task['question_type']) |
| `code/proof.py` | 109 | error branch (with condition) | N.mask_source(task['question_type']) is not None |
| `code/proof.py` | 113 | error branch (with condition) | decoded.get('errors') or any((c.get('kind') == 'error' for c in decoded['calls'])) |
| `code/proof.py` | 114 | error branch (with condition) | not P.replay(decoded, geo, None)['byte_equal'] |
| `code/report.py` | 58 | error branch (with condition) | not bundle['synthetic'] and (bundle.get('proof') != proof_pin or proof.get('read_binding') != bundle['request_binding']) |
| `code/s0.py` | 107-109,111,185-186,265-266,268,270-271,273-274,276,613-614,627-628,665,677 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/s0.py` | 110 | error branch (with condition) | benchmark_name in data |
| `code/s0.py` | 120 | error branch (with condition) | re.search('<think\\s*>', text, flags=re.IGNORECASE) |
| `code/s0.py` | 127 | error branch (with condition) | not lines |
| `code/s0.py` | 157 | error branch (with condition) | len(unique) == 1 and len(payload.split()) <= 6 |
| `code/s0.py` | 164-165 | error branch (with condition) | exception InvalidOperation |
| `code/s0.py` | 167 | error branch (with condition) | not value.is_finite() |
| `code/s0.py` | 187 | error branch (with condition) | normalized is not None |
| `code/s0.py` | 207 | error branch (with condition) | not (answer_type in ('numeric', 'integer', 'float')) |
| `code/s0.py` | 225 | error branch (with condition) | not isinstance(pred, str) |
| `code/s0.py` | 237 | error branch (with condition) | not math.isfinite(val) |
| `code/s0.py` | 267 | error branch (with condition) | qtype in OFFICIAL_MCA_TYPES |
| `code/s0.py` | 269 | error branch (with condition) | qtype in OFFICIAL_NA_TYPES |
| `code/s0.py` | 272 | error branch (with condition) | isinstance(opts, list) and len(opts) > 0 |
| `code/s0.py` | 275 | error branch (with condition) | re.match('^[A-D]$', gt, flags=re.IGNORECASE) |
| `code/s0.py` | 619 | error branch (with condition) | not (benchmark_name in ('vstibench_repr450_v3', 'vstibench_repr450_v2')) |
| `code/s0.py` | 622 | error branch (with condition) | expected_count > 0 and len(records) != expected_count |
| `code/s0.py` | 629-631 | error branch (with condition) | actual_ids != sorted(canon_ids) |
| `code/scorer.py` | 49 | error branch (with condition) | mismatches or val != expected or round(kit['primary'] * 100, 2) != expected or (abs(collapsed['primary'] - doc['primary_score']) > 1e-12) |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 26,65 | error branch (with condition) | path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 53 | error branch (with condition) | self.written + len(data) > self.limit |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 71 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: regular_files |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 72 | error branch (with condition) | path.exists() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 76-81,83-87,89-91,93 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: members |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 88 | error branch (with condition) | path.suffix in ('.pt', '.safetensors', '.png', '.jpg', '.jpeg') |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 92 | error branch (with condition) | not result |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 1-4,7-8,11-13,15,18-20,23-24,28,32-33,36-37,39,42-43,45-46,48,50-51,53-54,56-57,59,61-64,69-70,73 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 14 | error branch (with condition) | p.parts[1:2] == ('home',) or (len(p.parts) > 1 and p.parts[1].startswith('data')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 38 | error branch (with condition) | sha(value['path']) != value['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 44 | error branch (with condition) | receipt_pin.get('sha256') != FROZEN_COHORT_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 47 | error branch (with condition) | receipt.get('schema') != 'legs1-camera-cohort-v1' or receipt.get('frozen') is not True |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 49 | error branch (with condition) | receipt['frames']['sha256'] != frames_pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 52 | error branch (with condition) | receipt.get('model_reads_before_freeze') != 0 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 55 | error branch (with condition) | len(tasks) != 450 or len({t['id'] for t in tasks}) != 450 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 58 | error branch (with condition) | dict(counts) != {t: 150 for t in TYPES} or dict(counts) != receipt['counts'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 60 | error branch (with condition) | digest([t['id'] for t in tasks]) != receipt['ordered_ids_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 68 | error branch (with condition) | task['source_frame_indices'] != capture['anchor_indices'] or task['rgb32_sha256'] != digest(capture['frames']) or task.get('stratum') != 'camera_gt' or (task.get('label_authority') != 'native_camera_gt') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 72 | error branch (with condition) | not isinstance(pair, list) or len(pair) != 2 or any((type(v) is not int for v in pair)) or (not 1 <= pair[0] < pair[1] <= 32) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/common.py` | 19 | error branch (with condition) | p.parts[1:2] == ('home',) or (len(p.parts) > 1 and p.parts[1].startswith('data')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 18,23,25-26,31-33,35-36 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 24 | error branch (with condition) | sha(root / 'kit_combo3.tar.gz') != ARCHIVE_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 27 | error branch (with condition) | sha(root / name) != CODE[name] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 34 | error branch (with condition) | code != CODE or binding.get('code_sha256') != CODE or dense.get('code_sha256') != CODE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 38 | error branch (with condition) | type(settings.get('image_batch_size', 1)) is not int or settings.get('image_batch_size', 1) != 1 or settings.get('native_image_batch', False) is not False |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 18 | error branch (with condition) | len(frames) != n or len(slots) != 32 or slots[0] != 0 or (slots[-1] >= n) or (min(slots) < 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 20 | error branch (with condition) | any((type(i) is not int for i in indices + slots)) or any(np.diff(indices) <= 0) or any(np.diff(slots) <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 34 | error branch (with condition) | own_depth.shape != (32, 51, 51) or not np.isfinite(own_depth).all() or np.any(own_depth <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 61 | error branch (with condition) | m.get('schema') != GR.SCHEMA or m.get('checkpoint') != artifact |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 63 | error branch (with condition) | m.get('producer') != 'legs1-own-scale-gravity-v1' or m.get('producer_sha256') != sha(__file__) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 111 | error branch (with condition) | state.frame_indices[state.anchor_slots].tolist() != capture['anchor_indices'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 20-23,25,27 | error branch (with condition) | exception geometry_error |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 24 | error branch (with condition) | code != NONFATAL_CODE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 26 | error branch (with condition) | not isinstance(code, str) or not message |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 39 | error branch (with condition) | rotations.shape != (32, 3, 3) or head.shape != (3,) or tower.shape != (3,) or (not all((np.isfinite(value).all() for value in (rotations, head, tower)))) or (min(np.linalg.norm(head), np.linalg.norm(tower)) < 1e-06) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 56 | error branch (with condition) | manifest.get('schema') != SCHEMA or manifest.get('policy') != POLICY or manifest.get('checkpoint') != checkpoint or (not manifest.get('records')) or (not isinstance(manifest.get('videos'), dict)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 63 | error branch (with condition) | not isinstance(native, str) or not native or native in names or (not isinstance(clip, str)) or (len(clip) != 64) or (clip in clips) or (record.get('checkpoint') != checkpoint) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 68 | error branch (with condition) | record.get('error') is not None or not isinstance(record.get('output'), dict) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 76 | error branch (with condition) | not isinstance(error, dict) or error.get('code') != NONFATAL_CODE or any((not isinstance(error.get(key), str) or not error[key] for key in ('code', 'message', 'exception'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 78 | error branch (with condition) | not (record.get('status') == 'REFUSED') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 80 | error branch (with condition) | videos != manifest['videos'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 82 | error branch (with condition) | expected is not None and (len(expected) != len(set(expected)) or names != set(expected)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 92 | error branch (with condition) | task['id'] in seen or task['native'] not in by_native |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 2-12,17-20,23,27,29,33,37,49,70 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 2-8,19,21,24,27,29-30,32,34,36,45,59,69,77 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/vendor/phrase.py` | 3,11 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 23-24,26,38,40,55-60,62,66-74,85-86,90,92-97,100,104,106-117,120-121,123-124,126,162-163,165-168,170,172,174,176,178,180-182,185,187,189-193,195-196,198,200-201,203,205-207,209-211,213-220,222-223,225 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 25 | error branch (with condition) | present and (not artifact.get('mdg') or not cfg.get('mdg')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 39 | error branch (with condition) | family(typ) not in FAMILIES |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 61 | error branch (with condition) | len({t['id'] for t in tasks}) != len(tasks) or len({c['native'] for c in captures}) != len(captures) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 91,105 | error branch (with condition) | masks is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 98-99,118-119 | error branch (with condition) | exception P.MaskOperandMissing |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 122 | error branch (with condition) | admitted and (not runtime) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 140 | error branch (with condition) | (r.get('schema'), r.get('arm'), r.get('scope')) != (SCHEMA, 'paired', 'r1') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 143 | error branch (with condition) | (r.get('mask_source'), r.get('prompt_flag'), r.get('max_new_tokens'), r.get('thinking'), r.get('decoding'), r.get('layout')) != ('by_type', None, 16384, True, 'greedy', 'duplicate') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 145 | error branch (with condition) | r.get('decode_budget') != Q.DECODE_BUDGET or r.get('candidate_universe_policy') != Q.UNIVERSE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 147 | error branch (with condition) | r.get('geometry_refusal_policy') != GR.POLICY |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 149 | error branch (with condition) | r.get('fusion_policy') != FUSION or r['grounding'].get('allow_own_fallback') is not False or r['grounding'].get('depth_source') != 'tower_scaled' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 151 | error branch (with condition) | not re.fullmatch('[0-9a-f]{64}', r['artifact']['sha256']) or r['artifact']['sha256'] == '0' * 64 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 153 | error branch (with condition) | digest({k: v for k, v in r.items() if k != 'binding'}) != r['binding'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 155 | error branch (with condition) | r['adapter_sources'] != adapter_sources() or r['tree_sources'] != source_pins() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 157 | error branch (with condition) | r.get('runtime_tree') != tree_identity(TREE, r['tree_sources']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 164 | error branch (with condition) | r['candidate_policy'] != default_policy() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 169 | error branch (with condition) | has_mdg(artifact, cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 171 | error branch (with condition) | (cfg.get('frame_layout'), cfg.get('training_mode'), cfg.get('trace_program_version')) != ('duplicate', 'final', '3.14') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 173 | error branch (with condition) | cfg.get('depth_enabled') is not True or cfg.get('depth_fov_source') != 'pose_head' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 175 | error branch (with condition) | cfg.get('tool_mode_flag') or cfg.get('s1_route_policy', {}).get('name') != 'frozen-table-no-flag-v1' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 177 | error branch (with condition) | artifact.get('step') != r['step'] or artifact.get('trace_program_version') != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 179 | error branch (with condition) | r['route_table'] != cfg['route_table'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 184 | error branch (with condition) | r.get('query_journal') != Q.journal_policy([dict(key='devrows:' + t['id'], family=family(t['question_type'])) for t in chosen]) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 186 | error branch (with condition) | r['keys'] != ['devrows:' + t['id'] for t in chosen] or not chosen |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 188 | error branch (with condition) | any((r['route_table'].get(t['question_type']) != 'route' for t in chosen)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 194 | error branch (with condition) | r.get('geometry_refusals') != refused |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 197 | error branch (with condition) | r.get('mask_operand_refusals') != operand_refusals(served, refs, masks) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 199 | error branch (with condition) | r.get('candidate_universe_admission') != universe_admission(served, refs, masks) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 202 | error branch (with condition) | r['dry'] or r['parent_standin'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 204 | error branch (with condition) | not r.get('data_receipt') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 208 | error branch (with condition) | g is None or masks is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 212 | error branch (with condition) | g.get('config') != r['config'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 224 | error branch (with condition) | r['perceptions'] != expected |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 439-440,444-447,454,457,463 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: run |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 22-24,28-29,31,33,36-40,43,45,47,52-53,57-58,62-64,70-72,74,76,78-79,81-82,84,86-87,89-90,93-96,99,102-106,108-111,113-114,116,118-119,121,123-124,126-133,136-137,183-185,255,285-286,288,307,309-310,312-313,317,326,334 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 30 | error branch (with condition) | manifest.get('density') != SETTING or manifest.get('checkpoint_sha256') != SAM_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 32 | error branch (with condition) | manifest.get('experiment', {}).get('name') != 'dense_aliases' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 35 | error branch (with condition) | any((x.get('manifest_sha256') != manifest_sha or x.get('stub') is not False for x in (binding, complete))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 41 | error branch (with condition) | complete.get('captures') != len(manifest['captures']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 44 | error branch (with condition) | manifest.get('schema') != 'mask-recall-variant-v1' or len(manifest['captures']) != 152 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 46 | error branch (with condition) | any((c.get('cache_contract') != SETTING for c in manifest['captures'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 65 | error branch (with condition) | missing |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 73 | error branch (with condition) | r.get('schema') != 'legs1-frozen-mask-cache-v1' or r.get('setting') != SETTING |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 75 | error branch (with condition) | r.get('frozen_kit') != frozen_kit.identity() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 77 | error branch (with condition) | r.get('producer_sha256') != sha(Path(__file__).with_name('nomdg.py')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 83 | error branch (with condition) | len(self.captures) != len(self.manifest['captures']) or set(r['captures']) != set(self.captures) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 85 | error branch (with condition) | r['items']['sha256'] != self.manifest.get('items_sha256') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 88 | error branch (with condition) | sha(checked(r['sam_receipt'])) != self.manifest['receipt_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 92 | error branch (with condition) | (self.dense_manifest['experiment']['name'], self.dense_manifest['checkpoint_sha256'], self.dense_manifest['receipt_sha256']) != ('dense', SAM_SHA, self.manifest['receipt_sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 107 | error branch (with condition) | c['anchor_indices'] != list(batch['frame_indices']) or [f['sha256'] for f in c['frames']] != [f['sha256'] for f in si['frames']] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 115 | error branch (with condition) | not journal or journal[-1].get('event') != 'complete' or journal[-1].get('sha256') != entry['cache']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 120 | error branch (with condition) | not dj or dj[-1].get('event') != 'complete' or dj[-1].get('sha256') != entry['dense_cache']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 122 | error branch (with condition) | not any((e.get('event') == 'reuse_dense' and e.get('sha256') == entry['dense_cache']['sha256'] for e in journal)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 125 | error branch (with condition) | raw.get('receipt') != receipt or dense.get('receipt') != receipt |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 150 | error branch (with condition) | geometry.contract.profile != 'scaled_g3t_depth' or geometry.depth_scale_count != 1 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 196-200 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: session.PerceptionSession.execute |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 203,205-207,209-211,213-214 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: session.PerceptionSession._instances |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 204 | error branch (with condition) | ground_backend is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 212 | error branch (with condition) | applied.get(obj['instance_id']) is not True |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 229-230,232,234-236,238-239,241-242,244,248 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: generate |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 231 | error branch (with condition) | getattr(model, 'trace_program_version', None) != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 233 | error branch (with condition) | hasattr(getattr(model, 'auxiliary_heads', None), 'mdg') or getattr(model, 'mdg_head', None) is not None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 237 | error branch (with condition) | MAX_CALL_TOKENS != Q.DECODE_BUDGET['call_window_tokens'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 240 | error branch (with condition) | tokens is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 243 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: generate.process |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 287,328-330 | error branch (with condition) | typ == 'room_size_estimation' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 289-293,295-296,299-300,302-304,306,348-349,351-353 | error branch (with condition) | typ == 'object_abs_distance' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 294,346 | error branch (with condition) | not match |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 298 | error branch (with condition) | not re.search('(?<!\\w)' + re.escape(name) + '(?!\\w)', task['question'] + ' ' + ' '.join(task.get('options') or []), re.I) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 301 | error branch (with condition) | len(names) != 2 or len(set(names)) != 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 305 | error branch (with condition) | ref['segments'][-1]['call'] not in (old, new) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 308 | error branch (with condition) | typ not in ('camera_displacement', 'camera_movement_direction', 'camera_rotation') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 311 | error branch (with condition) | not match or any((not 1 <= int(n) <= 32 for n in match.groups())) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 322 | error branch (with condition) | record['errors'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 338 | error branch (with condition) | not values |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 341 | error branch (with condition) | abs(x) == abs(z) or max(abs(x), abs(z)) <= abs(y) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 350 | error branch (with condition) | not units |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 1-2,4,7,12-14,16,19,74 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 15 | error branch (with condition) | path.suffix != '.json' or path.stat().st_size > 16 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 20-27,30,35-39,43,45,47,50,52,54,56,58-59,61-67,71 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: prepared |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 29 | error branch (with condition) | any((name in data and type(data[name]) is not bool for name in ('production_authorized', 'gpu_first_step_pending'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 34 | error branch (with condition) | data.get('schema') != 's1-in-job-data-v1' or data.get('status') != 'PREPARED' or data.get('synthetic', False) is not False or (data.get('rehearsal') is not False) or (data.get('real_frames_verified') is not True) or (data.get('config') != config_pin) or (data.get('preparation') != cfg.get('preparation')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 42 | error branch (with condition) | receipt.get('schema') != 'c1-preparation-v1' or receipt.get('config_sha256') != identity or artifact.get('config_sha256') != identity or (receipt.get('trainer_commit') != commit) or (artifact.get('base_identity') != cfg['base_identity']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 44 | error branch (with condition) | set(cfg.get('streams', {})) != {'pose', 'pointing', 'routing', 'vqa'} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 46 | error branch (with condition) | any(('mdg' in value or 'geometry_online' in value for value in (cfg, receipt, artifact))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 49 | error branch (with condition) | (cfg.get('training_mode'), cfg.get('frame_layout'), cfg.get('trace_program_version'), cfg.get('depth_enabled'), cfg.get('depth_fov_source')) != ('final', 'duplicate', '3.14', True, 'pose_head') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 51 | error branch (with condition) | {name: value['receipt'] for name, value in receipt['streams'].items()} != cfg['streams'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 53 | error branch (with condition) | any((receipt.get(name) != cfg.get(name) for name in FIELDS)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 55 | error branch (with condition) | trainer.data.layout_settings(receipt) != trainer.data.layout_settings(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 57 | error branch (with condition) | receipt.get('s1_route_policy') != route_policy(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 60 | error branch (with condition) | receipt.get(name) != cfg.get(name) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 75-79,81-88,90,92-93,100 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: load_model |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 80 | error branch (with condition) | torch.device(device).type != 'cuda' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 89 | error branch (with condition) | artifact['base_identity'] != cfg['base_identity'] or artifact['config_sha256'] != trainer.identity(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 91 | error branch (with condition) | not hasattr(processor, '_routing_tokens') or model.trace_program_version != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 26 | error branch (with condition) | policy != DECODE_BUDGET |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 34 | error branch (with condition) | len(closing) != 1 or not self.close_ids or closing[0] not in self.close_ids or (type(self.eos) is not int) or (self.eos < 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 63-64,66,77,79-80,82,111-113,195-198,200-204 | UNEXPLAINED | Reachable statement has no execution or phase classification. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 65 | error branch (with condition) | not pending(tail[offset:]) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 71 | error branch (with condition) | ids |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 73 | error branch (with condition) | len(ids) <= self.previous_position |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 100-101 | error branch (with condition) | not self.close_emitted and self.active_call is not None and (self.deferred_samples < self.policy['call_window_tokens']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 123 | error branch (with condition) | type(total_tokens) is not int or total_tokens < self.callbacks |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 199 | error branch (with condition) | item['key'] in keys |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 17 | error branch (with condition) | recorded.get('schema') != 'legs1-runtime-tree-v1' or recorded.get('sources_sha256') != EXPECTED_SOURCES_SHA or digest(recorded['sources']) != EXPECTED_SOURCES_SHA or (recorded['files'] != len(recorded['sources'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 22 | error branch (with condition) | not local(path).is_relative_to(root) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 25,27 | error branch (with condition) | actual != recorded['sources'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 34 | error branch (with condition) | value != EXPECTED_SOURCES_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 21-22,24-26,28 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: checked |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 23 | error branch (with condition) | not path.is_absolute() or not path.is_file() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 27 | error branch (with condition) | actual != pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 32,34,37,39-40,42,44,46-49,51-52,54-60,62-63,65,67,69 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: configure |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 33 | error branch (with condition) | not sys.flags.isolated or not sys.dont_write_bytecode or os.environ.get('PYTHONPATH') |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 36 | error branch (with condition) | spec.get('schema') != SCHEMA or spec.get('runtime_archive_sha256') != ARCHIVE or spec.get('source_map_sha256') != SOURCE |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 38 | error branch (with condition) | checked(spec['python']).resolve() != Path(sys.executable).resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 41 | error branch (with condition) | any((not p.is_absolute() or not p.is_dir() for p in paths)) or len(set(paths)) != len(paths) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 43 | error branch (with condition) | set(spec['imports']) != set(IMPORTS) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 45 | error branch (with condition) | any((name in sys.modules for name in IMPORTS)) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 50 | error branch (with condition) | checked(spec['sitecustomize']).resolve() != site.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 53 | error branch (with condition) | spec.get('sitecustomize') is not None |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 61 | error branch (with condition) | not expected.resolve().is_relative_to(root) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 64 | error branch (with condition) | Path(value.__file__).resolve() != expected.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 66 | error branch (with condition) | name in REQUIRED_VERSIONS and getattr(value, '__version__', None) != REQUIRED_VERSIONS[name] |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 73-81,83-84,86-87,89-90 | GPU decode | Checkpoint/tower load, own-head preparation, GPU parity or greedy proof/decode: main |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 82 | error branch (with condition) | args.imports_only |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 85 | error branch (with condition) | not command |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 88 | error branch (with condition) | target.name not in spec['entrypoints'] or checked(spec['entrypoints'][target.name]).resolve() != target.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 25-26,28-29,31 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: physical |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 27 | error branch (with condition) | not path.is_absolute() or '..' in path.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 30 | error branch (with condition) | path.is_relative_to(logical) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 36-37 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: StorageRefusal.__init__ |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 41-47,49,51 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: active_mount |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 48 | error branch (with condition) | line.startswith('mnt_id:') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 55-66,69-71,74-75,77-78,81-83,86-87 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: storage_proof |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 72-73 | error branch (with condition) | exception (OSError, ValueError) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 76 | error branch (with condition) | len(matches) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 80 | error branch (with condition) | value['filesystem'] not in ('ext4', 'xfs', 'btrfs', 'tmpfs') or (value['filesystem'] != 'tmpfs' and (not value['source'].startswith('/dev/'))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 85 | error branch (with condition) | not str(job).isdigit() or value['mount'] != '/tmp' or 'job_tmp' not in parts or (str(job) not in parts) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 137-140 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: environment |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 39,42,45,49-52,54-55,57,60 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: card |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 53 | error branch (with condition) | len(assigned) != 1 or assigned[0][2] != 'NVIDIA H100 80GB HBM3' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 56 | error branch (with condition) | not visible or ',' in visible or (visible.startswith('GPU-') and visible != selected[1]) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 59 | error branch (with condition) | require_empty and (float(selected[3]) > 32 or float(selected[4]) != 0 or selected[1] in processes.stdout) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 107-108,111 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: environment |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 26-27,29,31 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: physical |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 28 | error branch (with condition) | not path.is_absolute() or '..' in path.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 30 | error branch (with condition) | path.is_relative_to(PROJECT) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 35-36,41 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: cloud_uri |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 40 | error branch (with condition) | not re.fullmatch('[a-z0-9_-]+/[A-Za-z0-9_./-]+', name) or '..' in Path(name).parts or (not str(record.get('generation', '')).isdigit()) or (not re.fullmatch('[0-9a-f]{64}', record.get('sha256', ''))) or (type(record.get('bytes')) is not int) or (record['bytes'] <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 50 | error branch (with condition) | not re.fullmatch('[0-9a-f]{64}', digest) or name in result |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 53 | error branch (with condition) | not result or len(result) > 20000 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 65,101 | error branch (with condition) | count >= 200000 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 67 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: extract_named |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 74 | error branch (with condition) | name in inventory or not entry.isfile() or entry.size < 0 or (total > Path(path).stat().st_size) or (entry.size > record.get('max_bytes', 8 * 1024 ** 3)) or ('bytes' in record and entry.size != record['bytes']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 78 | error branch (with condition) | target.is_symlink() or not target.parent.resolve().is_relative_to(root.resolve()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 85 | error branch (with condition) | output.write(chunk) != len(chunk) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 87 | error branch (with condition) | copied != entry.size or digest.hexdigest() != record['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 91 | error branch (with condition) | set(inventory) != set(wanted) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 103,105 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: runtime_links |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 104 | error branch (with condition) | entry.linkname not in RUNTIME_LINKS.get(name, ()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 110-118,131 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: namespace |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 135-136,138-139 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: copied |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 137 | error branch (with condition) | not path.is_absolute() or '..' in path.parts or path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 144,146 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: cloud |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 145 | error branch (with condition) | not record['name'].startswith(assets['cloud_prefix'] + '/') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 152 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: verify_inventory |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 153-156 | error branch (with condition) | actual != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 161-163,167-168,173,176-178,181-182,184,186-188,191-192 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: runtime_spec |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 183 | error branch (with condition) | required and (found is None or not found.resolve().is_relative_to(Path(paths[required]).resolve())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 185 | error branch (with condition) | found is None |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 190 | error branch (with condition) | not ptxas.is_file() or not ptxas.resolve().is_relative_to((root / 'fla/p').resolve()) or (not os.access(ptxas, os.X_OK)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 196-198,200-205,207-211,213 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: frames |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 199 | error branch (with condition) | S.sha(puller) != assets['frame_puller']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 217-219,221,223,226-227,232-233,235 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: gcs_header_range |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 220 | error branch (with condition) | not 0 <= start <= end < part['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 231 | error branch (with condition) | response.status != 206 or response.headers.get('x-goog-generation') != generation or response.headers.get('Content-Encoding') not in (None, 'identity') or (response.headers.get('Content-Length') != str(end - start + 1)) or (response.headers.get('Content-Range') != f"bytes {start}-{end}/{part['bytes']}") |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 234 | error branch (with condition) | len(data) != end - start + 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 239-241,243-244,246,276,291-298,300-302,305,307-313,315,317-322,324-325,327-328 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: export_headers |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 242 | error branch (with condition) | total != transport['archive_bytes'] or not parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 248,250,252-258,260-264,266,268-272,274 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: export_headers.read |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 249 | error branch (with condition) | size < 0 or offset < 0 or offset + size > total |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 251 | error branch (with condition) | consumed + size > 2 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 259 | error branch (with condition) | len(requests) >= 300 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 265 | error branch (with condition) | len(chunk) != count |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 273 | error branch (with condition) | len(data) != size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 277-282,284-285,287-289 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: export_headers.pax |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 283 | error branch (with condition) | count <= space - offset + 1 or end > len(data) or data[end - 1:end] != b'\n' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 286 | error branch (with condition) | key.startswith('GNU.sparse') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 299 | error branch (with condition) | pending or read(offset, 512) != b'\x00' * 512 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 303-304 | error branch (with condition) | exception tarfile.HeaderError |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 306 | error branch (with condition) | member.size < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 323 | error branch (with condition) | name in seen or size < 0 or offset + (size + 511) // 512 * 512 > total |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 336,338-340 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: validate_export_headers |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 337 | error branch (with condition) | not value['members'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 341 | error branch (with condition) | path.parts[0] != 'm' + str(step) or member['type'] not in ('0', '\x00', '5') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 345-347,349-356,358-361,363-372,374-376,379-380 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: export_destination |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 348 | error branch (with condition) | target.is_symlink() or not target.resolve().is_relative_to(root.resolve()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 357 | error branch (with condition) | relative in expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 362 | error branch (with condition) | target.exists() and (not target.is_dir()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 377 | error branch (with condition) | unexpected or missing |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 384-386,388,396-401,403-405,407-416,418-424,426-429,431-432,434-436,439-447,449,451-452,454-456,458-461,463-475,477-478,480-485,490,492-495,498,500-504 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: stage |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 390-391,393-394 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: stage.phase |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 402 | error branch (with condition) | total >= 1000000000 or len(assets['small_objects']) != 5 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 430 | error branch (with condition) | len(present) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 448 | error branch (with condition) | S.sha(manifest) != assets['fla']['manifest']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 453 | error branch (with condition) | source.stat().st_size != assets['fla']['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 462 | error branch (with condition) | S.sha(physical(root, assets['model_manifest']['path'])) != assets['model_manifest']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 479 | error branch (with condition) | authentication.returncode or not token or '\n' in token or ('\r' in token) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 491 | error branch (with condition) | receipt['bytes'] != transport['archive_bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 497 | error branch (with condition) | {name: row['bytes'] for name, row in inventory.items()} != {row['name']: row['size'] for row in headers['members'] if row['type'] in ('0', '\x00')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 499 | error branch (with condition) | S.sha(physical(root, config['worker']['artifact']['path'])) != config['worker']['artifact']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 39 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: UploadError.__init__ |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 43-48,50,52-53,55-58,60-61,63-65,70 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: upload |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 54 | error branch (with condition) | not generation.isdigit() or int(meta.get('size', -1)) != path.stat().st_size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 62 | error branch (with condition) | check.stat().st_size != path.stat().st_size or digest != sha(path) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 66-69,266-267,270-271,279-280,285-286 | error branch (with condition) | exception Exception |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 107 | error branch (with condition) | mode not in ('pilot', 'full') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 112-113,115,117,119,121 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: identity |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 114 | error branch (with condition) | not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or not 0 < rate <= 4 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 116 | error branch (with condition) | not pool.is_absolute() or '..' in pool.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 120 | error branch (with condition) | synthetic and (not pool.is_relative_to(allowed)) or (not synthetic and pool != allowed) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 125,127-131,137,139 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: pool_operation |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 132-136 | error branch (with condition) | exception subprocess.TimeoutExpired |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 138 | error branch (with condition) | process.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 235 | error branch (with condition) | not re.fullmatch('[0-9a-f]{64}', plan_sha256) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 239 | error branch (with condition) | not Path(cloud_config).is_absolute() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 262 | error branch (with condition) | (local / 'EXIT.json').stat().st_size > EXIT_RESERVE or usage(local) > cap |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 283 | error branch (with condition) | sum(((local / n).stat().st_size for n in ('result.tar.gz', 'EXIT.json', 'JOB.log', 'RETURN_RECEIPT.json'))) > cap |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 291 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: publish |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 28-32 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: sha |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 36 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: room |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 37 | error branch (with condition) | shutil.disk_usage(path).free < MIN_FREE + extra |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 43 | error branch (with condition) | path.is_absolute() or '..' in path.parts or '\x00' in name |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 54,56,73-74,77-79,82-83,85,87-88,90-91,93-94,98,100 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: extract_stream |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 55 | error branch (with condition) | not item.isdir() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 59 | error branch (with condition) | step is not None and path.parts[0] != 'm' + str(step) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 61 | error branch (with condition) | str(path) in seen |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 64 | error branch (with condition) | len(seen) > 200000 or item.size < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 67 | error branch (with condition) | total > limit |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 71 | error branch (with condition) | not parent.is_relative_to(destination) or target.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 80 | error branch (with condition) | RUNTIME_ABSOLUTE_LINKS.get(str(path)) != item.linkname |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 84 | error branch (with condition) | '..' in link.parts[first_name:] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 86 | error branch (with condition) | not Path(os.path.normpath(str(parent / str(link)))).is_relative_to(destination) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 92 | error branch (with condition) | not source.resolve().is_relative_to(destination) or source.is_symlink() or (not source.is_file()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 96 | error branch (with condition) | not item.isfile() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 99 | error branch (with condition) | not target.is_file() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 108,139 | error branch (with condition) | output.write(chunk) != len(chunk) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 110 | error branch (with condition) | copied != item.size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 117-120,122-133,135-138,140-142,144,146-148,150-151 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: copy_parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 121 | error branch (with condition) | destination.exists() or partial.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 134 | error branch (with condition) | copied > part['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 143 | error branch (with condition) | copied != part['bytes'] or hashed.hexdigest() != part['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 145 | error branch (with condition) | part.get('md5') and base64.b64encode(md5.digest()).decode() != part['md5'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 149 | error branch (with condition) | expected_sha is not None and whole.hexdigest() != expected_sha |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 156 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: ProcessStream.__init__ |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 159,161 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: ProcessStream.read |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 160 | error branch (with condition) | not select.select([self.process.stdout], [], [], 300)[0] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 166-167,169-171,174-177,181 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: process_stream |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 172 | error branch (with condition) | process.wait(timeout=60) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 178-180 | error branch (with condition) | exception subprocess.TimeoutExpired |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 185-186 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: unpack |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 190 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: cloud_environment |
| `code/venue.py` | 105,109 | venue staging (Trinity or Orchard) | Allocation, namespace, asset staging, phase supervision or return path: namespace |

Unreachable inherited code cannot execute from the read roots. Operator and fixture helpers have separate entry points outside that scope.

| File | Origin | Executable lines |
|---|---|---:|
| `code/indices.py` | operator or fixture helper | 17 |
| `code/orchard.py` | operator or fixture helper | 60 |
| `code/proof_stage.py` | operator or fixture helper | 33 |
| `code/s0.py` | inherited | 258 |
| `code/s1.py` | inherited | 178 |
| `code/s2.py` | inherited | 227 |
| `code/s3.py` | inherited | 596 |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | inherited | 40 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | inherited | 1 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_report.py` | inherited | 67 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/common.py` | inherited | 3 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | inherited | 55 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | inherited | 48 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | inherited | 53 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | inherited | 36 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/vendor/phrase.py` | inherited | 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | inherited | 287 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | inherited | 16 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | inherited | 105 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | inherited | 63 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | inherited | 158 |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | inherited | 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | inherited | 126 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | inherited | 259 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/FRAME_PULLER.py` | inherited | 56 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | inherited | 137 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | inherited | 71 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_cpu_replica.py` | inherited | 134 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | inherited | 161 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | inherited | 197 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | inherited | 227 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | inherited | 237 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_pin_graph.py` | inherited | 310 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | inherited | 229 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | inherited | 462 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | inherited | 94 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | inherited | 172 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | inherited | 94 |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | inherited | 146 |
| `code/u.py` | operator or fixture helper | 25 |
| `code/venue.py` | operator or fixture helper | 109 |
