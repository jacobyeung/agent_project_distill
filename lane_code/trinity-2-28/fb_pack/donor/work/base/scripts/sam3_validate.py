"""CPU preparation and orchestrator-scheduled SAM 3 parity/re-cache runs."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import random
import time
import sys

import numpy as np

from student_pilot.sam3_tower import attach_sam3_tower, normalize_phrase, sha256


def dump(path, value, *, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=None if compact else 2, allow_nan=False)
        f.write('\n')


def load_cache(path):
    with np.load(path, allow_pickle=False) as data:
        return json.loads(data['payload'].tobytes())


def rle_encode(mask):
    a = np.asarray(mask, dtype=np.uint8).ravel(order='F')
    counts = np.diff(np.r_[0, np.flatnonzero(np.diff(a)) + 1, a.size]).tolist()
    if a.size and a[0]:
        counts.insert(0, 0)
    return {'size': list(mask.shape), 'counts': counts}


def rle_decode(value):
    counts = np.asarray(value['counts'], dtype=np.int64)
    if (counts < 0).any() or counts.sum() != np.prod(value['size']):
        raise ValueError('Invalid reference RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape(value['size'], order='F')


def prepare(args):
    # Use only scene membership; no answers, masks, or GT fields enter manifests.
    with args.dev_items.open() as f:
        dev_scenes = {'scannet/' + json.loads(line)['scene_name'] for line in f if line.strip()}
    rows = [r for r in json.loads(args.scenes.read_text())['scenes'] if r['scene'] in dev_scenes]
    if len(rows) != 84 or len({r['scene'] for r in rows}) != 84:
        raise ValueError('Expected the complete 84-scene dev manifest')
    chosen = set(random.Random(17).sample(sorted(r['scene'] for r in rows), 10))
    parity = []
    recache = []
    for row in rows:
        scene = row['scene']
        paths = [args.frames / scene.replace('/', '__') / f'{k}.jpg' for k in range(32)]
        if not all(p.is_file() for p in paths):
            raise ValueError('Missing local RGB frames: ' + scene)
        item = {'scene': scene, 'phrases': row['phrases'],
                'frames': [str(p.resolve()) for p in paths]}
        recache.append(item)
        if scene in chosen:
            cache = args.reference / (scene.replace('/', '__') + '.npz')
            item = dict(item, frame_sha256=[sha256(p) for p in paths],
                        reference=str(cache.resolve()), reference_sha256=sha256(cache))
            parity.append(item)
    contract = {'joint_floor': .2, 'cap': 10, 'image_batch_size': 1, 'resolution': 1008,
                'precision': 'bf16 autocast', 'mask_threshold': .5,
                'phrase_rule': 'ttower/common.py phrase', 'training_labels': False}
    base = {'source_manifest': str(args.scenes), 'source_sha256': sha256(args.scenes),
            'membership_path': str(args.dev_items), 'membership_sha256': sha256(args.dev_items),
            'contract': contract, 'receipt_sha256': sha256(args.receipt)}
    dump(args.out/'parity_10.json', dict(base, scenes=parity, selection='seed 17 sample, fixed before inference',
                                      tolerance={'score_atol': .001, 'mask_iou_min': .99}))
    dump(args.out/'recache_dev.json', dict(base, scenes=recache))
    print(json.dumps({'parity_scenes': len(parity), 'recache_scenes': len(recache),
                      'parity_name_frames': sum(len(r['phrases'])*32 for r in parity),
                      'recache_name_frames': sum(len(r['phrases'])*32 for r in recache)}))


def compare(reference, fresh):
    """Reject score drift, missing/changed queries, and source-mask drift."""
    old_scores = np.sort(np.asarray(reference['all_instance_scores'], dtype=float))[::-1][:5]
    new_scores = np.sort(fresh.all_scores.numpy())[::-1][:5]
    if old_scores.shape != new_scores.shape:
        return {'ok': False, 'reason': 'proposal count differs'}
    score_error = float(np.max(np.abs(old_scores-new_scores))) if len(old_scores) else 0.
    presence_error = abs(reference['presence'] - fresh.presence)
    old = reference['instances']
    queries = fresh.query_ids.tolist()
    query_match = [i['query'] for i in old] == queries
    ious = []
    if query_match:
        for index, instance in enumerate(old):
            a, b = rle_decode(instance['mask']), fresh.masks[index].numpy()
            if a.shape != b.shape:
                ious.append(0.)
            else:
                union = int((a | b).sum())
                ious.append(float((a & b).sum()/union) if union else 1.)
    minimum = min(ious, default=1. if query_match else 0.)
    return {'ok': score_error <= .001 and presence_error <= .001 and query_match and minimum >= .99,
            'top5_score_max_abs_error': score_error, 'presence_abs_error': presence_error,
            'query_ids_match': query_match, 'mask_min_iou': minimum, 'masks_compared': len(ious)}


def compare_noise_aware(reference, fresh, *, gate=.3, joint_gate=False,
                        margin=.03, score_atol=.01, presence_atol=.01, mask_iou_min=.99):
    """Compare query identities, allowing only membership changes near the gate.

    Reordering is harmless. A retained identity change above gate+margin fails,
    including exchanges at the cap. Every common query's mask must agree. Score
    drift is checked by query over all proposals outside the gate band, so a
    score permutation cannot pass by preserving the sorted score distribution.
    """
    a = np.asarray(reference['all_instance_scores'], dtype=float)
    b = fresh.all_scores.numpy().astype(float)
    pa, pb = float(reference['presence']), fresh.presence
    if (a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or
            not np.isfinite(b).all() or not np.isfinite([pa, pb]).all() or
            not ((0 <= a).all() and (a <= 1).all() and (0 <= b).all() and (b <= 1).all()) or
            not (0 <= pa <= 1 and 0 <= pb <= 1)):
        return {'ok': False, 'reason': 'invalid probabilities or proposal count'}
    old_ids = [i['query'] for i in reference['instances']]
    new_ids = fresh.query_ids.tolist()
    if (len(set(old_ids)) != len(old_ids) or len(set(new_ids)) != len(new_ids) or
            any(not isinstance(q, int) or not 0 <= q < len(a) for q in old_ids+new_ids) or
            len(new_ids) != len(fresh.masks)):
        return {'ok': False, 'reason': 'invalid query ids or masks'}
    ga, gb = (a*pa, b*pb) if joint_gate else (a, b)
    near_gate = (np.abs(ga-gate) <= margin) & (np.abs(gb-gate) <= margin)
    score_error = float(np.max(np.abs(a[~near_gate]-b[~near_gate]))) if (~near_gate).any() else 0.
    gate_error = float(np.max(np.abs(ga[~near_gate]-gb[~near_gate]))) if (~near_gate).any() else 0.
    old_set, new_set = set(old_ids), set(new_ids)
    missing = old_set ^ new_set
    ambiguous = sorted({q for q in missing if near_gate[q]} |
                       {q for q in old_set | new_set if near_gate[q] and abs(a[q]-b[q]) > score_atol})
    changed = sorted(q for q in missing if not near_gate[q])
    cap = 10 if joint_gate else 5
    cap_exchange = (len(old_ids) == len(new_ids) == cap and
                    bool(old_set-new_set) and bool(new_set-old_set) and bool(changed))
    old = {i['query']: i for i in reference['instances']}
    ious = []; matched = []
    for index, q in enumerate(new_ids):
        if q not in old:
            continue
        x, y = rle_decode(old[q]['mask']), fresh.masks[index].numpy()
        if x.shape != y.shape:
            ious.append(0.)
        else:
            union = int((x | y).sum())
            ious.append(float((x & y).sum()/union) if union else 1.)
        matched.append(dict(query=q, score_abs_error=float(abs(a[q]-b[q])),
                            near_gate=bool(near_gate[q]), mask_iou=ious[-1]))
    minimum = min(ious, default=1.)
    ok = (not changed and score_error <= score_atol and gate_error <= score_atol and
          abs(pa-pb) <= presence_atol and minimum >= mask_iou_min)
    return dict(ok=bool(ok), status=('pass_with_gate_ambiguity' if ambiguous else 'pass') if ok else 'fail',
                score_max_abs_error_away_from_gate=score_error, gate_score_max_abs_error_away_from_gate=gate_error,
                all_score_max_abs_error=float(np.max(np.abs(a-b))) if len(a) else 0.,
                presence_abs_error=abs(pa-pb), query_sets_match=old_set == new_set,
                confident_query_ids_match=not changed, changed_query_ids=changed,
                high_score_cap_exchange=cap_exchange, matched_instances=matched,
                gate_ambiguous_query_ids=ambiguous, mask_min_iou=minimum, masks_compared=len(ious),
                gate=gate, joint_gate=joint_gate, margin=margin, score_atol=score_atol,
                presence_atol=presence_atol, mask_iou_min_required=mask_iou_min)


def aggregate_parity(checks):
    """Pool name-frames and matched instances, never average scene percentages.

    The gate band exempts score comparisons only when both scores lie in it.
    Presence, invalid proposals and confident exchanges at the cap fail hard.
    """
    n = len(checks)
    noise = [c['noise_aware'] for c in checks]
    valid = [c for c in noise if 'reason' not in c]
    matched = [m for c in valid for m in c['matched_instances']]
    scored = [m for m in matched if not m['near_gate']]
    real = sum(not c['confident_query_ids_match'] for c in valid)
    score_bad = sum(m['score_abs_error'] > .01 for m in scored)
    mask_bad = sum(m['mask_iou'] < .99 for m in matched)
    presence_bad = sum(c['presence_abs_error'] > .01 for c in valid)
    caps = sum(c['high_score_cap_exchange'] for c in valid)
    invalid = n-len(valid)
    # Integer comparisons keep exact 1% boundaries independent of rounding.
    ok = (n > 0 and not invalid and not presence_bad and not caps and
          real*100 <= n and score_bad*100 <= len(scored) and
          mask_bad*100 <= len(matched))
    strict = dict(checks=n, failed=sum(not c['ok'] for c in checks),
                  score_failures=sum(c.get('top5_score_max_abs_error', float('inf')) > .001 for c in checks),
                  presence_failures=sum(c.get('presence_abs_error', float('inf')) > .001 for c in checks),
                  ordered_id_failures=sum(not c.get('query_ids_match', False) for c in checks),
                  mask_failures=sum(c.get('mask_min_iou', 0.) < .99 for c in checks))
    return dict(policy='sam3-noise-aware-r7', ok=bool(ok), name_frames=n,
                real_identity_changes=real, real_identity_change_fraction=real/n if n else None,
                near_tie_name_frames=sum(bool(c['gate_ambiguous_query_ids']) for c in valid),
                matched_instances=len(matched), score_checked_instances=len(scored),
                score_band_exempt_instances=len(matched)-len(scored), score_failures=score_bad,
                score_pass_fraction=1-score_bad/len(scored) if scored else 1.,
                raw_matched_score_failures=sum(m['score_abs_error'] > .01 for m in matched),
                mask_failures=mask_bad, mask_pass_fraction=1-mask_bad/len(matched) if matched else 1.,
                presence_failures=presence_bad, invalid_checks=invalid, cap_exchange_failures=caps,
                per_check_failures=sum(not c['ok'] for c in noise), strict=strict,
                thresholds=dict(real_identity_change_max=.01, score_pass_min=.99, mask_pass_min=.99,
                                score_atol=.01, presence_atol=.01, mask_iou_min=.99, gate_margin=.03))


def summarize_parity(scenes):
    if len(scenes) != 10 or len({s['scene'] for s in scenes}) != 10 or any(not s['checks'] for s in scenes):
        raise ValueError('Require ten distinct nonempty parity scenes')
    return aggregate_parity([c for s in scenes for c in s['checks']])


def prediction(result):
    instances = [dict(query=int(q), score=float(s), joint_score=float(j), box=b.tolist(),
                      mask=rle_encode(m.numpy()))
                 for q, s, j, b, m in zip(result.query_ids, result.scores, result.joint_scores,
                                          result.boxes, result.masks)]
    return dict(presence=result.presence, all_instance_scores=result.all_scores.tolist(),
                instances=instances, joint_score=float(result.joint_scores[0]) if instances else -1.)


def runtime_attestation():
    """Record the runtime shared by the reference and tower in this process."""
    import importlib.metadata
    import platform
    import uuid
    import torch
    device = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device)
    libraries = {}
    for name in ('torch', 'torchvision', 'numpy', 'Pillow', 'triton'):
        try:
            libraries[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            libraries[name] = None
    return dict(run_id=uuid.uuid4().hex, hostname=platform.node(), pid=os.getpid(),
        python=platform.python_version(), libraries=libraries,
        hardware=dict(device_index=device, name=props.name, uuid=str(getattr(props, 'uuid', 'unavailable')),
                      capability=[props.major, props.minor], total_memory=props.total_memory,
                      cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES']),
        cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version(),
        tf32_matmul=torch.backends.cuda.matmul.allow_tf32, tf32_cudnn=torch.backends.cudnn.allow_tf32)


def verify_fresh_gate(report, scenes, diagnostics):
    """Recompute acceptance from saved fresh-reference checks, never the archive."""
    assert report['gate_reference'] == 'same-run-reference-b1'
    assert report['parity_rule'] == 'noise-aware'
    provenance = report['reference_provenance']
    assert provenance['same_card_and_precision_attested'] and provenance['same_process_and_model']
    assert provenance['source'] == 'same-run-reference-b1'
    attestation = provenance['runtime']
    assert attestation['run_id'] and attestation['hardware'] and attestation['libraries']
    assert provenance['reference_sources']
    assert len(diagnostics) == 10
    for scene, diagnostic in zip(scenes, diagnostics, strict=True):
        assert scene['scene'] == diagnostic['scene']
        assert diagnostic['runtime_run_id'] == attestation['run_id']
        assert diagnostic['reference_sources'] == provenance['reference_sources']
        hashes = provenance['frame_sha256'][scene['scene']]
        assert len(hashes) == 32 and all(len(h) == 64 for h in hashes)
        assert diagnostic['frame_sha256'] == hashes
        assert scene['checks'] == [c['reference_b1_vs_tower'] for c in diagnostic['checks']]
    aggregate = summarize_parity(scenes)
    assert aggregate == report['aggregate']
    assert aggregate == report['same_card_diagnostics']['candidate']
    assert report['ok'] == aggregate['ok']
    return aggregate


def run(args):
    cpu=getattr(sys,"_acceptance_cpu_e2e",None)
    if args.start_check:
        from acceptance_start_check import begin, sam_check
        begin(3,args)
        sam_check(args)
        return
    import torch
    from PIL import Image
    if not args.enable_sam3_tower:
        raise ValueError('GPU execution requires --enable-sam3-tower')
    if not cpu and (not os.environ.get('CUDA_VISIBLE_DEVICES') or torch.cuda.device_count() != 1):
        raise ValueError('The orchestrator must select exactly one GPU under vnice')
    if args.command == 'recache' and not args.b2_requested:
        raise ValueError('Re-cache requires B2 request and --b2-requested')
    manifest = json.loads(args.manifest.read_text())
    if manifest['receipt_sha256'] != sha256(args.receipt):
        raise ValueError('Manifest receipt pin differs')
    rows = manifest['scenes']
    if len(rows) != (10 if args.command == 'parity' else 84):
        raise ValueError('Unexpected scene count')
    # This tiny parent checks module registration; no student checkpoint is needed.
    parent = torch.nn.Linear(1, 1)
    before = tuple(parent.state_dict())
    tower = attach_sam3_tower(parent, {'checkpoint_path': str(args.checkpoint),
                                     'source_root': str(args.source_root),
                                     'receipt_path': str(args.receipt), 'device': 'cpu' if cpu else 'cuda',
                                     'precision': args.precision, 'image_batch_size': args.image_batch_size,
                                     'native_image_batch': args.native_image_batch}, enabled=True)
    contract = dict(manifest['contract'], image_batch_size=args.image_batch_size,
                    effective_image_batch_size=args.image_batch_size if args.native_image_batch else 1,
                    native_image_batch=args.native_image_batch, precision=args.precision,
                    proposal_order='score descending, query id ascending')
    assert tuple(parent.state_dict()) == before
    started = time.monotonic()
    written = 0
    results = []; parity_scenes = []
    floor_checks = []; same_card_checks = []; cache_reference_checks = []; archive_tower_checks = []
    frame_hashes = {}; reference_seconds = dict(b1=0., b4=0.)
    args.out.mkdir(parents=True, exist_ok=True)
    def budget():
        if time.monotonic()-started > args.max_seconds:
            raise RuntimeError('GPU time budget reached; stop without automatic retry')
    tower._load()
    ref_processor = None
    if args.command == 'parity' and getattr(args, 'measure_reference_floor', False):
        from scripts.sam3_reference import reference_processor, reference_records, as_detections
        from scripts.sam3_reference import paired_check, compact_record, measured_floor_proposal
        ref_processor = reference_processor(tower._backend.model, args.source_root, args.reference_writer_root,
                                        device=str(tower.device))
    if args.precision == 'float32':
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    provenance = None
    if ref_processor is not None:
        provenance = dict(source='same-run-reference-b1', precision=args.precision,
            same_card_and_precision_attested=True, same_process_and_model=True,
            runtime=cpu.attestation() if cpu else runtime_attestation(), reference_sources=ref_processor.reference_sources,
            frame_sha256=frame_hashes)
    load_seconds = time.monotonic()-started
    for row in rows:
        budget()
        scene = row['scene']
        target = args.out/(scene.replace('/', '__') + ('.json' if args.command == 'parity' else '.npz'))
        if target.exists():
            raise FileExistsError('Use a new output directory; completed files are never overwritten')
        if cpu: row=dict(row,phrases=row['phrases'][:1],frames=row['frames'][:4],frame_sha256=row['frame_sha256'][:4])
        paths = [Path(p) for p in row['frames']]
        if len(paths) != (4 if cpu else 32):
            raise ValueError('Expected 32 source frames')
        hashes = [sha256(p) for p in paths]
        frame_hashes[scene] = hashes
        if 'frame_sha256' in row and hashes != row['frame_sha256']:
            raise ValueError('Parity input RGB changed')
        old = None
        if args.command == 'parity':
            if sha256(row['reference']) != row['reference_sha256']:
                raise ValueError('Parity cache changed')
            old = load_cache(row['reference'])
            if old['scene'] != scene or (not cpu and old['phrases'] != row['phrases']):
                raise ValueError('Parity cache scene or phrases differ')
        frames = []
        for path in paths:
            with Image.open(path) as im:
                frames.append(im.convert('RGB'))
        reference_b1 = reference_b4 = None
        diagnostic_checks = []
        if ref_processor is not None:
            budget()
            cpu.sync() if cpu else torch.cuda.synchronize()
            reference_started = time.monotonic()
            reference_b1 = reference_records(ref_processor, frames, row['phrases'], batch_size=1,
                                              autocast=tower._autocast)
            cpu.sync() if cpu else torch.cuda.synchronize()
            reference_seconds['b1'] += time.monotonic()-reference_started
            budget()
            reference_started = time.monotonic()
            reference_b4 = reference_records(ref_processor, frames, row['phrases'], batch_size=4,
                                              autocast=tower._autocast)
            cpu.sync() if cpu else torch.cuda.synchronize()
            reference_seconds['b4'] += time.monotonic()-reference_started
            budget()
        cpu.sync() if cpu else torch.cuda.synchronize()
        cpu.sync() if cpu else torch.cuda.reset_peak_memory_stats()
        begin = time.monotonic()
        features = tower.encode(frames)
        cpu.sync() if cpu else torch.cuda.synchronize()
        encode_seconds = time.monotonic()-begin
        detect_seconds = 0.
        checks = []; archive_checks = []
        cache_frames = {str(k): dict(size=list(im.size), phrases={}) for k, im in enumerate(frames)}
        for phrase in row['phrases']:
            budget()
            begin = time.monotonic()
            detections = tower.detect(features, phrase)
            cpu.sync() if cpu else torch.cuda.synchronize()
            detect_seconds += time.monotonic()-begin
            if args.command == 'parity':
                legacy = tower.detect_cache_reference(features, phrase)
                for k, result in enumerate(legacy):
                    reference = old['frames'][str(k)]['phrases'][phrase]
                    check = compare(reference, result)
                    check['noise_aware'] = compare_noise_aware(reference, result)
                    archive_check = dict(scene=scene, frame=k, phrase=phrase, **check)
                    archive_checks.append(archive_check)
                    archive_tower_checks.append(archive_check)
                    if reference_b1 is not None:
                        from scripts.sam3_reference import paired_check, compact_record, as_detections
                        ref1, ref4 = reference_b1[k][phrase], reference_b4[k][phrase]
                        key = dict(scene=scene, frame=k, phrase=phrase)
                        floor = dict(key, **paired_check(ref1, as_detections(ref4)))
                        candidate = dict(key, **paired_check(ref1, result))
                        checks.append(candidate)
                        archive = dict(key, **paired_check(old['frames'][str(k)]['phrases'][phrase], as_detections(ref1)))
                        floor_checks.append(floor); same_card_checks.append(candidate); cache_reference_checks.append(archive)
                        diagnostic_checks.append(dict(key, reference_b1=compact_record(ref1),
                            reference_b4=compact_record(ref4), tower=compact_record(prediction(result)),
                            reference_b1_vs_b4=floor, reference_b1_vs_tower=candidate,
                            archived_reference_vs_reference_b1=archive))
                    else:
                        checks.append(archive_check)
                del legacy
            else:
                for k, result in enumerate(detections):
                    cache_frames[str(k)]['phrases'][normalize_phrase(phrase)] = prediction(result)
            del detections
        metric = dict(scene=scene, encode_seconds=encode_seconds, detect_seconds=detect_seconds,
                      seconds_per_clip=encode_seconds+detect_seconds,
                      peak_memory_allocated_bytes=0 if cpu else torch.cuda.max_memory_allocated(),
                      peak_memory_reserved_bytes=0 if cpu else torch.cuda.max_memory_reserved(),
                      feature_cpu_bytes=sum(t.numel()*t.element_size() for f in features.frames
                                            for values in f.values() for t in values))
        if args.command == 'parity':
            parity_scenes.append(dict(scene=scene, checks=checks))
            aggregate = aggregate_parity(checks)
            strict_ok = all(c['ok'] for c in checks)
            noise_aware_ok = aggregate['ok']
            metric.update(ok=strict_ok if args.parity_rule == 'strict' else noise_aware_ok,
                          aggregate=aggregate,
                          strict_ok=strict_ok, noise_aware_ok=noise_aware_ok,
                          strict_failures=sum(not c['ok'] for c in checks),
                          noise_aware_failures=sum(not c['noise_aware']['ok'] for c in checks),
                          gate_ambiguous_checks=sum(bool(c['noise_aware'].get('gate_ambiguous_query_ids')) for c in checks),
                          checks=checks)
            if reference_b1 is not None:
                metric.update(gate_reference='same-run-reference-b1',
                    archived_reference_vs_tower=aggregate_parity(archive_checks),
                    archived_reference_vs_tower_checks=archive_checks)
            dump(target, metric)
            if reference_b1 is not None:
                dump(args.out/(scene.replace('/', '__')+'_same_card.json'),
                     dict(scene=scene, checks=diagnostic_checks, frame_sha256=hashes,
                          reference_sources=ref_processor.reference_sources,
                          runtime_run_id=provenance['runtime']['run_id'],
                          image_batch_shapes=[1, 4], grounding_batch_size=1), compact=True)
        else:
            value = dict(schema='sam3-svp-cache-v1', scene=scene, phrases=row['phrases'],
                         contract=contract, receipt=tower.receipt,
                         frames=cache_frames, frame_sha256=hashes, **{'metrics': metric})
            payload = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
            buffer = io.BytesIO()
            np.savez_compressed(buffer, payload=np.frombuffer(payload, dtype=np.uint8))
            size = buffer.getbuffer().nbytes
            if written+size > args.max_write_bytes:
                raise RuntimeError('Re-cache output budget reached; ask orchestrator for storage')
            with target.open('xb') as f:
                f.write(buffer.getbuffer())
            written += size
        summary = {k: v for k, v in metric.items() if k not in ('checks', 'archived_reference_vs_tower_checks')}
        results.append(summary)
        print(json.dumps(summary), flush=True)
        del features, frames, cache_frames, old
    report = dict(command=args.command, scenes=results, model_state_dict_keys_unchanged=tuple(parent.state_dict()) == before,
                  model_load_seconds=load_seconds, total_seconds=time.monotonic()-started,
                  manifest_sha256=sha256(args.manifest), receipt_sha256=sha256(args.receipt),
                  torch_version=torch.__version__, cuda_version=torch.version.cuda,
                  tf32_matmul=torch.backends.cuda.matmul.allow_tf32,
                  tf32_cudnn=torch.backends.cudnn.allow_tf32,
                  device='cpu' if cpu else torch.cuda.get_device_name(), output_bytes=written,
                  contract=contract, parity_rule=args.parity_rule,
                  strict_ok=all(r.get('strict_ok', True) for r in results),
                  noise_aware_ok=all(r.get('noise_aware_ok', True) for r in results),
                  ok=all(r.get('ok', True) for r in results))
    if args.command == 'parity':
        aggregate = summarize_parity(parity_scenes)
        report.update(aggregate=aggregate, noise_aware_ok=aggregate['ok'],
                      ok=report['strict_ok'] if args.parity_rule == 'strict' else aggregate['ok'],
                      reference_provenance=dict(source='pinned external ttower SAM cache',
                          precision='bf16 autocast; cache hardware not attested',
                          same_card_and_precision_attested=False))
        print(json.dumps(dict(parity_rule=args.parity_rule, aggregate=aggregate)), flush=True)
        if ref_processor is not None:
            floor_report = measured_floor_proposal(floor_checks, same_card_checks)
            floor_report['archived_reference_vs_reference_b1'] = aggregate_parity(cache_reference_checks)
            floor_report['archived_reference_vs_tower'] = aggregate_parity(archive_tower_checks)
            floor_report['reference_sources'] = ref_processor.reference_sources
            floor_report['precision'] = args.precision
            floor_report['device'] = report['device']
            floor_report['frame_and_name_coverage'] = len(floor_checks)
            dump(args.out/'REFERENCE_FLOOR.json', floor_report)
            report['same_card_diagnostics'] = floor_report
            report.update(gate_reference='same-run-reference-b1', reference_provenance=provenance,
                          reference_seconds=dict(reference_seconds, total=sum(reference_seconds.values())))
            print(json.dumps(dict(reference_floor_strict=floor_report['floor']['strict'],
                                  same_card_tower_strict=floor_report['candidate']['strict'],
                                  archive_fresh_strict=floor_report['archived_reference_vs_reference_b1']['strict'],
                                  archive_tower_strict=floor_report['archived_reference_vs_tower']['strict'],
                                  within_measured_floor=floor_report['within_measured_floor'])), flush=True)
    dump(args.out/'REPORT.json', report)
    if not report['ok']:
        raise SystemExit('SAM 3 parity failed; inspect per-frame checks')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--scenes', type=Path, required=True)
    prep.add_argument('--dev-items', type=Path, required=True)
    prep.add_argument('--frames', type=Path, required=True)
    prep.add_argument('--reference', type=Path, required=True)
    prep.add_argument('--receipt', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    for name in ('parity', 'recache'):
        r = sub.add_parser(name)
        for flag in ('manifest', 'checkpoint', 'source-root', 'receipt', 'out'):
            r.add_argument('--'+flag, type=Path, required=True)
        r.add_argument('--start-check', action='store_true')
        r.add_argument('--enable-sam3-tower', action='store_true')
        r.add_argument('--b2-requested', action='store_true')
        r.add_argument('--max-seconds', type=float, default=3600)
        r.add_argument('--max-write-bytes', type=int, default=750_000_000)
        r.add_argument('--image-batch-size', type=int, default=1)
        r.add_argument('--native-image-batch', action='store_true',
                       help='Diagnostic only: use upstream batched encoding without the singleton guard')
        r.add_argument('--measure-reference-floor', action='store_true',
                       help='Gate against same-run ttower B1; retain B1/B4 and archive diagnostics')
        r.add_argument('--reference-writer-root', type=Path,
                       default=Path('/scratch/jjyeung/orch_cd/ttower/work/sam3'))
        r.add_argument('--precision', choices=('bf16', 'float32'), default='bf16')
        r.add_argument('--parity-rule', choices=('strict', 'noise-aware'), default='strict')
    args = p.parse_args()
    (prepare if args.command == 'prepare' else run)(args)


if __name__ == '__main__':
    main()
