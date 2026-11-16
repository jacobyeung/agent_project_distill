"""The reader core every read config drives (ORCH 1149Z: one reader; lane eff_reader_harness's
read.py calls this through one small interface).

    gen = E2EGenerator(model, processor, artifact, perception, hook, read_config)
    out = gen(item)        # item: {'id', 'row' (trainer row with frames + question), 'frames'}
    out -> {'id', 'text', 'tokens', 'finish', 'calls', 'audit', 'seconds', 'heads', 'scale',
            'guard_verdicts', 'frames': {'layout', 'count'}}

The generator writes no answer: the scored answer is the model's own text (USER 2026-11-16:
the model converts units and formats numbers in its CoT; no reader post-processes them).
Frame count (32 or 64) and layout are read-config parameters; the generator refuses a
layout that differs from the export's training layout unless the config states a reason.
"""
import time


class FrameLayoutError(ValueError):
    pass


def check_layout(read_frames, export_layout):
    """read_frames: {'layout', 'count', 'layout_override_reason'}; export_layout: same keys from
    the export's artifact.json (frame_layout) and its training config (frame count)."""
    same = (read_frames['layout'], int(read_frames['count'])) == (export_layout['layout'], int(export_layout['count']))
    if not same and not read_frames.get('layout_override_reason'):
        raise FrameLayoutError('read_frame_layout_differs_from_training: %r vs %r' % (read_frames, export_layout))
    return dict(read_frames, matches_training=same)


class E2EGenerator:
    def __init__(self, model, processor, artifact, perception, hook, read_config, *, export_layout,
                 prompt_batch, budget_factory=None, device='cuda:0'):
        self.model, self.processor, self.artifact = model, processor, artifact
        self.perception, self.hook = perception, hook
        self.frames = check_layout(read_config['frames'], export_layout)
        self.prompt_batch, self.budget_factory, self.device = prompt_batch, budget_factory, device

    def __call__(self, item):
        from .real import generate_real
        t0 = time.perf_counter()
        batch = self.prompt_batch(self.processor, item['row'])
        batch = {k: (v.to(self.device) if hasattr(v, 'to') else v) for k, v in batch.items()}
        budget = self.budget_factory() if self.budget_factory is not None else None
        out = generate_real(self.model, self.processor, batch, item['frames'], self.hook, self.perception,
                            artifact=self.artifact, budget=budget)
        out.update(id=item['id'], seconds=time.perf_counter() - t0, frames=self.frames)
        return out
