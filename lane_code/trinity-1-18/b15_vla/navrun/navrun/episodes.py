from dataclasses import dataclass, field
from pathlib import Path
from .io import read_json
from .paths import R2R, R2RIE, R2R_GT

PRIMITIVES = ('stop', 'forward', 'turn_left', 'turn_right')

def scene_name(value):
    return Path(str(value).replace('\\', '/')).stem

def canonical_scene(value):
    return scene_name(value).casefold()

@dataclass
class Episode:
    episode_id: str
    trajectory_id: str
    scene_id: str
    start_position: list
    start_rotation: list
    goals: list
    instruction: str
    reference_path: list
    info: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    @property
    def scene(self):
        return scene_name(self.scene_id)

    @property
    def goal(self):
        if not self.goals:
            raise ValueError('Test goals are unavailable')
        return self.goals[0]['position']

    @classmethod
    def from_dict(cls, d):
        ins = d.get('instruction', '')
        return cls(str(d['episode_id']), str(d.get('trajectory_id', '')), d['scene_id'],
                   d['start_position'], d['start_rotation'], d.get('goals', []),
                   ins.get('instruction_text', '') if isinstance(ins, dict) else ins,
                   d.get('reference_path', []), d.get('info', {}),
                   {k: d[k] for k in ('old_episode_id', 'error_information') if k in d})

def load_episodes(path):
    episodes = [Episode.from_dict(d) for d in read_json(path)['episodes']]
    if len({e.episode_id for e in episodes}) != len(episodes):
        raise ValueError('Duplicate episode ids')
    return episodes

def load_split(split, root=R2R):
    return load_episodes(Path(root) / split / (split + '.json.gz'))

def load_ie(split='val_unseen_error_v1_direction', root=R2RIE):
    p = Path(root) / split / split
    episodes = load_episodes(str(p) + '_bertidx.json.gz')
    gt = read_json(str(p) + '_gt.json.gz')
    pairs = {}
    for e in episodes:
        key = str(e.metadata['old_episode_id'])
        part = 'perturbed' if e.metadata['error_information']['episode_contains_error'] else 'clean'
        if part in pairs.setdefault(key, {}):
            raise ValueError('Duplicate member of an R2RIE pair')
        pairs[key][part] = e
    for key, pair in pairs.items():
        if set(pair) != {'clean', 'perturbed'}:
            raise ValueError('Incomplete pair ' + key)
        a, b = pair['clean'], pair['perturbed']
        if (a.scene_id, a.trajectory_id, a.start_position, a.start_rotation, a.reference_path) != (
                b.scene_id, b.trajectory_id, b.start_position, b.start_rotation, b.reference_path):
            raise ValueError('Mismatched pair geometry')
        if gt[a.episode_id] != gt[b.episode_id]:
            raise ValueError('Mismatched pair GT')
    return episodes, gt, pairs

def load_gt(split, root=R2R_GT, episodes=None):
    """Load official episode-id keyed GT; reject corrupt or incomplete input."""
    import numpy as np
    gt = read_json(Path(root) / split / (split + '_gt.json.gz'))
    for key, track in gt.items():
        actions, locations = track['actions'], np.asarray(track['locations'], float)
        if not isinstance(key, str) or not actions or actions[-1] != 0 or 0 in actions[:-1]:
            raise ValueError('Invalid GT action stream: ' + str(key))
        if any(type(a) is not int or a not in range(4) for a in actions):
            raise ValueError('Invalid GT primitive: ' + key)
        if track['forward_steps'] != actions.count(1) or locations.shape != (actions.count(1)+1, 3):
            raise ValueError('GT locations do not align with forward actions: ' + key)
        if not np.isfinite(locations).all():
            raise ValueError('Nonfinite GT locations: ' + key)
    if episodes is not None:
        for e in episodes:
            if e.episode_id not in gt:
                raise ValueError('Missing official GT episode: ' + e.episode_id)
            if not np.allclose(gt[e.episode_id]['locations'][0], e.start_position, rtol=0, atol=2e-6):
                raise ValueError('GT start pose differs: ' + e.episode_id)
    return {key: dict(track, source='supplied_official_r2r_ce_gt') for key, track in gt.items()}

def training_gt(train, root=R2R_GT):
    """Prefer official ids; use verified R2RIE only if the official file is absent."""
    if (Path(root) / 'train/train_gt.json.gz').exists():
        gt = load_gt('train', root, train)
        return {e.episode_id: gt[e.episode_id] for e in train}
    return r2rie_training_gt(train)

def r2rie_training_gt(train):
    """Labelled fallback through verified R2RIE trajectory matches."""
    ie, gt, _ = load_ie('train_error_v1_all')
    by_trajectory = {}
    for e in ie:
        key = (e.scene, e.trajectory_id)
        if key in by_trajectory and by_trajectory[key][1] != gt[e.episode_id]:
            raise ValueError('Conflicting trajectory GT')
        by_trajectory[key] = (e, gt[e.episode_id])
    found = {}
    for e in train:
        item = by_trajectory.get((e.scene, e.trajectory_id))
        if item:
            src, track = item
            if (e.start_position, e.start_rotation, e.reference_path) != (
                    src.start_position, src.start_rotation, src.reference_path):
                raise ValueError('Trajectory match changed geometry')
            found[e.episode_id] = dict(track, source='supplied_r2rie_trajectory_gt')
    return found
