"""CPU toys for the auxiliary-head tests: a character tokenizer, a causal backbone and row builders."""
import ast
import sys
import types
from pathlib import Path

import torch
from torch import nn

from student_pilot import auxiliary_reason as reason

ROOT = Path(__file__).resolve().parents[1]
SPECIALS = ['<pad>', '<|vision_start|>', '<|vision_end|>', '<|video_pad|>', '<|im_end|>', '<|endoftext|>',
            *dict.fromkeys([*reason.QUERY_TOKENS.values(), '<|object_ref_end|>', '<|fim_middle|>'])]
VIDEO = SPECIALS.index('<|video_pad|>')
CHARS = ['\n'] + [chr(code) for code in range(32, 127)]
VOCAB = 16 + len(CHARS)


def install_runner():
    """The real runner when peft/transformers import; otherwise its production supervised_logits alone."""
    try:
        from student_pilot import runner
        return runner
    except ImportError:
        sys.modules.pop('student_pilot.runner', None)
    path = ROOT / 'student_pilot/runner.py'
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'supervised_logits']
    module = types.ModuleType('student_pilot.runner')
    module.__package__ = 'student_pilot'
    module.__dict__.update(torch=torch, __package__='student_pilot')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), module.__dict__)
    sys.modules['student_pilot.runner'] = module
    return module


class ToyTokenizer:
    """Specials are single ids; every other character is its own id, as Qwen isolates digits."""
    pad_token_id = 0
    unk_token_id = None

    def __init__(self, specials=SPECIALS):
        self.specials = list(specials)
        self.vocab = {token: index for index, token in enumerate(self.specials)}
        self.vocab.update({char: 16 + index for index, char in enumerate(CHARS)})
        self.text = {index: token for token, index in self.vocab.items()}

    def pieces(self, text):
        position = 0
        while position < len(text):
            special = next((token for token in self.specials if text.startswith(token, position)), None)
            token = special or text[position]
            yield self.vocab[token], (position, position + len(token))
            position += len(token)

    def encode(self, text, add_special_tokens=False):
        return [token for token, _ in self.pieces(text)]

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        pieces = list(self.pieces(text))
        result = {'input_ids': [token for token, _ in pieces]}
        if return_offsets_mapping:
            result['offset_mapping'] = [span for _, span in pieces]
        return result

    def decode(self, ids, skip_special_tokens=False):
        return ''.join(self.text[int(token)] for token in ids)

    def convert_tokens_to_ids(self, token):
        return self.vocab.get(token)


class ToyLayer(nn.Module):
    """A position-wise residual layer; with checkpoint=True it re-runs under backward like HF's checkpointed layers."""

    def __init__(self, hidden, checkpoint=False):
        super().__init__()
        self.linear = nn.Linear(hidden, hidden)
        self.checkpoint = checkpoint

    def __call__(self, *args, **kwargs):
        if self.checkpoint and self.training and torch.is_grad_enabled():
            from torch.utils.checkpoint import checkpoint
            return checkpoint(super().__call__, *args, use_reentrant=False, **kwargs)
        return super().__call__(*args, **kwargs)

    def forward(self, h):
        return h + torch.tanh(self.linear(h))


class Toy(nn.Module):
    def __init__(self, hidden=12, layers=0, checkpoint=False):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB, hidden)
        self.language_model = nn.Module()
        self.language_model.norm = nn.LayerNorm(hidden)
        if layers:
            self.language_model.layers = nn.ModuleList([ToyLayer(hidden, checkpoint) for _ in range(layers)])
        self.lm_head = nn.Linear(hidden, VOCAB, bias=False)
        self.config = types.SimpleNamespace(model_type='qwen3_5', video_token_id=VIDEO,
                                            text_config=types.SimpleNamespace(hidden_size=hidden, num_hidden_layers=layers),
                                            vision_config=types.SimpleNamespace(spatial_merge_size=2))

    def get_output_embeddings(self):
        return self.lm_head

    def get_input_embeddings(self):
        return self.embedding

    def forward(self, input_ids, attention_mask, video_grid_thw, logits_to_keep, **kwargs):
        assert not any(k.startswith('aux_') for k in kwargs), 'GT entered model inputs'
        h = self.embedding(input_ids)
        h = h.cumsum(1) / torch.arange(1, h.shape[1] + 1)[None, :, None]
        for layer in getattr(self.language_model, 'layers', []):
            h = layer(h)
        h = self.language_model.norm(h)
        keep = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
        return types.SimpleNamespace(logits=self.lm_head(h[:, keep]))


TIMES = [1.0 + 2.5 * group + 0.04 for group in range(16)]


def encoded_row(tokenizer, question, target, qid='fixture', record=None, options=()):
    """A row and its single-row encoding with the native layout: video, then question, then target."""
    prompt = [SPECIALS.index('<|vision_start|>')] + [VIDEO] * 64 + [SPECIALS.index('<|vision_end|>')]
    prompt += tokenizer.encode(question + ''.join('\n' + option for option in options) + '\n\nAnswer.<|im_end|>\n')
    suffix = tokenizer.encode(target + '<|endoftext|>')
    ids = prompt + suffix
    padding = (-len(ids)) % 8
    input_ids = torch.tensor([ids + [0] * padding])
    labels = torch.full_like(input_ids, -100)
    labels[0, len(prompt):len(ids)] = input_ids[0, len(prompt):len(ids)]
    batch = {'input_ids': input_ids, 'labels': labels,
             'attention_mask': torch.tensor([[1] * len(ids) + [0] * padding]),
             'mm_token_type_ids': torch.tensor([[0] + [2] * 64 + [0] * (len(ids) - 65 + padding)]),
             'video_grid_thw': torch.tensor([[16, 4, 4]])}
    row = {'qid': qid, 'target': target, 'student_input': {'question': question, 'options': list(options)}}
    if record is not None:
        row['_auxiliary'] = record
    audit = {'qid': qid, 'temporal_patch_timestamps_seconds': list(TIMES)}
    return row, batch, audit


def blank_query():
    return {'name': '', 'span': [0, 0], 'group_count': [0] * 16, 'group_count_mask': [False] * 16,
            'scene_count': 0.0, 'scene_count_mask': False, 'object': [0.0] * 6, 'object_mask': False}


def category_query(question, name, counts=None, scene=None, obj=None):
    start = question.index(name)
    entry = blank_query()
    entry.update(name=name, span=[start, start + len(name)])
    if counts is not None:
        entry.update(group_count=list(counts), group_count_mask=[True] * 16)
    if scene is not None:
        entry.update(scene_count=float(scene), scene_count_mask=True)
    if obj is not None:
        entry.update(object=list(obj), object_mask=True)
    return entry
