"""Versioned witness/instance formatter. Geometry and selectors keep their owners."""
import copy
import hashlib
import re
from collections import Counter
from decimal import Decimal
import numpy as np
from scipy.spatial import cKDTree
from . import ground_v312 as legacy
from . import box_v313 as boxes
from . import room_v314 as room
from .instance_policy314 import valid_mask, mask_floor
from .program_errors import ProgramRefusal

INSTANCE = re.compile(r'<ground obj="(' + legacy.NAME + r')" mode="instances">')
SURFACE = re.compile(r'<surface_pair a="(' + legacy.NAME + r')" b="(' + legacy.NAME + r')" mode="closest_visible">')
EXTENT = re.compile(r'<extent_ends obj="(' + legacy.NAME + r')" axis="longest_observed">')


def witness_pair(backend, a, b):
    """Use precisely the legacy frame pair and full eligible point sets."""
    audit = []
    distance = backend.gap_objects(a, b, audit=audit)
    if distance is None:
        return None
    i, j = audit[-1]['frames']
    A, B = np.asarray(a['points'][str(i)]), np.asarray(b['points'][str(j)])
    tree = cKDTree(A)
    ds, ix = tree.query(B, workers=1)
    # Deterministic ties: B input index, then A input index, never a centroid proxy.
    bi = int(np.argmin(ds))
    near = tree.query_ball_point(B[bi], float(ds[bi]) + 1e-12)
    ai = min(near, key=lambda k: (float(np.linalg.norm(A[k]-B[bi])), k))
    got = float(np.linalg.norm(A[ai]-B[bi]))
    if abs(got-distance) > 1e-9:
        raise legacy.RowRefusal('witness_backend_distance_mismatch')
    return dict(distance_m=distance, positions=[A[ai], B[bi]], frames=[i, j], indices=[ai, bi])


def point_line(backend, geometry, registry, name, role, frame, position, tail=''):
    camera, f1 = backend.public_centres(geometry, frame, np.asarray(position, float))
    if camera[2] <= 0:
        raise legacy.RowRefusal('point_behind_camera')
    rounded = lambda xs: [float(backend.number(x)) for x in xs]
    point = registry.register(camera=rounded(camera), f1=rounded(f1), spread=0., requested_frame=int(frame))
    # Reliability zero is an internal registry placeholder; no spread is asserted.
    coords = point['line'].split(': ', 1)[1].rsplit('; spread ', 1)[0]
    return f"{point['label']}: {name} {role} {coords}{tail}"


def pair_distance(registry, lines):
    """Use the calculator's Decimal arithmetic on the published f1 points."""
    a, b = [line.split(':', 1)[0] for line in lines]
    return registry.execute(f'<dist {a} {b}>')['text']


def surface_support(backend, geometry, registry, names, frames, positions, surfaces):
    """Publish same-surface centroids and check the printed facing half-spaces.

    This conservative admission check is not a nearest-point selector. Concave
    surfaces can fail it even when the supplied nearest pair is geometrically valid.
    """
    centres = []
    for position, surface in zip(positions, surfaces):
        surface = np.asarray(surface, float)
        if (surface.ndim != 2 or surface.shape[1] != 3 or not len(surface)
                or not np.isfinite(surface).all()):
            return None
        if float(np.linalg.norm(surface - position, axis=1).min()) > 1e-6:
            return None
        centres.append(np.median(surface, axis=0))
    lines = [point_line(backend, geometry, registry, n, 'support centroid', f, p)
             for n, f, p in zip(names, frames, centres)]
    lines += [point_line(backend, geometry, registry, n, 'nearest point', f, p)
              for n, f, p in zip(names, frames, positions)]
    c0, c1, p0, p1 = [registry._points[line.split(':', 1)[0]]['f1'] for line in lines]
    direction = [b-a for a, b in zip(c0, c1)]
    if (not any(direction) or sum((p-c)*d for p,c,d in zip(p0,c0,direction)) < 0
            or sum((p-c)*(-d) for p,c,d in zip(p1,c1,direction)) < 0):
        return None
    return lines


class Session(legacy.Session):
    """instances(name) returns stable-ID GT masks; provider supplies selected keypoints.

    enabled=False delegates every call to v3.12.2, with no extra allocations.
    A v3.13 ground call requires an instance resolver to avoid silently merging
    ambiguous masks. The resolver may return a single verified binding.
    """
    def __init__(self, *args, enabled=True, witness_points=None, keypoint_calls=False,
                 instances=None, keypoint_provider=None, box_provider=None,
                 distance_rule=boxes.RULE, multi_instance=None, program_version=None, geometry_mode='sensor', **kwargs):
        super().__init__(*args, **kwargs)
        if geometry_mode not in ('sensor', 'predicted'):
            raise ValueError('geometry_mode must be sensor or predicted')
        self.geometry_mode = geometry_mode
        self.enabled = enabled
        self.witness_points = enabled if witness_points is None else bool(witness_points and enabled)
        self.keypoint_calls = bool(keypoint_calls and enabled)
        self.instances = instances
        self.distance_rule = distance_rule
        # v3.14: a box ground of a name with several instances prints every instance; gaps take the minimum pair.
        if program_version not in (None, '3.13', '3.14'):
            raise ValueError('unsupported_program_version')
        version = program_version or ('3.14' if multi_instance else '3.13')
        if multi_instance is not None and bool(multi_instance) != (version == '3.14'):
            raise ValueError('program_version_instance_mode_mismatch')
        self.multi_instance = version == '3.14'
        # geometry_mode (validated above): 'sensor' keeps fused boxes; 'predicted' uses the fusion-policy provider
        # on depth-cut box points. Only box and gap values differ.
        if box_provider is not None and version == '3.14' and (
                isinstance(box_provider, boxes.PolicyBoxProvider) != (self.geometry_mode == 'predicted')):
            raise ValueError('box_provider_geometry_mode_mismatch')
        self.box_provider = box_provider or boxes.provider_for(self.geometry_mode, version)
        self.box_provider_id = self.box_provider.provider_id
        self.box_registry = boxes.BoxRegistry()
        self.box_registry.program_version=version
        self.keypoint_provider = keypoint_provider
        self.spec_version = version if enabled else '3.12.2'
        self.instance_results, self.witness_audit = {}, []

    def _instances(self, name):
        if self.instances is None:
            raise legacy.RowRefusal('v313_requires_instance_resolver')
        result = []
        ids = set()
        for entry in self.instances(name):
            iid = str(entry['instance_id'])
            if iid in ids:
                raise legacy.RowRefusal('duplicate_native_instance')
            ids.add(iid)
            extra = dict(depth_cut=True) if self.geometry_mode == 'predicted' else {}
            lifted = self.backend.lift_object(name, entry['masks'], entry['prob'], self.geometry, tau=self.tau, **extra)
            if lifted['seen']:
                result.append(dict(lifted, instance_id=iid, first=min(lifted['frames'])))
        return sorted(result, key=lambda r: (r['first'], r['instance_id']))

    def _gap(self, a, bs):
        if any(self.objects.get(n, {}).get('unresolved') for n in [a, *bs]):
            return 'unresolved'
        if not all(self.objects.get(n, {}).get('seen') for n in [a, *bs]):
            return 'not seen'
        objects = [self.objects[b] for b in bs]
        if not self.witness_points:
            return (self.backend.render_gap(self.objects[a], objects[0]) if len(bs) == 1 else
                    self.backend.render_gaps(self.objects[a], objects))
        pairs = [witness_pair(self.backend, self.objects[a], b) for b in objects]
        if any(p is None for p in pairs):
            return 'not seen'
        lines, distances = [], []
        # Copy the registry so a bad transform cannot leave a partly allocated response.
        registry = copy.deepcopy(self.registry)
        for b, pair in zip(bs, pairs):
            for n, frame, pos in zip([a, b], pair['frames'], pair['positions']):
                lines.append(point_line(self.backend, self.geometry, registry, n, 'nearest point', frame, pos))
            distance = pair_distance(registry, lines[-2:])
            distances.append(distance)
            pair['printed_distance_m'] = distance.removesuffix(' m')
        if len(bs) == 1:
            body = distances[0]
        else:
            values = [Decimal(d.removesuffix(' m')) for d in distances]
            minimum = min(values)
            winners = ','.join(f'"{n}"' for n,d in zip(bs,values) if d == minimum)
            body = '\n'.join([f'{n}: {d}' for n,d in zip(bs,distances)]
                             + [f'min {winners} {minimum:.2f} m'])
        self.registry = registry
        self.witness_audit.extend(pairs)
        return body + '\n' + '\n'.join(lines)

    def _keypoints(self, operation, names):
        if not self.keypoint_calls:
            raise legacy.RowRefusal('keypoint_calls_disabled')
        if any(self.objects.get(n, {}).get('unresolved') for n in names):
            return 'unresolved'
        if not all(self.objects.get(n, {}).get('seen') for n in names):
            return 'not seen'
        if self.keypoint_provider is None:
            return 'unavailable'
        result = self.keypoint_provider(operation, names)
        if result.get('status') != 'ok':
            return 'unresolved' if result.get('status') == 'ambiguous' else 'unavailable'
        if not result.get('observed_surface_points'):
            raise legacy.RowRefusal('unverified_surface_points')
        positions, frames = result['positions'], result['frames']
        if len(positions) != 2 or len(frames) != 2:
            raise legacy.RowRefusal('invalid_keypoint_pair')
        distance = float(np.linalg.norm(np.asarray(positions[0])-positions[1]))
        if not np.isfinite(distance) or abs(distance-result['distance_m']) > 1e-9:
            raise legacy.RowRefusal('keypoint_distance_mismatch')
        registry = copy.deepcopy(self.registry)
        roles = ['nearest point'] * 2 if operation == 'surface_pair' else ['extent start', 'extent end']
        objects = names if len(names) == 2 else names * 2
        if operation == 'surface_pair':
            surfaces = [self.objects[n]['points'].get(str(f), []) for n,f in zip(names,frames)]
            lines = surface_support(self.backend, self.geometry, registry, names, frames, positions, surfaces)
            if lines is None:
                return 'unavailable'
        else:
            lines = [point_line(self.backend, self.geometry, registry, n, role, frame, pos)
                     for n, role, frame, pos in zip(objects, roles, frames, positions)]
        label = 'visible pair distance' if operation == 'surface_pair' else 'observed endpoint distance'
        printed_distance = pair_distance(registry, lines[-2:])
        lines.append(label + ' ' + printed_distance)
        if operation == 'surface_pair':
            full = result.get('full_surface_distance_m')
            # Full reference and visible-witness proof must both come from the authority.
            if (full is not None and result.get('true_closest_visible') is True
                    and result.get('full_surface_authority')):
                if abs(float(full)-distance) > result.get('pair_tolerance_m', 1e-6):
                    raise legacy.RowRefusal('full_surface_witness_mismatch')
                lines.append('full surface gap ' + printed_distance)
            else:
                lines.append('full surface gap unavailable')
        self.registry = registry
        return '\n'.join(lines)

    def _room(self):
        self.room_inputs = room.sample(self.geometry, self.geometry_mode)
        result = room.from_points(**self.room_inputs)
        self.events.append(dict(call=room.CALL, response=legacy.wrap(room.format_result(result)),
                                audit=dict(room=result)))
        return room.format_result(result)

    def execute(self, call):
        if call == room.CALL:
            if not self.enabled or not self.multi_instance:
                raise legacy.RowRefusal('form_requires_v3.14')
            return self._room()

        if not self.enabled:
            return super().execute(call)
        if self.spec_version == '3.13' and (boxes.CAMGAP.fullmatch(call) or (boxes.GAP.fullmatch(call) and boxes.GAP.fullmatch(call)[3] == boxes.RULE_GRID)):
            raise ProgramRefusal('form_requires_v3.14')
        if self.spec_version == '3.14' and ((boxes.GAP.fullmatch(call) and boxes.GAP.fullmatch(call)[3] != boxes.RULE_GRID) or legacy.GAP.fullmatch(call) or SURFACE.fullmatch(call) or EXTENT.fullmatch(call)):
            raise ProgramRefusal('form_requires_v3.13')
        if (m := boxes.GROUND.fullmatch(call)):
            body = boxes.ground(self, legacy.valid_name(m[1]))
        elif (m := boxes.GAP.fullmatch(call)):
            bs = re.findall(r' b="(' + legacy.NAME + r')"', m[2])
            body, _ = self.box_registry.gap(legacy.valid_name(m[1]), bs, m[3])
        elif (m := boxes.CAMGAP.fullmatch(call)):
            names = [legacy.valid_name(n) for n in re.findall(r' b="(' + legacy.NAME + r')"', m[2])]
            k = int(m[1])
            if not (1 <= k <= 32 and getattr(self.geometry, 'has_pose', getattr(self.geometry, 'has', lambda _: True))(k)):
                body = 'frame unavailable'
                centre = None
            else:
                centre = boxes.camera_centre_f1(self.geometry, k)
                body, _ = boxes.cam_gap_body(self.box_registry, k, names, centre)
        elif (m := INSTANCE.fullmatch(call)):
            name = legacy.valid_name(m[1])
            entries = self._instances(name)
            self.instance_results[name] = entries
            # Enumeration does not resolve a bare singular reference.
            self.objects.pop(name, None)
            self.box_registry.invalidate(name)
            body = f'{name}: {len(entries)} found'
            registry = copy.deepcopy(self.registry)
            lines = []
            for ordinal, obj in enumerate(entries, 1):
                pos = np.median(obj['points'][str(obj['best'])], axis=0)
                lines.append(point_line(self.backend, self.geometry, registry, name,
                    f'instance {ordinal}', obj['best'], pos, f"; first {obj['first']}"))
            if lines:
                body += '\n' + '\n'.join(lines)
            self.registry = registry
        elif (m := legacy.GROUND.fullmatch(call)):
            name = legacy.valid_name(m[1])
            entries = self._instances(name)
            if len(entries) > 1:
                self.objects[name] = dict(seen=False, unresolved=True)
                body = name + ': unresolved'
            elif not entries:
                self.objects[name] = dict(seen=False)
                body = name + ': not seen'
            else:
                obj = entries[0]
                if name in self.simulated_misses:
                    obj = dict(obj, seen=False, simulated_miss=True)
                self.objects[name] = obj
                body = self.backend.render_ground(obj, self.registry)
        elif (m := legacy.GAP.fullmatch(call)):
            a = legacy.valid_name(m[1])
            bs = [legacy.valid_name(n) for n in re.findall(r' b="(' + legacy.NAME + r')"', m[2])]
            if a in bs or len(set(bs)) != len(bs):
                raise legacy.RowRefusal('duplicate_gap_operand')
            body = self._gap(a, bs)
        elif (m := SURFACE.fullmatch(call)):
            names = [legacy.valid_name(n) for n in m.groups()]
            if names[0] == names[1]:
                raise legacy.RowRefusal('duplicate_surface_operand')
            body = self._keypoints('surface_pair', names)
        elif (m := EXTENT.fullmatch(call)):
            body = self._keypoints('extent_ends', [legacy.valid_name(m[1])])
        elif call.startswith(('<ground', '<gap', '<surface_pair', '<extent_ends')):
            raise legacy.RowRefusal('malformed_v313_call')
        else:
            body = super().execute(call)
            self.events[-1]['audit'] = dict(box_provider=self.box_provider_id, numpy_version=np.__version__, distance_rule=None)
            return body
        private = {}
        if (match := boxes.GROUND.fullmatch(call)) and self.box_registry.states.get(match[1]) == 'ok':
            labels=self.box_registry.bindings[match[1]]
            records=[self.box_registry.records[l] for l in labels]
            if self.spec_version=='3.14':
                private['instance_metadata']=[{k:r[k] for k in ('areas','instance_id')} for r in records]
            policy=self.box_provider_id==boxes.POLICY_ID
            if len(records)==1:
                private['full_precision_box']=boxes.audit_box(records[0]['value'])
                private['box_label']=records[0]['label']
                if policy:private['full_precision_gap_box']=boxes.audit_box(records[0]['gap_value'])
            else:
                private['full_precision_boxes']=[boxes.audit_box(r['value']) for r in records]
                private['box_labels']=labels
                if policy:private['full_precision_gap_boxes']=[boxes.audit_box(r['gap_value']) for r in records]
            if policy:private['gap_operands']=[r['gap_operand'] for r in records]
        if (match := boxes.CAMGAP.fullmatch(call)):
            names=re.findall(r' b="('+legacy.NAME+r')"',match[2])
            private['sampler']=dict(boxes.SAMPLER_GRID)
            private['ordered_box_labels']=[self.box_registry.audit_labels(n) for n in names]
            private['camera_centre_f1']=None if centre is None else [float(x) for x in centre]
        if (match := boxes.GAP.fullmatch(call)):
            names=[match[1],*re.findall(r' b="('+legacy.NAME+r')"',match[2])]
            private['sampler']=dict(boxes.SAMPLERS[match[3]])
            private['ordered_box_labels']=[self.box_registry.audit_labels(n) for n in names]
        self.events.append(dict(call=call, response=legacy.wrap(body),
            audit=dict(box_provider=self.box_provider_id, numpy_version=np.__version__,
                       distance_rule=boxes.GAP.fullmatch(call)[3] if boxes.GAP.fullmatch(call) else None, **private)))
        return body


def selector_provider(selector, rows, geometry, *, radius=.5, min_support=1, axis='longest_observed'):
    """Reuse hrp.selector; the caller pins and imports that existing module."""
    selections = selector.select_keypoints(selector.from_points(rows), geometry, radius=radius)
    def provide(operation, names):
        if operation == 'surface_pair':
            return selector.keypoint_gap(selections, *names, min_support=min_support)
        return selector.keypoint_extent(selections, names[0], axis, min_support=min_support)
    return provide


class GTInstances:
    """Exact native IDs, one raster per instance; no label-wide mask unions.

    vocab (v3.14, optional): category word -> raw labels the benchmark pools under it (VSI-Bench counts desks and
    coffee tables as tables); without it a name matches its own normalized label only."""
    def __init__(self, clip, vocab=None):
        self.clip = clip
        self.vocab = vocab
    def labels_for(self, name):
        from .category_vocab import normalized
        pooled = (self.vocab or {}).get(normalized(name))
        return {normalized(l) for l in pooled} if pooled else {normalized(name)}
    def __call__(self, name):
        from scipy import ndimage
        from .category_vocab import normalized
        geo = self.clip.geo
        wanted = self.labels_for(name)
        result = []
        for iid, label in zip(geo.ids, geo.labels):
            if normalized(label) not in wanted:
                continue
            native = geo.inst == iid
            masks = np.stack([ndimage.zoom(m, (80/m.shape[0], 112/m.shape[1]), order=0, prefilter=False)
                              for m in native])
            prob = np.array([valid_mask(m) for m in masks], dtype=float)
            result.append(dict(instance_id=int(iid), masks=masks, prob=prob))
        return result


class MergedInstances:
    """v3.14 instance resolver for per-frame detections without cross-frame identity (own grounding heads).

    components(name) returns, for frames 1..32, a list of boolean masks (one per detection in that frame). Each
    detection is lifted to the median of its eligible points; a detection joins the nearest cluster whose mean lies
    within `radius` metres in 3D and holds no detection from the same frame, otherwise it starts a cluster. Clusters
    become instances whose per-frame masks are the union of their detections (rule 'merge3d_1.5m_one_per_frame')."""
    rule = 'merge3d_1.5m_one_per_frame'

    def __init__(self, backend, geometry, components, radius=1.5, tau=.5):
        self.backend, self.geometry, self.components = backend, geometry, components
        self.radius, self.tau = float(radius), tau

    def __call__(self, name):
        per_frame = self.components(name)
        if len(per_frame) != 32:
            raise ValueError('components require 32 frames')
        clusters = []
        for k, dets in enumerate(per_frame, 1):
            for m in dets:
                m = np.asarray(m, bool)
                if not valid_mask(m):
                    continue
                stack = np.zeros((32,) + m.shape, bool); stack[k - 1] = m
                prob = np.zeros(32); prob[k - 1] = 1.
                lifted = self.backend.lift_object(name, stack, prob, self.geometry, tau=self.tau)
                if str(k) not in lifted['points']:
                    continue
                p = np.median(np.asarray(lifted['points'][str(k)], float), axis=0)
                best = None
                for c in clusters:
                    d = float(np.linalg.norm(c['sum'] / c['n'] - p))
                    if d < self.radius and k not in c['masks'] and (best is None or d < best[0]):
                        best = (d, c)
                if best:
                    c = best[1]; c['sum'] = c['sum'] + p; c['n'] += 1; c['masks'][k] = m
                else:
                    clusters.append(dict(sum=p.copy(), n=1, masks={k: m}))
        out = []
        for i, c in enumerate(clusters, 1):
            shape = next(iter(c['masks'].values())).shape
            masks = np.zeros((32,) + shape, bool); prob = np.zeros(32)
            for k, m in c['masks'].items():
                masks[k - 1] = m; prob[k - 1] = 1.
            out.append(dict(instance_id=f'm{i}', masks=masks, prob=prob))
        return out


def gt_frame_components(clip, vocab=None):
    """Per-frame GT instance masks with the cross-frame identity removed (the B-level input of MergedInstances)."""
    gti = GTInstances(clip, vocab)
    def components(name):
        frames = [[] for _ in range(32)]
        for entry in gti(name):
            for k in range(32):
                if entry['prob'][k] > 0 and entry['masks'][k].any():
                    frames[k].append(entry['masks'][k])
        return frames
    return components


def connected_components(mask_fn, min_cells=None):
    """Own-head input: split each frame's category mask (32 x h x w) into 8-connected components."""
    from scipy import ndimage
    def components(name):
        masks, prob = mask_fn(name)
        frames = []
        for k in range(32):
            if prob[k] < .5 or not masks[k].any():
                frames.append([]); continue
            lab, n = ndimage.label(masks[k], structure=np.ones((3, 3)))
            frames.append([lab == j for j in range(1, n + 1) if (lab == j).sum() >= (mask_floor(masks[k].shape) if min_cells is None else min_cells)])
        return frames
    return components


def render(item, session, token_count):
    if getattr(session,'spec_version',None)=='3.14':
        raise ValueError('Use derivgen_v7.derivgen.programs_v314.render to generate v3.14 traces')
    if (session.enabled and item['type'] in ('object_abs_distance', 'object_rel_distance')
            and item.get('target_distance_rule', session.distance_rule) in boxes.RULES):
        return boxes.render(item, session, token_count)
    if not session.enabled or item['type'] not in ('object_counting', 'object_appearance_order'):
        row = legacy.render(item, session, token_count)
        if session.enabled:
            row['training_admitted'] = False
        return row
    if session.events:
        raise ValueError('render requires a fresh session')
    roles = item['roles']
    names = [roles['obj']] if item['type'] == 'object_counting' else roles['cands']
    lines = ['<think>', 'I will list the observed instances and their first eligible frames.']
    counts, first = {}, {}
    for name in names:
        call = f'<ground obj="{legacy.valid_name(name)}" mode="instances">'
        body = session.execute(call)
        lines += [call, legacy.wrap(body)]
        entries = session.instance_results[name]
        counts[name] = len(entries)
        if entries:
            first[name] = min(e['first'] for e in entries)
    if item['type'] == 'object_counting':
        content = str(counts[names[0]])
        noun = 'instance' if content == '1' else 'instances'
        lines.append(f'The tool found {content} observed {noun}.')
    else:
        if len(set(names)) != len(names) or len(names) < 2 or len(first) != len(names):
            raise legacy.RowRefusal('appearance_missing_or_duplicate_operand')
        if item['question'].startswith('What will be the first-time appearance order of the following categories in the video: '):
            if len(set(first.values())) != len(names):
                raise legacy.RowRefusal('appearance_tied_first_frame')
            content = ', '.join(sorted(names, key=first.get))
            lines.append(f'The first eligible frames give the order {content}.')
        else:
            winners = [n for n in names if first[n] == min(first.values())]
            if len(winners) != 1:
                raise legacy.RowRefusal('appearance_tied_first_frame')
            content = winners[0]
            lines.append(f'{content} has the earliest first eligible frame.')
    answer = legacy.letter(item['options'], content) if item.get('options') else content
    # Counts refer to observed instances. Independent task GT is mandatory.
    if str(item.get('gt_answer')) != answer or not item.get('gt_authority'):
        raise legacy.RowRefusal('independent_gt_disagreement_or_missing')
    lines += ['</think>', f'<answer>{answer}</answer>']
    suffix = '\n'.join(lines)
    tokens = token_count(suffix)
    if type(tokens) is not int or tokens < 0 or tokens > 5000:
        raise legacy.RowRefusal('suffix_cap')
    return dict(qid=item['qid'], type=item['type'], question=item['question'], options=item.get('options', []),
                answer=answer, answer_content=content, suffix=suffix, suffix_tokens=tokens,
                events=list(session.events), spec_version='3.13', training_admitted=False,
                program_audit=dict(observed_counts=counts, first_frames=first,
                                   gt_authority=item['gt_authority']))


def balance_gap_positions(rows, limit):
    """Preserve v3.12 option ordering: call candidates MUST follow option content."""
    from .ground_v312_balance import uniform_subset
    from .ground_v312_quality import deduplicate
    unique, _ = deduplicate(rows)
    groups = {}
    for row in unique:
        if row['type'] != 'object_rel_distance':
            raise legacy.RowRefusal('gap_balance_requires_relative_distance')
        contents = list(legacy.option_map(row['options']).values())
        call = next(e['call'] for e in row['events'] if e['call'].startswith('<gap '))
        candidates = re.findall(r' b="(' + legacy.NAME + r')"', call)
        if candidates != contents:
            raise legacy.RowRefusal('candidate_order_not_option_order')
        groups.setdefault(len(contents), []).append(row)
    selected = [r for n, group in sorted(groups.items()) for r in uniform_subset(group, limit)]
    report = {str(n): dict(Counter(r['answer'] for r in selected if len(r['options']) == n)) for n in groups}
    return selected, dict(answer_letters=report, gap_minimum_positions=report,
                         policy='exact equality within option count; shortage drops rows')
