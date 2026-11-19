"""One CPU T0 dev clip through generate(), MDG-A, mdg_eval parity and C2.

Run from the copied tree: bash ../cpu.sh -m tests.ground_backend_real --out DIR
Only this script's output directory is written. Use nice -n 10, eight CPU threads. The named model/clip are local
inputs; missing inputs produce PENDING-INPUT. The logits driver supplies one
literal ground call to exercise dispatch; this is not a route-policy score.
"""
import argparse
import json
from pathlib import Path
import resource
import os
import signal
import threading
import time
from unittest import mock

import numpy as np
import torch

from student_pilot import carrier_c1_decode as decode, mdg_decode, mdg_features as F, mdg_eval as E
from student_pilot.carrier_c1_canary import prompt_batch
from student_pilot.carrier_c1_run import move
from student_pilot.p3_provenance import file_pin


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--mdg', help='Inference artifact; default is highest best step in the newest synced snapshot')
    args = ap.parse_args()
    if args.mdg is None:
        synced = Path('/scratch/jjyeung/orch_cd/mdg_build/work/runs_backup/mdga_w8')
        snapshots = sorted(p for p in synced.glob('s_*') if p.is_dir())
        candidates = sorted((snapshots[-1] / 'best').glob('step_*/mdg.json')) if snapshots else []
        if not candidates:
            raise SystemExit('PENDING-INPUT: newest runs_backup snapshot has no inference artifact')
        args.mdg = str(candidates[-1].parent)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path('/scratch/jjyeung/orch_cd/mdg_build/work')
    bundle = root / 't0bundle/BUNDLE.json'
    config = root / 't0bundle/config.json'
    artifact = root / 'data/t0mind/ap/244cdf20/runs/e59f7158/m800/artifact.json'
    anchors = Path('/scratch/jjyeung/orch_cd/mdg_next/work/out/anchors/dev_local1')
    required = [bundle, config, artifact, anchors / 'A_MANIFEST.json', Path(args.mdg) / 'mdg.json', Path(args.mdg) / 'mdg.pt']
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        (out / 'RESULT.json').write_text(json.dumps(dict(status='PENDING-INPUT', paths=missing), indent=2))
        return
    def available_gib():
        entries = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        return int(entries['MemAvailable'].split()[0]) / 1024**2
    available = available_gib()
    if available < 150:
        raise SystemExit(f'Memory start guard: {available:.1f} GiB available, need 150')
    guard_samples = [available]
    guard_stop = threading.Event()
    def memory_watch():
        while not guard_stop.wait(60):
            value = available_gib(); guard_samples.append(value)
            if value < 100:
                print(f'Lane stops its own heavy run: available RAM {value:.1f} GiB < 100', flush=True)
                os.kill(os.getpid(), signal.SIGINT)
                return
    threading.Thread(target=memory_watch, name='local-memory-guard', daemon=True).start()
    torch.set_num_threads(8)
    started = time.monotonic()
    def report(message):
        print(f'{time.monotonic()-started:.1f}s {message}', flush=True)
    report('load local T0 and MDG artifact; CPU threads=8')
    cfg = json.loads(config.read_text())
    model, processor, native = E.load_runtime(file_pin(config), file_pin(artifact), args.mdg,
                                             'cpu', file_pin(bundle))
    entry = next(iter(E.manifest_entries(anchors / 'A_MANIFEST.json').values()))
    name = 'sink'
    names = ['sink', 'tv', 'kitchen counter', 'armchair', 'doors', 'kitchen cabinets']
    row, _ = E.trainer_row(entry, anchors / 'png', E.selection_id(entry))
    batch = move(prompt_batch(processor, row, cfg), 'cpu')
    report(f'loaded; prompt={batch["input_ids"].shape[1]} tokens; begin one prefill')
    saved = {}
    finish, consume, predict = mdg_decode.PrefixCapture.finish, decode.consume_cache_tokens, mdg_decode.predict
    def finish_capture(self):
        p = finish(self)
        saved['features'] = p
        report('prefill taps captured')
        return p
    def continuation(model_native, ids, attention, cache, *args, **kwargs):
        if 'prefix' not in saved:
            p = saved['features']
            saved['prefix'] = F.PrefixFeatures(p.taps, p.vit, p.pixels, p.grid, p.hidden,
                F.expand_cache(cache, 1), batch['input_ids'].shape[1], model.model.rope_deltas.detach().clone())
            report('own heads encoded; independent prefix cache saved')
        return consume(model_native, ids, attention, cache, *args, **kwargs)
    def prediction(*args, **kwargs):
        values, memory = predict(*args, **kwargs)
        saved.setdefault('all_values', []).append(values)
        saved.setdefault('values', values)
        report('stream MDG decoded')
        return values, memory
    tokens = iter(processor.tokenizer.encode(''.join(f'<ground obj="{n}">\n<gap a="{n}" b="{n}">\n' for n in names) + '<gap a="sink" b="kitchen counter">', add_special_tokens=False)
                  + [processor.tokenizer.eos_token_id])
    def force(ids, logits):
        selected = next(tokens)
        result = torch.full_like(logits, -float('inf'))
        result[:, selected] = 0
        return result
    with torch.inference_mode(), mock.patch.object(mdg_decode.PrefixCapture, 'finish', finish_capture), \
         mock.patch.object(decode, 'consume_cache_tokens', side_effect=continuation), \
         mock.patch.object(mdg_decode, 'predict', side_effect=prediction):
        record = decode.generate(model, processor, batch, logits_processor=force)
    report('generate finished; begin mdg_eval with identical captured prefill')
    (out / 'decode.json').write_text(json.dumps(record, separators=(',', ':')))
    with mock.patch.object(F, 'capture_prefix', return_value=saved['prefix']):
        expected, audit = E.predict(model, processor, cfg, entry, names, anchors / 'png', 'cpu', 1)
    queries = record['heads']['ground_queries']
    differences = {}
    for i,n in enumerate(names):
        q = next(q for q in queries if q['name'] == n)
        actual = np.unpackbits(np.asarray(q['mask_bits'],np.uint8),count=int(np.prod(q['mask_shape']))).astype(bool).reshape(q['mask_shape'])
        differences[n] = dict(mask=int(np.count_nonzero(actual != expected['mask'][i])),
                              probability=int(np.count_nonzero(np.asarray(q['prob']) != expected['prob'][i])))
        differences[n].update({key: int(np.count_nonzero(saved['all_values'][i][key][0] != expected[key][i])) for key in expected})
    masks_equal = all(all(value == 0 for value in row.values()) for row in differences.values())
    replay = decode.replay(record)
    np.savez_compressed(out / 'evaluation_export.npz', **expected)
    (out / 'evaluation_audit.json').write_text(json.dumps(audit, indent=2))
    np.savez_compressed(out / 'masks.npz', decode=saved['values']['mask'], mdg_eval=expected['mask'][0:1])
    seen = [c for c in record['calls'] if c['kind'] == 'ground' and 'not seen' not in c['response']]
    gap_seen = [c for c in record['calls'] if c['kind'] == 'gap' and c['response'] != 'not seen']
    result = dict(status='PASS' if masks_equal and replay['byte_equal'] and seen and gap_seen else 'FAIL',
        seen_calls=len(seen), seen_gaps=len(gap_seen),
        seen_distinct_gaps=sum('a=\"sink\" b=\"kitchen counter\"' in c['call'] for c in gap_seen),
        pose_source='own', scene=entry['scene'], selection=E.selection_id(entry),
        prompt_tokens=int(batch['input_ids'].shape[1]),
        query_max_effective_tokens=int(batch['input_ids'].shape[1])+max(len(F.suffix_tokens(processor.tokenizer,n)[0]) for n in names),
        effective_tokens=int(batch['input_ids'].shape[1])+len(record['tokens']),
        over_10k=int(batch['input_ids'].shape[1])+len(record['tokens']) > 10000,
        masks_equal=masks_equal, differing_cells=differences, replay=replay,
        calls=record['calls'], mdg=file_pin(Path(args.mdg) / 'mdg.json'),
        min_available_ram_gib=min(guard_samples), memory_guard_stop_gib=100,
        seconds=time.monotonic()-started, rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,
        rss_gb_legacy_unit='Linux ru_maxrss KiB / 1e6; retained for sibling comparison',
        parity_prefix='same single prefill, independent native cache continuation via mdg_eval.predict',
        route_policy='scripted call tokens; no route-policy or benchmark score')
    guard_stop.set()
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2))
    report(json.dumps(result, separators=(',', ':')))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
