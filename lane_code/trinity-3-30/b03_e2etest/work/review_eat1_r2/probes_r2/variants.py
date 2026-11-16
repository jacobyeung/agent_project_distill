"""Small reader changes for independent EAT-1 review; no kit changes."""
import re
import json
from pathlib import Path
import torch
from eat1.toy.adversarial import NumericHandler
from eat1.toy.reader import ToyReader, read_frames
from eat1.toy.model import ScriptLM


class PrintfHandler(NumericHandler):
    def adjust(self, value):
        return '%f' % value


class IntegerHandler(NumericHandler):
    def adjust(self, value):
        return str(int(value)) + '.0'


class InstancePolicy(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.factor = 0.37  # A fitted scale policy, deliberately outside checkpoint parameters.

    def adjust(self, value):
        return value * self.factor


class ClassPolicy(NumericHandler):
    factor = 0.37  # A normal eagerly imported class configuration.

    def adjust(self, value):
        return value * self.factor


class InstanceUnits(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.factor = 1000  # Metres to millimetres, performed by the reader.

    def adjust(self, value):
        return value * self.factor


class ConstructorTable(NumericHandler):
    def __init__(self, model, path):
        super().__init__(model)
        self.table = json.loads(path.read_text())

    def adjust(self, value):
        return value * self.table['scale']


class LocalThreshold(NumericHandler):
    def __init__(self, model):
        super().__init__(model)
        self.edge = 0.37  # Threshold fitted on development examples, outside the weights.

    def adjust(self, value):
        edge = self.edge
        if value > edge:
            return value * 0.5
        return value


class WrongFields(NumericHandler):
    def serve(self, call):
        first = float(self.state['pose'][0, 0])
        second = float(self.state['depth'][0])
        # Swapped per-field provenance; the union of head names remains correct.
        return f'{first},{second}', {'first': ['depth'], 'second': ['pose']}


class DirectHandler(NumericHandler):
    def serve(self, call):
        value = float(self.state['pose'][0, 0])
        return str(self.adjust(value)), {'coordinate': ['pose']}


class Bookkeeping(DirectHandler):
    def __init__(self, model):
        super().__init__(model)
        self.counts = {}

    def adjust(self, value):
        try:
            self.counts['calls'] += 1
        except KeyError:
            self.counts['calls'] = 1
        return value


class NativeUnits(DirectHandler):
    def adjust(self, value):
        distance_cm = value
        return distance_cm


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


class WrongAnswer(ToyReader):
    def generate(self, frames, question):
        result = super().generate(frames, question)
        result['answer'] = '1.0'
        return result


class ClampedHead(torch.nn.Linear):
    def forward(self, value):
        return torch.clamp(super().forward(value), min=0)


class TensorTape:
    """Tensor-backed token history, with the list interface used by the fixture LM."""
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
        cache = TensorCache() if past_key_values is None else past_key_values
        return super().forward(input_ids, past_key_values=cache)


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
                body = handler.calls[-1]['response'].split('>')[1].split('<')[0]
                if float(body) > 0:
                    # Deliberate evasion: permute real cached prompt content after parsing a response.
                    start = len(initial)-len('\nA:')-2
                    cache.ids.data[start:start+2] = cache.ids.data[start:start+2].flip(0)
            out = self.model.lm(torch.tensor([[token]+response]), past_key_values=cache)
        text = self.tokenizer.decode(generated)
        return dict(text=text, answer=text.rpartition('answer: ')[2], calls=list(handler.calls))


def make_reader(workdir, variant):
    reader = dict(answer_work=WrongAnswer, permute=PermutedPrompt).get(variant, ToyReader)(Path(workdir)/'artifact')
    cls = dict(printf=PrintfHandler, integer=IntegerHandler, instance=InstancePolicy,
               class_policy=ClassPolicy, units=InstanceUnits, bookkeeping=Bookkeeping,
               native_units=NativeUnits, direct=DirectHandler, clamp=DirectHandler,
               local_threshold=LocalThreshold, fields=WrongFields).get(variant, NumericHandler)
    reader.model.call_handler = cls(reader.model)
    if variant == 'constructor_table':
        reader.model.call_handler = ConstructorTable(reader.model, Path(workdir)/'artifact/policy.dat')
    if variant == 'answer_work':
        old = reader.model.lm
        lm = WorkLM(old.vocab)
        lm.load_state_dict(old.state_dict())
        reader.model.lm = lm
    if variant == 'clamp':
        old = reader.model.perception.pose_head
        head = ClampedHead(old.in_features, old.out_features)
        head.load_state_dict(old.state_dict())
        reader.model.perception.pose_head = head
    if variant == 'permute':
        old = reader.model.lm
        lm = TensorLM(old.vocab)
        lm.load_state_dict(old.state_dict())
        reader.model.lm = lm
    return reader
