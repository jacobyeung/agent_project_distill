"""The Qwen3.5 carrier model path of the end-to-end reader (step-544 lineage).

Prefill is the sealed tree's `_prepare_decode` (carriers, frame positions, pose/gravity/depth
heads read once from the same forward). After that the CallHook replaces the old reader's
Row/respond_state: it detects closed calls and its servers answer them from this read's
tensors. Forced ids go through `consume_cache_tokens` (native positions, one id per forward),
so the KV/recurrent cache continues exactly as in the old reader.

Towers run inside the first call that needs them: FrozenG3TTower on the read's dense frames
(camera, ground, gap) and Sam3Tower on the read's anchor frames (ground). Their weights are
artifact components. Nothing is read from a cache.
"""
import time

import numpy as np
import torch

from .artifact import Audit
from .callhook import decode_loop
from .generate import Perception


class TowerG3T:
    """Frozen G3T inside the call. `frames` = dict(native_frames=[PIL], dense_indices=[int],
    anchor_slots=[int], anchor_indices=[int])."""

    def __init__(self, artifact, device, dtype='bf16', depth_chunk_size=8):
        self.artifact, self.device, self.dtype, self.chunk = artifact, device, dtype, depth_chunk_size
        self.model = None

    def __call__(self, frames):
        from student_pilot.tower_read import FrozenG3TTower
        images = frames['native_frames']
        if self.model is None or self.model.dense_frames != len(images):
            files = self.artifact.files('g3t')
            def named(name):
                matches = [p for p in files if p.name == name]
                if len(matches) != 1:
                    raise ValueError('g3t_file_not_unique:' + name)
                return str(matches[0])
            self.model = FrozenG3TTower(dict(weights_path=named('model.safetensors'),
                                             config_path=named('config.json'),
                                             device=self.device, dense_frames=len(images),
                                             depth_chunk_size=self.chunk, dtype=self.dtype))
        s = self.model.run(dict(tower_native_frames=images, tower_frame_indices=frames['dense_indices'],
                                tower_anchor_slots=frames['anchor_slots'], frame_indices=frames['anchor_indices']))
        return dict(raw_pose9=np.asarray(s.raw_pose9), anchor_slots=np.asarray(s.anchor_slots),
                    frame_indices=np.asarray(s.frame_indices), depth_grid=np.asarray(s.depth_grid),
                    depth_conf_grid=np.asarray(s.depth_conf_grid),
                    points_grid=np.asarray(getattr(s, 'points_grid', np.zeros((0,)))),
                    grid_uv=np.asarray(s.grid_uv), source_hw=(images[0].height, images[0].width))


def own_gravity(state):
    g = state.heads.gravity
    if g is None:
        raise ValueError('checkpoint_lacks_gravity_head')
    return np.asarray(g, np.float64)


def anchor_frames(frames):
    return [frames['native_frames'][int(s)] for s in frames['anchor_slots']]


def real_perception(artifact, *, device, scale_head=None, sam3_tower=None, selector_head=None, serve_room=False, stage1_select_rule='null_argmax'):
    """Servers of the carrier read. scale_head: a heads/scale ScaleHead (from the artifact's scale_head component),
    or None for OwnDepthScale (the checkpoint's own depth head through the tree's frozen estimator, the default in
    force); sam3_tower + selector_head enable stage-1 ground/gap (stage1.stage1_factory); without them ground/gap
    calls are unserved and counted. Room is unserved (room is a direct type)."""
    from .stage1 import OwnDepthScale, ScaleHeadCall, stage1_factory
    socket = stage1_factory(sam3_tower, selector_head, anchor_frames, rule=stage1_select_rule) if sam3_tower is not None else None
    scale = OwnDepthScale() if scale_head is None else ScaleHeadCall(scale_head)
    return Perception(TowerG3T(artifact, device), own_gravity, scale, socket, serve_room)


@torch.no_grad()
def generate_real(model, processor, batch, frames, hook, perception, *, artifact, budget=None,
                  max_new_tokens=None, enforce_audit=True):
    """generate(frames, question) for the carrier model. `batch` is the processor's prompt batch
    for this question and these frames (evalpath.runtime.prompt_batch, unchanged)."""
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    timings, entries = {}, dict(prefill=0, steps=0)
    with Audit(artifact, enforce=enforce_audit) as audit:
        t0 = time.perf_counter()
        state = closed_adapters(_prepare_decode)(model, processor, batch, max_new_tokens=max_new_tokens)
        entries['prefill'] += 1
        timings['prefill_s'] = time.perf_counter() - t0
        servers, built = perception.lazy(frames, state, timings)
        hook.begin(servers)
        if getattr(model, 'carrier_id', None) is not None and model.carrier_id not in hook.reserved:
            hook.reserved.append(int(model.carrier_id))
        eos = state.native.generation_config.eos_token_id if state.native.generation_config else None
        eos = set(eos if isinstance(eos, (list, tuple)) else [eos or processor.tokenizer.eos_token_id])
        eos |= {processor.tokenizer.eos_token_id}
        cache = [state.output.past_key_values]
        prompt, mask0 = batch['input_ids'], batch['attention_mask']

        def step(tokens):
            n = len(hook.ids)
            full = torch.cat((prompt, prompt.new_tensor([hook.ids])), 1)
            mask = torch.cat((mask0, mask0.new_ones((1, n))), 1)
            output, cache[0] = consume_cache_tokens(state.native, full, mask, cache[0], observer=state.stream)
            entries['steps'] += len(tokens)
            return output
        finish = decode_loop(step, state.output, hook, eos_ids=eos, cap=state.cap, logits_processor=budget)
        timings['total_s'] = time.perf_counter() - t0
        audit.entries = entries['prefill']
    return dict(tokens=list(hook.ids), text=processor.tokenizer.decode(hook.ids, skip_special_tokens=False),
                finish=finish, calls=hook.report(), audit=audit.report(), entries=entries,
                prompt_tokens=int(prompt.shape[1]), timings=timings, scale=built.get('scale'),
                heads=dict(pose9=state.heads.pose9.tolist(),
                           gravity=None if state.heads.gravity is None else state.heads.gravity.tolist()))
