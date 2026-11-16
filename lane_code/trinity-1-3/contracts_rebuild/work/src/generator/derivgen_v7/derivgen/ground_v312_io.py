"""Pinned, CPU-only GT input adapter and review build for SPEC v3.12."""
import gzip
import copy
import hashlib
import importlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
from scipy import ndimage
from .instance_policy314 import valid_mask
from student_pilot.phrases import annotation_labels

from .ground_v312 import (Session, TYPES, RowRefusal, histogram, load_backend,
                          parse_roles, render, replay, select_balanced)
from .ground_v312_quality import deduplicate, shuffled_item, miss_candidates, question_identity, set_report, candidate_identity, selection_refusal
from .ground_v312_degenerate import degeneracy_reasons
from .ground_v312_tokens import tokenizer_for_rows, gate_positions, OPENERS


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def checked(entry):
    path = Path(entry['path'])
    if sha(path) != entry['sha256']:
        raise ValueError('pin mismatch: ' + str(path))
    return path


def reference(root):
    sys.path.insert(0, str(root))
    from rk import programs
    from rk.ground import MaskGround
    from rk.scheme import V311Scene
    return programs, MaskGround, V311Scene


class Frame1GTGeometry:
    """Put native GT in decode's frame-1, z-up world before taking medians."""
    def __init__(self, raw):
        self.raw = raw
        self.room_geometry = raw
        rotation, self.origin = raw.cam(1)
        up = np.array([0., 0., 1.])
        heading = rotation[:, 2] - rotation[2, 2]*up
        if np.linalg.norm(heading) < 1e-6:
            raise ValueError('undefined GT level basis')
        heading /= np.linalg.norm(heading)
        self.basis = np.column_stack((np.cross(heading, up), heading, up))

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def cam(self, frame):
        r, t = self.raw.cam(frame)
        return self.basis.T @ r, (t-self.origin) @ self.basis

    def lift(self, frame, uv, mode='center'):
        p, pc, spread = self.raw.lift(frame, uv, mode=mode)
        return (p-self.origin) @ self.basis, pc, spread


class CalibratedGTSource:
    """Use rkit's lift unchanged with the recorded K of each exact frame."""
    def __init__(self, raw, matrices=None):
        self.raw, self.K_frames = raw, matrices
        self.frames = None
        if matrices is not None:
            matrices = np.asarray(matrices, float)
            if matrices.shape != (32,3,3) or not np.isfinite(matrices).all():
                raise ValueError('invalid K_frames')
            self.frames = []
            for K in matrices:
                if min(K[0,0],K[1,1]) <= 0:
                    raise ValueError('nonpositive focal length')
                frame = copy.copy(raw)
                frame.K, frame.Kinv = K, np.linalg.inv(K)
                self.frames.append(frame)

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def lift(self, k, uv, mode='center'):
        source = self.raw if self.frames is None else self.frames[k-1]
        return source.lift(k, uv, mode=mode)


class GTClip:
    """Exact-frame native raster, same GTSource as the rkit reference executor."""
    def __init__(self, path, frame_indices, programs, MaskGround):
        self.programs = programs
        raw = programs._reference.GTSource(path)
        with np.load(path, allow_pickle=False) as z:
            if 'frame_indices' not in z or not np.array_equal(z['frame_indices'], frame_indices):
                raise ValueError('GT frame mismatch')
            matrices = z['K_frames'] if 'K_frames' in z else None
        self.geo = Frame1GTGeometry(CalibratedGTSource(raw, matrices))
        if len(frame_indices) != 32 or any(self.geo.frame_of(k) != k for k in range(1, 33)):
            raise ValueError('requires 32 exact frames')
        self.cache, self.lift_cache = {}, {}
        self.MaskGround = MaskGround

    def masks(self, name):
        if name not in self.cache:
            T, geo = self.programs.T, self.geo
            labels = annotation_labels(name, geo.labels, T.match_labels)
            ids = [iid for iid, label in zip(geo.ids, geo.labels) if label in labels]
            native = np.isin(geo.inst, ids)
            masks = np.stack([ndimage.zoom(m, (80/m.shape[0], 112/m.shape[1]),
                                          order=0, prefilter=False) for m in native])
            prob = np.array([valid_mask(m) for m in masks], dtype=float)
            self.cache[name] = masks, prob
        return self.cache[name]

    def ground(self, names):
        clip = self
        class Ground(self.MaskGround):
            def __init__(self):
                self.names = list(dict.fromkeys(names))
                values = [clip.masks(n) for n in self.names]
                self.values = dict(mask=np.stack([v[0] for v in values]),
                                   prob=np.stack([v[1] for v in values]))
                self.tau, self.geo, self.cache = .5, clip.geo, {}
            def index(self, name):
                return self.names.index(name) if name in self.names else None
            def lifted(self, name, frame):
                key = name, frame
                if key not in clip.lift_cache:
                    clip.lift_cache[key] = super().lifted(name, frame)
                return clip.lift_cache[key]
        return Ground()

    def validate_operands(self, item, multi_instance=False):
        if multi_instance:
            return self.validate_operands_multi(item)
        bindings = {}
        for name in operands(item):
            labels = annotation_labels(name, self.geo.labels, self.programs.T.match_labels)
            ids = [int(i) for i, label in zip(self.geo.ids, self.geo.labels) if label in labels]
            if len(ids) != 1:
                raise RowRefusal('single_instance_required')
            from student_pilot.phrases import annotation_phrase as normalized
            if normalized(name) not in {normalized(label) for label in labels}:
                raise RowRefusal('unresolved_qualified_name')
            bindings[name] = ids[0]
            masks, prob = self.masks(name)
            if not any(prob[k-1] >= .5 and masks[k-1].any() for k in range(1,33) if self.geo.has(k)):
                raise RowRefusal('object_not_visible_drop')

        boxes = {n:self.geo.obb[i] for n,i in bindings.items()}
        try:
            reasons = degeneracy_reasons(item, boxes, {n:self.masks(n)[0] for n in bindings})
        except ValueError as exc:
            raise RowRefusal('invalid_operand_box') from exc
        if len(bindings) != len(operands(item)):
            reasons = sorted(set(reasons) | {'operand_mask_overlap', 'operand_box_containment'})
        if item['type'].startswith('object_rel_direction') or item['type'] == 'absolute_direction_object':
            item['facing_extent_boxes'] = [dict(
                axes_f1=(np.asarray(boxes[item['roles'][k]]['normalizedAxes']).reshape(3,3)@self.geo.basis)[:,[0,2,1]].tolist(),
                lengths=np.asarray(boxes[item['roles'][k]]['axesLengths']).tolist()) for k in ('stand','face')]
        if reasons:
            error = RowRefusal(reasons[0])
            error.reasons = reasons
            raise error

    def validate_operands_multi(self, item):
        """v3.14 distance rows: every native instance of each operand name enters (at most MAX_INSTANCES)."""
        from student_pilot.phrases import annotation_phrase as normalized
        from .ground_v312_degenerate import degeneracy_reasons_multi
        from . import box_v313 as boxes_mod
        if item['type'] not in ('object_abs_distance', 'object_rel_distance'):
            raise RowRefusal('multi_instance_distance_only')
        sets = {}
        for name in operands(item):
            labels = annotation_labels(name, self.geo.labels, self.programs.T.match_labels)
            ids = [int(i) for i, label in zip(self.geo.ids, self.geo.labels) if label in labels]
            if not ids or len(ids) > boxes_mod.MAX_INSTANCES:
                raise RowRefusal('instance_count_unsupported')
            if normalized(name) not in {normalized(label) for label in labels}:
                raise RowRefusal('unresolved_qualified_name')
            masks, prob = self.masks(name)
            if not any(prob[k-1] >= .5 and masks[k-1].any() for k in range(1,33) if self.geo.has(k)):
                raise RowRefusal('object_not_visible_drop')
            sets[name] = [self.geo.obb[i] for i in ids]
        try:
            reasons = degeneracy_reasons_multi(item, sets, {n: self.masks(n)[0] for n in sets})
        except ValueError as exc:
            raise RowRefusal('invalid_operand_box') from exc
        if len(sets) != len(operands(item)):
            reasons = sorted(set(reasons) | {'operand_mask_overlap', 'operand_box_containment'})
        if reasons:
            error = RowRefusal(reasons[0])
            error.reasons = reasons
            raise error

    def cached_backend(self, backend):
        """One independent immutable-input cache per producer/replayer and clip."""
        cache = {}
        def lift(name, masks, prob, geometry, *, tau):
            if geometry is not self.geo or tau != .5:
                raise ValueError('clip cache input mismatch')
            key = name, sha_array(masks), sha_array(prob)
            if key not in cache:
                cache[key] = backend.lift_object(name, masks, prob, geometry, tau=tau)
            return cache[key]
        return SimpleNamespace(lift_object=lift, public_centres=backend.public_centres, number=backend.number,
                               render_ground=backend.render_ground,
                               gap_objects=backend.gap_objects, render_gap=backend.render_gap,
                               render_gaps=backend.render_gaps)


def sha_array(array):
    value = np.asarray(array)
    return (value.shape, str(value.dtype), hashlib.sha256(value.tobytes()).hexdigest())


def operands(item):
    r, t = item['roles'], item['type']
    if t == 'object_counting': return [r['obj']]
    if t == 'relative_count': return [r['a'], r['b']]
    if t == 'object_abs_distance': return [r['a'], r['b']]
    if t == 'object_rel_distance': return [r['target'], *r['cands']]
    return [r[k] for k in ('stand', 'face', 'query')]


def baseline(item, clip, Scene):
    scene = Scene(clip.geo, clip.ground(operands(item)), gates=True)
    r, t = item['roles'], item['type']
    if t == 'object_abs_distance': return scene.distance(r['a'], r['b'])
    if t == 'object_rel_distance': return scene.relative_distance(r['target'], r['cands'], item['options'])
    return scene.direction(r, item['options'], hard=t.endswith('_hard'))


def agrees(answer, gt, typ):
    if answer is None or answer == 'not seen': return False
    if typ == 'object_abs_distance':
        # v3.11 section-0 label gate: <=5% relative error, no additive floor.
        return abs(float(answer)-float(gt)) <= .05*abs(float(gt))
    return str(answer) == str(gt)


def validate_revision(backend, spec_path):
    if getattr(backend,'VERSION',None) != '3.12.2':
        raise ValueError('requires shared lifting revision 3.12.2')
    if not Path(spec_path).read_text().startswith('# SPEC v3.12.2:'):
        raise ValueError('requires spec revision 3.12.2')


def build(config_path, output, *, box_provider=None):
    """Produce a review artifact. This command does not authorize training or bulk IO."""
    config = json.loads(Path(config_path).read_text())
    box_mode = config.get('distance_contract') == 'sampled_box_512'
    if config.get('distance_contract') not in (None, 'sampled_box_512'):
        raise ValueError('unknown distance contract')
    if box_mode:
        from . import box_v313 as boxes, ground_v313_distance as distance
        from .ground_v313_tokens import gate_positions as box_gate_positions
        checked(config['box_spec'])
        checked(config['box_provider_interface'])
        if np.__version__ != '2.2.6':
            raise ValueError('sampled_box_512 requires NumPy 2.2.6')
        if box_provider is None:
            if config.get('box_provider') != 'annotation_full_box_v1':
                raise ValueError('supply a versioned box provider explicitly')
            box_provider = boxes.AnnotationBoxProvider()
        if box_provider.provider_id != config.get('box_provider'):
            raise ValueError('box provider pin mismatch')
    if config.get('diagnostic_only') is not True:
        raise ValueError('production source admission is PENDING-INPUT; use diagnostic_only=true')
    miss_rate = config.get('miss_rate', .10)
    if not isinstance(miss_rate, (int, float)) or not 0 <= miss_rate <= 1:
        raise ValueError('invalid miss_rate')
    backend_path = checked(config['backend'])
    code_paths = list(Path(__file__).parent.glob('ground_v312*.py')) + [Path(__file__), Path(__file__).with_name('ground_v312.py'),
                  Path(__file__).with_name('ground_v312_tokens.py'),
                  Path(__file__).with_name('calculator.py'), Path(__file__).with_name('paraphrase.py')]
    code_pins = {str(path): sha(path) for path in code_paths}
    if box_mode:
        for name in ('box_v313', 'ground_v313', 'ground_v313_distance', 'ground_v313_tokens'):
            path = Path(__file__).with_name(name+'.py')
            code_pins[str(path)] = sha(path)
    checked(config['spec'])
    tokenizer_path = checked(config['tokenizer'])
    distribution_path = checked(config['benchmark_distribution'])
    source_path, registry_path = checked(config['items']), checked(config['scenes'])
    programs, MaskGround, Scene = reference(config['rkit_root'])
    for entry in config['reference_pins']:
        checked(entry)
    tokenizer = tokenizer_for_rows(tokenizer_path)
    count = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    backend = load_backend(backend_path)
    validate_revision(backend, checked(config['spec']))
    registry = json.loads(registry_path.read_text())
    opener = gzip.open if str(source_path).endswith('.gz') else open
    grouped, rejects, dispositions = defaultdict(list), Counter(), []
    with opener(source_path, 'rt') as stream:
        for line in stream:
            item = json.loads(line)
            if item['type'] not in TYPES:
                rejects['direct_type'] += 1
                continue
            try:
                parsed = parse_roles(item, programs.T)
            except (ValueError, KeyError):
                rejects['unparsed_question'] += 1
                dispositions.append(dict(candidate_id=candidate_identity(item), qid=item['qid'], reason='unparsed_question'))
                continue
            if 'roles' in item and any(item['roles'].get(k) != v for k, v in parsed.items() if k != 'parser'):
                raise ValueError('question_role_mismatch')
            item['roles'] = parsed
            grouped[item['scene']].append(item)
    all_items, duplicates = deduplicate([r for items in grouped.values() for r in items])
    grouped = defaultdict(list)
    for item in all_items:
        grouped[item['scene']].append(shuffled_item(item))
    all_items = [r for items in grouped.values() for r in items]
    miss_ids, miss_refusals, miss_eligible = miss_candidates(all_items, miss_rate, config.get('miss_seed',0))
    rows, accepted, metrics, nulls = [], [], defaultdict(Counter), []
    rule_refusals = defaultdict(Counter)
    natural_gt = []
    seen = set()
    for scene, items in sorted(grouped.items()):
        entry = registry[scene]
        if entry.get('excluded') is not False:
            raise ValueError('scene exclusion status must be explicit')
        clip = GTClip(checked(entry['gt']), entry['frame_indices'], programs, MaskGround)
        producer, replayer = clip.cached_backend(backend), clip.cached_backend(backend)
        for item in items:
            if item['qid'] in seen:
                raise ValueError('duplicate qid')
            seen.add(item['qid'])
            if item['frame_indices'] != entry['frame_indices']:
                raise ValueError('question frame mismatch')
            typ, metric = item['type'], metrics[item['type']]
            distance_row = box_mode and typ in ('object_abs_distance', 'object_rel_distance')
            if distance_row:
                item['trace_revision'] = '3.13'
                item['target_distance_rule'] = boxes.RULE
            metric['attempted'] += 1
            try:
                clip.validate_operands(item)
            except RowRefusal as exc:
                rejects[str(exc)] += 1
                rule_refusals[typ].update(getattr(exc,'reasons',[str(exc)]))
                dispositions.append(dict(candidate_id=candidate_identity(item), qid=item['qid'], type=typ, reason=str(exc)))
                metric['source_refused'] += 1
                continue
            metric['admitted_operands'] += 1
            if typ == 'object_abs_distance':
                natural_gt.append(float(item['gt_answer']))
            try:
                old = baseline(item, clip, Scene)
            except (ValueError, FloatingPointError):
                old = None
            metric['v311_agrees'] += agrees(old, item['gt_answer'], typ)
            misses = operands(item)[:1] if item['qid'] in miss_ids else []
            if misses:
                name = misses[0]
                masks, prob = clip.masks(name)
                if not producer.lift_object(name,masks,prob,clip.geo,tau=.5)['seen']:
                    misses = []
                    metric['miss_ineligible_lift'] += 1
            metric['miss_selected'] += bool(misses)
            distance_session = None
            try:
                if distance_row:
                    distance.prepare(item, clip)
                    distance_session = distance.make_session(producer, clip, misses, box_provider)
                    row = boxes.render(item, distance_session, count)
                    distance.replay_exact(row, distance.make_session(replayer, clip, misses, box_provider))
                else:
                    row = render(item, Session(producer, clip.geo, clip.masks, simulated_misses=misses), count)
                    # Independent lifting caches and fresh registries on both paths.
                    replay(row, Session(replayer, clip.geo, clip.masks, simulated_misses=misses))
                metric['replay_equal'] += 1
            except (ValueError, FloatingPointError) as exc:
                rejects[str(exc)] += 1
                metric['refused'] += 1
                if str(exc)=='lifted_facing_vector_below_object_extent':
                    rule_refusals[typ][str(exc)] += 1
                if misses and str(exc) in ('missing_direct_canonical', 'invalid_direct_canonical'):
                    metric['miss_dropped_no_canonical'] += 1
                dispositions.append(dict(candidate_id=candidate_identity(item, misses), qid=item['qid'], type=typ, reason=str(exc),
                                         gt_answer=item['gt_answer'], v311_answer=old))
                if distance_row:
                    dispositions[-1].update(
                        events=list(distance_session.events) if distance_session else [], roles=item['roles'], options=item['options'],
                        scene=scene, gt_authority=item['gt_authority'], training_admitted=False,
                        independent_ordered_boxes=item.get('independent_ordered_boxes'))
                continue
            row.update(question_identity=question_identity(item), roles=item['roles'],
                       source_join=item.get('source_join'), option_shuffle=item.get('option_shuffle'),
                       option_letter_map=item.get('option_letter_map',{}), scene=scene, frame_indices=item['frame_indices'], gt_answer=item['gt_answer'],
                       gt_authority=item['gt_authority'], source_answer=item.get('source_answer'),
                       v311_answer=old, diagnostic_only=True, training_admitted=False,
                       geometry_source='gt', mask_source='gt', scene_gt_sha256=entry['gt']['sha256'])
            row['mdg_gate_token_positions'] = (box_gate_positions if distance_row else gate_positions)(tokenizer, row['suffix'])
            if row['not_seen']:
                row['direct_canonical_source'] = {k:v for k,v in item['direct_canonical'].items() if k != 'body'}
            row['gt_agrees'] = agrees(row['answer'], item['gt_answer'], typ)
            if distance_row and typ == 'object_abs_distance':
                row['gt_agrees'] = distance.agrees(row['answer'], item['gt_answer'])
            row['v311_gt_agrees'] = agrees(old, item['gt_answer'], typ)
            metric['v312_agrees'] += row['gt_agrees']
            row['selection_refusal'] = selection_refusal(row)
            row['gt_accepted'] = row['selection_refusal'] is None
            row['balanced'] = False
            rows.append(row)
            dispositions.append(dict(candidate_id=row['candidate_id'], qid=item['qid'], type=typ,
                                     reason=row['selection_refusal'] or 'gt_match',
                                     gt_accepted=row['gt_accepted'], training_admitted=False))
            if row['not_seen']:
                nulls.append(row)
            if row['gt_accepted']:
                accepted.append(row)
        print(json.dumps(dict(scene=scene, attempted=len(items), rendered=len(rows))), flush=True)
    distribution = json.loads(distribution_path.read_text())
    edges = config.get('distance_bin_edges_m', [0,.25,.5,1,2,4,8,16,None])
    if (edges[0] != 0 or edges[-1] is not None or any(not np.isfinite(v) for v in edges[:-1])
            or any(a>=b for a,b in zip(edges[:-2],edges[1:-1]))):
        raise ValueError('invalid distance bin edges')
    bins = [dict(key=f'[{lo},{hi})', lo=lo, hi=hi) for lo,hi in zip(edges[:-1], edges[1:])]
    natural = {b['key']:sum(v>=b['lo'] and (b['hi'] is None or v<b['hi']) for v in natural_gt) for b in bins}
    distribution['object_abs_distance'] = dict(bins=bins,content={k:v for k,v in natural.items() if v},
        source='natural independent GT distribution of admitted scene operands; ORCH 0533Z',
        cap_per_bin=config.get('distance_bin_cap',10))
    checked(config['backend'])
    if any(sha(path) != value for path, value in code_pins.items()):
        raise ValueError('generator changed during build')
    balanced, balance_report = select_balanced(accepted, distribution, config.get('per_type', 25))
    for row in balanced:
        row['balanced'] = True
    gate = {t: dict(v, passes=v['v312_agrees'] >= v['v311_agrees']) for t, v in metrics.items()}
    admitted_gate = {t: dict(n=sum(r['type']==t for r in accepted),
                            v312_agrees=sum(r['type']==t and r['gt_agrees'] for r in accepted),
                            v311_agrees=sum(r['type']==t and r['v311_gt_agrees'] for r in accepted)) for t in metrics}
    receipt = dict(status='REVIEW-ONLY', spec='3.12.2', config_sha256=sha(config_path),
                   input_pins=config, code_pins=code_pins, agreement=gate,
                   accepted_agreement=admitted_gate, duplicates_removed=duplicates,
                   operand_rule_refusals={t:dict(c) for t,c in rule_refusals.items()},
                   miss_candidate_refusals=miss_refusals, miss_eligible=miss_eligible, miss_budget_rows=len(miss_ids),
                   canonical_wording_refusals={t:miss_refusals.get(t,{}).get('canonical_wording_contradiction',0) for t in TYPES},
                   set_before=set_report(accepted), set_after=set_report(balanced), rejects=dict(rejects),
                   candidates=len(rows), gt_accepted=len(accepted), balanced=len(balanced),
                   candidate_histogram=histogram(rows), accepted_histogram=histogram(accepted),
                   balanced_histogram=histogram(balanced), balance=balance_report,
                   distance_bin_natural_gt_counts=natural,
                   answer_letter_histogram_before={t:dict(Counter(r['answer'] for r in accepted if r['type']==t)) for t in TYPES},
                   answer_letter_histogram_after={t:dict(Counter(r['answer'] for r in balanced if r['type']==t)) for t in TYPES},
                   simulated_miss_by_type={t:dict(selected=metrics[t]['miss_selected'], rendered=sum(r['type']==t and bool(r['simulated_misses']) for r in nulls),
                       genuine_misses=sum(r['type']==t and not r['simulated_misses'] for r in nulls), dropped_no_canonical=metrics[t]['miss_dropped_no_canonical']) for t in TYPES},
                   selection_refusals_by_type={t:dict(Counter(r['selection_refusal'] for r in rows
                       if r['type']==t and r['selection_refusal'])) for t in TYPES},
                   selection_scope='GT-matched normal review rows; diagnostic misses excluded; consumer training admission pending',
                   not_seen=len(nulls), max_suffix_tokens=max((r['suffix_tokens'] for r in rows), default=0),
                   counting_rows=0, total_multimodal_token_gate='PENDING consumer tokenizer',
                   miss_rate_requested=miss_rate, miss_seed=config.get('miss_seed',0),
                   tokenizer_openers={o:tokenizer.token_to_id(o) for o in OPENERS},
                   simulated_misses_rendered=sum(bool(r['simulated_misses']) for r in rows),
                   realized_miss_rate=sum(bool(r['simulated_misses']) for r in rows)/max(1,len(rows)),
                   replay_cache='independent producer/replay per-clip mask+probability hashes; fresh registry per row',
                   visibility='native instance union area >= 0.002; resize nearest 80x112; tau 0.5')
    if box_mode:
        receipt.update(spec='3.13 distance / 3.12.2 direction', training_admitted=False,
                       box_provider=box_provider.provider_id, numpy_version=np.__version__,
                       sampler=boxes.SAMPLER, distance_contract=boxes.RULE,
                       relative_printed_margin_m='0.02',
                       relative_raw_margin='none; raw winner must match independent label',
                       audit_replay='every box event and ordered gap; exact producer/replayer audit equality')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    for name, data in [('candidates', rows), ('gt_accepted', accepted), ('balanced', balanced),
                       ('not_seen', nulls), ('dispositions', dispositions)]:
        with (out/(name+'.jsonl')).open('x') as f:
            for row in data: f.write(json.dumps(row, allow_nan=False)+'\n')
    (out/'RECEIPT.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
    return receipt
