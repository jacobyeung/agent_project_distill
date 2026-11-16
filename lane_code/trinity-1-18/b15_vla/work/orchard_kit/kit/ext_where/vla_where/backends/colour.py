"""Image-only perception stub for synthetic scenes: SAM 3 stand-in by colour components, presence by colour area,
pointing at the component nearest a reference object named in the phrase ("next to the plate"). It reads pixels only,
so T-10 (hidden-state perturbation with fixed whitelisted inputs) is meaningful with it."""
import hashlib
import re

import numpy as np
from scipy import ndimage

from .base import Proposal


class ColourPerception:
    def __init__(self, colours, nouns, tol=12, min_pixels=20):
        """colours: {noun: [(r, g, b), ...]}; nouns: {phrase: noun}."""
        self.colours, self.nouns, self.tol, self.min_pixels = colours, nouns, tol, min_pixels

    def _components(self, image, noun):
        img = np.asarray(image, dtype=np.int32)
        out = []
        for rgb in self.colours.get(noun, []):
            # shading scales colours by [0.4, 1]; match the hue direction and a bounded brightness
            ref = np.asarray(rgb, dtype=np.float64)
            scale = (img @ ref) / max(ref @ ref, 1e-9)
            close = np.abs(img - scale[..., None] * ref).max(-1) <= self.tol
            ok = close & (scale > 0.35) & (scale <= 1.05)
            labels, n = ndimage.label(ok)
            for k in range(1, n + 1):
                m = labels == k
                if m.sum() >= self.min_pixels:
                    out.append(m)
        return out

    def propose(self, images, noun, views):
        return [[Proposal(m, float(m.mean())) for m in self._components(im, noun)] for im in images]

    def p_yes(self, image, phrase, view):
        comps = self._components(image, self.nouns.get(phrase, phrase))
        area = sum(int(m.sum()) for m in comps)
        return float(min(1.0, area / (4.0 * self.min_pixels)))

    def point(self, image, phrase, view):
        comps = self._components(image, self.nouns.get(phrase, phrase))
        if not comps:
            return None
        ref = re.search(r'next to the (\w[\w ]*)$', phrase)
        pick = comps[0]
        if ref:
            anchors = self._components(image, self.nouns.get(ref.group(1), ref.group(1)))
            if anchors:
                a = np.argwhere(anchors[0]).mean(0)
                pick = min(comps, key=lambda m: np.linalg.norm(np.argwhere(m).mean(0) - a))
        else:
            pick = max(comps, key=lambda m: m.sum())
        y, x = np.argwhere(pick).mean(0)
        h, w = pick.shape
        yx = np.argwhere(pick)
        y, x = yx[np.square(yx - (y, x)).sum(1).argmin()]
        return (min(int((x + .5) / w * 1000), 1000), min(int((y + .5) / h * 1000), 1000))

    def sha(self):
        return hashlib.sha256(f'colour|{sorted(self.colours.items())}|{sorted(self.nouns.items())}|{self.tol}'
                              .encode()).hexdigest()
