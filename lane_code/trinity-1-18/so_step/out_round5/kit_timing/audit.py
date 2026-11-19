"""Observe the real processor and augmentation calls; do not substitute audit rows."""
from contextlib import contextmanager
import threading
import math


class Coverage:
    def __init__(self):
        self.augmented_pose_rows = 0
        self.augmentation_threads = set()
        self.max_grid = [0,0,0]
        self.grid_rows = 0
        self.observed_grids = set()

    @contextmanager
    def augmentation(self, module):
        original = module.augment
        def observe(arrays, settings):
            result = original(arrays, settings)
            if any(settings.get(k,0) != 0 for k in ('brightness','contrast','saturation','hue','blur_p','grayscale_p')):
                self.augmented_pose_rows += 1
                self.augmentation_threads.add(threading.current_thread().name)
            return result
        module.augment = observe
        try:
            yield
        finally:
            module.augment = original

    def observe(self, batch):
        for key in ('video_grid_thw','image_grid_thw'):
            if key not in batch:
                continue
            for grid in batch[key].tolist():
                if (len(grid) != 3 or any(v <= 0 for v in grid)
                        or grid[0] > 32 or grid[1] * grid[2] > 20 * 26):
                    raise ValueError('Processor output exceeds audited grid cap: t <= 32, h*w <= 520')
                if math.prod(grid) > math.prod(self.max_grid):
                    self.max_grid = list(grid)
                self.observed_grids.add(tuple(grid))
                self.grid_rows += 1

    def require(self, prefetch=False):
        if not self.augmented_pose_rows:
            raise ValueError('Audit did not execute augmented pose rows; keep prefetch OFF')
        if not self.grid_rows:
            raise ValueError('Audit did not observe processor grids')
        if prefetch and not any(n.startswith('c1-row-cpu') for n in self.augmentation_threads):
            raise ValueError('Augmented pose rows did not run on the prefetch worker')
