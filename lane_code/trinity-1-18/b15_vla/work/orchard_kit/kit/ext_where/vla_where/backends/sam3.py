"""SAM 3 proposals (schema 6.3 step 4): Sam3Tower.encode([wrist_t, agent_t]) once per call, then detect(features, noun)
per noun (up to 10 proposals per view with joint score >= 0.2; student_pilot/sam3_tower.py). The 32-frame TowerSAM3
wrapper is not used."""
import hashlib

import numpy as np

from .base import Proposal


class Sam3Proposals:
    def __init__(self, tower):
        self.tower = tower
        self._features = None

    @classmethod
    def load(cls, settings):
        from student_pilot.sam3_tower import Sam3Tower
        return cls(Sam3Tower(settings))

    def propose(self, images, noun, views=None):
        from PIL import Image
        key = tuple(hashlib.sha256(np.ascontiguousarray(i).tobytes()).hexdigest() for i in images)
        if self._features is None or self._features[0] != key:
            self._features = (key, self.tower.encode([Image.fromarray(np.asarray(i)) for i in images]))
        out = []
        for det in self.tower.detect(self._features[1], noun):
            masks, scores = det.masks.numpy().astype(bool), det.joint_scores.float().numpy()
            out.append([Proposal(m, float(s)) for m, s in zip(masks, scores)])
        return out

    def pin(self):
        from student_pilot.sam3_tower import CHECKPOINT_SHA256
        return CHECKPOINT_SHA256

    def sha(self):
        from student_pilot.sam3_tower import CHECKPOINT_SHA256, UPSTREAM_REVISION
        return hashlib.sha256(f'sam3|{CHECKPOINT_SHA256}|{UPSTREAM_REVISION}|joint>=0.2,top10'.encode()).hexdigest()
