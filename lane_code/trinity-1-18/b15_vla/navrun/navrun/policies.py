"""Blind policies take no geometric state. Oracles hold an explicit evaluation-only side channel."""
import hashlib
import math
import re
from collections import Counter
import numpy as np
from .click import label, lead_point, gt_lead_point
from .episodes import PRIMITIVES

class RandomPolicy:
    name = 'random'
    def __init__(self, statistics, seed=0):
        self.statistics, self.seed = statistics, seed
    def reset(self, episode_id):
        key = hashlib.sha256(f'{self.seed}:{episode_id}'.encode()).digest()
        self.rng = np.random.RandomState(int.from_bytes(key[:4], 'little'))
    def act(self, history_frames, instruction, state):
        return PRIMITIVES[self.rng.choice(4, p=self.statistics['action_probabilities'])]

class ForwardPolicy:
    name = 'forward-only'
    def __init__(self, statistics, seed=0):
        self.statistics = statistics
    def reset(self, episode_id):
        self.t = 0
    def act(self, history_frames, instruction, state):
        self.t += 1
        return 'forward' if self.t <= self.statistics['median_forward_steps'] else 'stop'

class InstructionPolicy(ForwardPolicy):
    name = 'instruction-prior'
    def reset(self, episode_id):
        self.t, self.plan = 0, None
    def act(self, history_frames, instruction, state):
        if self.plan is None:
            turns = re.findall(r'\b(left|right|around)\b', instruction.lower())
            budget = self.statistics['median_forward_steps']
            nturn = self.statistics['median_turn_run']
            self.plan = []
            for i in range(len(turns)+1):
                n = (i+1)*budget//(len(turns)+1) - i*budget//(len(turns)+1)
                self.plan += ['forward']*n
                if i < len(turns):
                    self.plan += ['turn_left' if turns[i] != 'right' else 'turn_right']*(12 if turns[i] == 'around' else nturn)
            self.plan += ['stop']
        action = self.plan[min(self.t, len(self.plan)-1)]
        self.t += 1
        return action

class OraclePolicy:
    name = 'shortest-path-oracle'
    def __init__(self, env):
        self.env = env
    def reset(self, episode_id):
        self.follower = self.env.follower(.5)
    def act(self, history_frames, instruction, state):
        return self.follower.next_action_along(np.array(self.env.episode.goal, np.float32))

class OracleClickPolicy:
    name = 'oracle-click-no-occlusion'
    def __init__(self, env):
        self.env = env
    def reset(self, episode_id):
        pass
    def act(self, history_frames, instruction, state):
        distance, path = self.env.path(self.env.position, self.env.episode.goal)
        if not path:
            return 'stop'
        return label(self.env.position, self.env.heading, lead_point(path), distance, len(history_frames))[0]

class OracleGTClickPolicy:
    name = 'oracle-gt-click-no-occlusion'
    def __init__(self, env, references):
        self.env, self.references = env, references
    def reset(self, episode_id):
        self.locations = self.references[episode_id]
    def resume_identity(self):
        from .io import digest
        from vla_where.nav import CLICK, SENSOR
        return dict(type=type(self).__name__, references=digest(self.references), click=CLICK, sensor=SENSOR,
                    stop_radius=self.env.config.success_radius)
    def act(self, history_frames, instruction, state):
        distance = self.env.distance()
        if distance < self.env.config.success_radius:
            return 'stop'
        point = gt_lead_point(self.locations, self.env.position)
        return label(self.env.position, self.env.heading, point, distance, len(history_frames))[0]

class ScriptPolicy:
    name = 'script'
    def __init__(self, answers):
        self.answers = answers
    def reset(self, episode_id):
        self.index = 0
    def act(self, history_frames, instruction, state):
        result = self.answers[min(self.index, len(self.answers)-1)]
        self.index += 1
        return result

def action_statistics(tracks):
    from itertools import groupby
    counts, lengths, turns = Counter(), [], []
    provenance = Counter()
    for track in tracks.values():
        a = track['actions']
        counts.update(a)
        lengths.append(a.count(1))
        turns.extend(len(list(g)) for k, g in groupby(a) if k in (2, 3))
        provenance[track['source']] += 1
    total = sum(counts.values())
    return dict(action_counts={PRIMITIVES[k]: counts[k] for k in range(4)},
                action_probabilities=[counts[k]/total for k in range(4)],
                median_forward_steps=int(round(float(np.median(lengths)))),
                median_turn_run=int(round(float(np.median(turns)))),
                source_counts=dict(provenance),
                definition='random: iid empirical primitive frequencies including STOP, sha256(seed:episode_id) RNG; forward-only: median training forward count then STOP; instruction-prior: same forward budget divided evenly around lexical left/right/around occurrences, median training turn-run for left/right and 12 left primitives for around')
