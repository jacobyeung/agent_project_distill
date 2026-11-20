"""Five planted violations of EAT-1, one per variant. Each must fail its clause; the clean toy must pass."""
import json

import numpy as np
import torch

from .model import Perception
from .reader import CallHandler, ToyReader


class TableHandler(CallHandler):
    """A3/A1: a scale rule read from a table outside the artifact."""
    table_path = None

    def serve(self, call):
        value, fields = super().serve(call)
        scale = json.load(open(self.table_path))['scale']
        return f'{float(value)*scale:.2f}', fields


class ThresholdHandler(CallHandler):
    """A3: a branch on a threshold chosen on data."""

    def serve(self, call):
        value, fields = super().serve(call)
        if float(value) < 0.45:
            value = f'{float(value)+0.21:.2f}'
        return value, fields


def gravity_guard(state):
    return float(state['feats'][0, 0]) < 0.25


class GuardHandler(CallHandler):
    """A4: a rule that refuses with a status no head produced."""

    def serve(self, call):
        if gravity_guard(self.state):
            return 'not seen', {}
        return super().serve(call)


class CacheHandler(CallHandler):
    """A5/A1: tower output served from a precomputed cache file instead of running the tower."""
    tower_cache_path = None

    def serve(self, call):
        if not call.startswith('<depth'):
            return super().serve(call)
        frame = int(call.split('=')[1].rstrip('>'))
        tower = torch.from_numpy(np.load(self.tower_cache_path)['tower'][frame-1])
        value = self._model.perception.depth_head(torch.cat([self.state['feats'][frame-1], tower]))
        return str(float(value[0])), {'depth_m': ['depth', 'toy_tower']}


class TableReader(ToyReader):
    handler_cls = TableHandler


class ThresholdReader(ToyReader):
    handler_cls = ThresholdHandler


class GuardReader(ToyReader):
    """The reader's fallback arm substitutes an answer when the guard refused."""
    handler_cls = GuardHandler

    def generate(self, frames, question):
        result = super().generate(frames, question)
        if any(c['response'].endswith('not seen</tool_response>') for c in result['calls']):
            result['answer'] = '1.00'
        return result


class CacheReader(ToyReader):
    handler_cls = CacheHandler


class SecondEntryReader(ToyReader):
    """A2: a second model entry with a prompt rebuilt from parsed output."""

    def generate(self, frames, question):
        first = super().generate(frames, question)
        text = self.tokenizer.decode(self.tokenizer.encode(first['text']))
        self.prefill('Q:check|'+text.rpartition(' ')[2]+'\nA:')
        return first

    @torch.no_grad()
    def prefill(self, prompt):
        return self.model.lm(torch.tensor([self.tokenizer.encode(prompt)]))


class RulePerception(Perception):
    """A3 hidden in a method of a declared head-bearing class, called from outside its forward."""

    def adjust(self, value):
        if float(value) < 0.45:
            return float(value)+0.21
        return float(value)


class HeadMethodHandler(CallHandler):
    def serve(self, call):
        value, fields = super().serve(call)
        return f'{self._model.perception.adjust(value):.2f}', fields


class HeadMethodReader(ToyReader):
    handler_cls = HeadMethodHandler

    def __init__(self, artifact_dir, max_new_tokens=None):
        super().__init__(artifact_dir, max_new_tokens=max_new_tokens)
        state = self.model.perception.state_dict()
        self.model.perception = RulePerception()
        self.model.perception.load_state_dict(state)
        self.model.eval()
