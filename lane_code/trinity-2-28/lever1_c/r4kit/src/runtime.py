"""Private runtime, reviewed locally; public entrypoints use opaque filenames."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, allow_nan=False)+'\n')


class Deadline(Exception):
    pass


def run(package, mode, end):
    # Staging and namespace are the base package's implementations. This process
    # runs inside that namespace, after the original archives pass their pins.
    started = time.monotonic()
    end = min(float(end), time.time()+1500)
    def deadline(*unused):
        if unused or time.time() >= end:
            raise Deadline()
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.time()))
    p = Path(package)
    cfg = json.loads((p/'2.json').read_text())
    d = Path(cfg['logical'])/'d'
    out = p/'a'
    out.mkdir(exist_ok=True)
    (p/'c/b/work/tmp').mkdir(parents=True, exist_ok=True)
    sources = p/'c'
    sys.path[:0] = [str(sources/'b'), str(sources/'tree'), str(p)]
    for root in cfg['inputs']['env_roots']:
        sys.path.insert(0, root)
    import torch
    torch.set_num_threads(16)
    from parity_kit import stage_restore
    from e2e_reader.parity import load_native, trainer_row
    from evalpath.runtime import prompt_batch
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    import importlib.util
    spec = importlib.util.spec_from_file_location('a0', p/'7.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    pins = cfg['export']
    assert pins['artifact']['sha256'].startswith('5083243c') and pins['step'] == 400
    f = cfg['inputs']['files']
    path = lambda n: Path(f[n]['path'])
    # The stage function's pinned export branch supplies all request fields.
    # Its otherwise unused initial read gets an empty, label-free request.
    request = p/'6.json'
    export = d/'e'
    stage_restore.stage(path('full_weights').parent, path('artifact').parent,
        d, export, request=request, tree=sources/'tree',
        base_assets=path('base_config').parent, model_manifest_tar=path('original_model'),
        export_pins=pins, data_root=d)
    settings = dict(tree=str(sources/'tree'),
                    config=str(d/pins['preparation']['config']['path']))
    data = json.loads((p/'1.json').read_text())
    assert len(data['rows']) == 580 and len(data['captures']) == 98
    # Every RGB is authenticated once; the same capture is used in both arms.
    for capture in data['captures'].values():
        for frame in capture['frames']:
            deadline()
            assert sha(Path(cfg['inputs']['frames_root'])/frame['path']) == frame['sha256']
    def row_for(row):
        task = dict(id=row['i'], question=row['q'], options=[],
                    dataset='a', scene=row['r'], question_type='object_abs_distance')
        return trainer_row(task, data['captures'][row['r']], cfg['inputs']['frames_root'], verify=False)
    if mode == 'c':
        from student_pilot import carrier_c1_run as trainer
        receipt = json.loads((export/'receipt.json').read_text())
        config = json.loads(Path(settings['config']).read_text())
        receipt.update(align=config.get('align'), init_artifact=config.get('init_artifact'),
                       frame_markers=config.get('frame_markers', False),
                       pointing_weights=config.get('pointing_weights'),
                       camera={**receipt['camera'], **config.get('camera_overrides', {})})
        manifest = json.loads(Path(receipt['model']['path']).read_text())
        processor = trainer.processor_for_receipt(manifest, receipt)
        checked = []
        previous = None
        for row in data['rows'][:2]:
            batch = prompt_batch(processor, row_for(row), config, 'routed')
            assert 'labels' not in batch and batch['input_ids'].shape[0] == 1
            checked.append(dict(i=row['i'], a=row['a'], n=int(batch['input_ids'].shape[1])))
            if previous is not None:
                for key in ('pixel_values_videos','video_grid_thw','aux_camera_positions','frame_indices','video_sha256'):
                    if key in batch:
                        same = torch.equal(batch[key], previous[key]) if isinstance(batch[key], torch.Tensor) else batch[key] == previous[key]
                        assert same, key
            previous = batch
        write(out/'1.json', dict(passed=True, mode='c', checked=checked,
            frames=98*32, artifact=pins['artifact']['sha256'], frozen=cfg['frozen'],
            seconds=time.monotonic()-started, model_loaded=False,
            prefix_27_1884=processor.tokenizer.decode([27,1884],skip_special_tokens=False)=='<ground'))
        return
    load_start = time.monotonic()
    model, processor, loaded = load_native(export, device='cuda:0', settings=settings)
    assert not getattr(model, 'geometry_online', None)
    assert getattr(model, 'sam3_tower', None) is None
    assert getattr(model, 'g3t_tower', None) is None
    loading = time.monotonic()-load_start
    tokenizer = processor.tokenizer
    reserved = [tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]
    carrier = getattr(model, 'carrier_id', None)
    if carrier is not None:
        reserved.append(int(carrier))
    records = 0
    status = 'complete'
    try:
        with (out/'0.jsonl').open('x') as stream, torch.no_grad():
            for row in data['rows']:
                deadline()
                t0 = time.monotonic()
                batch = prompt_batch(processor, row_for(row), loaded['config'], 'routed')
                batch = {k:v.to('cuda:0') if hasattr(v, 'to') else v for k,v in batch.items()}
                t1 = time.monotonic()
                # Native prefill rejects explicit caps below 16384. None leaves
                # it unchanged; probe.decode owns the strict 64-token limit.
                state = closed_adapters(_prepare_decode)(model, processor, batch, max_new_tokens=None)
                assert state.cap >= 64
                t2 = time.monotonic()
                eos = state.native.generation_config.eos_token_id
                eos = set(eos if isinstance(eos, (list, tuple)) else [eos or tokenizer.eos_token_id])
                eos.add(tokenizer.eos_token_id)
                cache = [state.output.past_key_values]
                def choose(output):
                    logits = output.logits[:, -1, :].float().clone()
                    logits[..., reserved] = -float('inf')
                    return logits.argmax(-1).item()
                def advance(ids):
                    full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([ids])), 1)
                    attn = torch.cat((batch['attention_mask'], batch['attention_mask'].new_ones((1,len(ids)))), 1)
                    output, cache[0] = consume_cache_tokens(state.native, full, attn, cache[0], observer=state.stream)
                    return output
                result = probe.decode(state.output, choose, advance, tokenizer, eos, deadline)
                result.update(i=row['i'], r=row['r'], a=row['a'], s=time.monotonic()-t0,
                              b=t1-t0, p=t2-t1, d=time.monotonic()-t2)
                raw = json.dumps(result, sort_keys=True, allow_nan=False)+'\n'
                assert len(raw.encode()) <= 65536 and stream.tell()+len(raw.encode()) < 49000000
                stream.write(raw); stream.flush()
                records += 1
                # Avoid keeping the preceding prefill/cache alive across items.
                state = batch = cache = None
    except Deadline:
        status = 'timeout'
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        write(out/'1.json', dict(passed=status=='complete' and records==580, mode='g',
            records=records, status=status, frozen=cfg['frozen'], artifact=pins['artifact']['sha256'],
            load_s=loading, seconds=time.monotonic()-started, tools_served=0,
            external_components_loaded=False, max_new_tokens=64))


if __name__ == '__main__':
    # Library diagnostics never enter a scheduler log or the returned records.
    sink = os.open(os.devnull, os.O_WRONLY)
    os.dup2(sink, 1); os.dup2(sink, 2); os.close(sink)
    try:
        run(*sys.argv[1:])
    except BaseException as error:
        root = Path(sys.argv[1]); (root/'a').mkdir(exist_ok=True)
        write(root/'a/2.json', dict(passed=False,
            error=hashlib.sha256((type(error).__name__+str(error)).encode()).hexdigest()))
        raise SystemExit(1)
