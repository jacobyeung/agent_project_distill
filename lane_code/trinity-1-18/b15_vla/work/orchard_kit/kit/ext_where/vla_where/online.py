"""Online form for closed-loop evaluation (design 5.7: the provider and the policy run as two processes).

OnlineProvider keeps the wrist frames and proprio of the last 33 control steps, re-grounds at every chunk start
(t % 8 == 0; the policy executes all 8 actions open loop) and returns that output until the next chunk start. t = 0 is
the first observation the policy acts on: call reset() after the 10 wait steps. Every grounding is appended to an
optional JSONL log (the `shuffled` condition replays those records).

WhereServer serves an OnlineProvider over a Unix socket inside the lane folder (never a network port), authenticated
by a random key in a 0600 file next to it; WhereClient is the policy-side stub with the same reset/observe interface.
"""
import json
import os
import secrets
from multiprocessing.connection import Client, Listener
from pathlib import Path

import numpy as np

from .provider import view_list
from .types import Observation, WhereOutput


class OnlineProvider:
    def __init__(self, provider, chunk=8, log_path=None):
        self.provider, self.chunk = provider, chunk
        self.keep = max(provider.cfg.history_offsets) + 1
        self.log_path = Path(log_path) if log_path else None
        self.reset('')

    def reset(self, instruction, episode=''):
        """episode is a log label only; it never reaches the provider."""
        self.instruction, self.episode = instruction, episode
        self.wrist, self.proprio = {}, {}
        self.t, self.current, self.calls = 0, None, 0

    def observe(self, agent, wrist, proprio):
        t = self.t
        self.wrist[t] = np.asarray(wrist, dtype=np.uint8)
        self.proprio[t] = np.asarray(proprio, dtype=np.float64)
        for k in [k for k in self.wrist if k <= t - self.keep]:
            del self.wrist[k], self.proprio[k]
        if t % self.chunk == 0:
            steps = [k for r, k in view_list(t, self.provider.cfg.history_offsets) if r == 'wrist']
            obs = Observation(self.instruction, t, np.asarray(agent, dtype=np.uint8),
                              {k: self.wrist[k] for k in steps}, {k: self.proprio[k] for k in steps})
            self.current = self.provider.where(obs)
            self.calls += 1
            if self.log_path:
                with self.log_path.open('a') as f:
                    f.write(json.dumps(dict(episode=self.episode, t=t, chunk=t // self.chunk,
                                            output=self.current.to_dict()), sort_keys=True) + '\n')
        self.t += 1
        return self.current


def _key_path(socket_path):
    return Path(str(socket_path) + '.key')


class WhereServer:
    def __init__(self, online, socket_path):
        self.online, self.path = online, Path(socket_path)
        if len(str(self.path)) > 100:
            raise ValueError('Unix socket path too long')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise FileExistsError(f'{self.path} exists; another server may be running')
        key = secrets.token_bytes(32)
        fd = os.open(_key_path(self.path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
        self.listener = Listener(str(self.path), family='AF_UNIX', authkey=key)

    def serve(self, max_connections=None):
        served = 0
        try:
            while max_connections is None or served < max_connections:
                with self.listener.accept() as conn:
                    served += 1
                    while True:
                        try:
                            op, kwargs = conn.recv()
                        except EOFError:
                            break
                        if op == 'close':
                            break
                        try:
                            if op == 'reset':
                                self.online.reset(**kwargs)
                                conn.send(('ok', None))
                            elif op == 'observe':
                                conn.send(('ok', self.online.observe(**kwargs).to_dict()))
                            elif op == 'sha':
                                conn.send(('ok', self.online.provider.sha()))
                            else:
                                conn.send(('error', 'unknown op ' + str(op)))
                        except Exception as exc:  # the client re-raises; the server keeps serving
                            conn.send(('error', f'{type(exc).__name__}: {exc}'))
        finally:
            self.close()

    def close(self):
        self.listener.close()
        for p in (self.path, _key_path(self.path)):
            if p.exists():
                p.unlink()


class WhereClient:
    def __init__(self, socket_path):
        self.conn = Client(str(socket_path), family='AF_UNIX', authkey=_key_path(socket_path).read_bytes())

    def _call(self, op, **kwargs):
        self.conn.send((op, kwargs))
        status, value = self.conn.recv()
        if status != 'ok':
            raise RuntimeError('where service: ' + value)
        return value

    def reset(self, instruction, episode=''):
        return self._call('reset', instruction=instruction, episode=episode)

    def observe(self, agent, wrist, proprio):
        return WhereOutput.from_dict(self._call('observe', agent=agent, wrist=wrist, proprio=proprio))

    def sha(self):
        return self._call('sha')

    def close(self):
        try:
            self.conn.send(('close', {}))
        finally:
            self.conn.close()
