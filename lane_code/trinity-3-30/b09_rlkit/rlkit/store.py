"""Per-draw atomic commits with resume.

Layout under a run directory:
  RUN_CONFIG.json                     config and its hash (written once)
  draws/<k[:2]>/<k>/d<draw>.json      one committed rollout; k = sha256(prompt_id)[:24]
A committed draw carries its own checksum and the config hash. Resume skips verified
draws, repeats only missing draws, and refuses a changed config or a corrupt commit.
Files named *.part are unfinished writes and are ignored.
"""
import hashlib
import json
from pathlib import Path

from .common import atomic_write_json, canonical, sha256_obj


class StoreError(RuntimeError):
    pass


def prompt_key(prompt_id):
    return hashlib.sha256(str(prompt_id).encode()).hexdigest()[:24]


class DrawStore:
    def __init__(self, root, config):
        self.root = Path(root)
        self.config = config
        self.config_hash = sha256_obj(config)
        head = self.root / 'RUN_CONFIG.json'
        if head.exists():
            stored = json.loads(head.read_text())
            if stored.get('config_hash') != self.config_hash:
                raise StoreError('run directory holds another config (%s != %s); refuse to mix'
                                 % (stored.get('config_hash'), self.config_hash))
        else:
            atomic_write_json(head, dict(config=config, config_hash=self.config_hash))

    def path(self, prompt_id, draw):
        k = prompt_key(prompt_id)
        return self.root / 'draws' / k[:2] / k / ('d%03d.json' % int(draw))

    def load(self, prompt_id, draw):
        """Verified committed record, or None when absent; raise on a corrupt or foreign commit."""
        p = self.path(prompt_id, draw)
        if not p.exists():
            return None
        try:
            env = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            raise StoreError(f'corrupt commit {p}: {exc}') from exc
        body = env.get('record')
        if not isinstance(body, dict) or env.get('sha256') != sha256_obj(body):
            raise StoreError(f'checksum mismatch in {p}')
        if env.get('config_hash') != self.config_hash:
            raise StoreError(f'commit {p} belongs to config {env.get("config_hash")}')
        if body.get('prompt_id') != prompt_id or body.get('draw') != draw:
            raise StoreError(f'commit {p} names another prompt/draw')
        return body

    def commit(self, record):
        prompt_id, draw = record['prompt_id'], record['draw']
        if self.load(prompt_id, draw) is not None:
            raise StoreError(f'draw already committed: {prompt_id} {draw}')
        canonical(record)  # must serialise
        atomic_write_json(self.path(prompt_id, draw),
                          dict(record=record, sha256=sha256_obj(record), config_hash=self.config_hash))

    def pending(self, prompts, draws):
        """(prompt, draw) pairs not yet committed, in a fixed order."""
        return [(p, d) for p in prompts for d in range(draws) if self.load(p['prompt_id'], d) is None]

    def groups(self, prompts, draws, *, require_complete=True):
        """{prompt_id: [records in draw order]}."""
        out = {}
        for prompt in prompts:
            group = []
            for d in range(draws):
                rec = self.load(prompt['prompt_id'], d)
                if rec is None:
                    if require_complete:
                        raise StoreError(f'missing draw {d} of {prompt["prompt_id"]}')
                    continue
                group.append(rec)
            out[prompt['prompt_id']] = group
        return out
