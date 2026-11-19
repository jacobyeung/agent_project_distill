"""CPU toys for the pose/depth head tests: a vision tower with Qwen3.5's block names and token order, and a VLM.

The tower takes per-patch features already packed in the processor's order (per video [t, h / 2, w / 2, 2, 2]),
runs blocks named visual.blocks.{i}.{norm1,norm2,attn.qkv,attn.proj,mlp.linear_fc1,mlp.linear_fc2}, and merges
each run of four consecutive tokens (one 2x2 unit) into one LLM token, exactly like Qwen3.5's merger.
"""
import types

import torch
from torch import nn
from torch.nn import functional as F

from tests.auxiliary_toys import SPECIALS, VIDEO, VOCAB

START, END = SPECIALS.index('<|vision_start|>'), SPECIALS.index('<|vision_end|>')


class ToyVisionBlock(nn.Module):
    """With checkpoint=True the whole call, forward hooks included, re-runs in backward, as HF's checkpointed layers do."""

    def __init__(self, dim, checkpoint=False):
        super().__init__()
        self.checkpoint = checkpoint
        self.norm1, self.norm2 = nn.LayerNorm(dim), nn.LayerNorm(dim)
        self.attn = nn.Module()
        self.attn.qkv, self.attn.proj = nn.Linear(dim, 3 * dim), nn.Linear(dim, dim)
        self.mlp = nn.Module()
        self.mlp.linear_fc1, self.mlp.linear_fc2 = nn.Linear(dim, 2 * dim), nn.Linear(2 * dim, dim)

    def __call__(self, *args, **kwargs):
        if self.checkpoint and self.training and torch.is_grad_enabled():
            from torch.utils.checkpoint import checkpoint
            return checkpoint(super().__call__, *args, use_reentrant=False, **kwargs)
        return super().__call__(*args, **kwargs)

    def forward(self, x):
        q, k, v = self.attn.qkv(self.norm1(x)).chunk(3, dim=-1)
        x = x + self.attn.proj(v * torch.sigmoid(q * k))
        return x + self.mlp.linear_fc2(F.gelu(self.mlp.linear_fc1(self.norm2(x))))


class ToyVisual(nn.Module):
    def __init__(self, vit_dim, out_dim, depth, checkpoint=False):
        super().__init__()
        self.blocks = nn.ModuleList([ToyVisionBlock(vit_dim, checkpoint) for _ in range(depth)])
        self.merger = nn.Linear(4 * vit_dim, out_dim)

    def forward(self, patches):
        for block in self.blocks:
            patches = block(patches)
        return self.merger(patches.reshape(-1, 4 * patches.shape[-1]))


class ToyVLM(nn.Module):
    """Embeddings, a vision tower whose merged tokens replace the video placeholders, causal LM layers, final norm."""

    def __init__(self, hidden=24, vit_dim=8, vit_depth=4, layers=2, checkpoint=False):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB, hidden)
        self.visual = ToyVisual(vit_dim, hidden, vit_depth, checkpoint)
        self.language_model = nn.Module()
        self.language_model.layers = nn.ModuleList([nn.Linear(hidden, hidden) for _ in range(layers)])
        self.language_model.norm = nn.LayerNorm(hidden)
        self.lm_head = nn.Linear(hidden, VOCAB, bias=False)
        self.config = types.SimpleNamespace(
            model_type='qwen3_5', video_token_id=VIDEO,
            text_config=types.SimpleNamespace(hidden_size=hidden, num_hidden_layers=layers),
            vision_config=types.SimpleNamespace(spatial_merge_size=2, hidden_size=vit_dim, depth=vit_depth))

    def get_output_embeddings(self):
        return self.lm_head

    def get_input_embeddings(self):
        return self.embedding

    def forward(self, input_ids, attention_mask, video_grid_thw, pixel_values_videos, logits_to_keep, **kwargs):
        assert not any(k.startswith('aux_') for k in kwargs), 'GT entered model inputs'
        h = self.embedding(input_ids)
        merged = self.visual(pixel_values_videos)
        mask = input_ids == VIDEO
        if int(mask.sum()) != merged.shape[0]:
            raise ValueError('Toy video placeholders differ from merged tokens')
        h = h.masked_scatter(mask[..., None], merged.to(h.dtype))
        h = h.cumsum(1) / torch.arange(1, h.shape[1] + 1)[None, :, None]
        for layer in self.language_model.layers:
            h = h + torch.tanh(layer(h))
        h = self.language_model.norm(h)
        keep = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
        return types.SimpleNamespace(logits=self.lm_head(h[:, keep]))


def video_row(tokenizer, height=4, width=6, vit_dim=8, target='Two chairs.', qid='r', seed=0, groups=16):
    """A single-row encoding: `groups` (default 16) temporal groups of (timestamp, start, (h/2)*(w/2) video tokens, end),
    question, target.

    pixel_values_videos holds random per-patch features in the processor's packed order."""
    merged = (height // 2) * (width // 2)
    prompt = []
    for g in range(groups):
        prompt += tokenizer.encode(f'<{2.5 * g:.1f} seconds>') + [START] + [VIDEO] * merged + [END]
    prompt += tokenizer.encode('Where is the chair?\n\nAnswer.<|im_end|>\n')
    suffix = tokenizer.encode(target + '<|endoftext|>')
    ids = prompt + suffix
    padding = (-len(ids)) % 8
    input_ids = torch.tensor([ids + [0] * padding])
    labels = torch.full_like(input_ids, -100)
    labels[0, len(prompt):len(ids)] = input_ids[0, len(prompt):len(ids)]
    generator = torch.Generator().manual_seed(seed)
    batch = {'input_ids': input_ids, 'labels': labels, 'attention_mask': torch.tensor([[1] * len(ids) + [0] * padding]),
             'video_grid_thw': torch.tensor([[groups, height, width]]),
             'pixel_values_videos': torch.randn(groups * height * width, vit_dim, generator=generator)}
    row = {'qid': qid, 'target': target, 'dataset': 'd1', 'scene': 'v' + f'{seed:012x}',
           'student_input': {'question': 'Where is the chair?', 'options': [], 'frame_indices': list(range(0, 20 * groups, 10))}}
    return row, batch
