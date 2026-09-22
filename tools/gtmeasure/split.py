import copy
import hashlib
import json
import math
from pathlib import Path

from .assets import safe_scene
from .blocking import scene_key
from .io import pin, read_json, verify_pin


ARM_C = Path('/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z/split.json')
ARM_C_SHA256 = '4dd7467fd3b63b6a124bebf7c9a7be1749e3ac7696f6c7acaaaa49755efe4083'
PUBLISHED = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_interim_build_20260922T0325Z/work/PUBLISHED_SPLIT_interim.json')
SPLIT_RULE = 'student/landing/student_pilot/dataset_builder.py:184-192; SHA256 of indent=2, ensure_ascii=False, sort_keys=True JSON ["student-scene-split-v1",17,physical_group] plus newline; heldout iff digest < int(0.1 * 2**256)'


def group_id(dataset, scene):
    safe_scene({'dataset': dataset, 'scene_name': scene})
    dataset, scene = scene_key(dataset.casefold(), scene)
    dataset = 'scannetppv2' if dataset == 'scannetpp' else dataset
    return dataset + '/' + scene


def split_group(text):
    if not isinstance(text, str) or text.count('/') != 1:
        raise ValueError('published split scene must be dataset/scene')
    return group_id(*text.split('/'))


def hash_side(group, seed=17, fraction=.1):
    if type(seed) is not int or not math.isfinite(fraction) or not 0 < fraction < 1:
        raise ValueError('invalid split seed or fraction')
    group = split_group(group)
    payload = json.dumps(['student-scene-split-v1', seed, group], sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    score = int(hashlib.sha256(payload.encode()).hexdigest(), 16)
    return 'heldout' if score < int(fraction * 2**256) else 'train'


class SplitPolicy:
    def __init__(self, published, inherited=None, inherited_pin=None, published_pin=None):
        self.published = copy.deepcopy(published)
        self.inherited_pin = copy.deepcopy(inherited_pin)
        self.published_pin = copy.deepcopy(published_pin)
        self.seed = published.get('seed')
        self.fraction = published.get('validation_fraction', published.get('heldout_fraction_of_groups', .1))
        if self.seed != 17 or self.fraction != .1:
            raise ValueError('published seed 17 and heldout fraction 0.1 are required')
        self.known = {}
        for record in [inherited, published]:
            if record is None:
                continue
            for side in ('train', 'heldout'):
                fields = (side + '_scenes', side + '_group_ids', 'new_' + side + '_scenes')
                for name in (name for field in fields for name in record.get(field, [])):
                    key = split_group(name)
                    if key in self.known and self.known[key] != side:
                        raise ValueError('published split inheritance changes a scene side')
                    self.known[key] = side

    def side(self, dataset, scene):
        group = group_id(dataset, scene)
        return self.known.get(group, hash_side(group, self.seed, self.fraction))

    def partition(self, rows):
        train, heldout = [], []
        for row in rows:
            (train if self.side(row['dataset'], row['scene']) == 'train' else heldout).append(row)
        self.assert_train(train)
        train_groups = {group_id(row['dataset'], row['scene']) for row in train}
        heldout_groups = {group_id(row['dataset'], row['scene']) for row in heldout}
        if train_groups & heldout_groups:
            raise ValueError('physical scene crosses the train/heldout boundary')
        return train, heldout

    def assert_train(self, rows):
        for row in rows:
            if self.side(row['dataset'], row['scene']) != 'train':
                raise ValueError('heldout scene reached training rows')

    def record(self, train, heldout):
        self.assert_train(train)
        groups = {group_id(row['dataset'], row['scene']) for row in [*train, *heldout]}
        new = {side: sorted(group for group in groups if group not in self.known and hash_side(group, self.seed, self.fraction) == side)
               for side in ('train', 'heldout')}
        all_heldout = sorted({key for key, side in self.known.items() if side == 'heldout'} | set(new['heldout']))
        return {'schema': 'gtmeasure-inherited-scene-split-v1', 'seed': self.seed, 'validation_fraction': self.fraction,
                'inherited_split': self.inherited_pin, 'parent_split': self.published_pin, 'new_scene_rule': SPLIT_RULE,
                'train_scenes': copy.deepcopy(self.published['train_scenes']),
                'heldout_scenes': copy.deepcopy(self.published['heldout_scenes']),
                'new_train_scenes': sorted(set(self.published.get('new_train_scenes', [])) | set(new['train'])),
                'new_heldout_scenes': sorted(set(self.published.get('new_heldout_scenes', [])) | set(new['heldout'])),
                'all_heldout_groups': all_heldout,
                'train_qids': [row['qid'] for row in train], 'heldout_qids': [row['qid'] for row in heldout],
                'counts': {'train_rows': len(train), 'heldout_rows': len(heldout),
                           'train_groups': len({group_id(row['dataset'], row['scene']) for row in train}),
                           'heldout_groups_with_rows': len({group_id(row['dataset'], row['scene']) for row in heldout}),
                           'published_heldout_groups': sum(side == 'heldout' for side in self.known.values()),
                           'new_heldout_groups': len(new['heldout']), 'heldout_in_train': 0}}


def load_split(path):
    published = read_json(path)
    published_pin = pin(path)
    inherited_pin = published.get('inherited_split', {'path': str(Path(path).resolve()), 'sha256': published_pin['sha256']})
    if inherited_pin['sha256'] != ARM_C_SHA256:
        raise ValueError('split does not inherit the pinned arm C publication')
    inherited = read_json(verify_pin(inherited_pin))
    if inherited.get('seed') != 17 or inherited.get('heldout_fraction_of_groups') != .1:
        raise ValueError('arm C split contract drift')
    return SplitPolicy(published, inherited, inherited_pin, published_pin)
