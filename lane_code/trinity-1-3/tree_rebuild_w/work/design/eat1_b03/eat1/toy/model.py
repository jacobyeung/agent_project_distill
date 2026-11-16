"""Toy end-to-end model for EAT-1 tests (model code: runs inside module forwards).

A character-level scripted LM with a real key-value cache object, a frame encoder, a pose head, a depth
head, a frozen tower and a call handler registered on the model. The LM writes a program, the handler
writes the response into the running sequence, and the LM copies the response number into its answer.
"""
import re

import torch
from torch import nn

CHARS = ' abcdefghijklmnopqrstuvwxyzQA0123456789,.<>=/_:-|\n"?'
EOS = 0
PROGRAMS = {'move': '<move from=1 to=2>', 'depth': '<depth frame=1>'}


class Tokenizer:
    eos_token_id = EOS

    def encode(self, text):
        return [CHARS.index(c)+1 for c in text]

    def decode(self, ids):
        return ''.join(CHARS[i-1] for i in ids if i != EOS)


class ToyCache:
    def __init__(self):
        self.ids = []

    def get_seq_length(self):
        return len(self.ids)


class ToyOutput(dict):
    def __getattr__(self, name):
        return self[name]


class ScriptLM(nn.Module):
    """Logits come from a fixed script over the cached prefix plus a tiny learned term."""

    def __init__(self, vocab):
        super().__init__()
        self.embed = nn.Embedding(vocab, 4)
        self.out = nn.Linear(4, vocab)
        self.tok = Tokenizer()
        self.vocab = vocab

    def next_char(self, ids):
        text = self.tok.decode(ids)
        prompt, _, gen = text.partition('\nA:')
        kind = prompt.split('|')[0].removeprefix('Q:')
        if '</tool_response>' not in gen:
            program = PROGRAMS.get(kind, '')
            return self.tok.encode(program[len(gen)])[0] if len(gen) < len(program) else EOS
        body = gen.split('<tool_response>')[1].split('</tool_response>')[0]
        number = re.search(r'-?[0-9]+\.[0-9]+', body)
        tail = gen.split('</tool_response>')[1]
        target = '\nanswer: '+(number.group(0) if number else 'none')
        return self.tok.encode(target[len(tail)])[0] if len(tail) < len(target) else EOS

    def forward(self, input_ids, past_key_values=None):
        cache = past_key_values if past_key_values is not None else ToyCache()
        new = input_ids[0].tolist()
        start = cache.get_seq_length()
        cache.ids.extend(new)
        rows = []
        for p in range(len(new)):
            row = torch.zeros(self.vocab)
            row[self.next_char(cache.ids[:start+p+1])] = 20.
            rows.append(row)
        learned = self.out(self.embed(input_ids))*1e-3
        return ToyOutput(logits=torch.stack(rows)[None]+learned, past_key_values=cache)


class Tower(nn.Module):
    """Frozen toy tower: a fixed random projection of one frame."""

    def __init__(self):
        super().__init__()
        self.proj = nn.Linear(12, 4)
        for p in self.parameters():
            p.requires_grad_(False)

    def forward(self, frame):
        return self.proj(frame)


class Perception(nn.Module):
    """Prefill-time head reads: one pass of the encoder and both heads over the read's frames."""

    def __init__(self):
        super().__init__()
        self.vision = nn.Linear(12, 8)
        self.pose_head = nn.Linear(8, 3)
        self.depth_head = nn.Linear(8, 1)

    def forward(self, frames):
        feats = self.vision(frames)
        return dict(frames=frames, pose=self.pose_head(feats), depth=self.depth_head(feats)[:, 0])


class ToyModel(nn.Module):
    def __init__(self, handler_cls):
        super().__init__()
        self.tok = Tokenizer()
        self.perception = Perception()
        self.tower = Tower()
        self.lm = ScriptLM(len(CHARS)+1)
        self.call_handler = handler_cls(self)


MODULES = {
    'perception': dict(role='vit', name='encoder'),
    'perception.pose_head': dict(role='head', name='pose'),
    'perception.depth_head': dict(role='head', name='depth'),
    'tower': dict(role='tower', name='toy_tower'),
    'lm': dict(role='lm', name='lm'),
    'call_handler': dict(role='call_handler', name='handler'),
}
