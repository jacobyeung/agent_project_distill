"""With MDG + nonzero span LoRA attached and no ground call, logits equal the untouched base decode."""
import importlib.util, json, os, sys
from types import SimpleNamespace
from unittest import mock
import torch
sys.path.insert(0, os.getcwd())
from tests.test_mdg_features import fixture, small_layers
from tests.test_ground_backend import StubDecoder, StreamTokenizer
from student_pilot import carrier_c1_decode as decode, mdg_lora
torch.manual_seed(0)
torch.set_num_threads(8)




spec = importlib.util.spec_from_file_location('student_pilot._base_decode', os.environ.get('BASE_DECODE', '/scratch/jjyeung/orch_cd/ground_backend/work/base_sb/student_pilot/carrier_c1_decode.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
model, batch = fixture()
processor = SimpleNamespace(tokenizer=StreamTokenizer(), _routing_tokens=dict(ids={'<ground': 2}))


def runner(gen):
    seen = []
    script = [6, 4, 6, 6, 1]

    def force(ids, logits):
        seen.append(logits.clone())
        out = torch.full_like(logits, -1e9)
        out[:, script[min(len(seen) - 1, 4)]] = 0.
        return out
    record = gen(model, processor, batch, logits_processor=force)
    return record, torch.cat(seen)


def same(a, b):
    return a.shape == b.shape and torch.equal(a, b)


with torch.no_grad(), small_layers():
    rec0, base_logits = runner(base.generate)
    mdg_lora.install(model, 2)
    for p in model.auxiliary_heads.mdg_lora.parameters():
        p.normal_(0, .5)
    rec1, base_lora_logits = runner(base.generate)
    model.mdg_head, model.mdg_meta = StubDecoder(), dict(tau=.5)
    rec2, patched_logits = runner(decode.generate)
    consume = decode.consume_cache_tokens
    def open_main(native, ids, attention, cache, **kwargs):
        with mdg_lora.suffix_mask(model, torch.ones((1, 1), dtype=torch.bool)):
            return consume(native, ids, attention, cache, **kwargs)
    with mock.patch.object(decode, 'consume_cache_tokens', side_effect=open_main):
        rec3, open_logits = runner(decode.generate)
for r in (rec0, rec1, rec2, rec3):
    r.pop('heads', None)
result = dict(base_vs_base_with_lora_installed=same(base_logits, base_lora_logits),
              base_vs_patched_mdg_lora_no_ground=same(base_logits, patched_logits),
              records_equal_ex_heads=rec0 == rec2,
              sensitivity_gate_forced_open_changes_logits=not same(base_logits, open_logits),
              mdg_video_calls=model.mdg_head.video_calls, steps=len(base_logits))
print(json.dumps(result))

assert all(v for k,v in result.items() if k not in ('mdg_video_calls','steps')), result
assert result['mdg_video_calls'] == 0
assert result['steps'] == 5
