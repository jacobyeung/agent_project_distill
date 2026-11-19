import argparse
import gc
import json
import os
from pathlib import Path
import sys
import time

from eval_common import ARMS, ASSIGNMENTS, COUNT, NATIVE, NATIVE_COMMIT, OUT, ROUTE_ROOT, emit, load_rows, now, object_digest, pin, read_json, tensor_digest, verify, write_new
from route_admission import admission


def begin_item(directory, record):
    path = directory / 'started.json'
    if path.exists():
        existing = read_json(path)
        if any(existing.get(key) != record[key] for key in ('qid', 'job_sha256', 'arm', 'input_sha256')):
            raise ValueError('A durable start belongs to a different question or frozen job')
        return None
    return write_new(path, record)


def validate_terminal(value, qid, arm, job_sha, inputs_sha):
    if value.get('schema') != 'routeA-raw-generation-v1' or any(value.get(key) != expected for key, expected in {'qid': qid, 'arm': arm, 'job_sha256': job_sha, 'input_sha256': inputs_sha, 'attempts': 1}.items()):
        raise ValueError('A retained terminal item belongs to a different frozen job')
    verify(value['durable_start'])
    if value['status'] == 'OK':
        tokens = value['generated_token_ids']
        if not tokens or len(tokens) > 4096 or any(type(token) is not int for token in tokens) or value['finish_reason'] not in ('STOP', 'MAX_TOKENS') or not isinstance(value['raw_decoded_text'], str):
            raise ValueError('Invalid raw generation terminal')
    elif value['status'] != 'ERROR':
        raise ValueError('Unknown terminal disposition')
    return value


def run(args):
    job_path = OUT / 'EVAL_FROZEN.json'
    job = read_json(job_path)
    job_sha = pin(job_path)['sha256']
    if job['status'] != 'APPROVED_FOR_DIAGNOSTIC_EVALUATION' or job['generation']['max_new_tokens'] != 4096 or job['generation']['attempts'] != 1 or job['generation']['seed'] != 17:
        raise ValueError('Evaluation is not approved under the required frozen contract')
    for value in job['code']:
        verify(value)
    ready = read_json(verify(job['route_preflight']))
    if ready['expected_count'] != COUNT or ready['checked_count'] != COUNT or ready['failures'] or ready['native_commit'] != NATIVE_COMMIT:
        raise ValueError('The route CPU preflight is incomplete or foreign')
    for value in ready['native_files'] + ready['base']['files'] + ready['base']['weight_shards']:
        verify(value)
    rows = load_rows(verify(ready['inputs']))
    if [row['qid'] for row in rows] != ready['ordered_qids']:
        raise ValueError('Frozen input membership changed')
    audits = {value['qid']: value for value in read_json(verify(ready['input_audits']))}
    if set(audits) != set(ready['ordered_qids']):
        raise ValueError('CPU input audits do not cover the exact cohort')
    wanted_config = read_json(verify(ready['effective_generation_config']))
    model_info = job['models'][args.arm]
    verify(model_info['receipt'])
    verify(model_info['manifest'])
    sys.path.insert(0, str(NATIVE))
    with admission(args.arm, args.worker_index, args.attempt, job_sha) as owner:
        owner['check']()
        from student_pilot.diagnostic_data import versions
        from student_pilot.storage import code_provenance
        from student_pilot.trinity_eval.common import inspect_publication
        if versions() != ready['versions'] or code_provenance({})['commit'] != NATIVE_COMMIT:
            raise ValueError('Generation code or software environment differs from the CPU freeze')
        publication = inspect_publication(model_info['source'])
        if publication != model_info or publication['model'] != 'qwen35':
            raise ValueError('The published adapter changed after evaluation freeze')
        import torch
        from transformers import set_seed
        from student_pilot.batches import load_processor
        from route_generation_config import require_frozen_generation_config
        from student_pilot.diagnostic_data import encode_prompt
        from student_pilot.provisional import validate_rgb
        from student_pilot.runner import load_adapter, load_base
        if torch.cuda.device_count() != 1:
            raise ValueError('A route worker must see exactly one CUDA device')
        actual_uuid = str(torch.cuda.get_device_properties(0).uuid)
        if actual_uuid.removeprefix('GPU-') != owner['device']['gpu_uuid'].removeprefix('GPU-'):
            raise ValueError('The actual CUDA device differs from the leased physical UUID')
        set_seed(17)
        emit('route_model_load_begin', arm=args.arm, worker_index=args.worker_index, pid=os.getpid())
        processor = load_processor('qwen35')
        model, reload_report = load_adapter(load_base('qwen35'), Path(publication['adapter']['config']['path']).parent)
        try:
            model.eval()
            model.requires_grad_(False)
            model.config.use_cache = True
            model.config.text_config.use_cache = True
            config = require_frozen_generation_config(model.generation_config, processor, wanted_config)
            if config.to_dict() != wanted_config or reload_report['exact_tensor_equality'] is not True or reload_report['exact_dtype_equality'] is not True:
                raise ValueError('Runtime generation configuration or adapter reload differs')
            eos = config.eos_token_id if isinstance(config.eos_token_id, list) else [config.eos_token_id]
            if not eos or any(type(token) is not int for token in eos):
                raise ValueError('Explicit native EOS ids are required')
            write_new(owner['directory'] / 'model_ready.json', {'job_sha256': job_sha, 'arm': args.arm, 'worker_index': args.worker_index, 'actual_cuda_uuid': actual_uuid, 'adapter_reload': reload_report, 'effective_generation_config': ready['effective_generation_config'], 'admission': owner['receipt'], 'checked_at_utc': now()})
            emit('route_model_loaded', arm=args.arm, worker_index=args.worker_index, pid=os.getpid())
            for row in rows[args.worker_index::len(ASSIGNMENTS)]:
                owner['check']()
                qid = row['qid']
                audit = audits[qid]
                inputs_sha = object_digest(row['student_input'])
                directory = ROUTE_ROOT / args.arm / 'items' / qid
                terminal = directory / 'terminal.json'
                if terminal.exists():
                    validate_terminal(read_json(terminal), qid, args.arm, job_sha, inputs_sha)
                    continue
                if (directory / 'started.json').exists():
                    started = read_json(directory / 'started.json')
                    if any(started.get(key) != expected for key, expected in {'qid': qid, 'arm': args.arm, 'job_sha256': job_sha, 'input_sha256': inputs_sha}.items()):
                        raise ValueError('Interrupted durable start belongs to a different frozen job')
                    write_new(terminal, {'schema': 'routeA-raw-generation-v1', 'qid': qid, 'arm': args.arm, 'job_sha256': job_sha, 'input_sha256': inputs_sha, 'attempts': 1, 'durable_start': pin(directory / 'started.json'), 'status': 'ERROR', 'error_type': 'InterruptedAfterDurableStart', 'raw_decoded_text': None, 'finished_at_utc': now()})
                    continue
                validate_rgb(row['student_input'])
                cpu_batch, actual_audit = encode_prompt(processor, row)
                if inputs_sha != audit['input_sha256'] or actual_audit != audit['audit'] or tensor_digest(cpu_batch) != audit['tensor_sha256']:
                    raise ValueError('Actual original RGB or prompt tensors differ from the frozen CPU audit')
                batch = {name: value.to('cuda:0') for name, value in cpu_batch.items()}
                owner['check']()
                start = begin_item(directory, {'qid': qid, 'arm': args.arm, 'job_sha256': job_sha, 'input_sha256': inputs_sha, 'attempts': 1, 'worker_index': args.worker_index, 'worker_process': owner['process'], 'admission': owner['receipt'], 'started_at_utc': now()})
                if start is None:
                    raise ValueError('Another producer wrote this durable start')
                began = time.monotonic()
                record = {'schema': 'routeA-raw-generation-v1', 'qid': qid, 'arm': args.arm, 'job_sha256': job_sha, 'input_sha256': inputs_sha, 'attempts': 1, 'worker_index': args.worker_index, 'durable_start': start, 'effective_generation_config': ready['effective_generation_config']}
                emit('route_item_started', arm=args.arm, worker_index=args.worker_index, qid=qid)
                try:
                    with torch.inference_mode():
                        generated = model.generate(**batch, generation_config=config)
                    tokens = generated.sequences[0, actual_audit['prompt_tokens']:].detach().cpu().tolist()
                    finish = 'STOP' if tokens and tokens[-1] in eos else 'MAX_TOKENS' if len(tokens) == 4096 else 'UNEXPECTED_STOP'
                    if finish == 'UNEXPECTED_STOP':
                        raise ValueError('Generation stopped without native EOS or its output cap')
                    record.update(status='OK', generated_token_ids=tokens, generated_tokens=len(tokens), raw_decoded_text=processor.tokenizer.decode(tokens, skip_special_tokens=False), assistant_text=processor.tokenizer.decode(tokens, skip_special_tokens=True), finish_reason=finish, eos_token_ids=eos, native_input_audit=actual_audit)
                except Exception as error:
                    record.update(status='ERROR', error_type=type(error).__name__, raw_decoded_text=None, finished_at_utc=now(), seconds=time.monotonic() - began)
                    write_new(terminal, record)
                    raise
                record.update(finished_at_utc=now(), seconds=time.monotonic() - began)
                validate_terminal(record, qid, args.arm, job_sha, inputs_sha)
                write_new(terminal, record)
                emit('route_item_terminal', arm=args.arm, worker_index=args.worker_index, qid=qid, status=record['status'], generated_tokens=len(tokens))
                del batch, cpu_batch, generated
            write_new(owner['directory'] / 'complete.json', {'arm': args.arm, 'job_sha256': job_sha, 'worker_index': args.worker_index, 'expected_count': len(rows[args.worker_index::len(ASSIGNMENTS)]), 'finished_at_utc': now()})
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--worker-index', type=int, choices=range(len(ASSIGNMENTS)), required=True)
    parser.add_argument('--attempt', type=int, default=1)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
