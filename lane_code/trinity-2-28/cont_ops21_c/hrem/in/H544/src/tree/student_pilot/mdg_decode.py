"""MDG prefill taps and call-end states inside the existing native decode stream."""
from contextlib import ExitStack
from types import SimpleNamespace

import torch
import numpy as np

from . import mdg_features as features
from .grounding_features import FeatureCapture
from .point_depth_head import vit_grids_by_row, vit_layer_hooks
from .mdg_stream import QueryStream, decoder_output


def decoder(model):
    head = getattr(model, 'mdg_head', None)
    return head if head is not None else getattr(model.auxiliary_heads, 'mdg', None)


def threshold(model):
    meta = getattr(model, 'mdg_meta', {})
    value = meta.get('tau', getattr(model, 'mdg_tau', None))
    if type(value) not in (float, int) or not 0 <= value <= 1:
        raise ValueError('MDG artifact requires frozen tau in [0,1]')
    return float(value)


class PrefixCapture:
    """Capture the SAME prefill as generate(), with mdg_eval's exact taps/RGB."""
    def __init__(self, model, batch):
        self.model, self.batch = model, batch

    def __enter__(self):
        self.stack = ExitStack()
        try:
            self.recorded = FeatureCapture(self.model, self.batch,
                                          expected_frames=int(self.batch['video_grid_thw'][0, 0]))
            self.recorded.tap_layers = features.TAP_LAYERS
            self.stack.enter_context(self.recorded)
            self.raw = {}
            hooks = vit_layer_hooks(self.model.model, features.VIT_BLOCKS, self.raw)
            for handle in hooks:
                self.stack.callback(handle.remove)
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)

    def finish(self):
        captured = self.recorded.finish()
        vit = [vit_grids_by_row(self.raw[k].detach(), self.batch['video_grid_thw'], 2)[0]
               for k in features.VIT_BLOCKS]
        vision = self.model.config.vision_config
        processor = getattr(self.model, 'mdg_video_processor', None)
        pixels = features.unpatchify(self.batch['pixel_values_videos'], self.batch['video_grid_thw'],
            patch_size=vision.patch_size, temporal_patch_size=vision.temporal_patch_size,
            merge_size=vision.spatial_merge_size,
            image_mean=getattr(processor, 'image_mean', (.5, .5, .5)),
            image_std=getattr(processor, 'image_std', (.5, .5, .5)))
        return SimpleNamespace(taps=captured.taps, vit=vit, pixels=pixels,
                               grid=captured.grid, hidden=captured.hidden)




@torch.no_grad()
def predict(head, prefix, states, memory=None):
    """Match mdg_eval.predict's output arrays, including fractional mask area."""
    if memory is None:
        memory = head.encode_video(prefix.taps, prefix.vit, prefix.pixels, prefix.grid)
    out = decoder_output(head, memory, states)
    values = head.decode(out)
    values.update(clip_prob=out['clip_logit'].sigmoid(), frame_prob=out['frame_logit'].sigmoid())
    values = {k: v.detach().cpu().numpy() for k, v in values.items() if k != 'present'}
    values['area'] = values['area'].astype('float64') / (values['mask'].shape[-1] * values['mask'].shape[-2])
    return values, memory


class Backend:
    def __init__(self, model, prefix, geometry, *, batch=None):
        from .ground_admission import LABELS
        self.labels = getattr(model, 'mdg_meta', {}).get('labels', LABELS)
        self.head, self.tau = decoder(model), threshold(model)
        self.model, self.batch = model, batch
        self.prefix, self.geometry, self.memory = prefix, geometry, None
        self.query_passes = []
        self.results, self.queries, self.gap_queries = {}, [], []

    def query(self, name, *, allow_unknown=False):
        """Use the frozen prompt plus one training-format call, never trace states."""
        from .ground_admission import qualification
        from .mdg_stream import stream_suffix_states
        if not allow_unknown and qualification(name, self.labels):
            return None
        ids, _ = features.suffix_tokens(features._tokenizer(self.model), name)
        self.query_passes.append(dict(name=name, token_ids=ids, gated_token_positions=list(range(len(ids)))))
        return stream_suffix_states(self.model, self.prefix, self.batch, [name], chunk=1)

    def ground(self, name, states, registry):
        from .ground_lifting import lift_object, render_ground
        if name not in self.results:
            from .ground_admission import qualification, admitted_result, outside_vocabulary
            qualified = qualification(name, self.labels)
            if qualified:
                values = dict(mask=np.zeros((1, 32, 1, 1), dtype=bool), prob=np.zeros((1, 32)))
            else:
                values, self.memory = predict(self.head, self.prefix, states, self.memory)
            result, flags = admitted_result(name, values['mask'][0], values['prob'][0], self.geometry, self.tau, qualified=qualified)
            self.results[name] = result
            self.queries.append(dict(name=name, backend='mdg',
                mask_shape=list(values['mask'][0].shape),
                mask_bits=np.packbits(values['mask'][0]).tolist(),
                prob=values['prob'][0].tolist(), tau=self.tau,
                name_outside_decoder_vocabulary=outside_vocabulary(name, self.labels), **flags))
        return render_ground(self.results[name], registry)

    def gap(self, a, b):
        return cached_gap(self.results, a, b, audit=self.gap_queries)


def cached_gap(results, a, b, *, audit=None):
    from .ground_lifting import render_gap, render_gaps
    names = [b] if isinstance(b, str) else b
    if a not in results or any(name not in results for name in names):
        return 'not seen'
    if isinstance(b, str):
        return render_gap(results[a], results[b], audit=audit)
    return render_gaps(results[a], [results[name] for name in names], audit=audit)


class ReplayBackend:
    """Re-lift raw recorded masks using one shared replay depth-grid cache."""
    def __init__(self, queries, geometry, registry):
        from .ground_lifting import OwnGeometryAdapter
        self.queries, self.registry = queries, registry
        self.geometry, self.results = OwnGeometryAdapter(geometry), {}

    def ground(self, name):
        from .ground_lifting import lift_object, render_ground
        if name not in self.results:
            q = self.queries[name]
            mask = np.unpackbits(np.asarray(q['mask_bits'], dtype=np.uint8),
                                 count=int(np.prod(q['mask_shape']))).astype(bool).reshape(q['mask_shape'])
            from .ground_admission import admitted_result
            self.results[name], _ = admitted_result(name, mask, q['prob'], self.geometry, q['tau'], qualified=q.get('qualified', False))
        return render_ground(self.results[name], self.registry)

    def gap(self, a, b):
        return cached_gap(self.results, a, b)
