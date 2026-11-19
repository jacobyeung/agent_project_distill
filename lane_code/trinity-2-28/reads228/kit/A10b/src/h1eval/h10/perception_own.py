"""Own-prefill geometry and the reviewed reader's artifact-bound StageOne socket."""
from functools import partial


def perception_factory(artifact, model, device, *, processor=None, item=None,
                       settings=None, mode=None, donor=None, gt=None, socket=None):
    from h1eval.perception import OwnPerception
    from h1eval.modes import applies
    if item is not None and not applies(mode or {'name': 'none'}, item):
        raise ValueError('Perturbation does not apply to this item type')
    if socket is None:
        socket = getattr(model, 'h10_stage1_socket', None)
    if socket is None:
        socket = LazyStageOne(artifact, model, device, settings)
    # Import the fixed math before entering b04's generation audit. The launcher pins
    # this adapter; model/formatter/SAM code remains bound by b04's artifact.
    from student_pilot import carrier_c1_decode, p3_printed_calculator, scene_state, geometry_profiles
    from e2e_reader import grounding

    class BoundOwnPerception(OwnPerception):
        def lazy(self, frames, prefill_state, timings):
            import numpy as np
            frames = dict(frames)
            if item is not None:
                frames['capture_id'] = item['native']
            if 'source_hw' not in frames:
                from e2e_reader.real import anchor_frames
                images = anchor_frames(frames)
                frames['source_hw'] = (images[0].height, images[0].width)
            routes, built = super().lazy(frames, prefill_state, timings)
            heads = built['heads']
            depth_map = getattr(prefill_state.heads, 'depth_map', None)
            if depth_map is not None:
                import torch
                depth_finite = bool(torch.isfinite(depth_map).all())
            else:
                depth_finite = all(np.isfinite(heads.depth(i, np.array([[500., 500.]]))).all()
                                   for i in range(1, 33))
            finite = dict(pose9=bool(np.isfinite(heads.pose9).all()),
                          gravity=bool(np.isfinite(heads.gravity).all()), depth=depth_finite)
            built['finite_heads'] = finite
            if not all(finite.values()):
                raise ValueError('Non-finite own heads')
            return routes, built

    from e2e_reader.perception_memo import process_memo
    value = BoundOwnPerception(socket, mode=mode, donor=donor, gt=gt)
    value.memo = process_memo(settings or {})
    return value


def configured(mode, **kwargs):
    return partial(perception_factory, mode=mode, **kwargs)


class LazyStageOne:
    """Share frozen SAM/selector weights across items; create a new socket per read."""
    def __init__(self, artifact, model, device, settings=None):
        self.artifact, self.model, self.device = artifact, model, device
        self.settings = settings or {}
        self.socket = None

    def __call__(self, frames, geometry):
        if self.socket is None:
            from e2e_reader.stage1 import stage1_factory
            from e2e_reader.real import anchor_frames
            cached = getattr(self.model, '_h10_ground_components', None)
            if cached is None:
                sam = getattr(self.model, 'sam3_tower', None)
                selector = getattr(self.model, 'selector_head', None)
                if sam is None or selector is None:
                    from pathlib import Path
                    from e2e_reader.parity import _head
                    from student_pilot.sam3_tower import Sam3Tower
                    if not self.settings.get('sam3') or not self.settings.get('selector_head'):
                        raise ValueError('Own ground/gap requires staged SAM 3 and selector_head in settings')
                    config = dict(self.settings['sam3'], device=self.device)
                    for name in ('checkpoint_path', 'receipt_path'):
                        if Path(config[name]).resolve() not in self.artifact.files('sam3'):
                            raise ValueError('SAM file missing from artifact: ' + name)
                    selector = _head(self.artifact, self.settings['selector_head'], 'selector_head')
                    sam = Sam3Tower(config)
                cached = (sam, selector)
                self.model._h10_ground_components = cached
            from e2e_reader.perception_memo import process_memo
            self.socket = stage1_factory(*cached, anchor_frames,
                                         rule=self.settings.get('stage1_select_rule', 'null_argmax'),
                                         memo=process_memo(self.settings),
                                         artifact=self.artifact)
        return self.socket(frames, geometry)
