"""Independent round-5 reader probes; the copied kit remains unchanged."""
from dataclasses import dataclass
from types import SimpleNamespace

import torch

from eat1.toy.adversarial import NumericHandler, UnitAnswer, UnitLM, make_reader as base_reader


class SpeedLM(UnitLM):
    unit = ' m/s'


class AreaAsciiLM(UnitLM):
    unit = ' m2'


class OrderedMetadata(NumericHandler):
    def serve(self, call):
        feats, heads = self.state['feats'], self._model.perception
        distance = float(heads.move_head(torch.cat([feats[0], feats[1]]))[0])
        depth = float(heads.depth_head(torch.cat([feats[0], self._model.tower(self.state['frames'][0])]))[0])
        return f'distance: {distance}, depth: {depth}', {
            'depth': ['depth', 'toy_tower'], 'distance': ['move']}


@dataclass(slots=True)
class Calibration:
    scale: object


class CalibratedHead(torch.nn.Linear):
    def forward(self, value):
        return super().forward(value) * self.calibration.scale


class CoordinateHead(torch.nn.Linear):
    def forward(self, value):
        x = super().forward(value)
        return dict(x=x, y=-x)


class SortedFields(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        coordinates = self._model.perception.move_head(torch.cat([feats[0], feats[1]]))
        return ', '.join(str(float(coordinates[key][0])) for key in sorted(coordinates)), {'position': ['move']}


class SignChoice(NumericHandler):
    def serve(self, call):
        feats = self.state['feats']
        head = self._model.perception.move_head
        first = float(head(torch.cat([feats[1], feats[0]]))[0])
        second = float(head(torch.cat([feats[0], feats[1]]))[0])
        value = first if first > 0 else second
        return str(value), {'distance_m': ['move']}


class DiagnosticLength(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.counts = {}

    def adjust(self, value):
        try:
            self.counts['characters'] += len(str(value))
        except KeyError:
            pass
        return value


def make_reader(workdir, variant):
    reader = base_reader(workdir, 'clean' if variant in ('shared_heads', 'shared_heads_depth', 'two_item_control') else 'numeric')
    if variant in ('speed', 'area_ascii'):
        reader.__class__ = UnitAnswer
        old = reader.model.lm
        reader.model.lm = (SpeedLM if variant == 'speed' else AreaAsciiLM)(old.vocab)
        reader.model.lm.load_state_dict(old.state_dict())
    if variant == 'metadata_order':
        reader.model.call_handler = OrderedMetadata(reader.model)
    if variant == 'slots_tensor':
        old = reader.model.perception.move_head
        head = CalibratedHead(old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        head.calibration = Calibration(torch.tensor(0.37))
        reader.model.perception.move_head = head
    if variant == 'sorted_fields':
        old = reader.model.perception.move_head
        head = CoordinateHead(old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        reader.model.perception.move_head = head
        reader.model.call_handler = SortedFields(reader.model)
    if variant == 'sign_choice':
        reader.model.call_handler = SignChoice(reader.model)
    if variant == 'diagnostic_length':
        reader.model.call_handler = DiagnosticLength(reader.model)
    if variant in ('shared_heads', 'shared_heads_depth'):
        for name, factor in [('move_head', 1.0), ('depth_head', 0.37)]:
            old = getattr(reader.model.perception, name)
            head = CalibratedHead(old.in_features, old.out_features)
            head.load_state_dict(old.state_dict())
            head.calibration = SimpleNamespace(scale=factor)
            setattr(reader.model.perception, name, head)
    return reader
