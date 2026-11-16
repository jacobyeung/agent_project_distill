"""Demonstration replays with ground truth -> (Episode, GTStore, id): the input of the pre-checks and of `gt_where`.

One episode = one `<episode id>.npz` (np.savez, no pickles) written by vla_libero's replay renderer. Images, depth and
segmentation are in the training dataset's orientation (schema 6.2: LIBERO LeRobot 256 x 256); cameras are OpenCV
axes in the robot base frame (schema 0: R_opencv = R_mujoco diag(1, -1, -1), plus diag(-1, -1, 1) for a 180-degree
image rotation).

  instruction                str (0-d)
  agent, wrist               [T, H, W, 3] uint8
  agent_depth, wrist_depth   [T, H, W] float32, optical-axis metres
  agent_seg, wrist_seg       [T, H, W] int32 object ids (0 = background, robot or table)
  seg_names                  str (0-d) JSON {id: object name} (LIBERO BDDL names, e.g. "akita_black_bowl_1")
  K_agent, K_wrist           [3, 3] or [T, 3, 3] float64, continuous pixels
  T_base_agent, T_base_wrist [T, 4, 4] float64 camera-to-base, OpenCV axes
  proprio                    [T, 8] float64 (the training data's state)
  names                      str (0-d) JSON {phrase: object name} for the step's target and place
  nouns                      str (0-d) JSON {noun: [object names]} (every instance of the noun in the scene)
vla_libero's renders_v2 files carry T_world_agent / T_world_wrist (world = the proprio frame) and target / place object
names instead of names / nouns; load_episode accepts both (derive_names).
The provider receives only the Episode (instruction, agent, wrist, proprio); the GTStore feeds GT backends and metrics.
"""
import json
from pathlib import Path

import numpy as np

from .backends.gt import GTStore
from .cache import Episode

REQUIRED = ('instruction', 'agent', 'wrist', 'agent_depth', 'wrist_depth', 'agent_seg', 'wrist_seg', 'seg_names',
            'K_agent', 'K_wrist', 'proprio')


def _str(a):
    return str(np.asarray(a).item())


def load_episode(path):
    path = Path(path)
    with np.load(path, allow_pickle=False) as data:
        missing = [k for k in REQUIRED if k not in data]
        if missing:
            raise ValueError(f'{path.name} lacks {missing}')
        d = {k: data[k] for k in data.files}
    ids = {int(k): v for k, v in json.loads(_str(d['seg_names'])).items()}
    pose = 'T_base_{}' if 'T_base_agent' in d else 'T_world_{}'
    frames = {}
    for t in range(len(d['agent'])):
        views = {}
        for role in ('agent', 'wrist'):
            K = np.asarray(d[f'K_{role}'], dtype=np.float64)
            seg = d[f'{role}_seg'][t]
            views[role] = dict(depth=d[f'{role}_depth'][t].astype(np.float64),
                               seg={name: seg == i for i, name in ids.items()},
                               T_base_cam=np.asarray(d[pose.format(role)][t], dtype=np.float64),
                               K=K if K.ndim == 2 else K[t])
        frames[t] = views
    if 'names' in d:
        names, nouns = json.loads(_str(d['names'])), json.loads(_str(d['nouns']))
    else:
        names, nouns = derive_names(_str(d['instruction']), _str(d['target']), _str(d['place']), ids.values())
    store = GTStore()
    store.bind(frames, names, nouns, path.stem)
    ep = Episode(_str(d['instruction']), d['agent'], d['wrist'], d['proprio'].astype(np.float64))
    return ep, store, path.stem


def derive_names(instruction, target, place, objects, table=None):
    """vla_libero's first render format (target and place object names): phrase -> object from the phrase table's
    step 0, noun -> every BDDL object whose name holds the noun with underscores (black bowl -> akita_black_bowl_1/2)."""
    from .phrases import default_table
    step = (table or default_table()).step(instruction)
    names, nouns = {step.target.phrase: target}, {}
    if step.place is not None and place:
        names[step.place.phrase] = place
    for ph in (step.target, step.place):
        if ph is not None:
            nouns[ph.noun] = sorted(o for o in objects if ph.noun.replace(' ', '_') in o)
    return names, nouns


def episodes(directory):
    for path in sorted(Path(directory).glob('*.npz')):
        yield load_episode(path)


def write_episode(path, ep, frames, names, nouns):
    """Inverse of load_episode (synthetic scenes and the format test)."""
    objects = sorted({o for v in frames[0].values() for o in v['seg']})
    ids = {i + 1: o for i, o in enumerate(objects)}
    arrays = {}
    for role in ('agent', 'wrist'):
        seg = np.zeros((len(ep), *ep.agent.shape[1:3]), np.int32)
        for t in range(len(ep)):
            for i, o in ids.items():
                seg[t][frames[t][role]['seg'][o]] = i
        arrays[f'{role}_seg'] = seg
        arrays[f'{role}_depth'] = np.stack([frames[t][role]['depth'] for t in range(len(ep))]).astype(np.float32)
        arrays[f'K_{role}'] = np.stack([frames[t][role]['K'] for t in range(len(ep))])
        arrays[f'T_base_{role}'] = np.stack([frames[t][role]['T_base_cam'] for t in range(len(ep))])
    np.savez(path, instruction=np.array(ep.instruction), agent=ep.agent, wrist=ep.wrist, proprio=ep.proprio,
             seg_names=np.array(json.dumps({str(k): v for k, v in ids.items()})), names=np.array(json.dumps(names)),
             nouns=np.array(json.dumps(nouns)), **arrays)
