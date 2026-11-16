"""Deterministic CPU stand-in for the SAM 3 tower (tests only): colour-blob proposals with hashed scores."""
from __future__ import annotations

import hashlib

import numpy as np

from .common import rle_encode


class StubTower:
    stub = True

    def __init__(self, floor, cap):
        self.floor, self.cap = floor, cap

    def encode(self, frames):
        return [np.asarray(f, dtype=np.uint8) for f in frames]

    def detect(self, feats, name):
        out = []
        for k, a in enumerate(feats):
            h, w = a.shape[:2]
            seed = int(hashlib.sha256(f'{name}|{k}|{a[::37, ::41].tobytes().hex()[:64]}'.encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(seed)
            presence = float(rng.uniform())
            inst = []
            for q in range(int(rng.integers(0, 4))):
                y0, x0 = int(rng.integers(0, h // 2)), int(rng.integers(0, w // 2))
                y1, x1 = y0 + int(rng.integers(8, h // 2)), x0 + int(rng.integers(8, w // 2))
                m = np.zeros((h, w), bool)
                m[y0:y1, x0:x1] = True
                s = float(rng.uniform())
                if s * presence < self.floor:
                    continue
                inst.append(dict(query=q, score=s, joint_score=s * presence, box=[x0, y0, x1, y1], mask=rle_encode(m)))
            inst = sorted(inst, key=lambda r: -r['joint_score'])[:self.cap]
            out.append(dict(presence=presence, all_instance_scores=[float(x) for x in rng.uniform(size=8)],
                            instances=inst, joint_score=inst[0]['joint_score'] if inst else -1.0, prompt=name,
                            n_above_floor=len(inst)))
        return out
