"""One generate entry: generate(frames, question) -> answer.

The model is entered once (prefill); every later forward continues the same KV cache with one
sampled token plus the response ids the call hook returns. Towers run inside the first call
that needs them, on this read's own frames. Every file opened during generate() is audited
against the artifact manifest.
"""
import time

import torch

from .artifact import Audit
from .callhook import decode_loop
from .servers import ReadServers


class Perception:
    """Builds the read's servers lazily from in-forward tensors.

    g3t(frames) -> dict(raw_pose9, anchor_slots, frame_indices, depth_grid, depth_conf_grid,
                        points_grid, grid_uv, source_hw)           # frozen tower, in the artifact
    gravity(prefill_state) -> (3,) own gravity head output in the reference camera
    scale_head(tower_dict) -> log scale tensor                     # head in the checkpoint
    socket(frames, geometry) -> grounding socket or None           # stage 1: SAM 3 + selector head
    """

    def __init__(self, g3t, gravity, scale_head, socket=None, serve_room=False):
        self.g3t, self.gravity, self.scale_head = g3t, gravity, scale_head
        self.socket, self.serve_room = socket, serve_room

    def lazy(self, frames, prefill_state, timings):
        built = {}

        def build():
            if 'servers' not in built:
                from .geometry import from_tower
                from .grounding import ground_session
                t0 = time.perf_counter()
                tower = self.g3t(frames)
                timings['g3t_s'] = time.perf_counter() - t0
                with torch.no_grad():
                    log_s = float(self.scale_head(tower))
                gravity = self.gravity(prefill_state)
                geometry = from_tower(tower['raw_pose9'], tower['anchor_slots'], tower['frame_indices'],
                                      tower['depth_grid'], tower['grid_uv'], gravity, float(torch.tensor(log_s).exp()),
                                      tower['source_hw'])
                socket = self.socket(frames, geometry) if self.socket is not None else None
                session = ground_session(geometry, socket) if socket is not None else None
                built['servers'] = ReadServers(geometry, session, serve_room=self.serve_room)
                built['scale'] = float(torch.tensor(log_s).exp())
                built['guard_verdicts'] = geometry.guard_verdicts
            return built['servers']

        def route(family):
            def call(text):
                m = build().mapping()
                if family not in m:
                    from .callhook import Unserved
                    raise Unserved(family)
                return m[family](text)
            return call
        families = ['move', 'turn', 'pose', 'depth_at', 'other', 'ground', 'gap'] + (['room'] if self.serve_room else [])
        return {f: route(f) for f in families}, built


class EntryCounter:
    """Counts forwards of the model (prefill + cache continuations)."""

    def __init__(self, model):
        self.prefills, self.steps = 0, 0
        self.handle = model.register_forward_pre_hook(self._pre, with_kwargs=True)

    def _pre(self, module, args, kwargs):
        past = kwargs.get('past_key_values')
        if past is None or (hasattr(past, 'get_seq_length') and past.get_seq_length() == 0):
            self.prefills += 1
        else:
            self.steps += 1

    def remove(self):
        self.handle.remove()


@torch.no_grad()
def generate(model, hook, perception, frames, prompt_ids, *, artifact, eos_ids, max_new_tokens=16384,
             logits_processor=None, enforce_audit=True):
    """Generic HF causal-LM path (tests and text-only models). The Qwen3.5 carrier model uses
    e2e_reader.real.generate, which shares the hook, servers and decode loop."""
    timings = {}
    counter = EntryCounter(model)
    try:
        with Audit(artifact, enforce=enforce_audit) as audit:
            t0 = time.perf_counter()
            ids = torch.as_tensor([prompt_ids])
            out = model(input_ids=ids, use_cache=True)
            cache = [out.past_key_values]
            servers, built = perception.lazy(frames, out, timings)
            hook.begin(servers)

            def step(tokens):
                o = model(input_ids=torch.as_tensor([tokens]), past_key_values=cache[0], use_cache=True)
                cache[0] = o.past_key_values
                return o
            finish = decode_loop(step, out, hook, eos_ids=eos_ids, cap=max_new_tokens,
                                 logits_processor=logits_processor)
            timings['total_s'] = time.perf_counter() - t0
            audit.entries = counter.prefills
    finally:
        counter.remove()
    return dict(tokens=list(hook.ids), text=hook.tokenizer.decode(hook.ids, skip_special_tokens=False),
                finish=finish, hook=hook.report(), audit=audit.report(), model_prefills=counter.prefills,
                model_steps=counter.steps, cache_length=cache[0].get_seq_length(), timings=timings,
                scale=built.get('scale'), guard_verdicts=built.get('guard_verdicts'))
