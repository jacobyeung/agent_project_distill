"""Frame layout of a read, in the `frames` form of orchkit-read-v1, with the training-layout guard.

The evaluator's `frame_list` (direct kits f42aa1a4 / ea1a1b2d, reader/evaluator/media.py) admits
32 anchors (duplicate or spread) and 64 anchors (spread only). A read's layout must equal the layout
the export was trained with (ARCHITECTURE_CURRENT: mismatch costs 3-13 points); step 544 and the D0
lineage train on 32 anchors, duplicated, and the carrier readout needs all 32 frames. A different
layout binds only when the export records it, or with an override reason that the binding carries.
"""

LAYOUTS = {(32, 'duplicate'), (32, 'spread'), (64, 'spread')}
TRAINED_32_DUPLICATE = dict(count=32, layout='duplicate')
EXPORT_LAYOUT = {'step544': TRAINED_32_DUPLICATE}


class FrameError(ValueError):
    pass


def processor_frames(count, layout):
    return count * 2 if layout == 'duplicate' else count


def bind_frames(count=32, layout='duplicate', *, export='step544', export_layout=None, override_reason=None):
    """Return {layout, count, layout_override_reason, ...} or raise FrameError.

    export_layout: {count, layout} recorded by a D0 export's completion record; for `step544` the
    trained layout is known. A layout that differs from the trained one needs override_reason.
    """
    if (count, layout) not in LAYOUTS:
        raise FrameError('frames must be one of %s' % sorted(LAYOUTS))
    trained = export_layout or EXPORT_LAYOUT.get(export)
    if trained is None and not override_reason:
        raise FrameError('the export records no training frame layout; pass it or an override reason')
    mismatch = trained is not None and (trained['count'], trained['layout']) != (count, layout)
    if mismatch and not override_reason:
        raise FrameError('read layout %s x %d differs from the trained layout %s x %d'
                         % (layout, count, trained['layout'], trained['count']))
    n = processor_frames(count, layout)
    return dict(count=count, layout=layout, layout_override_reason=override_reason or None,
                trained=trained, processor_frames=n,
                # Qwen3.5 merges temporal_patch_size=2 frames per visual group (check the processor config).
                temporal_groups=n // 2,
                anchor_rule='k*(N-1)//%d for k in 0..%d, PyAV rgb24 at stream fps' % (count - 1, count - 1))
