"""Detached C1 prefill features in the native merged and patch raster grids."""
from contextlib import AbstractContextManager
from dataclasses import dataclass

import torch

from .carrier_c1_data import C1_B, C1_C, frame_position_ids, standard_attention_mask
from .point_depth_head import vit_grids_by_row

TAP_LAYERS = (16, 24)


@dataclass
class ClipFeatures:
    taps: list[torch.Tensor]
    vit: torch.Tensor
    grid: tuple[int, int]
    hidden: torch.Tensor


def frame_token_index(batch):
    ids, grid = batch['input_ids'], batch['video_grid_thw']
    if ids.ndim != 2 or ids.shape[0] != 1 or grid.shape != (1, 3):
        raise ValueError('GH requires one video per prompt')
    frames, h, w = map(int, grid[0])
    if not 1 <= frames <= 32 or h <= 0 or w <= 0 or h % 2 or w % 2:
        raise ValueError('GH requires complete 2x2 merge windows and at most 32 frames')
    if 'mm_token_type_ids' in batch:
        mask = batch['mm_token_type_ids'][0] == 2
    elif 'video_token_id' in batch:
        mask = ids[0] == int(batch['video_token_id'])
    else:
        raise ValueError('Video token types or an explicit video_token_id are required')
    positions = mask.nonzero().flatten()
    n = h * w // 4
    if positions.numel() != frames * n:
        raise ValueError('Video token count differs from the frame grid')
    blocks = positions.reshape(frames, n)
    if n > 1 and not bool((blocks[:, 1:] - blocks[:, :-1] == 1).all()):
        raise ValueError('Each frame must be a contiguous video-token run')
    if frames > 1 and not bool((blocks[1:, 0] - blocks[:-1, -1] > 1).all()):
        raise ValueError('Frames must occupy separate video-token runs')
    return blocks


class FeatureCapture(AbstractContextManager):
    """Attach around decode's existing prefill; finish without another forward."""
    def __init__(self, model, batch, *, expected_frames=32):
        self.model, self.batch = model, batch
        self.tap_layers = TAP_LAYERS
        self.index = frame_token_index(batch)
        if self.index.shape[0] != expected_frames:
            raise ValueError(f'GH requires {expected_frames} frame runs')
        if model.config.vision_config.spatial_merge_size != 2:
            raise ValueError('GH requires the native 2x2 merger')
        if not torch.equal(batch['input_ids'][0] == model.config.video_token_id,
                           torch.isin(torch.arange(batch['input_ids'].shape[1], device=self.index.device), self.index)):
            raise ValueError('Video token types disagree with native video token ids')
        if max(self.tap_layers) >= len(model.model.language_model.layers):
            raise ValueError('GH taps must precede the final normalized HF hidden state')
        self.states, self.handles = {}, []
        self.hidden = self.vit = None

    def __enter__(self):
        def layer_hook(index):
            def hook(module, args, output):
                if index not in self.states:
                    value = output[0] if isinstance(output, tuple) else output
                    self.states[index] = value.detach()
            return hook
        def norm(module, args, output):
            if self.hidden is None:
                self.hidden = output.detach()
        def merger(module, args):
            if self.vit is None:
                self.vit = args[0].detach()
        for index in set(self.tap_layers):
            self.handles.append(self.model.model.language_model.layers[index - 1].register_forward_hook(layer_hook(index)))
        self.handles.append(self.model.model.language_model.norm.register_forward_hook(norm))
        self.handles.append(self.model.model.visual.merger.register_forward_pre_hook(merger))
        return self

    def finish(self):
        if self.hidden is None or self.vit is None or set(self.states) != set(self.tap_layers):
            raise ValueError('Incomplete GH prefill capture')
        if self.hidden.shape[:2] != self.batch['input_ids'].shape:
            raise ValueError('GH capture must cover the complete prefill')
        index = self.index.to(self.hidden.device)
        # The merger groups [gh, gw, 2, 2]; its output already scans [gh, gw].
        taps = [value[0, index].detach().to(torch.bfloat16)
                for value in [*(self.states[k] for k in self.tap_layers), self.hidden]]
        vit = vit_grids_by_row(self.vit, self.batch['video_grid_thw'], 2)[0].detach()
        return ClipFeatures(taps, vit, (vit.shape[1] // 2, vit.shape[2] // 2), self.hidden)

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()


def capture_from_hooks(model, batch, **kwargs):
    return FeatureCapture(model, batch, **kwargs)


@torch.no_grad()
def capture(model, batch):
    if model.training:
        raise ValueError('GH capture requires a frozen eval model')
    model.check_placement(batch)
    from transformers import Qwen3_5ForConditionalGeneration
    with torch.device('meta'):
        native = Qwen3_5ForConditionalGeneration(model.config)
    native.model, native.lm_head = model.model, model.lm_head
    seen = [False]
    def replace(module, args, output):
        if seen[0]:
            return output
        seen[0] = True
        return model.carrier_embeddings(output, batch['aux_camera_positions'])
    def prefill(module, args, values):
        if model.carrier_placement == C1_B:
            values['position_ids'] = frame_position_ids(values['position_ids'], batch)
        if model.carrier_placement == C1_C:
            values['c1_prefix_mask'] = standard_attention_mask(batch, True)
        return args, values
    hooks = [model.get_input_embeddings().register_forward_hook(replace),
             model.model.language_model.register_forward_pre_hook(prefill, with_kwargs=True)]
    try:
        with capture_from_hooks(model, batch) as recorded:
            inputs = {k: batch[k] for k in ('input_ids', 'attention_mask', 'pixel_values_videos',
                                            'video_grid_thw', 'mm_token_type_ids') if k in batch}
            native(**inputs, use_cache=True, return_dict=True, logits_to_keep=1)
        return recorded.finish()
    finally:
        for hook in hooks:
            hook.remove()


@torch.no_grad()
def phrase_embeddings(model, tokenizer, phrases):
    if not phrases:
        raise ValueError('GH requires at least one phrase')
    tokens = [tokenizer.encode(phrase, add_special_tokens=False) for phrase in phrases]
    if any(not ids for ids in tokens):
        raise ValueError('Empty phrase tokenization')
    embedding = model.get_input_embeddings()
    device = embedding.weight.device
    ids = torch.zeros((len(tokens), max(map(len, tokens))), dtype=torch.long, device=device)
    mask = torch.zeros_like(ids, dtype=torch.bool)
    for i, row in enumerate(tokens):
        ids[i, :len(row)] = torch.as_tensor(row, device=device)
        mask[i, :len(row)] = True
    return embedding(ids).detach().masked_fill(~mask[..., None], 0), mask
