"""Own-prefill geometry; b04 retains the model and decoding implementation."""
from functools import partial


def perception_factory(artifact, model, device, *, mode=None, donor=None, gt=None, socket=None):
    from h1eval.perception import OwnPerception
    if socket is None:
        # b04 may attach its already-bound stage-1 socket to the loaded model.
        socket = getattr(model, 'h10_stage1_socket', None)
    if socket is None:
        socket = LazyStageOne(artifact, model, device)
    return OwnPerception(socket, mode=mode, donor=donor, gt=gt)


def configured(mode, **kwargs):
    return partial(perception_factory, mode=mode, **kwargs)


class LazyStageOne:
    """Load SAM/selector only for ground/gap; never construct G3T or a scale head."""
    def __init__(self, artifact, model, device):
        self.artifact, self.model, self.device = artifact, model, device
        self.socket = None

    def __call__(self, frames, geometry):
        if self.socket is None:
            from e2e_reader.stage1 import stage1_factory
            from e2e_reader.real import anchor_frames
            sam = getattr(self.model, 'sam3_tower', None)
            selector = getattr(self.model, 'selector_head', None)
            if sam is None or selector is None:
                raise ValueError('Own ground/gap requires b04 to bind model.h10_stage1_socket '
                                 'or model.sam3_tower and model.selector_head; no fallback geometry')
            self.socket = stage1_factory(sam, selector, anchor_frames)
        return self.socket(frames, geometry)
