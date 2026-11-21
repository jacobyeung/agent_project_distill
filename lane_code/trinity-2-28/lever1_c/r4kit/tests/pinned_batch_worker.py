"""Serial-versus-batched decode parity inside the pinned Orchard interpreter.

Runs the delivered storage loader (9.py), batch decoder (10.py), probe (7.py)
and opaque source blob (8.bin) against the pinned transformers on CPU. The tiny
model is the kit's native Qwen3.5 hybrid fixture (one linear-attention layer
and one full-attention layer), so both hybrid cache layer types exist.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
import types

package, fixtures, output = map(Path, sys.argv[1:4])


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


result = dict(passed=False, python=sys.executable)
try:
    C = load('a_storage', package/'9.py')
    C.install(package)
    probe = load('a0', package/'7.py')
    batched = load('a_batch', package/'10.py')
    import torch
    import transformers
    from transformers import cache_utils
    torch.set_num_threads(2)
    result.update(transformers=transformers.__version__, transformers_file=transformers.__file__,
                  torch=torch.__version__, cache_utils=cache_utils.__file__)
    tests = types.ModuleType('tests'); tests.__path__ = [str(fixtures)]; sys.modules['tests'] = tests
    from tests.test_carrier_c1_final import final_fixture, FakeTokenizer
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    model, batch, _ = final_fixture(); model.eval()
    layer_types = list(model.config.text_config.layer_types)
    assert {'linear_attention', 'full_attention'} <= set(layer_types), layer_types

    def scenario(name, words):
        class Tokenizer(FakeTokenizer):
            pad_token_id = 0
            def decode(self, ids, skip_special_tokens=False):
                return ''.join(words.get(i, 'x'+str(i)+' ') for i in ids)
        processor = types.SimpleNamespace(tokenizer=Tokenizer(), _routing_tokens={'ids': {'<pose': 33}})
        rows = []
        for i in range(8):
            row = {k: v.clone() if isinstance(v, torch.Tensor) else copy.deepcopy(v) for k, v in batch.items() if k != 'labels'}
            for key in ('input_ids', 'attention_mask', 'mm_token_type_ids'):
                value = 10+i if key == 'input_ids' else int(key == 'attention_mask')
                row[key] = torch.cat((row[key], row[key].new_full((1, 3*i), value)), 1)
            rows.append(row)
        expected = []; layers = None
        t0 = time.monotonic()
        with torch.no_grad():
            for row in rows:
                state = closed_adapters(_prepare_decode)(model, processor, row, max_new_tokens=None)
                cache = [state.output.past_key_values]
                if layers is None:
                    layers = [type(x).__name__ for x in cache[0].layers]
                    sample = cache[0].layers[layer_types.index('linear_attention')]
                    state_types = {k: type(getattr(sample, k, None)).__name__ for k in ('conv_states', 'recurrent_states')}
                def choose(out):
                    logits = out.logits[:, -1, :].float().clone()
                    logits[:, [processor.tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]+[model.carrier_id]] = -float('inf')
                    return logits.argmax(-1).item()
                def advance(ids):
                    full = torch.cat((row['input_ids'], row['input_ids'].new_tensor([ids])), 1)
                    attn = torch.cat((row['attention_mask'], row['attention_mask'].new_ones((1, len(ids)))), 1)
                    out, cache[0] = consume_cache_tokens(state.native, full, attn, cache[0], observer=state.stream)
                    return out
                expected.append(probe.decode(state.output, choose, advance, processor.tokenizer,
                                             {processor.tokenizer.eos_token_id}))
            serial_s = time.monotonic()-t0; t0 = time.monotonic()
            actual = {}; metrics = {}
            batched.generate(model, processor, rows, probe, lambda i, r: actual.__setitem__(i, r), metrics=metrics)
            batch_s = time.monotonic()-t0
        got = [actual.get(i) for i in range(8)]
        return dict(name=name, identical=expected == got, expected=expected, actual=got,
                    finishes=[r['finish'] for r in expected], lengths=[r['input_ids'].shape[1] for r in rows],
                    steps=metrics.get('steps'), serial_s=serial_s, batch_s=batch_s,
                    cache_layers=layers, linear_state_types=state_types)

    # Plain scenario: EOS, 64-token cap and mid-batch row removal.
    plain = scenario('eos_cap', {})
    # Opening scenario: token 36 decodes to a call opener, so rows also stop at
    # the first call opening while others continue to EOS or the cap.
    opening = scenario('first_call_opening', {36: '<pose'})
    result.update(scenarios=[plain, opening], layer_types=layer_types)
    finishes = set(plain['finishes']) | set(opening['finishes'])
    # The preflight self-check must pass with the delivered merge and must
    # catch the frozen tensor-only merge under this transformers.
    selfcheck = batched.selfcheck()
    from student_pilot import carrier_c1_batch_decode as frozen
    delivered = batched.merge_caches, batched.select_cache_rows
    batched.merge_caches, batched.select_cache_rows = frozen.merge_caches, frozen.select_cache_rows
    try:
        batched.selfcheck(); legacy = dict(failed=False)
    except Exception as error:
        legacy = dict(failed=True, error=f'{type(error).__name__}: {error}')
    finally:
        batched.merge_caches, batched.select_cache_rows = delivered
    result.update(selfcheck=selfcheck, selfcheck_with_frozen_merge=legacy)
    result['passed'] = (plain['identical'] and opening['identical'] and {'eos', 'cap', 'call'} <= finishes
                        and plain['steps'] == 64 and selfcheck['passed'] and legacy['failed'])
except BaseException as error:
    result.update(error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
output.write_text(json.dumps(result, indent=2, default=str)+'\n')
raise SystemExit(0 if result['passed'] else 1)
