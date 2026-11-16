"""Perception interfaces of the provider (schema 6.3 steps 2-4 and 6.5). Every backend exposes `sha()`, which enters the
provider sha and the cache key's pins.

`view` is (role, step) with role in {'wrist', 'agent'}; real backends read only the image and ignore it (table stubs in
the conformance tests key their answers on it).

- Presence.p_yes(image, phrase, view) -> float: the student's P(yes) from the first answer token (verify_kit V1).
- Pointer.point(image, phrase, view) -> (u1000, v1000) or None: the student's {"point_2d": ...} answer.
- Proposals.propose(images, noun, views) -> per view a list of Proposal(mask [H, W] bool, score): SAM 3 proposals
  (joint score >= 0.2, at most 10 per view).
- Geometry.run(images, views) -> geometry_viewset.ViewSetResult.
"""
from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Proposal:
    mask: np.ndarray
    score: float


class Presence(Protocol):
    def p_yes(self, image, phrase, view) -> float: ...
    def sha(self) -> str: ...


class Pointer(Protocol):
    def point(self, image, phrase, view): ...
    def sha(self) -> str: ...


class Proposals(Protocol):
    def propose(self, images, noun, views) -> list: ...
    def sha(self) -> str: ...


class Geometry(Protocol):
    def run(self, images, views): ...
    def sha(self) -> str: ...
