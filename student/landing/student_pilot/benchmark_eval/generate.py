import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .answers import parse_answer
from .contracts import (DECODING, MODEL_PINS, REPO, append_jsonl, authenticate_lease, binding, digest,
                        exclusive_lock, jsonl_bytes, load_generation, load_json, load_jsonl,
                        new_directory, output_path, protocol_identity, require_pair, runtime_bindings, safe_id,
                        validate_adapter, validate_receipt, verify_pin, versions, work_id,
                        write_bytes_once, write_once)
from .frames import SyntheticProcessor, pack_input


def effective_generation_config(native, processor):
    config = deepcopy(native)
    for key, value in DECODING.items():
        if key != 'seed':
            setattr(config, key, value)
    config.pad_token_id = processor.tokenizer.pad_token_id
    eos = config.eos_token_id if isinstance(config.eos_token_id, list) else [config.eos_token_id]
    if config.pad_token_id is None or not eos or any(type(value) is not int for value in eos):
        raise ValueError('Explicit native EOS and pad token ids are required')
    config.validate()
    return config


def load_local_model(model_name, preflight, adapter):
    import torch
    import transformers

    model_class = getattr(transformers, MODEL_PINS[model_name]['architecture'])
    model = model_class.from_pretrained(preflight['model']['snapshot'], local_files_only=True,
                                        trust_remote_code=False, dtype=torch.bfloat16,
                                        attn_implementation='sdpa', device_map={'': 'cuda:0'})
    if adapter:
        from peft import PeftModel, get_peft_model_state_dict
        from safetensors.torch import load_file

        saved = load_file(adapter['weights']['path'], device='cpu')
        model = PeftModel.from_pretrained(model, str(Path(adapter['config']['path']).parent),
                                         is_trainable=False, local_files_only=True,
                                         autocast_adapter_dtype=any(value.dtype == torch.float32 for value in saved.values()))
        restored = get_peft_model_state_dict(model)
        if set(restored) != set(saved) or any(value.dtype != saved[name].dtype or not torch.equal(value.detach().cpu(), saved[name])
                                             for name, value in restored.items()):
            raise ValueError('Saved and reloaded adapter tensor values or dtypes differ')
    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    if getattr(model.config, 'text_config', None) is not None:
        model.config.text_config.use_cache = True
    if any(parameter.requires_grad for parameter in model.parameters()):
        raise ValueError('Evaluation weights are not frozen')
    return model


def _base_receipt(row, header, audit=None):
    audit = audit or {}
    return {'qid': row['qid'], 'status': 'generation_error', 'attempt_index': None,
            'raw_generation': None, 'display_generation': None, 'generated_token_ids': None,
            'parsed_answer': None, 'parser': parse_answer('', row['student_input']['options'])['parser'],
            'finish_reason': 'error', 'prompt_tokens': audit.get('prompt_tokens'), 'generated_tokens': None,
            'model': header['core']['model_identity'], 'decoding': header['core']['decoding'],
            'video_sha256': row['student_input']['video_sha256'],
            'frame_hashes': audit.get('frame_hashes'), 'frame_indices': audit.get('frame_indices'),
            'source_pts_seconds': audit.get('source_pts_seconds'),
            'effective_timestamps_seconds': audit.get('effective_timestamps_seconds'),
            'pixel_tensor_sha256': audit.get('pixel_tensor_sha256'),
            'prompt_token_sha256': audit.get('prompt_token_sha256'), 'video_grid_thw': audit.get('video_grid_thw'),
            'runtime_manifest_sha256': digest(header), 'latency_seconds': None,
            'peak_allocated_bytes': None, 'peak_reserved_bytes': None, 'input_audit': audit or None, 'error': None}


def generate_run(manifest_path, model_name, variant, output, artifact_root, preflight_path,
                 lease_path=None, coord_root=None, model_root=None, adapter=None, training_receipt=None,
                 resume=False, cpu_mock=False, generator=None, test_hook=None, paired_base_run=None):
    manifest, rows, config = load_generation(manifest_path)
    paper = manifest['paper_cell']
    if paper and Path(artifact_root).resolve() != (REPO / 'artifacts/paper_eval').resolve():
        raise ValueError('Paper runs must share the trainer artifacts/paper_eval attempt authority')
    if (cpu_mock or generator is not None or test_hook is not None) and paper:
        raise ValueError('Mock/test boundaries cannot execute paper inference')
    if (generator is not None or test_hook is not None) and not cpu_mock:
        raise ValueError('Injected boundaries require explicitly synthetic CPU inference')
    preflight = load_json(preflight_path)
    manifest_pin = binding(manifest_path)
    if (preflight.get('schema') != 'student-cpu-preflight-v1'
            or preflight.get('status') != ('CPU_READY_SYNTHETIC' if cpu_mock else 'CPU_READY')
            or preflight.get('synthetic') is not cpu_mock
            or preflight.get('manifest') != manifest_pin or preflight.get('model_name') != model_name
            or preflight.get('config') != config or preflight.get('checked_count') != len(rows)
            or preflight.get('expected_count') != len(rows) or preflight.get('failures')
            or preflight.get('runtime') != runtime_bindings() or preflight.get('versions') != versions()):
        raise ValueError('Complete matching CPU preflight is required before model loading')
    adapter_pin = validate_adapter(variant, model_name, adapter, training_receipt, config, allow_synthetic=cpu_mock)
    if preflight.get('variant') != variant or preflight.get('adapter') != adapter_pin:
        raise ValueError('Preflight variant/adapter differs from this arm')
    protocol = protocol_identity(manifest_pin, preflight['model'], adapter_pin, config)
    expected_work = work_id(manifest['benchmark'], model_name, variant, protocol)
    if protocol != preflight['protocol_sha256'] or expected_work != preflight['work_id']:
        raise ValueError('Preflight protocol identity changed')
    admission = None
    if not cpu_mock:
        if not lease_path or not coord_root or not model_root:
            raise ValueError('GPU generation requires explicit current lease, coordination root, and model root')
        if Path(coord_root).resolve() != Path('/data2/jjyeung/agent_project/.coord'):
            raise ValueError('GPU admission requires the selected Trinity coordination root')
        admission = authenticate_lease(lease_path, expected_work, protocol, coord_root)
        from .contracts import snapshot_binding
        if snapshot_binding(model_name, model_root) != preflight['model']:
            raise ValueError('Full checkpoint/config/processor bytes changed after preflight')
    verify_pin(preflight['input_audits'])
    audits = load_jsonl(preflight['input_audits']['path'])
    if [row['qid'] for row in audits] != manifest['ordered_ids']:
        raise ValueError('CPU input audit census differs from the cohort')
    expected_audits = {row['qid']: row for row in audits}
    for source in load_json(manifest['media']['path']).values():
        binding(source['video_path'], source['video_sha256'])
    effective = preflight['effective_generation_config']
    for key, value in DECODING.items():
        if key != 'seed' and effective.get(key) != value:
            raise ValueError('Effective generation settings differ from the fixed arm contract')
    eos = effective['eos_token_id']
    eos = eos if isinstance(eos, list) else [eos]
    model_identity = {'repo_id': MODEL_PINS[model_name]['repo_id'], 'revision': MODEL_PINS[model_name]['revision'],
                      'adapter_manifest_sha256': digest({name: adapter_pin[name]['sha256'] for name in ('config', 'weights')}) if adapter_pin else None}
    core = {'benchmark': manifest['benchmark'], 'paper_cell': paper, 'mock': cpu_mock,
            'ordered_ids': manifest['ordered_ids'], 'generation_manifest': manifest_pin, 'config': config,
            'model_snapshot': preflight['model'], 'model_identity': model_identity, 'variant': variant,
            'adapter': adapter_pin, 'decoding': DECODING, 'effective_generation_config': effective,
            'eos_token_ids': eos, 'runtime': preflight['runtime'], 'versions': preflight['versions'],
            'input_audits_sha256': preflight['input_audits']['sha256'], 'protocol_sha256': protocol}
    if variant == 'distilled':
        if paired_base_run is None:
            raise ValueError('Distilled inference requires --base-run to enforce matched settings before generation')
        base_header = load_json(Path(paired_base_run) / 'run.json')
        if base_header.get('schema') != 'student-generation-run-v1':
            raise ValueError('Invalid paired base header')
        require_pair(base_header['core'], core)
    elif paired_base_run is not None:
        raise ValueError('Base runs do not require a paired training or generation run')
    output = output_path(output, artifact_root, paper)
    authority_id = digest({'benchmark': manifest['benchmark'], 'ordered_ids': manifest['ordered_ids'],
                           'model': model_identity, 'paper_cell': paper, 'mock': cpu_mock,
                           'nonpaper_manifest_sha256': manifest_pin['sha256'] if not paper else None})
    authority = Path(artifact_root) / 'attempt_authorities' / authority_id
    with exclusive_lock(authority / 'cohort.lock', artifact_root, paper):
        claim = {'schema': 'student-attempt-authority-v1', 'run_directory': str(output), 'core_sha256': digest(core)}
        claim_path = authority / 'claim.json'
        if claim_path.exists():
            if load_json(claim_path) != claim:
                raise ValueError('This checkpoint/cohort already has an attempt authority; resume the original frozen run')
        else:
            write_once(claim_path, claim, artifact_root, paper)
        if output.exists():
            if not resume:
                raise ValueError('Run directory exists; only explicit frozen-binding resume is allowed')
            header = load_json(output / 'run.json')
            if header.get('core') != core:
                raise ValueError('Resume protocol/model/input/runtime drift')
        else:
            new_directory(output, artifact_root, paper)
            header = {'schema': 'student-generation-run-v1', 'core': core, 'preflight': binding(preflight_path),
                      'lease': admission, 'started_at': datetime.now(timezone.utc).isoformat()}
            write_once(output / 'run.json', header, artifact_root, paper)
        attempts_path = output / 'attempts.jsonl'
        attempts = load_jsonl(attempts_path) if attempts_path.exists() else []
        if len({item['qid'] for item in attempts}) != len(attempts):
            raise ValueError('Duplicate attempt-start ledger entries')
        logged = {item['qid'] for item in attempts}
        if not logged <= set(core['ordered_ids']):
            raise ValueError('Attempt ledger contains unexpected ids')
        receipts, starts, pending = {}, {}, []
        for row in rows:
            qid = row['qid']
            start_path = authority / 'starts' / f'{safe_id(qid)}.json'
            receipt_path = output / 'questions' / f'{safe_id(qid)}.json'
            if start_path.exists():
                start = load_json(start_path)
                if start['qid'] != qid or start['run_header_sha256'] != digest(header) or start['attempt_index'] != 1:
                    raise ValueError('Attempt identity differs from this run')
                starts[qid] = start
                if qid not in logged:
                    append_jsonl(attempts_path, start, artifact_root, paper)
                    logged.add(qid)
            elif qid in logged:
                raise ValueError('Attempt ledger has no durable cohort start')
            if receipt_path.exists():
                receipt = validate_receipt(load_json(receipt_path), header)
                if (receipt['attempt_index'] == 1) != (qid in starts):
                    raise ValueError('Receipt/start accounting mismatch')
                receipts[qid] = receipt
            elif qid in starts:
                receipt = _base_receipt(row, header, expected_audits[qid])
                receipt.update(status='interrupted', attempt_index=1, finish_reason='interrupted',
                               error='Durable start without a terminal receipt; the attempt will not be repeated')
                write_once(receipt_path, validate_receipt(receipt, header), artifact_root, paper)
                receipts[qid] = receipt
            else:
                pending.append(row)
        if (output / 'completion.json').exists():
            if pending or len(receipts) != len(rows):
                raise ValueError('Completion marker disagrees with terminal census')
            completion = load_json(output / 'completion.json')
            verify_pin(completion['generations'])
            return completion
        processor = model = generation_config = None
        if pending:
            if cpu_mock:
                processor = SyntheticProcessor()
            else:
                import torch
                from transformers import AutoProcessor, set_seed

                set_seed(17)
                processor = AutoProcessor.from_pretrained(preflight['model']['snapshot'], local_files_only=True, trust_remote_code=False)
                processor.tokenizer.padding_side = 'right'
                model = load_local_model(model_name, preflight, adapter_pin)
                generation_config = effective_generation_config(model.generation_config, processor)
                if generation_config.to_dict() != effective:
                    raise ValueError('Loaded model generation config differs from CPU preflight')
                if adapter_pin:
                    write_once(output / 'adapter_reload.json', {'exact_tensor_equality': True, 'adapter': adapter_pin}, artifact_root, paper)
        for row in pending:
            qid = row['qid']
            receipt = _base_receipt(row, header)
            try:
                batch, audit = pack_input(processor, row, model_name, config)
                if audit != expected_audits[qid]:
                    raise ValueError('Prompt/pixels/timestamps changed after CPU preflight')
            except (ValueError, OSError, RuntimeError) as error:
                receipt.update(status='media_error', error=f'{type(error).__name__}: {error}')
            else:
                if not cpu_mock:
                    authenticate_lease(lease_path, expected_work, protocol, coord_root, fresh=False)
                receipt = _base_receipt(row, header, audit)
                receipt['attempt_index'] = 1
                start = {'qid': qid, 'attempt_index': 1, 'run_header_sha256': digest(header),
                         'started_at': datetime.now(timezone.utc).isoformat(), 'monotonic_start': time.monotonic()}
                write_once(authority / 'starts' / f'{safe_id(qid)}.json', start, artifact_root, paper)
                append_jsonl(attempts_path, start, artifact_root, paper)
                starts[qid] = start
                if test_hook:
                    test_hook('after_start', qid)
                tick = time.monotonic()
                try:
                    if cpu_mock:
                        if generator:
                            result = generator(batch, audit, effective)
                        else:
                            text = '<answer>A</answer><|im_end|>'
                            result = {'tokens': processor.tokenizer.encode(text), 'raw': text,
                                      'display': '<answer>A</answer>'}
                    else:
                        torch.cuda.reset_peak_memory_stats(0)
                        device_batch = {key: value.to('cuda:0') for key, value in batch.items()}
                        with torch.inference_mode():
                            generated = model.generate(**device_batch, generation_config=generation_config)
                        tokens = generated.sequences[0, audit['prompt_tokens']:].detach().cpu().tolist()
                        result = {'tokens': tokens, 'raw': processor.tokenizer.decode(tokens, skip_special_tokens=False),
                                  'display': processor.tokenizer.decode(tokens, skip_special_tokens=True)}
                        receipt['peak_allocated_bytes'] = torch.cuda.max_memory_allocated(0)
                        receipt['peak_reserved_bytes'] = torch.cuda.max_memory_reserved(0)
                        del generated, device_batch
                    tokens = result['tokens']
                    parsed = parse_answer(result['raw'], row['student_input']['options'])
                    receipt.update(raw_generation=result['raw'], display_generation=result['display'],
                                   generated_token_ids=tokens, parsed_answer=parsed['answer'], parser=parsed['parser'],
                                   generated_tokens=len(tokens))
                    finish = 'eos' if tokens and tokens[-1] in eos else 'max_new_tokens' if len(tokens) == DECODING['max_new_tokens'] else None
                    if finish is None:
                        raise ValueError('Generation stopped without a native EOS or the exact fixed token cap')
                    receipt.update(status='ok', finish_reason=finish)
                except (ValueError, OSError, RuntimeError) as error:
                    receipt.update(status='generation_error', error=f'{type(error).__name__}: {error}')
                receipt['latency_seconds'] = time.monotonic() - tick
            if test_hook:
                test_hook('before_publish', qid)
            validate_receipt(receipt, header)
            write_once(output / 'questions' / f'{safe_id(qid)}.json', receipt, artifact_root, paper)
            receipts[qid] = receipt
        ordered = [receipts[qid] for qid in core['ordered_ids']]
        generations_path = output / 'generations.jsonl'
        if generations_path.exists():
            if generations_path.read_bytes() != jsonl_bytes(ordered):
                raise ValueError('Published JSONL differs from the immutable terminal receipts')
            generations_pin = binding(generations_path)
        else:
            generations_pin = write_bytes_once(generations_path, jsonl_bytes(ordered), artifact_root, paper)
        now = datetime.now(timezone.utc)
        completion = {'schema': 'student-generation-completion-v1', 'status': 'TERMINAL_CENSUS_COMPLETE',
                      'run': binding(output / 'run.json'), 'generations': generations_pin,
                      'scheduled_ids': core['ordered_ids'], 'outcomes': {qid: receipts[qid]['status'] for qid in core['ordered_ids']},
                      'expected_count': len(rows), 'terminal_count': len(ordered), 'started_count': len(starts),
                      'finished_count': sum(row['status'] in ('ok', 'generation_error') for row in ordered),
                      'interrupted_count': sum(row['status'] == 'interrupted' for row in ordered),
                      'never_started_count': len(rows) - len(starts),
                      'coverage': sum(row['status'] == 'ok' for row in ordered) / len(rows),
                      'duration_seconds': (now - datetime.fromisoformat(header['started_at'])).total_seconds(),
                      'completed_at': now.isoformat(), 'paper_cell': paper, 'offline_scoring_performed': False}
        write_once(output / 'completion.json', completion, artifact_root, paper)
        return completion
