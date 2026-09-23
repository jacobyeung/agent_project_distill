from collections import Counter, defaultdict
import copy
from decimal import Decimal
import itertools

from .assets import EXCLUDED
from .conventions import FAMILIES, MEASURES, box_corners, camera0_points
from .formats import TYPE_FAMILY, UNIT_METERS, format_observation_value, format_value, render_question
from .geometry import camera_object_distance, object_count, object_distance, object_size
from .io import digest, pin
from .room_labels import AREA_UNITS, RoomLabelDeferred, label_measurement
from .targets import render_target, validate_student_input, validate_target


CATEGORIES = {'absolute_count': 'object_counting', 'absolute_size_object': 'object_size_estimation',
              'absolute_distance_object': 'object_abs_distance', 'relative_distance_object': 'object_rel_distance',
              'camera_obj_abs_dist': 'camera_obj_abs_dist', 'absolute_size_room': 'room_size_estimation'}


def interleave(iterators):
    active = list(iterators)
    while active:
        remaining = []
        for iterator in active:
            try:
                yield next(iterator)
                remaining.append(iterator)
            except StopIteration:
                pass
        active = remaining


def intermediate_observations(scene, conventions, family, object_ids, frame_index=None, room_label=None):
    if family == 'gtm_room_size':
        if room_label is None:
            raise RoomLabelDeferred('room_label_unavailable')
        return [conventions['observation_templates']['room_label']['template'].format(
            answer=room_label['answer'], units=room_label['units'])]
    objects = {obj['id']: obj for obj in scene.objects}
    selected = [objects[iid] for iid in sorted(set(object_ids))]
    poses, up = scene.arrays['camera_poses'], scene.receipt['gravity_up']

    def render(name, **values):
        return conventions['observation_templates'][name]['template'].format(**values)

    def coordinates(point):
        return dict(zip(('x', 'y', 'z'), map(format_observation_value, point)))

    def extents(obj):
        box_corners(obj['obb'])
        return dict(zip(('length', 'width', 'height'),
                        (format_observation_value(2 * float(half)) for half in obj['obb']['axesLengths'])))

    if family == 'gtm_object_size':
        obj, = selected
        return [render('object_extents', target=obj['label'], **extents(obj))]
    if family not in ('gtm_object_count', 'gtm_object_distance', 'gtm_camera_object_distance'):
        raise ValueError('unsupported structured observation family')
    centers = camera0_points([obj['obb']['centroid'] for obj in selected], poses, up)
    lines = []
    for obj, center in zip(selected, centers):
        values = {'target': obj['label'], 'instance_id': obj['id'], **coordinates(center)}
        if family == 'gtm_object_count':
            lines.append(render('instance_center', **values))
        else:
            lines.append(render('object_geometry', **values, **extents(obj)))
    if family == 'gtm_camera_object_distance':
        if type(frame_index) is not int or not 1 <= frame_index <= 32:
            raise ValueError('camera observation requires a one-based selected RGB frame')
        camera = camera0_points([poses[frame_index - 1, :3, 3]], poses, up)[0]
        lines.insert(0, render('camera_position', frame_index=frame_index, **coordinates(camera)))
    return lines


def rewrite_room_row(row, conventions, room_labels, *, commit, config_sha, structure='v2'):
    if row['family'] != 'gtm_room_size' or row['source_question_type'] != 'absolute_size_room':
        raise ValueError('room repair requires a room-size row')
    unit = row['ground_truth']['units']
    if set(AREA_UNITS.findall(row['student_input']['question'])) != {unit} or row['student_input']['options']:
        raise ValueError('room question and declared area unit disagree')
    if structure not in ('v1', 'v2'):
        raise ValueError('structure must be v1 or v2')
    label = room_labels.lookup(row['dataset'], row['scene'])
    measurement = label_measurement(label, unit, conventions)
    answer = measurement['rounded_value']
    observations = intermediate_observations(None, conventions, 'gtm_room_size', [], room_label=label) if structure == 'v2' else []
    observations.append(f'The full-room area is {answer} {unit}.')
    result = copy.deepcopy(row)
    result.update(object_ids=[], observations=observations, derivations=[], generation_commit=commit, config_sha256=config_sha,
                  ground_truth={'answer': answer, 'measurements': [measurement], 'units': unit, 'value': measurement['value']})
    result['provenance'].update(measure=copy.deepcopy(MEASURES['gtm_room_size']), room_label=label,
                               room_label_repair={'parent_row_canonical_sha256': digest(row),
                                                  'parent_generation_commit': row['generation_commit'],
                                                  'parent_config_sha256': row['config_sha256']})
    result['target'] = render_target(observations, answer)
    result['checks'] = validate_target(result['target'])
    validate_student_input(result['student_input'])
    return result


class Questions:
    def __init__(self, scene, conventions, seed, density, config_sha, commit, structure='v1', room_labels=None):
        self.scene, self.conventions = scene, conventions
        self.structure, self.room_labels = structure, room_labels
        self.seed, self.density, self.config_sha, self.commit = seed, density, config_sha, commit
        self.identity = [seed, scene.receipt['dataset'], scene.receipt['scene_name']]
        self.receipt_pin = pin(scene.receipt_path)
        self.objects = {obj['id']: obj for obj in scene.objects if obj['label'] not in EXCLUDED}
        self.groups = defaultdict(list)
        for obj in self.objects.values():
            self.groups[obj['label']].append(obj['id'])
        self.frames = {frame: scene.observations(frame) for frame in range(1, 33)}
        self.visible = {obj['id'] for rows in self.frames.values() for obj in rows}
        self.complete = {label for label, ids in self.groups.items() if all(iid in self.visible for iid in ids)}
        self.unique = {ids[0] for label, ids in self.groups.items() if label in self.complete and len(ids) == 1}
        self.distance_cache, self.rejections = {}, Counter()

    def rank(self, value):
        return digest([self.identity, value])

    def variants(self, kind, items):
        specs = self.conventions['templates'][kind]
        items = sorted(items, key=lambda item: self.rank([kind, item]))
        for variant in range(len(specs)):
            for item in items:
                offset = int(self.rank(['wording', kind, item])[:16], 16)
                yield item, specs[(offset + variant) % len(specs)]

    def measurement(self, value, kind, unit, ids):
        try:
            text = format_value(value, kind, unit, self.conventions)
        except ValueError as error:
            if str(error) != 'rounding_midpoint_not_specified_by_authority':
                raise
            self.rejections[str(error)] += 1
            return None
        return {'value_si': value, 'si_unit': 'square meters' if kind == 'absolute_size_room' else 'instances' if kind == 'absolute_count' else 'meters',
                'value': float(Decimal(str(value)) / UNIT_METERS[unit]), 'units': unit, 'rounded_value': text, 'object_ids': list(ids)}

    def row(self, kind, spec, values, measurements, observations, answer, derivations=(), frame_index=None, witness_frame=None, room_label=None):
        question, options = render_question(spec, **values)
        student_input = self.scene.student_input(question, options)
        validate_student_input(student_input)
        family = TYPE_FAMILY[kind]
        ids = sorted({iid for measurement in measurements for iid in measurement['object_ids']})
        if self.structure == 'v2':
            observations = intermediate_observations(self.scene, self.conventions, family, ids, frame_index, room_label) + observations
        target = render_target(observations, answer, derivations)
        checks = validate_target(target)
        authority = self.conventions['authorities']['vsti' if kind == 'camera_obj_abs_dist' else 'vsi']
        provenance = {'scene_receipt': self.receipt_pin,
                      'assets': {key: self.scene.receipt[key] for key in ('dense', 'calibration', 'instances', 'instance_mesh', 'annotations', 'alignment', 'source_provenance', 'video')},
                      'template': {'id': spec['id'], 'authority': authority, 'line': spec['source_line']},
                      'measure': MEASURES[family], 'visibility_witness_frame': witness_frame,
                      'visible_object_ids': sorted(self.visible), 'seed': self.seed}
        if room_label is not None:
            provenance['room_label'] = copy.deepcopy(room_label)
        ground_truth = {'answer': answer, 'measurements': measurements, 'units': measurements[0]['units'],
                        'value': measurements[0]['value'] if len(measurements) == 1 else [m['value'] for m in measurements]}
        return {'dataset': self.scene.receipt['dataset'], 'scene': self.scene.receipt['scene_name'], 'family': family,
                'category': CATEGORIES[kind], 'source_question_type': kind, 'source': 'gtmeasure_v1',
                'frame_index': frame_index, 'object_ids': ids, 'ground_truth': ground_truth,
                'student_input': student_input, 'target': target, 'observations': observations, 'derivations': list(derivations),
                'generation_commit': self.commit, 'config_sha256': self.config_sha, 'provenance': provenance, 'checks': checks}

    def counts(self):
        kind = 'absolute_count'
        for label, spec in self.variants(kind, self.complete):
            value = object_count(self.objects.values(), label)
            measurement = self.measurement(value, kind, spec['unit'], self.groups[label])
            if measurement:
                text = measurement['rounded_value']
                yield self.row(kind, spec, {'target': label}, [measurement],
                               [f'The scene contains {text} distinct {label} instances.'], text)

    def sizes(self):
        kind = 'absolute_size_object'
        for iid, spec in self.variants(kind, self.unique):
            obj = self.objects[iid]
            measurement = self.measurement(object_size(obj), kind, spec['unit'], [iid])
            if measurement:
                text = measurement['rounded_value']
                yield self.row(kind, spec, {'target': obj['label']}, [measurement],
                               [f'The longest dimension of the {obj["label"]} is {text} {spec["unit"]}.'], text)

    def distance(self, first, second):
        key = tuple(sorted((first, second)))
        if key not in self.distance_cache:
            self.distance_cache[key] = object_distance(self.objects[first], self.objects[second])
        return self.distance_cache[key]

    def distances(self):
        kind = 'absolute_distance_object'
        for (first, second), spec in self.variants(kind, itertools.combinations(sorted(self.unique), 2)):
            a, b = self.objects[first], self.objects[second]
            measurement = self.measurement(self.distance(first, second), kind, spec['unit'], [first, second])
            if measurement:
                text = measurement['rounded_value']
                yield self.row(kind, spec, {'object_0': a['label'], 'object_1': b['label']}, [measurement],
                               [f'The closest-point distance between the {a["label"]} and the {b["label"]} is {text} {spec["unit"]}.'], text)

    def mc_distances(self):
        kind = 'relative_distance_object'
        if kind not in self.conventions['emitted_mc_types']:
            return
        specs = self.conventions['templates'][kind]
        for frame in sorted(self.frames, key=lambda item: self.rank(['mc-frame', item])):
            observed = {obj['id'] for obj in self.frames[frame]}
            references = sorted(self.unique & observed, key=lambda item: self.rank(['mc-reference', frame, item]))
            for reference in references:
                label = self.objects[reference]['label']
                labels = self.complete & {self.objects[iid]['label'] for iid in observed} - {label}
                labels = sorted(labels, key=lambda value: self.rank(['mc-pool', frame, reference, value]))
                for pool in itertools.islice(itertools.combinations(labels, 4), max(16, self.density)):
                    measurements = []
                    for choice in pool:
                        pairs = [(self.distance(reference, iid), iid) for iid in self.groups[choice]]
                        distance, closest_id = min(pairs)
                        measurement = self.measurement(distance, 'absolute_distance_object', 'meters', [reference, *self.groups[choice]])
                        if measurement is None:
                            break
                        measurement.update(label=choice, closest_instance_id=closest_id)
                        measurements.append(measurement)
                    if len(measurements) != 4:
                        continue
                    values = [m['value_si'] for m in measurements]
                    displayed = [Decimal(m['rounded_value']) for m in measurements]
                    best = values.index(min(values))
                    if values.count(values[best]) != 1 or displayed.count(min(displayed)) != 1 or displayed.index(min(displayed)) != best:
                        self.rejections['mc_tie_or_rounding_ambiguity'] += 1
                        continue
                    spec = specs[int(self.rank(['mc-template', frame, reference, pool])[:16], 16) % len(specs)]
                    slots = {'reference': label, **{f'option_{i}': value for i, value in enumerate(pool)}}
                    answer = spec['option_letters'][best]
                    observations = [f'The closest-point distance from the {label} to the nearest {m["label"]} is {m["rounded_value"]} meters.' for m in measurements]
                    derivations = [f'The {pool[best]} has the smallest distance, so the answer is {answer}.']
                    yield self.row(kind, spec, slots, measurements, observations, answer, derivations, witness_frame=frame)

    def camera_distances(self):
        kind = 'camera_obj_abs_dist'
        candidates = [(frame, obj['id']) for frame, objects in self.frames.items() for obj in objects if obj['id'] in self.unique]
        for (frame, iid), spec in self.variants(kind, candidates):
            obj = self.objects[iid]
            value = camera_object_distance(obj, self.scene.arrays['camera_poses'][frame - 1])
            measurement = self.measurement(value, kind, spec['unit'], [iid])
            if measurement:
                text = measurement['rounded_value']
                yield self.row(kind, spec, {'target': obj['label'], 'frame_index': frame, 'frame_count': 32}, [measurement],
                               [f'In frame {frame}, the closest point of the {obj["label"]} is {text} meters from the camera.'], text,
                               frame_index=frame, witness_frame=frame)

    def rooms(self):
        kind = 'absolute_size_room'
        try:
            if self.room_labels is None:
                raise RoomLabelDeferred('room_label_unavailable')
            label = self.room_labels.lookup(self.scene.receipt['dataset'], self.scene.receipt['scene_name'])
        except RoomLabelDeferred as error:
            self.rejections[str(error)] += 1
            return
        for _, spec in self.variants(kind, [0]):
            try:
                measurement = label_measurement(label, spec['unit'], self.conventions)
            except ValueError as error:
                if str(error) != 'rounding_midpoint_not_specified_by_authority':
                    raise
                self.rejections[str(error)] += 1
                continue
            text = measurement['rounded_value']
            yield self.row(kind, spec, {}, [measurement], [f'The full-room area is {text} {spec["unit"]}.'], text, room_label=label)

    def generate(self):
        sources = [self.counts(), self.sizes(), interleave([self.distances(), self.mc_distances()]), self.camera_distances(), self.rooms()]
        rows, seen = [], set()
        for row in interleave(sources):
            identity = digest(row['student_input'])
            if identity in seen:
                self.rejections['duplicate_student_input'] += 1
                continue
            seen.add(identity)
            rows.append(row)
            if len(rows) == self.density:
                break
        rows.sort(key=lambda row: self.rank([row['family'], row['student_input']['question'], row['object_ids']]))
        for ordinal, row in enumerate(rows, 1):
            row['qid'] = f'gtmeasure_{row["dataset"]}__{row["scene"]}_{ordinal:05d}'
        coverage = {'rows': len(rows), 'by_family': {family: sum(row['family'] == family for row in rows) for family in FAMILIES},
                    'by_question_type': dict(Counter(row['source_question_type'] for row in rows)),
                    'official_object_instances': len(self.objects), 'visible_instances': len(self.visible),
                    'complete_categories': len(self.complete), 'unique_visible_labels': len(self.unique),
                    'unseen_object_ids': sorted(set(self.objects) - self.visible), 'rejections': dict(self.rejections)}
        return rows, coverage


def generate_scene(scene, conventions, *, seed=17, density=30, config_sha='', commit='', structure='v1', room_labels=None):
    if type(seed) is not int or type(density) is not int or not 1 <= density <= 99999:
        raise ValueError('seed must be an integer and density must lie in 1..99999')
    if structure not in ('v1', 'v2'):
        raise ValueError('structure must be v1 or v2')
    return Questions(scene, conventions, seed, density, config_sha, commit, structure, room_labels).generate()
