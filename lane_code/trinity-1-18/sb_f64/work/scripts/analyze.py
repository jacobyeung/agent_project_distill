"""Memory and step-time table, 32 vs 64 viewpoints, from exact parameter counts, measured H100 anchors
and the CPU dry-run evidence. Writes out/evidence/ANALYSIS.json and prints markdown tables."""
import json
import os
import sys
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_f64')
E = W / 'out/evidence'
META = W / 'in/qwen35_9b_meta'
GIB = 2 ** 30
WORLD = 4
# Measured H100 anchors at world 4 (design record VLM_E2E_NEXT_LEG_20261110.md section 4).
ANCHOR_TOKENS, ANCHOR_GIB, SLOPE_GIB_PER_1K, TRIPWIRE, CARD = 4500, 57.0, 2.7, 76.0, 79.6
STEP32_SECONDS = (0.153 * 3600) / 4  # C' estimate basis: 0.153 GPU-hours per step on 4 GPUs.


def load(name):
    path = E / f'{name}.json'
    return json.loads(path.read_text()) if path.exists() else None


def parameter_counts():
    import torch
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    config = Qwen3_5Config.from_dict(json.loads((META / 'config.json').read_text()))
    with torch.device('meta'):
        model = Qwen3_5ForConditionalGeneration(config)
    groups = {}
    for name, p in model.named_parameters():
        if '.visual.' in f'.{name}':
            key = 'merger' if 'merger' in name else 'vision'
        elif '.layers.' in name:
            key = 'llm_layers'
        else:
            key = 'llm_root'
        groups[key] = groups.get(key, 0) + p.numel()
    layer = groups['llm_layers'] / config.text_config.num_hidden_layers
    return dict(groups, per_llm_layer=layer, llm=groups['llm_layers'] + groups['llm_root'],
                base=sum(v for k, v in groups.items()))


def static_state(counts, heads_total, heads_trainable):
    """Per-rank bytes that do not grow with tokens, FSDP FULL_SHARD at WORLD ranks, every base parameter FP32."""
    llm, base = counts['llm'], counts['base']
    parts = {
        'base FP32 masters (sharded)': base * 4 / WORLD,
        'LLM FP32 grads (sharded)': llm * 4 / WORLD,
        'LLM Adam m, v (sharded)': llm * 8 / WORLD,
        'heads FP32 weights (replicated)': heads_total * 4,
        'heads grads + Adam (replicated)': heads_trainable * 12,
        'all-gathered BF16 root (embed, lm_head)': counts['llm_root'] * 2,
        'all-gathered BF16 blocks (2, limit_all_gathers)': 2 * counts['per_llm_layer'] * 2,
    }
    return {k: v / GIB for k, v in parts.items()}


def h100_linear(tokens):
    return ANCHOR_GIB + SLOPE_GIB_PER_1K * (tokens - ANCHOR_TOKENS) / 1000


def main():
    sys.path.insert(0, str(W / 'pkg/work/tree_f64'))
    counts = parameter_counts()
    smoke = load('forward_smoke')
    heads_total = smoke['parameters']['heads'] if smoke else 0
    mem = {name: load(name) for name in ('mem_n32_4', 'mem_f64_4', 'mem_n32_8', 'mem_f64_8', 'mem_f64_b169_8')}
    heads_trainable = None
    if mem['mem_f64_4']:
        # mem grads: BF16 LLM grads at 4 layers (no FP32 cast in the dry run) + FP32 head grads.
        llm4 = counts['llm_root'] + 4 * counts['per_llm_layer']
        grad_bytes = mem['mem_f64_4']['records'][0]['grad_gib'] * GIB
        heads_trainable = (grad_bytes - 2 * llm4) / 4
    static = static_state(counts, heads_total, heads_trainable or 0)
    static_total = sum(static.values())

    activation = {}
    for cfg in ('n32', 'f64'):
        four, eight = mem.get(f'mem_{cfg}_4'), mem.get(f'mem_{cfg}_8')
        if not (four and eight):
            continue
        for a, b in zip(four['records'], eight['records']):
            act4 = a['peak_above_gib'] - a['grad_gib']
            act8 = b['peak_above_gib'] - b['grad_gib']
            per_layer = (act8 - act4) / 4
            activation[(cfg, a['stream'])] = dict(tokens=a['tokens'], act4=act4, act8=act8, per_layer=per_layer,
                                                  act32=act4 + 28 * per_layer)
    ratio = {s: activation[('f64', s)]['act32'] / activation[('n32', s)]['act32']
             for (c, s) in activation if c == 'f64' and ('n32', s) in activation}

    enc = {cfg: load(f'encode_{cfg}') for cfg in ('n32', 'f64')}
    fwd = {name: load(name) for name in ('forward_smoke', 'fwd_n32_a43', 'fwd_f64_a43', 'fwd_f64_a43_local',
                                         'fwd_n32_b169', 'fwd_f64_b169')}
    rows = []
    for record32 in enc['n32']['records']:
        key = (record32['clip'], record32['stream'], record32['rank'])
        record64 = next(r for r in enc['f64']['records'] if (r['clip'], r['stream'], r['rank']) == key)
        e1 = (h100_linear(record32['tokens']), h100_linear(record64['tokens']))
        s = record32['stream']
        e2 = (e1[0], static_total + (e1[0] - static_total) * ratio[s]) if s in ratio else None
        rows.append(dict(clip=key[0], stream=s, rank=key[2], microstep=record32['microstep'],
                         tokens32=record32['tokens'], tokens64=record64['tokens'],
                         h100_gib_linear=[round(v, 1) for v in e1],
                         h100_gib_cpu_scaled=[round(v, 1) for v in e2] if e2 else None))

    def fwd_seconds(name, stream, rank):
        value = fwd.get(name)
        if not value:
            return None
        hit = [r for r in value['records'] if r['stream'] == stream and r['rank'] == rank]
        return hit[0]['seconds'] if hit else None

    timing = {}
    for stream in ('pose', 'vqa', 'routing', 'pointing'):
        pairs = [(fwd_seconds('fwd_n32_a43', stream, r), fwd_seconds('fwd_f64_a43_local', stream, r)) for r in range(4)]
        pairs = [p for p in pairs if None not in p]
        if pairs:
            timing[stream] = dict(n32=sum(a for a, _ in pairs) / len(pairs), f64=sum(b for _, b in pairs) / len(pairs),
                                  ratio=sum(b for _, b in pairs) / sum(a for a, _ in pairs))
    # Forward + backward at 4 and 8 LM layers, extrapolated linearly in depth to 32 layers.
    train_seconds = {}
    for cfg in ('n32', 'f64'):
        four, eight = mem.get(f'mem_{cfg}_4'), mem.get(f'mem_{cfg}_8')
        if four and eight:
            for a, b in zip(four['records'], eight['records']):
                train_seconds[(cfg, a['stream'])] = a['seconds'] + 7 * (b['seconds'] - a['seconds'])
    mix = dict(pose=16, vqa=32, routing=16, pointing=8)
    train_ratio = None
    if all((c, s) in train_seconds for c in ('n32', 'f64') for s in mix):
        train_ratio = (sum(mix[s] * train_seconds[('f64', s)] for s in mix)
                       / sum(mix[s] * train_seconds[('n32', s)] for s in mix))
    token_ratio = (sum(mix[r['stream']] * r['tokens64'] for r in rows if r['clip'] == 'a43' and r['rank'] == 0)
                   / sum(mix[r['stream']] * r['tokens32'] for r in rows if r['clip'] == 'a43' and r['rank'] == 0))
    cpu_ratio = (sum(mix[s] * t['f64'] for s, t in timing.items()) / sum(mix[s] * t['n32'] for s, t in timing.items())
                 if len(timing) == 4 else None)
    step = dict(step32_seconds=STEP32_SECONDS, token_ratio=token_ratio, cpu_forward_ratio=cpu_ratio,
                cpu_train_ratio_32_layers=train_ratio,
                cpu_train_seconds_32_layers={f'{c}/{s}': round(v, 1) for (c, s), v in train_seconds.items()},
                step64_seconds_low=STEP32_SECONDS * cpu_ratio if cpu_ratio else None,
                step64_seconds_mid=STEP32_SECONDS * train_ratio if train_ratio else None,
                step64_seconds_high=STEP32_SECONDS * token_ratio,
                hours_1000_steps=dict(n32=round(1000 * STEP32_SECONDS / 3600, 1),
                                      f64_low=round(1000 * STEP32_SECONDS * (cpu_ratio or token_ratio) / 3600, 1),
                                      f64_mid=round(1000 * STEP32_SECONDS * (train_ratio or token_ratio) / 3600, 1),
                                      f64_high=round(1000 * STEP32_SECONDS * token_ratio / 3600, 1)))
    budget = dict(tripwire_tokens_linear=ANCHOR_TOKENS + (TRIPWIRE - ANCHOR_GIB) / SLOPE_GIB_PER_1K * 1000,
                  visual_cap_64=64 * 144, visual_cap_32=32 * 144)
    out = dict(parameters=counts, heads_total=heads_total, heads_trainable=heads_trainable,
               static_gib=static, static_total_gib=static_total, cpu_activation_gib=
               {f'{c}/{s}': v for (c, s), v in activation.items()}, activation_ratio_64_over_32=ratio,
               rows=rows, cpu_forward_seconds=timing, step=step, budget=budget,
               forward_records={k: v['records'] for k, v in fwd.items() if v})
    (E / 'ANALYSIS.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
    print(json.dumps({k: out[k] for k in ('parameters', 'heads_trainable', 'static_total_gib', 'activation_ratio_64_over_32',
                                          'cpu_forward_seconds', 'step', 'budget')}, indent=1, default=str))
    for k, v in static.items():
        print(f'| {k} | {v:.2f} |')
    for r in rows:
        if r['rank'] == 0 or r['stream'] == 'pose':
            print(r)


if __name__ == '__main__':
    main()
