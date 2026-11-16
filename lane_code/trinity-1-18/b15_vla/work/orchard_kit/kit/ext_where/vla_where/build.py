"""Provider factory for scripts and tests.

  student    the frozen provider student (full_weights), ViewSetG3T on the pinned tower, SAM 3; GPU host only
  gt_where   the same provider code with GT inputs through a GTStore (schema 5.5), flag proprio_handeye
  reference  as gt_where with flag metric_test (pre-check GT definition)
  noisy      GT-reading stubs with injected perception errors and an arbitrary G3T unit (CPU pre-check)
  tiny       image-only colour perception + the tree's tiny real-architecture G3T on CPU (T-10, smoke)
"""
import json

from .provider import Config, WhereProvider
from .scale import HandEye


def parse_params(text):
    """'a=1,b=0.5' or a JSON object -> dict."""
    text = (text or '').strip()
    if text.startswith('{'):
        return json.loads(text)
    out = {}
    for part in filter(None, text.split(',')):
        key, value = part.split('=', 1)
        out[key.strip()] = json.loads(value)
    return out


def build_provider(kind, params=None, config=None, *, hand_eye=None, store=None):
    from .backends import gt
    params, config = dict(params or {}), config or Config()
    if kind in ('gt_where', 'reference'):
        flag = 'proprio_handeye' if kind == 'gt_where' else 'metric_test'
        return WhereProvider(gt.GTPresence(store), gt.GTPointer(store), gt.GTProposals(store),
                             gt.GTGeometry(store, flag), hand_eye, config)
    if kind == 'noisy':
        pick = lambda keys: {k: params.pop(k) for k in keys if k in params}
        perception = gt.NoisyPerception(store, **pick(('false_yes', 'miss', 'wrong', 'jitter_px')))
        geometry = gt.NoisyGeometry(store, **pick(('unit', 'depth_sigma', 'pose_t_sigma', 'pose_r_deg', 'mirror')))
        if params:
            raise ValueError(f'Unknown noisy parameters {sorted(params)}')
        return WhereProvider(perception, perception, perception, geometry, hand_eye, config)
    if kind == 'tiny':
        from . import synth
        from .backends.colour import ColourPerception
        from .geometry_viewset import ViewSetG3T, tiny_module
        colours = {'black bowl': [synth.COLOURS['black bowl']], 'plate': [synth.COLOURS['plate']]}
        nouns = {'black bowl next to the plate': 'black bowl', 'plate': 'plate'}
        perception = ColourPerception(colours, nouns, **params)
        return WhereProvider(perception, perception, perception, TinyG3T(ViewSetG3T(tiny_module())), hand_eye, config)
    if kind == 'student':
        return build_student(config, **params)
    raise ValueError('kind must be student, gt_where, reference, noisy or tiny')


class TinyG3T:
    """ViewSetG3T on the tiny module, run at 28 px under the tree test's patches (CPU only)."""

    def __init__(self, viewset):
        self.viewset = viewset

    def run(self, images, views):
        from contextlib import ExitStack
        from .geometry_viewset import tiny_patches
        with ExitStack() as stack:
            for p in tiny_patches():
                stack.enter_context(p)
            return self.viewset.run(images, views)

    def pin(self):
        return self.viewset.pin()

    def sha(self):
        return self.viewset.sha()


def build_student(config, *, full_weights, g3t_weights, g3t_config, sam3, hand_eye, hand_eye_sha256, device='cuda'):
    """sam3: Sam3Tower settings {checkpoint_path, receipt_path, source_root, ...}; hand_eye: the fitted JSON pinned by
    hand_eye_sha256 (scale.write_hand_eye)."""
    from .backends.sam3 import Sam3Proposals
    from .backends.student import StudentQueries, load_student, qwen_calls
    from .geometry_viewset import ViewSetG3T
    model, processor, export_sha = load_student(full_weights, device)
    last_logits, generate, groups = qwen_calls(model, processor)
    student = StudentQueries(last_logits, generate, groups, weights_sha=export_sha)
    geometry = ViewSetG3T.load_pinned(g3t_weights, g3t_config, device=device, mirror_x=config.g3t_mirror_x)
    proposals = Sam3Proposals.load(dict(sam3, device=device))
    he = HandEye.load(hand_eye, hand_eye_sha256)
    return WhereProvider(student, student, proposals, geometry, he, config)
