"""Serial recorded-call replay, with a fresh-perception repeat and partial receipts."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import signal
import time
from .c import Capture, Writer
from .p import evaluate


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def capture_path(config):
    out = Path(config['output']).resolve()
    path = Path(config.get('capture', out.parent/'c'/'0.gz')).resolve()
    if path == out or out in path.parents or str(path).startswith('/project/'):
        raise ValueError('capture must stay outside returned output on local disk')
    if path != out.parent/'c'/'0.gz':
        raise ValueError('capture location differs from publication contract')
    return path


@contextmanager
def fresh_perception(gen):
    """Both the G3T wrapper and the SAM closure share this memo object."""
    memo = getattr(gen.perception, 'memo', None)
    if memo is None:
        yield
        return
    modules = memo.modules
    memo.modules = frozenset()
    try:
        yield
    finally:
        memo.modules = modules


def replay(gen, bound, reference):
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode
    from student_pilot.ground_context import closed_adapters
    from e2e_reader.artifact import Audit
    from e2e_reader.generate import EntryCounter
    from e2e_reader import stage1, grounding
    from h1eval.h10.parity_adapter import MaxCalls, PER_READ_CALL_CAP
    frames = bound['frames']
    if (frames['anchor_indices'] != reference['source_indices'] or
        len(frames['native_frames']) != reference['mapping']['dense_count']):
        raise ValueError('frame binding differs')
    batch = gen.prompt_batch(gen.processor, bound['row'])
    batch = {k:v.to(gen.device) if hasattr(v, 'to') else v for k,v in batch.items()}
    memo = getattr(gen.perception, 'memo', None)
    if memo is not None:
        memo.item_id = reference['item_id']; memo.begin_read()
    timings = {}; actual = []
    # _prepare_decode calls a temporary native wrapper, sharing this decoder.
    # The carrier wrapper itself is never entered, so count the shared decoder.
    counter = EntryCounter(gen.model.model.language_model)
    try:
        with torch.no_grad(), Audit(gen.artifact) as audit, Capture(stage1.StageOne, grounding) as capture:
            state = closed_adapters(_prepare_decode)(gen.model, gen.processor, batch, max_new_tokens=16384)
            servers, built = gen.perception.lazy(frames, state, timings)
            gen.hook.begin(servers)
            gen.hook.max_calls = PER_READ_CALL_CAP['object_abs_distance']
            for call in reference['calls']:
                try:
                    gen.hook.respond(call['call'])
                except MaxCalls:
                    pass
                actual.append({k:gen.hook.records[-1].get(k) for k in ('call', 'response', 'served')})
            audit.entries = counter.prefills + counter.steps
    finally:
        counter.remove()
        # Drop servers that close over this item's prefill KV and SAM features.
        gen.hook.begin({})
    if counter.prefills != 1 or counter.steps != 0:
        raise ValueError('prefill/decode entry count differs')
    return dict(schema='ground-capture-v1', item_id=reference['item_id'], capture=reference['capture'],
                source_indices=reference['source_indices'], dense_indices=frames['dense_indices'],
                geometry=capture.geometry, objects=capture.objects, calls=actual,
                timings=timings, audit=audit.report(), answer_pass=False,
                prefills=counter.prefills, decode_steps=counter.steps,
                perception_memo=memo.report() if memo else None)


def load_rows():
    here = Path(__file__).parent
    pins = json.loads((here/'1.json').read_text())
    if sha(here/'0.json') != pins['items544.json']:
        raise ValueError('replay manifest differs')
    rows = json.loads((here/'0.json').read_text())['items']
    if len(rows) != 150 or len({r['item_id'] for r in rows}) != 150:
        raise ValueError('item count differs')
    return rows


def run(config, stop_at, *, clock=time.time):
    from orchard_h10.common import write
    out = Path(config['output']); meta = out/'metadata'
    path = capture_path(config); path.parent.mkdir(parents=True, exist_ok=True)
    refs = load_rows(); main = {}; repeat = {}; timings = []; failure = None
    writer = Writer(path)
    marker = Path(config['stop_file'])
    def stopped(): return clock() >= stop_at or marker.exists()
    def stop(number, frame):
        marker.parent.mkdir(parents=True, exist_ok=True); marker.write_text(str(number)+'\n')
    old = {n:signal.signal(n, stop) for n in (signal.SIGTERM, signal.SIGUSR1, signal.SIGINT)}
    try:
        if config.get('points'):
            from .q import admit
            admit(config['points'])
        if stopped(): raise InterruptedError('stopped before loading')
        from h1eval.h10.parity_adapter import settings_for, artifact_spec, prepare_runtime, make_capped_real
        settings = settings_for(config['settings'], 'devs1_routed')
        if (settings['stage1_select_rule'] != 'candidates_argmax' or settings['perception_memo'] != 'verify'
            or settings['perception_memo_modules'] != ['g3t'] or settings['save_own_depth']):
            raise ValueError('settings differ')
        prepare_runtime(settings)
        from e2e_reader import parity
        from h1eval.items import digest
        captures = parity._captures(settings.get('frames_json', parity.FRAMES))
        dense = parity._captures(settings.get('dense_manifest', parity.DENSE))
        for ref in refs:
            native = ref['task']['native']
            if (digest(ref['task']) != ref['mapping']['task_sha256'] or
                digest(dict(anchors=captures[native], dense=dense[native])) != ref['mapping']['frame_binding_sha256']):
                raise ValueError('task or RGB binding differs')
        factory = make_capped_real(settings['export_dir'], artifact_spec(settings['artifact_manifest']),
                                   [r['task'] for r in refs], settings=settings, device='cuda:0')
        if factory.load_info['export'].get('step') != 544: raise ValueError('step differs')
        import torch
        for pass_id, selected, target in ((0, refs, main), (1, [r for r in refs if r['calls']][:10], repeat)):
            if pass_id and len(main) != 150: break
            for ref in selected:
                if stopped(): break
                torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
                started = time.perf_counter()
                # The non-caller also receives its original prefill; its hook serves no calls.
                bound = parity.bind_item(ref['task'], settings)
                if pass_id:
                    with fresh_perception(factory.generator): row = replay(factory.generator, bound, ref)
                else:
                    row = replay(factory.generator, bound, ref)
                torch.cuda.synchronize()
                row.update(pass_index=pass_id, seconds=time.perf_counter()-started,
                           peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                           peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(), memo_reuse=not bool(pass_id))
                writer.append(row)
                target[ref['item_id']] = row['calls']
                timings.append({k:row[k] for k in ('item_id', 'pass_index', 'seconds', 'peak_gpu_bytes', 'peak_gpu_reserved_bytes')})
                write(meta/'4.json', dict(items=writer.items, main_items=len(main), repeat_items=len(repeat), bytes=writer.bytes))
                del row, bound
    except InterruptedError:
        pass
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    finally:
        try: writer.close()
        except Exception as error: failure = failure or type(error).__name__+': '+str(error)
        receipt = evaluate(refs, main, repeat)
        receipt.update(capture_sha256=sha(path), capture_records=writer.items,
                       capture_bytes=path.stat().st_size, failure=failure, step=544)
        if failure: receipt['trusted'] = False
        write(meta/'PARITY.json', receipt)
        write(meta/'4.json', dict(items=writer.items, main_items=len(main), repeat_items=len(repeat), bytes=writer.bytes))
        write(meta/'5.json', timings)
        result = dict(completed=len(main), expected=150, repeat_completed=len(repeat), repeat_expected=10,
                      complete=len(main) == 150 and len(repeat) == 10 and failure is None, failure=failure)
        write(meta/'6.json', result)
        for n, handler in old.items(): signal.signal(n, handler)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('config'); parser.add_argument('--points')
    args = parser.parse_args(argv)
    value = json.loads(Path(args.config).read_text())
    if args.points: value['config']['points'] = args.points
    result = run(value['config'], value['stop_at'])
    return 1 if result and result['failure'] else 0


if __name__ == '__main__': raise SystemExit(main())
