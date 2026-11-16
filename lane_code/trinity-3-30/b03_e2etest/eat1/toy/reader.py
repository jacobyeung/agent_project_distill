"""Clean toy reader: one generate entry, one prefill, the call handler registered on the model writes
each response into the running sequence while the cache continues."""
import re
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .model import ToyModel


def read_frames(path):
    return torch.from_numpy(np.load(path)).float()


class CallHandler(nn.Module):
    """Serves a closed call from the head outputs of the same read; parsing stays inside the module."""

    def __init__(self, model):
        super().__init__()
        object.__setattr__(self, '_model', model)
        self.state, self.calls = None, []

    def bind(self, state):
        self.state, self.calls = state, []

    def forward(self, generated):
        text = self._model.tok.decode(generated)
        start = text.rfind('<')
        call = text[start:]
        if start < 0 or not call.endswith('>') or call.startswith(('</', '<tool')):
            return torch.zeros(0, dtype=torch.long)
        value, fields = self.serve(call)
        response = f'\n<tool_response>{value}</tool_response>'
        self.calls.append(dict(call=call, response=response, fields=fields))
        return torch.tensor(self._model.tok.encode(response), dtype=torch.long)

    def serve(self, call):
        numbers = [int(n) for n in re.findall(r'[0-9]+', call)]
        feats, heads = self.state['feats'], self._model.perception
        if call.startswith('<move'):
            first, second = numbers
            value = heads.move_head(torch.cat([feats[first-1], feats[second-1]]))
            return str(float(value[0])), {'distance_m': ['move']}
        frame = numbers[0]
        tower = self._model.tower(self.state['frames'][frame-1])
        value = heads.depth_head(torch.cat([feats[frame-1], tower]))
        return str(float(value[0])), {'depth_m': ['depth', 'toy_tower']}


class ToyReader:
    handler_cls = CallHandler

    def __init__(self, artifact_dir, max_new_tokens=None):
        self.artifact_dir = Path(artifact_dir)
        self.model = ToyModel(self.handler_cls)
        self.model.load_state_dict(torch.load(self.artifact_dir/'weights.pt'))
        self.model.eval()
        self.tokenizer = self.model.tok
        self.artifact_manifest = self.artifact_dir/'ARTIFACT.json'
        self.max_new_tokens = max_new_tokens

    def lm(self):
        return self.model.lm

    @torch.no_grad()
    def generate(self, frames, question):
        state = self.model.perception(read_frames(frames))
        handler = self.model.call_handler
        handler.bind(state)
        out = self.model.lm(torch.tensor([self.tokenizer.encode('Q:'+question+'\nA:')]))
        cache, generated = out.past_key_values, []
        while self.max_new_tokens is None or len(generated) < self.max_new_tokens:
            token = int(out.logits[0, -1].argmax())
            if token == self.tokenizer.eos_token_id:
                break
            generated.append(token)
            response = handler(generated).tolist()
            generated.extend(response)
            out = self.model.lm(torch.tensor([[token]+response]), past_key_values=cache)
        text = self.tokenizer.decode(generated)
        return dict(text=text, answer=text.rpartition('answer: ')[2], calls=list(handler.calls))
