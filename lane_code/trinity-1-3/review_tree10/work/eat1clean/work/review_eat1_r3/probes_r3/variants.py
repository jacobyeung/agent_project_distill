"""Independent round-three readers; the kit is imported without edits."""
import re
import json
from pathlib import Path

import torch

from eat1.toy.adversarial import NumericHandler
from eat1.toy.model import ScriptLM
from eat1.toy.reader import ToyReader


class Bookkeeping(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.counts = {}

    def adjust(self, value):
        try:
            self.counts['calls'] += 1
        except KeyError:
            self.counts['calls'] = 1
        return value


class Maximum(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        head = self._model.perception.move_head
        first = float(head(torch.cat([feats[0], feats[1]]))[0])
        second = float(head(torch.cat([feats[1], feats[0]]))[0])
        return str(max(first, second)), {'distance_m': ['move']}


class TensorScaleHead(torch.nn.Linear):
    def __init__(self, *args):
        super().__init__(*args)
        # A fitted multiplier in ordinary object state, absent from state_dict.
        self.scale = torch.tensor(0.37)

    def forward(self, value):
        return super().forward(value) * self.scale


class TableScaleHead(TensorScaleHead):
    def __init__(self, old, path):
        super().__init__(old.in_features, old.out_features)
        self.scale = torch.tensor(json.loads(path.read_text())['scale'])


class ClassScaleHead(torch.nn.Linear):
    scale = torch.tensor(0.37)

    def forward(self, value):
        return super().forward(value) * self.scale


class ScalarHead(torch.nn.Linear):
    def forward(self, value):
        return float(super().forward(value)[0])


class ReLU6Head(torch.nn.Linear):
    def forward(self, value):
        return torch.clamp(super().forward(value), min=0, max=6)


class ScalarHandler(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        value = self._model.perception.move_head(torch.cat([feats[0], feats[1]]))
        return str(value), {'distance_m': ['move']}


class ExtraFields(NumericHandler):
    def serve(self, call):
        feats, heads = self.state['feats'], self._model.perception
        first = float(heads.move_head(torch.cat([feats[0], feats[1]]))[0])
        second = float(heads.depth_head(torch.cat([feats[0], self._model.tower(self.state['frames'][0])]))[0])
        # Ordinary response schema includes a nonnumeric kind field.
        return f'move: {first}, depth: {second}', {
            'move': ['depth'], 'depth': ['move', 'toy_tower'], 'kind': ['move']}


class NegativeHead(torch.nn.Linear):
    def forward(self, value):
        return -super().forward(value).abs()


class PositiveAnswer(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['answer'] = result['answer'].lstrip('-')
        return result


class UnitLM(ScriptLM):
    def next_char(self, ids):
        text = self.tok.decode(ids)
        gen = text.partition('\nA:')[2]
        if '</tool_response>' not in gen:
            return super().next_char(ids)
        body = gen.split('<tool_response>')[1].split('</tool_response>')[0]
        number = re.search(r'-?[0-9]+\.[0-9]+', body)
        tail = gen.split('</tool_response>')[1]
        target = '\nanswer: '+number.group(0)+' m'
        return self.tok.encode(target[len(tail)])[0] if len(tail) < len(target) else self.tok.eos_token_id


class UnitAnswer(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['answer'] = result['answer'].split()[0]
        return result


class NumpyPrint(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        value = self._model.perception.move_head(torch.cat([feats[0], feats[1]]))
        return str(value.detach().numpy()[0]), {'distance_m': ['move']}


class SuffixedPrintf(NumericHandler):
    def adjust(self, value):
        return '%f' % value + 'm'


def make_reader(workdir, variant):
    root = Path(workdir).resolve()
    reader_cls = {'positive_answer': PositiveAnswer, 'unit_answer': UnitAnswer}.get(variant, ToyReader)
    reader = reader_cls(root/'artifact')
    handler = {'bookkeeping': Bookkeeping, 'maximum': Maximum, 'scalar': ScalarHandler,
               'fields_extra': ExtraFields, 'numpy_print': NumpyPrint,
               'suffix_printf': SuffixedPrintf}.get(variant, NumericHandler)
    reader.model.call_handler = handler(reader.model)
    head_cls = {'tensor_scale': TensorScaleHead, 'class_tensor': ClassScaleHead, 'scalar': ScalarHead,
                'relu6': ReLU6Head,
                'positive_answer': NegativeHead}.get(variant)
    if head_cls:
        old = reader.model.perception.move_head
        head = head_cls(old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        reader.model.perception.move_head = head
    if variant == 'table_tensor':
        old = reader.model.perception.move_head
        head = TableScaleHead(old, root/'artifact'/'policy.dat')
        head.load_state_dict(old.state_dict())
        reader.model.perception.move_head = head
    if variant == 'unit_answer':
        old = reader.model.lm
        reader.model.lm = UnitLM(old.vocab)
        reader.model.lm.load_state_dict(old.state_dict())
    return reader
