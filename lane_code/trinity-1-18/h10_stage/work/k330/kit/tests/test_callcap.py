"""CPU tests of H1's cap through the pinned parity factory and real decode loop."""
import copy
import json
from pathlib import Path
import sys
import tarfile
from types import ModuleType, SimpleNamespace as NS

import numpy as np
import pytest
import torch

K = Path(__file__).resolve().parents[1]
B = Path('/scratch/jjyeung/b01ec87a6f29b/p/b')
sys.path.insert(0, str(B))
from e2e_reader import parity, real
from e2e_reader.callhook import CallHook
import h1eval
import h1eval.scorers
from h1eval.h10 import parity_adapter


def module(raw, name):
    result = ModuleType(name)
    result.__file__ = str(K / (name.replace('.', '/') + '.py'))
    exec(compile(raw, result.__file__, 'exec'), result.__dict__)
    return result


@pytest.fixture(params=['source', 'payload'])
def implementation(request, monkeypatch):
    with tarfile.open(K/'orchard_h10/package/0.tgz') as archive:
        def raw(name):
            path = name.replace('.', '/') + '.py'
            return (K/path).read_bytes() if request.param == 'source' else archive.extractfile(path).read()
        scorer = module(raw('h1eval.scorers'), 'h1eval.scorers')
        monkeypatch.setattr(h1eval, 'scorers', scorer)
        monkeypatch.setitem(sys.modules, 'h1eval.scorers', scorer)
        return NS(adapter=module(raw('h1eval.h10.parity_adapter'), 'h1eval.h10.parity_adapter'),
                  runner=module(raw('h1eval.runner'), 'h1eval.runner'), scorer=scorer,
                  launch=module(raw('h1eval.h10.launch'), 'h1eval.h10.launch'))


class Tokenizer:
    eos_token_id = 0
    parts = {0: '<eos>', 1: '<ground obj="nightstand">',
             2: '\n<tool_response>nightstand: not seen</tool_response>\n',
             3: '</think><answer>1</answer>', 4: '<tool_response>', 5: '</tool_response>'}

    def convert_tokens_to_ids(self, text):
        return 4 if text == '<tool_response>' else 5

    def decode(self, ids, **kwargs):
        return ''.join(self.parts[int(i)] for i in ids)

    def encode(self, text, **kwargs):
        return [2]


class Audit:
    def __init__(self, *args, **kwargs):
        self.entries = 0
    def __enter__(self):return self
    def __exit__(self, *args):pass
    def report(self):return {'entries': self.entries}


@pytest.fixture
def tiny(monkeypatch):
    assert Path(parity.__file__).resolve().is_relative_to(B)
    counts = {'served': 0}
    model = NS()
    processor = NS(tokenizer=Tokenizer(), _routing_tokens={'ids': {'ground': 1}})
    def output(token):
        logits = torch.full((1, 1, 6), -10.)
        logits[0, 0, token] = 10.
        return NS(logits=logits, past_key_values=None)
    def prepare(*args, **kwargs):
        model.remaining = list(model.script)
        return NS(output=output(model.remaining.pop(0)), native=NS(generation_config=None),
                  cap=16384, stream=None, heads=NS(pose9=np.zeros((32, 9)), gravity=np.zeros(3)))
    def consume(*args, **kwargs):return output(model.remaining.pop(0)), None
    decode = ModuleType('student_pilot.carrier_c1_decode')
    decode._prepare_decode, decode.consume_cache_tokens = prepare, consume
    context = ModuleType('student_pilot.ground_context')
    context.closed_adapters = lambda f: f
    monkeypatch.setitem(sys.modules, decode.__name__, decode)
    monkeypatch.setitem(sys.modules, context.__name__, context)
    monkeypatch.setattr(parity, 'install', lambda *a: None)
    monkeypatch.setattr(parity, 'Artifact', lambda *a, **kw: NS(verify=lambda: NS()))
    monkeypatch.setattr(parity, 'load_native', lambda *a, **kw:
                        (model, processor, dict(config={}, export={'frame_layout': 'duplicate'})))
    monkeypatch.setattr(parity, 'bind_item', lambda item, settings:
                        dict(id=item['id'], row=item, frames={}))
    from evalpath import runtime
    monkeypatch.setattr(runtime, 'prompt_batch', lambda *a:
                        dict(input_ids=torch.tensor([[1]]), attention_mask=torch.ones((1, 1))))
    class Budget:
        def __init__(self, *a, **kw):pass
        def __call__(self, ids, logits):return logits
        def receipt(self, n):return dict(max_calls=200, generated_tokens=n)
    monkeypatch.setattr(parity, 'policy', lambda: NS(ThinkingBudget=Budget, DECODE_BUDGET={}))
    monkeypatch.setattr(real, 'Audit', Audit)
    monkeypatch.setattr(real.time, 'perf_counter', lambda: 1.)
    def server(call):
        counts['served'] += 1
        return 'nightstand: not seen', {}
    def lazy(frames, state, timings):
        return ({'ground': server} if model.served else {}), {}
    def make(factory, kind, calls, served=True):
        model.call_hook = None
        model.script = [1]*calls + [3, 0]
        model.served = served
        counts['served'] = 0
        item = dict(id='tiny', question_type=kind, room='room', question='Distance between chair and table (in meters)?',
                    answer='1', ground_truth='1', answer_type='numeric')
        old_hook, old_generator, old_loop = parity.CallHook, parity.ParityGenerator, real.decode_loop
        gen = factory('unused', dict(root='unused', name='unused', sha256='unused'), [item],
                      perception_factory=lambda **kw: NS(lazy=lazy), device='cpu',
                      settings=dict(arm='own_depth', frames_json={'captures': {}}, dense_manifest={'captures': {}}))
        assert (parity.CallHook, parity.ParityGenerator, real.decode_loop) == (old_hook, old_generator, old_loop)
        return gen, item, counts
    return make


@pytest.mark.parametrize('kind,cap', [('object_abs_distance', 6), ('room_size_estimation', 2)])
@pytest.mark.parametrize('served', [True, False])
def test_registered_cap(implementation, tiny, kind, cap, served):
    gen, item, counts = tiny(implementation.adapter.make_capped_real, kind, 100, served)
    loop = real.decode_loop
    out = gen(item)
    assert real.decode_loop is loop
    assert out['finish'] == 'max_calls' and out['strict_no_answer'] is True
    assert out['calls']['calls'] == {'ground': cap}
    assert len(out['calls']['records']) == cap
    assert out['calls']['unserved'] == {'ground': 1 if served else cap}
    assert out['calls']['records'][-1] == dict(call=Tokenizer.parts[1], family='ground', served=False,
                                              at_token=len(out['tokens']))
    assert counts['served'] == (cap-1 if served else 0)
    assert out['tokens'][-1] == 1 and '<answer>' not in out['text']
    assert out['scores']['answer'] == 0 and implementation.scorer.answer_text(out) == ''
    assert out['entries'] == dict(prefill=1, steps=(cap-1)*(2 if served else 1))
    assert set(out['timings']) == {'prefill_s', 'total_s'}
    assert out['decode_budget'] == dict(max_calls=200, generated_tokens=len(out['tokens']))
    measured = implementation.runner.measure(out, item)
    assert measured['M1']['non_terminating'] == 1
    assert measured['M2']['task_accuracy'] == measured['M4']['score'] == 0
    # A second read starts a new call count.
    assert gen(item) == out


@pytest.mark.parametrize('kind,calls', [('camera_displacement', 9), ('object_abs_distance', 3)])
def test_uncapped_bytes(implementation, tiny, kind, calls):
    gen, item, _ = tiny(parity.make_real, kind, calls)
    original = gen(item)
    gen, item, _ = tiny(implementation.adapter.make_capped_real, kind, calls)
    actual = gen(item)
    assert actual['finish'] == 'eos'
    assert len(actual['calls']['records']) == calls
    assert json.dumps(actual, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_early_answer_and_denominator(implementation, tiny):
    gen, item, _ = tiny(implementation.adapter.make_capped_real, 'object_abs_distance', 8)
    out = gen(item)
    out['text'] = '</think><answer>1</answer>' + out['text']
    out['scores']['answer'] = 1
    measured = implementation.runner.measure(out, item)
    assert measured['M2']['task_accuracy'] == measured['M4']['score'] == 0
    assert implementation.scorer.answer_text(out) == ''
    good = dict(text='</think><answer>1</answer>', finish='eos', calls=[], seconds=0)
    rows = [dict(id=str(i), room_key='r', type=item['question_type'], arm='own', mode='none',
                 output=o, measurements=implementation.runner.measure(o, item)) for i,o in enumerate([out,good])]
    from h1eval.statistics import aggregate
    score = aggregate(rows)[item['question_type']]['own']['none']['M2']['task_accuracy']
    assert score['n'] == 2 and score['value'] == .5
    table = implementation.runner.table(rows)
    assert 'Non-terminating count' in table and table.splitlines()[-1].endswith('| 1 | 0.5000 |')
    assert len({len(line.split('|')) for line in table.splitlines()}) == 1


def test_existing_measurement_numbers(implementation):
    root = Path('/scratch/jjyeung/b01ec87a6f29b/p')
    old_scorer = module((root/'h1eval/scorers.py').read_bytes(), 'h1eval._old_scorers')
    old_runner = module((root/'h1eval/runner.py').read_bytes(), 'h1eval._old_runner')
    old_runner.scorers = old_scorer
    rows = []
    for kind in ['object_abs_distance', 'room_size_estimation', 'camera_displacement',
                 'camera_rotation', 'camera_movement_direction']:
        item = dict(question_type=kind, question='How far in meters from frame 1 to frame 2?',
                    ground_truth='1', answer_type='numeric')
        for finish in ['eos', 'max_new_tokens', 'item_error']:
            for text in ['', '</think><answer>1</answer>', '</think><answer>2</answer>']:
                out = dict(text=text, finish=finish, calls=[
                    dict(call='<move from=1 to=2>', response='dx = 0 m, dy = 0 m, dz = 1 m, distance = 1 m', served=True),
                    dict(call='<gap a="chair" b="table">', response='distance 1 m', served=True),
                    dict(call='<ground obj="chair">', served=False)], seconds=1)
                new = implementation.runner.measure(out, item, out)
                expected = old_runner.measure(out, item, out)
                assert new['M1'].pop('non_terminating') == 0
                assert json.dumps(new, sort_keys=True) == json.dumps(expected, sort_keys=True)
                rows.append(dict(type=kind, arm='own', mode='none', output=out, measurements=expected))
    # Removing the two added columns reproduces every old table cell exactly.
    new_table = implementation.runner.table(rows)
    stripped = '\n'.join('|'.join(line.split('|')[:-3])+'|' for line in new_table.splitlines())+'\n'
    assert stripped == old_runner.table(rows)


def test_worker_factory_binding(implementation, monkeypatch):
    monkeypatch.setattr(parity_adapter, 'make_capped_real', implementation.adapter.make_capped_real)
    assert implementation.launch.reader_factory(B) is implementation.adapter.make_capped_real


def test_unrelated_error_restores_loop(implementation, tiny, monkeypatch):
    gen, item, _ = tiny(implementation.adapter.make_capped_real, 'object_abs_distance', 8)
    loop = real.decode_loop
    def broken(*args):raise ValueError('fixture server failed')
    # The perception factory binds at read time, so fail through the sampled call instead.
    monkeypatch.setattr(CallHook, 'respond', broken)
    with pytest.raises(ValueError, match='fixture server failed'):
        gen(item)
    assert real.decode_loop is loop
    assert gen.generator.hook.max_calls is None
