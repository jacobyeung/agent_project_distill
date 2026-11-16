"""Episode loop with the single policy interface act(history_frames, instruction, state)."""
import json
import hashlib
import time
import numpy as np
from pathlib import Path
from .actions import Decoder
from .config import Config
from .metrics import metrics
from .prompts import history_indices
from .vendor.nav_text import FALLBACK
from .io import digest, ordered_id_sha256

def policy_identity(policy):
    if hasattr(policy, 'resume_identity'):
        return policy.resume_identity()
    if policy.__class__.__module__ != 'navrun.policies':
        raise ValueError('A custom policy needs resume_identity() for persistent evaluation')
    return dict(type=policy.__class__.__name__, name=policy.name,
                statistics=getattr(policy, 'statistics', None), seed=getattr(policy, 'seed', None),
                answers=getattr(policy, 'answers', None))

def execution_sha256():
    root = Path(__file__).parent
    files = [root / (name + '.py') for name in ('runner','actions','controller_v2','sim','metrics','click','policies','config','prompts')]
    files.append(root / 'vendor/nav_text.py')
    import vla_where.nav
    files.append(Path(vla_where.nav.__file__))
    return hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()

class Runner:
    def __init__(self, env, config=None, click_backend=None):
        self.env, self.config = env, config or env.config
        self.decoder = Decoder(self.config, click_backend)

    def episode(self, episode, policy, reference=None, stop_file=None, trace=None):
        start = time.monotonic()
        frames = [self.env.reset(episode)]
        if hasattr(policy, 'reset'):
            policy.reset(episode.episode_id)
        self.decoder.reset()
        executed, parse_events, decisions = [], [], 0
        distances = [self.env.distance()]
        shortest = distances[0]
        termination = 'step_cap'
        decision_positions = []
        while self.env.steps < self.config.step_cap and decisions < self.config.step_cap:
            if stop_file and Path(stop_file).exists():
                return None
            indices = history_indices(self.env.steps, self.config.history_frames)
            history = [frames[i] for i in indices]
            # State and backend observations contain no simulator objects, poses, depth or ids.
            obs = dict(frames=history, instruction=episode.instruction, executed=tuple(executed),
                       decision_index=decisions, constants=self.config.constants())
            state = {k: obs[k] for k in ('executed', 'decision_index', 'constants')}
            primitives = None
            for attempt in range(2):
                answer = policy.act(history, episode.instruction, state)
                primitives, info = self.decoder.decode(answer, obs)
                if primitives is not None:
                    break
                parse_events.append(dict(decision_index=decisions, attempt=attempt+1, answer=repr(answer),
                                         fallback=attempt == 1))
            if primitives is None:
                primitives = list(FALLBACK)
            decision_positions.append(self.env.position.copy())
            observation = dict(step=self.env.steps, position=self.env.position.tolist(),
                               heading=self.env.heading, answer=answer, controller=info,
                               primitives=list(primitives), executed=[])
            if trace is not None:
                trace.append(observation)
            decisions += 1
            commanded = 0.
            for action in primitives:
                if stop_file and Path(stop_file).exists():
                    return None
                if self.env.steps >= self.config.step_cap:
                    break
                before = self.env.position
                frames.append(self.env.step(action))
                executed.append(action)
                observation['executed'].append(action)
                blocked = self.decoder.executed(action, float(np.linalg.norm(self.env.position-before)))
                if action == 'forward':
                    commanded += .25
                distances.append(self.env.distance() if action == 'forward' else distances[-1])
                if self.env.stopped:
                    termination = 'stop'
                    break
                if blocked:
                    break
            if self.config.output_format == 'click':
                self.decoder.click_backend.executed_commanded(commanded)
            if self.env.stopped:
                break
        if decisions >= self.config.step_cap and self.env.steps < self.config.step_cap and not self.env.stopped:
            termination = 'decision_cap'
        result = metrics(self.env.positions, reference if reference is not None else episode.reference_path,
                         distances, shortest, self.env.stopped, self.config.success_radius, self.config.dtw)
        tail = np.asarray(decision_positions[-20:])
        tail_span = float(np.linalg.norm(tail-tail[-1], axis=1).max())
        return dict(result, stationary_tail=len(tail)==20 and tail_span < 1e-4,
                    tail_span_from_last_m=tail_span,
                    episode_id=episode.episode_id, scene=episode.scene,
                    trajectory_id=episode.trajectory_id, steps=len(executed), decisions=decisions,
                    actions=executed, parse_events=parse_events, termination=termination,
                    wall_seconds=time.monotonic()-start)

    def evaluate(self, episodes, policy, journal, references=None, stop_file=None, limit=None):
        """Resume completed episodes. An interrupted episode restarts deterministically from its start."""
        journal = Path(journal)
        journal.parent.mkdir(parents=True, exist_ok=True)
        signature = digest(dict(protocol=2, code=execution_sha256(), config=self.config.to_dict(),
                                ids=ordered_id_sha256([e.episode_id for e in episodes]),
                                episodes=[vars(e) for e in episodes],
                                references={e.episode_id:(references or {}).get(e.episode_id) for e in episodes},
                                policy=policy_identity(policy)))
        records = []
        needs_newline = False
        if journal.exists():
            raw = journal.read_bytes()
            needs_newline = bool(raw and not raw.endswith(b'\n'))
            lines = raw.splitlines()
            for i, line in enumerate(lines):
                try:
                    row = json.loads(line)
                except ValueError:
                    if i != len(lines)-1:
                        raise ValueError('Corrupt interior journal record')
                    # A partial record is retained; a separate continuation file avoids deletion.
                    return self._continue(episodes, policy, journal, records, signature, references, stop_file, limit)
                if row.get('signature') != signature:
                    raise ValueError('Resume signature differs (config/list/policy)')
                if row.get('kind') == 'episode':
                    records.append(row['result'])
        if len({r['episode_id'] for r in records}) != len(records):
            raise ValueError('Duplicate journal result')
        done = {r['episode_id'] for r in records}
        with journal.open('a') as f:
            if needs_newline:
                f.write('\n')
            if journal.stat().st_size == 0:
                f.write(json.dumps(dict(kind='header', signature=signature))+'\n'); f.flush()
            count = 0
            for ep in episodes:
                if ep.episode_id in done:
                    continue
                if limit is not None and count >= limit:
                    break
                result = self.episode(ep, policy, (references or {}).get(ep.episode_id), stop_file)
                if result is None:
                    break
                f.write(json.dumps(dict(kind='episode', signature=signature, result=result), allow_nan=False)+'\n')
                f.flush()
                records.append(result)
                count += 1
        return records

    def _continue(self, episodes, policy, journal, records, signature, references, stop_file, limit):
        continuation = journal.with_name(journal.name + '.continuation')
        if not continuation.exists():
            with continuation.open('w') as f:
                f.write(json.dumps(dict(kind='header', signature=signature))+'\n')
                for result in records:
                    f.write(json.dumps(dict(kind='episode', signature=signature, result=result))+'\n')
        return self.evaluate(episodes, policy, continuation, references, stop_file, limit)
