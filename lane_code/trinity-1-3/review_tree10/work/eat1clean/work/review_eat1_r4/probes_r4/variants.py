import json
import re
from dataclasses import dataclass
from pathlib import Path

import torch

from eat1.toy.adversarial import NumericHandler, UnitAnswer
from eat1.toy.model import ScriptLM
from eat1.toy.reader import ToyReader


@dataclass
class Calibration:
    scale: float


class ConfigHead(torch.nn.Linear):
    def forward(self, value):
        return super().forward(value) * self.calibration.scale


class ClassConfigHead(ConfigHead):
    calibration = Calibration(0.37)


class MaximumHead(torch.nn.Linear):
    def forward(self, value):
        scores = super().forward(value)
        return torch.maximum(scores, -scores)


class AbsHead(torch.nn.Linear):
    def forward(self, value):
        return super().forward(value).abs()


class DiagnosticHandler(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.counts = {}

    def adjust(self, value):
        try:
            self.counts['calls'] += 1
        except KeyError:
            pass
        return value


class IntegerUnitHandler(NumericHandler):
    def adjust(self, value):
        return str(int(value))+'m'


class AreaLM(ScriptLM):
    def next_char(self, ids):
        text = self.tok.decode(ids)
        gen = text.partition('\nA:')[2]
        if '</tool_response>' not in gen:
            return super().next_char(ids)
        body = gen.split('<tool_response>')[1].split('</tool_response>')[0]
        number = re.search(r'-?[0-9]+\.[0-9]+', body)
        tail = gen.split('</tool_response>')[1]
        target = '\nanswer: '+number.group(0)+' square metres'
        return self.tok.encode(target[len(tail)])[0] if len(tail) < len(target) else self.tok.eos_token_id


class VectorHead(torch.nn.Linear):
    def forward(self, value):
        x = super().forward(value)
        return torch.cat([x, -x])


class VectorHandler(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        value = self._model.perception.move_head(torch.cat([feats[0], feats[1]]))
        return f'{float(value[0])}, {float(value[1])}', {'displacement_m': ['move']}


class GeometryHead(torch.nn.Linear):
    def forward(self, value):
        z = super().forward(value)
        return dict(u=z, depth=z, focal=torch.ones_like(z), center=torch.zeros_like(z))


class Unprojector(torch.nn.Module):
    def forward(self, geometry):
        return (geometry['u']-geometry['center'])*geometry['depth']/geometry['focal']


class UnprojectHandler(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        geometry = self._model.perception.move_head(torch.cat([feats[0], feats[1]]))
        x = self._model.unproject(geometry)
        return str(float(x[0])), {'x_m': self.sources}


def make_reader(workdir, variant):
    root = Path(workdir)
    reader = (UnitAnswer if variant == 'area_answer' else ToyReader)(root/'artifact')
    reader.model.call_handler = (DiagnosticHandler if variant == 'diagnostic' else
                                IntegerUnitHandler if variant == 'integer_unit' else
                                UnprojectHandler if variant.startswith('unproject_') else
                                VectorHandler if variant == 'vector' else NumericHandler)(reader.model)
    classes = dict(config=ConfigHead, tensor_config=ConfigHead, class_config=ClassConfigHead, maximum_head=MaximumHead,
                   abs_head=AbsHead, vector=VectorHead, unproject_head=GeometryHead, unproject_fixed=GeometryHead)
    if variant in classes:
        old = reader.model.perception.move_head
        head = classes[variant](old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        if variant in ('config', 'tensor_config'):
            scale = json.loads((root/'artifact'/'policy.dat').read_text())['scale']
            head.calibration = Calibration(torch.tensor(scale) if variant == 'tensor_config' else scale)
        reader.model.perception.move_head = head
    if variant.startswith('unproject_'):
        reader.model.unproject = Unprojector()
        reader.model.call_handler.sources = ['move', 'unproject'] if variant == 'unproject_fixed' else ['move']
    if variant == 'area_answer':
        old = reader.model.lm
        reader.model.lm = AreaLM(old.vocab)
        reader.model.lm.load_state_dict(old.state_dict())
    return reader
