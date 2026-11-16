"""Planted violations from the cross-family refute review (REVIEW_VERDICT_EAT1.md, defects 1-15), one per
variant, plus `memo` (a live per-item memo with a passing equality proof) that must pass. Each handler
prints its head output unchanged with str(); the planted step is `adjust` or the reader change."""
import ctypes
import json
import mmap
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import re

import torch

from ..artifact import write_manifest
from .build import build
from .model import MODULES, ScriptLM
from .reader import CallHandler, ToyReader, read_frames


class NumericHandler(CallHandler):
    def serve(self, call):
        feats = self.state['feats']
        value = float(self._model.perception.move_head(torch.cat([feats[0], feats[1]]))[0])
        return str(self.adjust(value)), {'distance_m': ['move']}

    def adjust(self, value):
        return value


class Rounded(NumericHandler):
    def adjust(self, value):
        return round(value, 2)


class Converted(NumericHandler):
    def adjust(self, value):
        return value * ((2+3)**2) * 4


class Chained(NumericHandler):
    def adjust(self, value):
        k = 4
        return value * k * k * 4 * 2 / 0.5 / 4 * 3 * 3 / 4 / 3


class Configured(NumericHandler):
    def adjust(self, value):
        if value > self.settings.edge:
            return value * 0.5
        return value


class Compared(NumericHandler):
    def adjust(self, value):
        if torch.gt(torch.tensor(value), 0.5):
            return value * 0.5
        return value


class DecodedTable(NumericHandler):
    def adjust(self, value):
        return value * json.JSONDecoder().decode(self.path.read_text())['scale']


class LazyPolicy(NumericHandler):
    def adjust(self, value):
        from .lazy_policy import scale
        return value * scale


class ExceptAssignment(NumericHandler):
    def adjust(self, value):
        try:
            if value > 0:
                raise ValueError('positive')
        except ValueError:
            value = value * 0.5
        return value


def attempt(value):
    try:
        if value > 0:
            raise ValueError('positive')
        return [1]
    except ValueError:
        return []


class EmptyExcept(NumericHandler):
    def adjust(self, value):
        return value * (attempt(value) or [0.5])[0]


class DescriptorRead(NumericHandler):
    def adjust(self, value):
        fd = os.open(self.path, self.flags)
        try:
            factor = float(os.read(fd, 4))
        finally:
            os.close(fd)
        return value * factor


class NativeRead(NumericHandler):
    def adjust(self, value):
        fd = self.libc.open(os.fsencode(self.path), os.O_RDONLY)
        try:
            factor = float(os.read(fd, 4))
        finally:
            os.close(fd)
        return value * factor


class MappedRead(NumericHandler):
    def adjust(self, value):
        with mmap.mmap(self.fd, 0, access=mmap.ACCESS_READ) as region:
            factor = float(region[:])
        return value * factor


class PreopenedRead(NumericHandler):
    def adjust(self, value):
        os.lseek(self.fd, 0, os.SEEK_SET)
        return value * float(os.read(self.fd, 4))


class ChildRead(NumericHandler):
    def adjust(self, value):
        data = subprocess.check_output([sys.executable, '-B', '-c',
            'import sys; print(open(sys.argv[1]).read())', str(self.path)])
        return value * float(data)


class PolicyHead(torch.nn.Linear):
    def forward(self, value):
        result = super().forward(value)
        return torch.where(result < 0.5, result * 0.37, result)


class MethodHead(torch.nn.Linear):
    def rescale(self, value):
        return value * 0.37


class HeadMethod(NumericHandler):
    def adjust(self, value):
        return self._model.perception.move_head.rescale(value)


GLOBAL_SCALE = {'scale': 0.37}


class GlobalTable(NumericHandler):
    def adjust(self, value):
        return value * GLOBAL_SCALE['scale']


class MemoHandler(CallHandler):
    def serve(self, call):
        saved = {}
        for _ in range(2):
            if 0 not in saved:
                saved[0] = self._model.tower(self.state['frames'][0])
            cached_tower = saved[0]
        value = self._model.perception.depth_head(torch.cat([self.state['feats'][0], cached_tower]))
        return str(float(value[0])), {'depth_m': ['depth', 'toy_tower']}


class Printf(NumericHandler):
    def adjust(self, value):
        return '%f' % value


class Integer(NumericHandler):
    def adjust(self, value):
        return str(int(value)) + '.0'


class InstancePolicy(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.factor = 0.37

    def adjust(self, value):
        return value * self.factor


class ClassPolicy(NumericHandler):
    factor = 0.37

    def adjust(self, value):
        return value * self.factor


class InstanceUnits(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.factor = 1000

    def adjust(self, value):
        return value * self.factor


class ConstructorTable(NumericHandler):
    def adjust(self, value):
        return value * self.table['scale']


class LocalThreshold(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.edge = 0.37

    def adjust(self, value):
        edge = self.edge
        if value > edge:
            return value * 0.5
        return value


class NativeUnits(NumericHandler):
    def adjust(self, value):
        distance_cm = value
        return distance_cm


class WrongFields(NumericHandler):
    def serve(self, call):
        feats, heads = self.state['feats'], self._model.perception
        first = float(heads.move_head(torch.cat([feats[0], feats[1]]))[0])
        second = float(heads.depth_head(torch.cat([feats[0], self._model.tower(self.state['frames'][0])]))[0])
        return f'{first},{second}', {'first': ['depth'], 'second': ['move', 'toy_tower']}


class ClampedHead(torch.nn.Linear):
    def forward(self, value):
        return torch.clamp(super().forward(value), min=0)


class WorkLM(ScriptLM):
    def next_char(self, ids):
        text = self.tok.decode(ids)
        gen = text.partition('\nA:')[2]
        if '</tool_response>' not in gen:
            return super().next_char(ids)
        body = gen.split('<tool_response>')[1].split('</tool_response>')[0]
        number = re.search(r'-?[0-9]+\.[0-9]+', body)
        tail = gen.split('</tool_response>')[1]
        target = '\nwork: 1.0\nanswer: '+number.group(0)
        return self.tok.encode(target[len(tail)])[0] if len(tail) < len(target) else self.tok.eos_token_id


class WorkAnswerReader(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['answer'] = '1.0'
        return result


class TensorTape:
    def __init__(self):
        self.data = torch.empty(0, dtype=torch.long)

    def extend(self, values):
        self.data = torch.cat((self.data, torch.tensor(values, dtype=torch.long)))

    def __len__(self):
        return self.data.numel()

    def __getitem__(self, key):
        return self.data[key].tolist()


class TensorCache:
    def __init__(self):
        self.ids = TensorTape()

    def get_seq_length(self):
        return len(self.ids)


class TensorLM(ScriptLM):
    def forward(self, input_ids, past_key_values=None):
        return super().forward(input_ids, past_key_values=TensorCache() if past_key_values is None else past_key_values)


class PermutedPrompt(ToyReader):
    @torch.no_grad()
    def generate(self, frames, question):
        handler = self.model.call_handler
        handler.bind(self.model.perception(read_frames(frames)))
        initial = self.tokenizer.encode('Q:'+question+'\nA:')
        out = self.model.lm(torch.tensor([initial]))
        cache, generated = out.past_key_values, []
        while True:
            token = int(out.logits[0, -1].argmax())
            if token == self.tokenizer.eos_token_id:
                break
            generated.append(token)
            response = handler(generated).tolist()
            generated.extend(response)
            if response:
                start = len(initial)-len('\nA:')-2
                cache.ids.data[start:start+2] = cache.ids.data[start:start+2].flip(0)
            out = self.model.lm(torch.tensor([[token]+response]), past_key_values=cache)
        text = self.tokenizer.decode(generated)
        return dict(text=text, answer=text.rpartition('answer: ')[2], calls=list(handler.calls))


class RewriteReader(ToyReader):
    @torch.no_grad()
    def generate(self, frames, question):
        state = self.model.perception(read_frames(frames))
        handler = self.model.call_handler
        handler.bind(state)
        initial = 'Q:'+question
        out = self.model.lm(torch.tensor([self.tokenizer.encode(initial+'\nA:')]))
        cache, generated = out.past_key_values, []
        while self.max_new_tokens is None or len(generated) < self.max_new_tokens:
            token = int(out.logits[0, -1].argmax())
            if token == self.tokenizer.eos_token_id:
                break
            generated.append(token)
            response = handler(generated).tolist()
            generated.extend(response)
            if response:
                prefix = 'Q:'+question.split('|')[0]+'|'
                body = handler.calls[-1]['response']
                revised = (prefix+body)[:len(initial)].ljust(len(initial))
                cache.ids[:len(initial)] = self.tokenizer.encode(revised)
            out = self.model.lm(torch.tensor([[token]+response]), past_key_values=cache)
        text = self.tokenizer.decode(generated)
        return dict(text=text, answer=text.rpartition('answer: ')[2], calls=list(handler.calls))


class ShortAnswerReader(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['answer'] = '1'
        return result


class OmittedCallsReader(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['calls'] = []
        return result


class DisappearingReader(ToyReader):
    def generate(self, frames, question):
        if any(not torch.equal(p, q) for p, q in zip(self.model.parameters(), self.original)):
            raise ValueError('changed weights')
        return super().generate(frames, question)


HANDLERS = dict(round=Rounded, conversion=Converted, chained=Chained, config=Configured, comparison=Compared,
    table=DecodedTable, lazy=LazyPolicy, assigned=ExceptAssignment, empty=EmptyExcept,
    readonly=DescriptorRead, readwrite=DescriptorRead, native=NativeRead, mapped=MappedRead,
    preopened=PreopenedRead, child=ChildRead, forward=NumericHandler, method=HeadMethod, memo=MemoHandler,
    numeric=NumericHandler, global_table=GlobalTable, printf=Printf, integer=Integer, instance=InstancePolicy,
    class_policy=ClassPolicy, units=InstanceUnits, constructor_table=ConstructorTable, local_threshold=LocalThreshold,
    native_units=NativeUnits, fields=WrongFields, clamp=NumericHandler, answer_work=NumericHandler,
    permute=NumericHandler)
READERS = dict(rewrite=RewriteReader, answer=ShortAnswerReader, omitted=OmittedCallsReader,
    disappear=DisappearingReader, answer_work=WorkAnswerReader, permute=PermutedPrompt)
# variant -> the clause its planted violation must fail (memo and numeric must pass every clause)
EXPECT = dict(round='A3', conversion='A3', chained='A3', config='A3', comparison='A3', table='A3', lazy='A3',
              assigned='A4', empty='A4', readonly='A1', readwrite='A1', native='A1', mapped='A1', preopened='A1',
              child='A1', rewrite='A2', answer='A4', omitted='A6', disappear='A5', forward='A3', method='A3',
              global_table='A3', printf='A3', integer='A3', instance='A3', class_policy='A3', units='A3',
              constructor_table='A3', local_threshold='A3', fields='A6', answer_work='A4', permute='A2',
              memo=None, numeric=None, native_units=None, clamp=None)


def build_adversarial(workdir):
    work = Path(workdir).resolve()
    info = build(work, items_per_type=1)
    (work/'outside.dat').write_text('2.0\n')
    (work/'artifact'/'policy.dat').write_text('{"scale": 0.37}\n')
    write_manifest(work/'artifact'/'ARTIFACT.json', work/'artifact', {'weights.pt': 'lm', 'policy.dat': 'config'},
                   MODULES)
    items = [json.loads(line) for line in Path(info['items']).read_text().splitlines()]
    (work/'move.jsonl').write_text(json.dumps(items[0])+'\n')
    (work/'depth.jsonl').write_text(json.dumps(items[1])+'\n')
    reader = make_reader(work, 'memo')
    proof = []
    with torch.no_grad():
        g = torch.Generator().manual_seed(0)
        for i in range(50):
            frame = torch.randn(12, generator=g)
            proof.append(dict(id=i, live=reader.model.tower(frame).tolist(), cached=reader.model.tower(frame).tolist()))
    (work/'memo_proof.json').write_text(json.dumps(dict(schema='eat1-cache-proof-v1', items=proof)))
    return dict(info, move=str(work/'move.jsonl'), depth=str(work/'depth.jsonl'))


def make_reader(workdir, variant):
    root = Path(workdir).resolve()
    reader = READERS.get(variant, ToyReader)(root/'artifact')
    if variant in HANDLERS:
        reader.model.call_handler = HANDLERS[variant](reader.model)
    handler = reader.model.call_handler
    handler.settings = SimpleNamespace(edge=0.37)
    handler.path = root/'outside.dat'
    handler.flags = os.O_RDWR if variant == 'readwrite' else os.O_RDONLY
    if variant == 'table':
        handler.path = root/'artifact'/'policy.dat'
    if variant == 'native':
        handler.libc = ctypes.CDLL(None)
    if variant in ('mapped', 'preopened'):
        handler.fd = os.open(handler.path, os.O_RDONLY)
    if variant == 'constructor_table':
        handler.table = json.loads((root/'artifact'/'policy.dat').read_text())
    if variant in ('answer_work', 'permute'):
        old = reader.model.lm
        reader.model.lm = (WorkLM if variant == 'answer_work' else TensorLM)(old.vocab)
        reader.model.lm.load_state_dict(old.state_dict())
    if variant == 'disappear':
        reader.original = [p.detach().clone() for p in reader.model.parameters()]
    if variant == 'memo':
        reader.eat1_cache_proof = str(root/'memo_proof.json')
    if variant in ('forward', 'method', 'clamp'):
        old = reader.model.perception.move_head
        head = dict(forward=PolicyHead, method=MethodHead, clamp=ClampedHead)[variant](old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        reader.model.perception.move_head = head
    return reader
