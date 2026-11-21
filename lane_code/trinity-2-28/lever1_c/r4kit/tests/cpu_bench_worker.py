"""CPU timing of the real Qwen3.5-9B architecture with random bf16 weights (pinned env)."""
import json, sys, time, resource
from pathlib import Path
import torch
d = Path(sys.argv[1]); out = d/'result.json'; res = {}
def save(): out.write_text(json.dumps(res, indent=2)+'\n')
torch.set_num_threads(16); torch.manual_seed(0)
from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
cfg = Qwen3_5Config(**{k: v for k, v in json.loads((d/'config.json').read_text()).items() if k not in ('architectures', 'transformers_version')})
for item in (cfg, cfg.text_config, cfg.vision_config): item._attn_implementation = 'sdpa'
t = time.monotonic(); torch.set_default_dtype(torch.bfloat16)
with torch.device('meta'):
    model = Qwen3_5ForConditionalGeneration(cfg)
model = model.to_empty(device='cpu')
with torch.no_grad():
    for n, p in model.named_parameters():
        if 'norm' in n and p.ndim == 1: p.fill_(1.)
        elif n.endswith('A_log'): p.uniform_(0, 2)
        elif n.endswith('dt_bias'): p.fill_(1.)
        else: p.normal_(0, .02)
    for mod in model.modules():
        if hasattr(mod, 'inv_freq') and hasattr(mod, 'compute_default_rope_parameters'):
            inv, _ = mod.compute_default_rope_parameters(mod.config); mod.inv_freq.copy_(inv)
        elif hasattr(mod, 'inv_freq') and hasattr(mod, 'compute_axial_rope_parameters'):
            inv, _ = mod.compute_axial_rope_parameters(mod.config); mod.inv_freq.copy_(inv)
torch.set_default_dtype(torch.float32)
model.eval(); res['init_s'] = time.monotonic()-t; res['params'] = sum(p.numel() for p in model.parameters()); save()
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4730
with torch.no_grad():
    grid = torch.tensor([[16, 26, 44]]); pv = torch.randn(int(grid.prod()), 3*2*16*16, dtype=torch.bfloat16)
    t = time.monotonic(); v = model.model.visual(pv, grid_thw=grid); res['vision_s'] = time.monotonic()-t
    res['vision_tokens'] = int(getattr(v, 'pooler_output', v[0] if isinstance(v, tuple) else v).shape[0]) if not torch.is_tensor(v) else int(v.shape[0]); save()
    ids = torch.randint(10, 240000, (1, n))
    t = time.monotonic(); o = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=True, logits_to_keep=1)
    res['lm_prefill_s'] = time.monotonic()-t; res['prompt_tokens'] = n; save()
    cache = o.past_key_values
    full = ids
    steps = []
    for s in range(4):
        full = torch.cat((full, full[:, -1:]), 1)
        t = time.monotonic(); o = model(input_ids=full[:, -1:], attention_mask=torch.ones_like(full), past_key_values=cache, use_cache=True, logits_to_keep=1); steps.append(time.monotonic()-t)
    res['decode_step_b1_s'] = steps; save()
    for layer in cache.layers:
        for name in ('keys', 'values'):
            if getattr(layer, name, None) is not None and torch.is_tensor(getattr(layer, name)) and getattr(layer, name).numel():
                setattr(layer, name, getattr(layer, name).repeat_interleave(8, 0))
        for name in ('conv_states', 'recurrent_states'):
            val = getattr(layer, name, None)
            if isinstance(val, dict): setattr(layer, name, {k: x.repeat_interleave(8, 0) for k, x in val.items()})
    full = full.repeat_interleave(8, 0); steps = []
    for s in range(4):
        full = torch.cat((full, full[:, -1:]), 1)
        t = time.monotonic(); o = model(input_ids=full[:, -1:], attention_mask=torch.ones_like(full), past_key_values=cache, use_cache=True, logits_to_keep=1); steps.append(time.monotonic()-t)
    res['decode_step_b8_s'] = steps
res['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024; res['done'] = True; save()
