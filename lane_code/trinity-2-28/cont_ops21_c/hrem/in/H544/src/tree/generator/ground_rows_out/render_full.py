"""Render CP2: render_full.sh POOL_ROOT GEOMETRY_ROOT OUTPUT_ROOT [--workers 1..8]."""
import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
import tarfile
import time
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from derivgen import box_v313 as B, ground_v313_distance as distance
from derivgen.ground_v312 import TYPES, RowRefusal, Session, parse_roles, render, replay, option_map
from derivgen.ground_v312_io import GTClip, reference, load_backend, operands, agrees, sha, checked, baseline
from derivgen.ground_v312_quality import normalized, question_identity, shuffled_item
from derivgen.ground_v312_degenerate import degeneracy_reasons
from derivgen.ground_v312_tokens import tokenizer_for_rows, gate_positions as direction_positions
from derivgen.ground_v313_tokens import gate_positions as box_positions
from orchard_ground_adapter import pack, validate, install
from select_ground_rows import select
from test_v312_benchmark import BENCHMARK, benchmark_templates, expected_question

ROOT = Path(__file__).resolve().parents[1]
RT = Path('/scratch/jjyeung/orch_cd/orchard_cp2/work/rt')
ORCHARD = RT.parent/'c1mix_ow4'
SPLITS = Path('/scratch/jjyeung/orch_cd/rev_ctrl/out/splits.json')
REGISTRY = ROOT/'work/inputs/routing356_scenes.json'
# v3.14: distance rows use the benchmark's 5 cm box grid and keep every instance of an operand name (minimum
# over instance pairs); directions keep the v3.13 single-instance rule.
from derivgen.gaps_v314 import NEW_TYPES
from derivgen.ground_v313_tokens import gate_positions as gap_positions
import render_gaps_v314 as gaps
from derivgen.room_rows_v314 import TYPE as ROOM_TYPE
import render_room_v314 as room_renderer
TYPES = tuple(dict.fromkeys((*TYPES, *NEW_TYPES, ROOM_TYPE)))
V314 = True
DIST_TYPES = ('object_abs_distance', 'object_rel_distance')
ALIASES = {'absolute_distance_object':'object_abs_distance', 'relative_distance_object':'object_rel_distance'}
STAGES = ['inputs','parse','dev_scan_and_room_exclusion','frames','deduplication','geometry_accessible',
          'single_instance','exact_name','visible','mask_disjoint','not_contained','box_overlap_rule',
          'native_facing_extent','independent_label','measurement_and_token_gates','gt_agreement','admitted']


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def pin(path):
    path = Path(path)
    return dict(path=str(path.resolve()), sha256=sha(path))


def write_json(path, value):
    path = Path(path)
    pending = path.parent/'.pending_records'
    pending.mkdir(exist_ok=True)
    staged = pending/(path.name+'-'+uuid.uuid4().hex)
    with staged.open('x') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False)+'\n')
        f.flush()
        os.fsync(f.fileno())
    # Atomic publication without rename, replacement, or deletion. The staging
    # inode remains available if the process is interrupted before publication.
    os.link(staged, path)


def append_line(f, value):
    f.write(encoded(value)+'\n')


def room(scan):
    return re.sub(r'_\d{2}$', '', scan)


def progress(event, **fields):
    print(encoded(dict(event=event, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **fields)), flush=True)


def local_path(path):
    p = Path(path)
    if not str(p).startswith(('/scratch/', '/dev/shm/')):
        raise ValueError('Only local /scratch or /dev/shm paths are accepted: '+str(p))
    return p


def orchard_local(path):
    return RT/'U'/path.split('/users/jyeung/', 1)[1]


def manifest_bytes(pool, wanted):
    """Read each named manifest once, including CP2's archived delivery manifests."""
    found, archives = {}, defaultdict(set)
    for path in wanted:
        p = local_path(path)
        if p.is_file():
            found[path] = p.read_bytes()
        else:
            m = re.search(r'/out/(v3_scenes_([^/]+)/[^/]+/RGB.json)$', path)
            if not m:
                raise ValueError('Missing named RGB manifest: '+path)
            archives[m[2]].add((path, 'out/'+m[1]))
    for build, targets in sorted(archives.items()):
        archive = pool.parent/('V3_EXPORTB_'+build+'.tar')
        with tarfile.open(local_path(archive), 'r:') as tf:
            for path, member in sorted(targets):
                found[path] = tf.extractfile(member).read()
    return found


def load_input(args, cfg):
    pool, geometry = args.pool_root, args.geometry_root
    registry_pin = pin(REGISTRY)
    descriptor = pool/'RENDER_INPUT.json'
    if descriptor.is_file():
        d = json.loads(descriptor.read_text())
        registry_pin = d['registry']
        registry = json.loads(checked(registry_pin).read_text())
        fixture = bool(d.get('pilot_fixture'))
    else:
        checked(dict(path=str(REGISTRY),sha256='6c2649cdc95fb7a8458b9c7c2b6cecfef280b9945df5325b06f76a9ac4de8fb2'))
        registry = json.loads(REGISTRY.read_text()); fixture = False
    P, _, _ = reference(cfg['rkit_root'])
    splits = json.loads(SPLITS.read_text())
    dev = set(splits['all_scenes']); devrooms = {room(s) for s in dev}
    rows, sources, wanted, ignored = [], [], {}, Counter()
    for name in ('M_rows_selected.jsonl', 'L_rows_selected.jsonl'):
        path = pool/name; h = hashlib.sha256(); n = 0
        with path.open('rb') as f:
            for line in f:
                h.update(line); n += 1; raw = json.loads(line)
                typ = ALIASES.get(raw['question_type'], raw['question_type'])
                if typ not in TYPES:
                    ignored[raw['question_type']] += 1; continue
                pr = raw['provenance']; scene = pr['alias'].split('/')[-1]
                item = dict(qid=raw['qid'], type=typ, scene=scene, question=raw['question'],
                            options=raw['options'], frame_indices=pr['frame_indices'], gt_answer=raw['gt_answer'],
                            source_provenance=pr, source_question_type=raw['question_type'],
                            source_line_sha256=hashlib.sha256(line).hexdigest())
                rows.append(item)
                m = pr['rgb_manifest']
                if m['path'] in wanted and wanted[m['path']] != m['sha256']:
                    raise ValueError('conflicting RGB manifest pin')
                wanted[m['path']] = m['sha256']
        sources.append(dict(path=str(path), sha256=h.hexdigest(), rows=n, bytes=path.stat().st_size))
    raw_manifests = manifest_bytes(pool, wanted)
    manifests = {}
    for path, raw in raw_manifests.items():
        if hashlib.sha256(raw).hexdigest() != wanted[path]:
            raise ValueError('RGB manifest hash mismatch: '+path)
        manifests[wanted[path]] = json.loads(raw)
    # Use Orchard's already staged, pinned timing/frame manifests. Do not read RGB bytes.
    rgb_index_pin = None; rgb_index = None
    if not fixture:
        stage = json.loads((RT/'stage_summary_s1.json').read_text())
        idx = stage['rgb_index']; idx_path = orchard_local(idx['path'])
        if sha(idx_path) != idx['sha256']:
            raise ValueError('Orchard RGB index hash mismatch')
        rgb_index_pin = dict(path=str(idx_path), sha256=idx['sha256'])
        rgb_index = json.loads(idx_path.read_text())
    groups, prelim, counters, seen, qids, timed = defaultdict(list), [], {t:Counter() for t in TYPES}, set(), set(), {}
    entries = {}
    for item in sorted(rows, key=lambda x:x['qid']):
        typ = item['type']; c = counters[typ]; c['inputs'] += 1
        qid, scene, pr = item['qid'], item['scene'], item['source_provenance']
        if qid in qids:
            raise ValueError('duplicate source qid: '+qid)
        qids.add(qid)
        reason = None
        try:
            item['roles'] = {} if typ == ROOM_TYPE else parse_roles(item, P.T)
        except (ValueError, KeyError, AttributeError):
            reason = 'unparsed_question'
        if reason is None:
            c['parse'] += 1
            if pr['canonical'] in dev or room(pr['canonical']) in devrooms:
                reason = 'dev_scan_or_room'
        if reason is None:
            c['dev_scan_and_room_exclusion'] += 1
            e = registry[scene]; m = manifests[pr['rgb_manifest']['sha256']]
            if (pr['canonical'] != e['canonical'] or pr['gt_sha256'] != e['gt']['sha256'] or
                    item['frame_indices'] != e['frame_indices'] or m['canonical'] != e['canonical'] or
                    [f['source_index'] for f in m['frames']] != item['frame_indices'] or
                    m.get('frame_indices', item['frame_indices']) != item['frame_indices'] or e['excluded'] is not False):
                raise ValueError('manifest/GT/canonical/frame binding mismatch: '+qid)
            c['frames'] += 1
            identity = question_identity(item)
            if identity in seen:
                reason = 'duplicate'
            else:
                seen.add(identity); c['deduplication'] += 1
        if reason:
            prelim.append(dict(qid=qid, type=typ, scene=scene, reason=reason)); continue
        if scene not in entries:
            e = copy.deepcopy(e)
            if fixture:
                relative = e['geometry_relative_path']
            else:
                old = e['gt']['path']
                relative = old.split('/jjyeung_ground_gt/',1)[1]
            if Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('invalid geometry relative path')
            e['gt'] = dict(path=str(geometry/relative), sha256=e['gt']['sha256'])
            entries[scene] = e
        msha = pr['rgb_manifest']['sha256']
        if msha not in timed:
            if fixture:
                timed[msha] = dict(data=manifests[msha], pin=pr['rgb_manifest'])
            else:
                mpin = rgb_index['manifests'][msha]
                if not isinstance(mpin, dict):
                    mpin = dict(path=mpin, sha256=msha)
                p = orchard_local(mpin['path'])
                if sha(p) != mpin['sha256']:
                    raise ValueError('Orchard timed RGB manifest hash mismatch')
                data = json.loads(p.read_text()); original = manifests[msha]
                if (data['canonical'] != original['canonical'] or
                    [(f['source_index'],f['sha256']) for f in data['frames']] !=
                    [(f['source_index'],f['sha256']) for f in original['frames']]):
                    raise ValueError('Orchard RGB substitution changed frame identity')
                timed[msha] = dict(data=data, pin=dict(path=str(p),sha256=mpin['sha256']))
            if timed[msha]['data']['fps'] <= 0 or timed[msha]['data']['total_num_frames'] <= max(item['frame_indices']):
                raise ValueError('invalid source frame timing')
        item['authority'] = dict(kind='hash-verified-native-geometry', scene_registry=registry_pin,
                                 rgb_manifest=pr['rgb_manifest'], gt=entries[scene]['gt'],
                                 canonical=pr['canonical'], frame_indices=item['frame_indices'])
        groups[scene].append(item)
    return dict(groups=dict(groups), entries=entries, prelim=prelim, counts=counters, sources=sources,
                registry=registry_pin, fixture=fixture, dev=sorted(dev), devrooms=sorted(devrooms),
                timed=timed, rgb_index=rgb_index_pin, ignored=dict(ignored))


def independent_label(item, clip, P):
    if item['type'] in NEW_TYPES:
        return gaps.independent_label(item, clip, P)
    r, typ = item['roles'], item['type']
    def boxes(name):
        labels = P.T.match_labels(name, clip.geo.labels)
        return [clip.geo.obb[int(i)] for i,l in zip(clip.geo.ids,clip.geo.labels) if l in labels]
    if V314 and typ in DIST_TYPES:
        native = lambda n: [B.box(o['centroid'], o['axesLengths'], np.asarray(o['normalizedAxes'], float).reshape(3, 3))
                            for o in boxes(n)]
        if typ == 'object_abs_distance':
            return B.measure(B.RULE_GRID, native(r['a']), native(r['b']))
        values = [B.measure(B.RULE_GRID, native(r['target']), native(c)) for c in r['cands']]
        return P.T.letter_of(item['options'], r['cands'][int(np.argmin(values))])
    if typ == 'object_abs_distance':
        return P.T.obb_closest(boxes(r['a']), boxes(r['b']))
    if typ == 'object_rel_distance':
        values = [P.T.obb_closest(boxes(r['target']), boxes(c)) for c in r['cands']]
        return P.T.letter_of(item['options'], r['cands'][int(np.argmin(values))])
    theta = P.T.floor_angle(*[boxes(r[k])[0]['centroid'] for k in ('stand','face','query')])[0]
    return P.T.letter_of(item['options'], P.T.direction_label(typ, theta))


def check_row(row, item, clip, replayer, tokenizer, templates, dev, devrooms):
    """The pilot and full pool run this identical validator for every admitted row."""
    if row['type'] in NEW_TYPES:
        return gaps.check_row(row,item,clip,replayer,tokenizer,templates,dev,devrooms)
    typ = row['type']; result = Counter()
    if typ in ('object_abs_distance','object_rel_distance'):
        values = distance.replay_exact(row, distance.make_session(replayer, clip, [], B.AnnotationBoxProvider(),
                                                                   multi_instance=V314))
        if not np.allclose(values, row['program_audit']['unrounded_replay_m'], atol=1e-12, rtol=0):
            raise ValueError('unrounded audit mismatch')
        boxes = [e['audit'].get('full_precision_box') for e in row['events'] if B.GROUND.fullmatch(e['call'])]
        reverse = ([B.sampled_box_512(b, boxes[0]) for b in boxes[1:]]
                   if row['program_audit']['target_distance_rule'] == B.RULE and None not in boxes else values)
        result['audit_pairs'] = len(values)
        result['reversed_draws_detected'] = sum(abs(a-b)>1e-12 for a,b in zip(values,reverse))
    else:
        replay(row, Session(replayer, clip.geo, clip.masks))
    result['exact_replay'] += 1
    if row['question'] != expected_question(row, templates):
        raise ValueError('benchmark template mismatch')
    result['templates'] += 1
    source = item['source_join']; opts = option_map(source['options'])
    if opts:
        order = sorted(opts, key=lambda k:hashlib.sha256((row['qid']+'\0'+k).encode()).digest())
        mapping = {k:chr(65+i) for i,k in enumerate(order)}
        if (row['options'] != [f'{chr(65+i)}. {opts[k]}' for i,k in enumerate(order)] or
                row['option_letter_map'] != mapping or str(row['gt_answer']) != mapping[str(source['gt_answer'])]):
            raise ValueError('option shuffle or label map mismatch')
    result['shuffles'] += 1
    equal = distance.agrees(row['answer'], row['gt_answer']) if typ == 'object_abs_distance' else str(row['answer']) == str(row['gt_answer'])
    if not equal:
        raise ValueError('label equality failed')
    if opts and option_map(row['options'])[row['answer']] != row['answer_content']:
        raise ValueError('option content mismatch')
    result['label_equality'] += 1
    canonical = item['source_provenance']['canonical']
    if canonical in dev or room(canonical) in devrooms:
        raise ValueError('dev scan/room leakage')
    if row['not_seen'] or row['simulated_misses'] or not row['gt_accepted'] or not row['gt_agrees'] or row['training_admitted']:
        raise ValueError('membership flag mismatch')
    result['flags_and_dev_exclusion'] += 1
    positions = (box_positions if typ in ('object_abs_distance','object_rel_distance') else direction_positions)(tokenizer, row['suffix'])
    if positions != row['mdg_gate_token_positions'] or row['suffix_tokens'] != len(tokenizer.encode(row['suffix'],add_special_tokens=False).ids):
        raise ValueError('token count or gate positions mismatch')
    result['tokens_and_gate_positions'] += 1
    return result


def render_scan(task):
    scene, items, entry, cfg, scan_root, run_key, dev, devrooms = task
    start, cpu = time.monotonic(), time.process_time()
    P, M, S = reference(cfg['rkit_root'])
    tokenizer = tokenizer_for_rows(cfg['tokenizer']['path'])
    token_count = lambda text:len(tokenizer.encode(text,add_special_tokens=False).ids)
    templates = benchmark_templates()
    backend = load_backend(cfg['backend']['path'])
    clip = GTClip(checked(entry['gt']), entry['frame_indices'], P, M)
    producer, replayer = clip.cached_backend(backend), clip.cached_backend(backend)
    out = Path(scan_root)/('attempt-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    counts, checks, refused = {t:Counter() for t in TYPES}, Counter(), Counter()
    source_agreement, metadata = Counter(), []
    with (out/'admitted.jsonl').open('x') as admitted, (out/'packed.jsonl').open('x') as packed, (out/'dispositions.jsonl').open('x') as dispositions:
        for index, source in enumerate(items):
            item = copy.deepcopy(source); typ = item['type']; c = counts[typ]; c['geometry_accessible'] += 1
            if typ == ROOM_TYPE:
                try:
                    if item['source_provenance']['canonical'] != entry['canonical']:
                        raise RowRefusal('room_scene_binding_mismatch')
                    item['gt_authority'] = item.get('gt_authority', item.get('authority'))
                    item['physical_group'] = item['source_provenance'].get('physical_group')
                    row, _ = room_renderer.prepare(item, clip, producer, tokenizer,
                        canonical=entry['canonical'], pin=entry['gt'], frames=entry['frame_indices'],
                        dev=set(dev) | set(devrooms))
                except (RowRefusal, ValueError, FloatingPointError) as exc:
                    reason = str(exc); refused[typ+'|'+reason] += 1
                    append_line(dispositions,dict(qid=item['qid'],type=typ,scene=scene,
                        reason=reason,training_admitted=False))
                    continue
                row['room'] = room(entry['canonical'])
                row['source_gt_answer'] = item['gt_answer']
                row['native_independent_label'] = row['program_audit']['room']['area_m2']
                checks.update(row['room_checks'])
                provenance = dict(item['source_provenance'], ground_authority=item['gt_authority'],
                                  cp2_row_sha256=item['source_line_sha256'])
                packed_row = pack(row, provenance); validate(packed_row)
                append_line(admitted,row); append_line(packed,packed_row)
                append_line(dispositions,dict(qid=row['qid'],candidate_id=row['candidate_id'],type=typ,
                    scene=scene,reason='gt_match',gt_accepted=True,training_admitted=False))
                metadata.append({k:row[k] for k in ('candidate_id','type','answer','gt_answer','options','canonical','room')})
                source_agreement[typ+':True'] += 1
                for stage in ('independent_label','measurement_and_token_gates','gt_agreement','admitted'):
                    c[stage] += 1
                continue
            if typ in NEW_TYPES:
                try:
                    canonical = item['source_provenance']['canonical']
                    physical = item['source_provenance'].get('physical_group', room(canonical))
                    if canonical in dev or room(canonical) in devrooms or physical in devrooms:
                        raise RowRefusal('dev_scan_or_room')
                    row, item = gaps.prepare(item, clip, P, producer, token_count, entry)
                except (RowRefusal, ValueError, FloatingPointError) as exc:
                    reason = str(exc)
                    refused[typ+'|'+reason] += 1
                    append_line(dispositions,dict(qid=item['qid'],type=typ,scene=scene,reason=reason,
                        training_admitted=False))
                    continue
                row['room'] = room(entry['canonical'])
                row['mdg_gate_token_positions'] = gap_positions(tokenizer,row['suffix'])
                checks.update(check_row(row,item,clip,replayer,tokenizer,templates,set(dev),set(devrooms)))
                provenance = dict(item['source_provenance'],ground_authority=item['gt_authority'],
                                  cp2_row_sha256=item['source_line_sha256'])
                packed_row = pack(row,provenance); validate(packed_row); checks['pack_roundtrip'] += 1
                append_line(admitted,row); append_line(packed,packed_row)
                append_line(dispositions,dict(qid=row['qid'],candidate_id=row['candidate_id'],type=typ,
                    scene=scene,reason='gt_match',gt_accepted=True,training_admitted=False))
                metadata.append({k:row[k] for k in ('candidate_id','type','answer','gt_answer','options','canonical','room')})
                c['admitted'] += 1
                continue
            names = operands(item); matches = {n:P.T.match_labels(n,clip.geo.labels) for n in names}
            ids = {n:[int(i) for i,l in zip(clip.geo.ids,clip.geo.labels) if l in matches[n]] for n in names}
            reason = None
            multi_ok = V314 and typ in DIST_TYPES and all(1 <= len(ids[n]) <= B.MAX_INSTANCES for n in names)
            if any(len(ids[n]) != 1 for n in names) and not multi_ok:
                reason = 'single_instance_required_multi_instance' if all(ids[n] for n in names) else 'single_instance_required_missing_name'
            else:
                c['single_instance'] += 1
                if any(normalized(n) not in {normalized(l) for l in matches[n]} for n in names):
                    reason = 'unresolved_qualified_name'
            if reason is None:
                c['exact_name'] += 1
                if any(not any(clip.masks(n)[1][k-1]>=.5 and clip.masks(n)[0][k-1].any()
                               for k in range(1,33) if clip.geo.has(k)) for n in names):
                    reason = 'object_not_visible_drop'
            if reason is None:
                c['visible'] += 1
                item['target_distance_rule'] = ((B.RULE_GRID if V314 else B.RULE) if typ in DIST_TYPES else 'direction')
                try:
                    if multi_ok:
                        from derivgen.ground_v312_degenerate import degeneracy_reasons_multi
                        reasons = set(degeneracy_reasons_multi(item, {n: [clip.geo.obb[i] for i in ids[n]] for n in names},
                                                               {n: clip.masks(n)[0] for n in names}))
                    else:
                        bb = {n:clip.geo.obb[ids[n][0]] for n in names}
                        reasons = set(degeneracy_reasons(item,bb,{n:clip.masks(n)[0] for n in names}))
                except ValueError:
                    reasons = set(); reason = 'invalid_operand_box'
                if len(set(names)) != len(names):
                    reasons.update(['operand_mask_overlap','operand_box_containment'])
                if reason is None:
                    for rule, stage in [('operand_mask_overlap','mask_disjoint'),('operand_box_containment','not_contained'),
                                        ('operand_box_overlap','box_overlap_rule'),('facing_vector_below_object_extent','native_facing_extent')]:
                        if rule in reasons:
                            reason = rule; break
                        c[stage] += 1
            if reason is None:
                clip.validate_operands(item, multi_instance=multi_ok)
                label = independent_label(item,clip,P)
                if label is None:
                    raise ValueError('independent label unavailable after operand admission')
                # CP2 numeric source labels are printed to two decimals; retain them for
                # equality checking while the audit records the full native measurement.
                source_agreement[typ+':'+str(B.number(float(label),2)==B.number(float(item['gt_answer']),2)
                    if typ=='object_abs_distance' else str(label)==str(item['gt_answer']))] += 1
                item['source_gt_answer'] = item['gt_answer']
                item['native_independent_label'] = label
                if typ != 'object_abs_distance' or (V314 and typ in DIST_TYPES):
                    item['gt_answer'] = label
                item['gt_authority'] = dict(item['authority'], native_independent_label=label,
                                            label_rule=('native OBB box_grid_5cm, minimum over instance pairs / native centroid direction'
                                                        if V314 else 'rkit native OBB sampled_box_512 / native centroid direction'))
                item = shuffled_item(item); c['independent_label'] += 1
                try:
                    old = baseline(item,clip,S)
                except (ValueError,FloatingPointError):
                    old = None
                try:
                    if typ in ('object_abs_distance','object_rel_distance'):
                        distance.prepare(item,clip,rule=item['target_distance_rule'],multi_instance=V314)
                        row = B.render(item,distance.make_session(producer,clip,[],B.AnnotationBoxProvider(),
                                                                  multi_instance=V314),token_count)
                    else:
                        row = render(item,Session(producer,clip.geo,clip.masks),token_count)
                except (RowRefusal, ValueError, FloatingPointError) as exc:
                    reason = 'render:'+str(exc)
                if reason is None:
                    c['measurement_and_token_gates'] += 1
                    equal = distance.agrees(row['answer'],item['gt_answer']) if typ=='object_abs_distance' else agrees(row['answer'],item['gt_answer'],typ)
                    if not equal:
                        reason = 'gt_mismatch'
                    elif row['not_seen']:
                        reason = 'diagnostic_miss_without_admitted_vqa'
                    else:
                        c['gt_agreement'] += 1
            if reason is not None:
                refused[typ+'|'+reason] += 1
                append_line(dispositions,dict(qid=item['qid'],type=typ,scene=scene,reason=reason,
                    natural_miss=reason=='render:missing_direct_canonical', training_admitted=False))
                continue
            row.update(scene=scene, canonical=entry['canonical'], room=room(entry['canonical']),
                       roles=item['roles'], frame_indices=item['frame_indices'], gt_answer=item['gt_answer'],
                       source_gt_answer=item['source_gt_answer'], native_independent_label=item['native_independent_label'],
                       gt_authority=item['gt_authority'], source_join=item['source_join'],
                       question_identity=question_identity(item), option_shuffle=item.get('option_shuffle'),
                       option_letter_map=item.get('option_letter_map',{}), diagnostic_only=True,
                       training_admitted=False, gt_accepted=True, gt_agrees=True, selection_refusal=None,
                       geometry_source='gt',mask_source='gt',scene_gt_sha256=entry['gt']['sha256'],v311_answer=old)
            row['mdg_gate_token_positions'] = (box_positions if typ in ('object_abs_distance','object_rel_distance') else direction_positions)(tokenizer,row['suffix'])
            checks.update(check_row(row,item,clip,replayer,tokenizer,templates,set(dev),set(devrooms)))
            provenance = dict(item['source_provenance'],ground_authority=item['gt_authority'],
                              cp2_row_sha256=item['source_line_sha256'])
            packed_row = pack(row,provenance); validate(packed_row); checks['pack_roundtrip'] += 1
            append_line(admitted,row); append_line(packed,packed_row)
            append_line(dispositions,dict(qid=row['qid'],candidate_id=row['candidate_id'],type=typ,scene=scene,
                                           reason='gt_match',gt_accepted=True,training_admitted=False))
            metadata.append({k:row[k] for k in ('candidate_id','type','answer','gt_answer','options','canonical','room')})
            c['admitted'] += 1
            if (index+1)%50 == 0:
                progress('scan_progress',scene=scene,processed=index+1,total=len(items),admitted=len(metadata))
    write_json(out/'metadata.json',metadata)
    files = {p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in out.iterdir() if p.is_file()}
    done = dict(schema='ground-scan-complete-v1',run_key=run_key,scene=scene,canonical=entry['canonical'],
                input_rows=len(items),counts=counts,checks=checks,refused=refused,source_label_agreement=source_agreement,
                cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start,files=files,
                gt=entry['gt'],admitted=len(metadata),path=str(out))
    write_json(out/'DONE.json',done)
    progress('scan_complete',scene=scene,admitted=len(metadata),inputs=len(items),seconds=round(done['wall_seconds'],1))
    return done


def completed_scan(scan_root, run_key):
    if not scan_root.is_dir():
        return None
    for done_path in sorted(scan_root.glob('attempt-*/DONE.json')):
        done = json.loads(done_path.read_text())
        if done['run_key'] != run_key:
            raise ValueError('scan completion belongs to a different run')
        for name, entry in done['files'].items():
            p = done_path.parent/name
            if p.stat().st_size != entry['bytes'] or sha(p) != entry['sha256']:
                raise ValueError('completed scan output changed: '+str(p))
        return done
    return None


def reader_test(packed_path, timed, wanted=64):
    sys.path.insert(0,str(ORCHARD))
    from student_pilot import carrier_c1_routing as native
    module = install(native)
    buckets = defaultdict(list)
    with packed_path.open() as f:
        for line in f:
            r = json.loads(line)
            if len(buckets[r['question_type']]) < wanted:
                buckets[r['question_type']].append(r)
    picked = []
    for i in range(wanted):
        for typ in TYPES:
            if i<len(buckets[typ]) and len(picked)<wanted:
                picked.append(buckets[typ][i])
    if len(picked) != wanted:
        raise ValueError('fewer than 64 admitted rows for Orchard reader test')
    for raw in picked:
        rgb = timed[raw['provenance']['rgb_manifest']['sha256']]['data']
        row = module.c1_row(raw,rgb)
        if (row['target'] != raw['target'] or row['student_input']['question'] != raw['question'] or
            row['student_input']['options'] != raw['options'] or row['student_input']['frame_indices'] != raw['provenance']['frame_indices'] or
            row['routing']['ground_record'] != raw['ground_record'] or row['routing']['tool_output_spans'] != raw['tool_output_spans']):
            raise ValueError('Orchard c1_row mapping mismatch')
        if module.render(row['routing']['events'],row['routing']['answer'])[0] != row['target']:
            raise ValueError('Orchard render mismatch')
    return dict(rows=len(picked),by_type=dict(Counter(r['question_type'] for r in picked)),
                reader=pin(Path(native.__file__)),adapter=pin(ROOT/'out/orchard_ground_adapter.py'),
                entrypoint='student_pilot.carrier_c1_routing.c1_row (with grounding adapter installed)',
                cpu_only=True,rgb_bytes_read=0,frame_identity_and_timing_checked=True,
                targets_options_spans_and_audits_equal=True)


def assemble(args, data, done, run_key, resumed):
    root = args.output_root
    receipt_path = root/'RECEIPT.json'
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text())
        if receipt['run_key'] != run_key:
            raise ValueError('complete receipt run key differs')
        for entry in receipt['outputs'].values():
            checked(entry)
        progress('resume_verified',scans=resumed,admitted=receipt['admitted_rows'],receipt=str(receipt_path))
        return receipt
    out = root/('selections-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    metadata, checks, counts, reasons, source_agreement = [], Counter(), data['counts'], Counter(), Counter()
    for d in done:
        metadata.extend(json.loads((Path(d['path'])/'metadata.json').read_text()))
        checks.update(d['checks']); reasons.update(d['refused']); source_agreement.update(d['source_label_agreement'])
        for typ,c in d['counts'].items():
            counts[typ].update(c)
    for r in data['prelim']:
        reasons[r['type']+'|'+r['reason']] += 1
    ids = {r['candidate_id'] for r in metadata}
    if len(ids) != len(metadata):
        raise ValueError('duplicate admitted candidate identity')
    selected, selection = select(metadata,BENCHMARK)
    nfull=nbal=0; readmeta={r['candidate_id']:r for r in metadata}
    with (out/'full.packed.jsonl').open('xb') as full, (out/'balanced.packed.jsonl').open('xb') as balanced, (out/'membership.jsonl').open('x') as membership:
        for d in sorted(done,key=lambda r:r['scene']):
            with (Path(d['path'])/'packed.jsonl').open('rb') as f:
                for line in f:
                    r=json.loads(line); validate(r)
                    cid=r['candidate_id']; g=r['ground_record']; m=readmeta[cid]
                    if any(g[k]!=m[k] for k in ('type','answer','gt_answer','options')):
                        raise ValueError('metadata selection differs from packed record')
                    full.write(line); nfull+=1
                    if cid in selected:
                        balanced.write(line); nbal+=1
                    append_line(membership,dict(candidate_id=cid,full=True,balanced=cid in selected,
                                                packed_line_sha256=hashlib.sha256(line).hexdigest()))
    if nfull != len(ids) or nbal != len(selected):
        raise ValueError('selection membership count mismatch')
    with (out/'dispositions.jsonl').open('x') as f:
        for r in data['prelim']:append_line(f,r)
        for d in sorted(done,key=lambda r:r['scene']):
            with (Path(d['path'])/'dispositions.jsonl').open() as src:
                for line in src:f.write(line)
    admitted_scans={r['canonical'] for r in metadata}; admitted_rooms={r['room'] for r in metadata}
    if admitted_scans & set(data['dev']) or admitted_rooms & set(data['devrooms']):
        raise ValueError('selection dev overlap')
    for typ,c in counts.items():
        stages=[c[s] for s in STAGES]
        if any(a<b for a,b in zip(stages,stages[1:])):
            raise ValueError('nonmonotonic gates '+typ)
        if c['inputs'] != c['admitted']+sum(n for k,n in reasons.items() if k.startswith(typ+'|')):
            raise ValueError('input disposition mismatch '+typ)
    reader = reader_test(out/'full.packed.jsonl',data['timed'])
    write_json(out/'ORCHARD_READER_TEST.json',reader)
    # Export actual pinned RGB metadata for the builder, without copying frame bytes.
    rgb_dir=out/'rgb';rgb_dir.mkdir()
    rgb_index={}
    for original_sha,record in sorted(data['timed'].items()):
        p=rgb_dir/(original_sha+'.json');write_json(p,record['data']);rgb_index[original_sha]=pin(p)
    write_json(out/'rgb_index.json',dict(manifests=rgb_index,path_map={}))
    full_pin, balanced_pin = pin(out/'full.packed.jsonl'),pin(out/'balanced.packed.jsonl')
    selection.update(benchmark=pin(BENCHMARK),source=full_pin,output=balanced_pin,
                     membership=pin(out/'membership.jsonl'),per_type=dict(Counter(r['type'] for r in metadata if r['candidate_id'] in selected)))
    write_json(out/'SELECTION_RECEIPT.json',selection)
    write_json(out/'FULL_SELECTION_RECEIPT.json',dict(schema='ground-full-selection-v1',rows=nfull,output=full_pin,
                 membership=pin(out/'membership.jsonl'),per_type={t:counts[t]['admitted'] for t in TYPES},row_mutations=0))
    natural=sum(n for k,n in reasons.items() if k.endswith('|render:missing_direct_canonical'))
    receipt=dict(schema='ground-full-render-v8',run_key=run_key,status='rendered, checked, packed; training lane chooses selection',
                 training_admitted=False,pilot_fixture=data['fixture'],input_rows=sum(c['inputs'] for c in counts.values()),
                 admitted_rows=nfull,balanced_rows=nbal,scans=len(admitted_scans),rooms=len(admitted_rooms),
                 dev_scan_overlap=[],dev_room_overlap=[],counts={t:{s:counts[t][s] for s in STAGES} for t in TYPES},
                 refusal_counts=dict(reasons),natural_misses=dict(rows=natural,reason='render:missing_direct_canonical',
                     policy='No direct continuations joined; every natural miss is excluded',
                     full_pool_sizing_reference=5157 if not data['fixture'] else None),checks=dict(checks),
                 source_label_agreement=dict(source_agreement),cpu_seconds=sum(d['cpu_seconds'] for d in done),
                 workers=args.workers,resumed_scans=resumed,scan_receipts=[pin(Path(d['path'])/'DONE.json') for d in done],
                 sources=data['sources'],registry=data['registry'],splits=pin(SPLITS),benchmark=pin(BENCHMARK),
                 outputs={p.name:pin(p) for p in out.iterdir() if p.is_file()},orchard_reader=reader,
                 byte_count=sum(f['bytes'] for d in done for f in d['files'].values())+
                    sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
                 integration='Install orchard_ground_adapter in the builder process; use allow_paired_anchor=True for ground_aggregate rows. Own-head scheduled sampling requires ground_backend integration.')
    write_json(receipt_path,receipt)
    progress('complete',admitted=nfull,balanced=nbal,natural_misses=natural,receipt=str(receipt_path))
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pool_root',type=Path);p.add_argument('geometry_root',type=Path);p.add_argument('output_root',type=Path)
    p.add_argument('--workers',type=int,default=8)
    p.add_argument('--check-inputs-only',action='store_true',help='Verify CP2 and RGB pins without opening geometry or writing rows')
    p.add_argument('--stop-after-scans',type=int,help='Finish this many new scans, then return a deliberate resumable checkpoint')
    args=p.parse_args()
    if not 1<=args.workers<=8 or (args.stop_after_scans is not None and args.stop_after_scans<1):
        p.error('workers must be 1..8; stop-after-scans must be positive')
    if os.uname().nodename.split('.')[0]=='trinity':
        raise ValueError('Do not run agents or compute on the head node')
    for name in ('pool_root','geometry_root','output_root'):
        setattr(args,name,local_path(getattr(args,name).absolute()))
    if args.output_root in (args.pool_root,args.geometry_root):
        raise ValueError('output must be a separate directory')
    if np.__version__!='2.2.6':
        raise ValueError('NumPy 2.2.6 is required for audit replay')
    cfg=json.loads((ROOT/'work/CONFIG_v7.json').read_text())
    fixed=[cfg[k] for k in ('backend','tokenizer','spec','box_spec','box_provider_interface')]+cfg['reference_pins']
    for entry in fixed:checked(entry)
    progress('input_scan',pool=str(args.pool_root),workers=args.workers)
    data=load_input(args,cfg)
    if args.check_inputs_only:
        progress('inputs_verified',sources=data['sources'],registry=data['registry'],
                 counts=data['counts'],scans=len(data['groups']),rgb_manifests=len(data['timed']))
        return
    code_paths=list((ROOT/'work/derivgen_v7/derivgen').glob('*.py'))+[
        ROOT/'out/render_full.py',ROOT/'out/render_full.sh',ROOT/'out/build_orchard_ground.sh',ROOT/'out/select_ground_rows.py',
        ROOT/'out/orchard_ground_adapter.py',ROOT/'work/derivgen_v7/test_v312_benchmark.py',
        ORCHARD/'student_pilot/carrier_c1_routing.py']
    run=dict(sources=data['sources'],registry=data['registry'],splits=pin(SPLITS),benchmark=pin(BENCHMARK),
             config=pin(ROOT/'work/CONFIG_v7.json'),geometry_root=str(args.geometry_root),
             fixed_pins=fixed,code=[pin(path) for path in code_paths],numpy=np.__version__,
             pilot_fixture=data['fixture'],rgb_index=data['rgb_index'],
             manifest_pins=sorted((k,v['pin']) for k,v in data['timed'].items()))
    run_key=digest(run);run['run_key']=run_key
    args.output_root.mkdir(parents=True,exist_ok=True)
    run_path=args.output_root/'RUN.json'
    if run_path.exists():
        if encoded(json.loads(run_path.read_text()))!=encoded(run):
            raise ValueError('Run inputs/code changed; use a new output root')
    else:write_json(run_path,run)
    done,pending,resumed=[],[],0
    for scene,items in sorted(data['groups'].items()):
        scan_root=args.output_root/'scans'/scene
        result=completed_scan(scan_root,run_key)
        if result:
            checked(data['entries'][scene]['gt'])
            done.append(result);resumed+=1
        else:
            pending.append((scene,items,data['entries'][scene],cfg,str(scan_root),run_key,data['dev'],data['devrooms']))
    progress('prepared',inputs=sum(c['inputs'] for c in data['counts'].values()),scans=len(data['groups']),
             resumed_scans=resumed,pending_scans=len(pending))
    tasks=pending[:args.stop_after_scans] if args.stop_after_scans else pending
    if args.workers==1:
        for task in tasks:done.append(render_scan(task))
    else:
        # ProcessPoolExecutor uses pipes and semaphores, never a loopback socket.
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures=[executor.submit(render_scan,task) for task in tasks]
            for future in as_completed(futures):done.append(future.result())
    if len(tasks)<len(pending):
        progress('checkpoint_complete',completed_scans=len(done),remaining_scans=len(pending)-len(tasks))
        return
    assemble(args,data,done,run_key,resumed)


if __name__=='__main__':
    if '--program-items' in sys.argv:
        from render_programs_v314 import main as render_program_items
        sys.argv[sys.argv.index('--program-items')]='--items'
        render_program_items()
    else:
        main()
