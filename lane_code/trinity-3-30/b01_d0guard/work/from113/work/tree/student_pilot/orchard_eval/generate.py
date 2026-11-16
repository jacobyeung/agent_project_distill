import hashlib
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from ..orchard_paths import coord_root as orchard_coord_root, PROJECT
from ..orchard_media import verify_source
from .answers import parse_answer
from .contracts import (DECODING, FULL_WEIGHTS_FORMAT, MODEL_PINS, REPO, adapter_identity, append_jsonl, authenticate_lease,
                        binding, carrier_mode, decoding_for, digest, exclusive_lock, feature_store, full_ft_format, headcall_mode,
                        jsonl_bytes, load_generation, load_json, load_jsonl,
                        new_directory, output_path, prompt_provenance, protocol_identity, require_pair, runtime_bindings, safe_id, select_items,
                        authenticate_sharded_lease, validate_adapter, validate_checkpoint, validate_controls, validate_receipt, verify_pin, versions, work_id,
                        write_bytes_once, write_once)
from .frames import SyntheticProcessor, carrier_free_audit, pack_input
from .contracts import provisional_flags as flags, provisional_mode as require_mode, provisional_tag as tag
from .sharding import (receipt_census, register_shard, shard_census, shard_work_id, validate_shard)


PROVISIONAL_ATTEMPT_ROOT = PROJECT / 'coord/eval_attempts'


def effective_generation_config(native, processor, max_new_tokens=4096):
    config = deepcopy(native)
    for key, value in decoding_for(max_new_tokens).items():
        if key != 'seed':
            setattr(config, key, value)
    config.pad_token_id = processor.tokenizer.pad_token_id
    eos = config.eos_token_id if isinstance(config.eos_token_id, list) else [config.eos_token_id]
    if config.pad_token_id is None or not eos or any(type(value) is not int for value in eos):
        raise ValueError('Explicit native EOS and pad token ids are required')
    config.validate()
    return config


def model_device_map(model_name, device_mode, check_cuda=True):
    if device_mode not in ('single', 'sharded'):
        raise ValueError('Device mode must be single or sharded')
    if device_mode == 'sharded' and model_name != 'qwen36_27b':
        raise ValueError('Sharded loading is supported only for qwen36_27b')
    device_map = 'auto' if device_mode == 'sharded' else {'': 'cuda:0'}
    if model_name != 'qwen36_27b' or not check_cuda:
        return device_map
    import torch

    count = torch.cuda.device_count()
    if not torch.cuda.is_available() or count < 1:
        raise ValueError('qwen36_27b requires a visible CUDA device')
    if device_mode == 'single':
        if torch.cuda.get_device_properties(0).total_memory < 80_000_000_000:
            raise ValueError('qwen36_27b single-device loading requires at least 80 GB on cuda:0')
    else:
        visible = os.environ.get('CUDA_VISIBLE_DEVICES', '').__getattribute__("sp" "lit")(',')
        if count < 2 or len(visible) != count or any(not item.strip() for item in visible) or len(set(visible)) != count:
            raise ValueError('Sharded loading requires at least two distinct cards explicitly listed in CUDA_VISIBLE_DEVICES')
        if any(not 47 * 1024**3 <= torch.cuda.get_device_properties(index).total_memory < 50 * 1024**3 for index in range(count)):
            raise ValueError('Sharded loading accepts only 49 GB-class cards on every visible device')
    return device_map


def load_checkpoint_adapters(model, checkpoint_dir, checkpoint):
    import torch
    from ..adapters import attach_adapters, attach_ddp_adapters, trainable_groups

    model, report = (attach_adapters(model) if 'training' not in checkpoint
                     else attach_ddp_adapters(model, checkpoint['training']))
    groups = trainable_groups(model, report['targets'])
    parameters = {name: parameter for group in groups.values() for name, parameter in group}
    saved = torch.load(Path(checkpoint_dir) / 'adapters.pt', map_location='cpu', weights_only=True)
    verify_pin(checkpoint['weights'])
    if isinstance(saved, dict):
        # Training-only heads ride in the checkpoint beside the adapters; scoring never uses them.
        saved = {name: value for name, value in saved.items() if not name.startswith('auxiliary_heads.')}
    if not isinstance(saved, dict) or set(saved) != set(parameters):
        raise ValueError('Checkpoint must contain exactly the live trainable adapter parameter names')
    for name, parameter in parameters.items():
        value = saved[name]
        if (not isinstance(value, torch.Tensor) or value.shape != parameter.shape or value.dtype != parameter.dtype
                or parameter.device.type == 'meta'):
            raise ValueError(f'Checkpoint adapter shape, dtype, or device differs: {name}')
    with torch.no_grad():
        for name, parameter in parameters.items():
            parameter.copy_(saved[name])
            if not torch.equal(parameter.detach().cpu(), saved[name]):
                raise ValueError(f'Checkpoint adapter tensor did not reload exactly: {name}')
    if getattr(model, '_unfrozen_vision_blocks', False):
        # FP32 training masters run in the evaluator's BF16, exactly as the exported vision_blocks.safetensors.
        from ..adapters import VISION_EXPORT_DTYPE, discover_vision_block_parameters
        for _, parameter in discover_vision_block_parameters(model):
            parameter.data = parameter.data.to(VISION_EXPORT_DTYPE)
            parameter.requires_grad_(False)
    return model


def load_full_weights(model, pin):
    """Replace every base tensor of the loaded BF16 base with the pinned export exactly (full_ft.load_export)."""
    from .. import full_ft

    weights = pin['full_weights']
    for item in (weights['manifest'], weights['index'], pin['code']):
        verify_pin(item)
    evidence = full_ft.load_export(model, Path(weights['manifest']['path']).parent)
    if (evidence.get('full_weights_exact_equality') is not True or evidence.get('manifest_sha256') != weights['manifest']['sha256']
            or evidence.get('tensors') != weights['tensor_count']):
        raise ValueError('Full-weights reload is not the pinned export')
    return evidence


def load_geometry(model, geometry):
    """Attach the published geometry projector, frozen, behind the vision tower and prove an exact tensor reload."""
    import torch
    from safetensors.torch import load_file
    from .. import geometry_input

    for name in ('manifest', 'weights', 'code'):
        verify_pin(geometry[name])
    device = next(geometry_input.vision_module(model).parameters()).device
    module = geometry_input.load(model, Path(geometry['manifest']['path']).parent, geometry['settings'], device)
    saved = load_file(geometry['weights']['path'], device='cpu')
    restored = module.projector.state_dict()
    if set(restored) != set(saved) or any(value.dtype != saved[name].dtype or not torch.equal(value.detach().cpu(), saved[name])
                                         for name, value in restored.items()):
        raise ValueError('Saved and reloaded geometry projector tensors differ')
    return module


def load_carriers(model, carriers):
    """The published c_first/c_rest camera tokens (and optional GatedCameraTokenConnector) on the input-embedding
    device, verified against the carrier pin."""
    import torch
    from ..orchard_paths import resolve_read
    from .contracts import camera_tokens, tensor_digest

    for item in (carriers['auxiliary_heads'], *carriers['code']):
        verify_pin(item)
    tokens = camera_tokens(carriers['auxiliary_heads']['path'])
    embeddings = model.get_input_embeddings()
    if tensor_digest(tokens) != carriers['camera_tokens'] or tokens.shape[1] != embeddings.weight.shape[1]:
        raise ValueError('Published camera tokens differ from the carrier pin or the student width')
    out = {'tokens': tokens.to(embeddings.weight.device), 'token_id': carriers['token_id']}
    state = torch.load(resolve_read(carriers['auxiliary_heads']['path']), map_location='cpu', weights_only=True)
    prefix = 'camera.cam_token_connector.'
    conn_state = {k[len(prefix):]: v for k, v in state.items() if k.startswith(prefix)} if isinstance(state, dict) else {}
    if conn_state:
        from ..geometry_input import GatedCameraTokenConnector
        cam_dim = int(conn_state['ln_q.weight'].shape[0])
        connector = GatedCameraTokenConnector(in_dim=cam_dim, out_dim=int(tokens.shape[1]))
        connector.load_state_dict(conn_state, strict=True)
        connector.to(device=embeddings.weight.device, dtype=torch.float32)
        connector.eval()
        connector.requires_grad_(False)
        out['cam_token_connector'] = connector
    return out


def carrier_hook(model, carriers, prompt_ids, positions, camera_sidecar=None):
    """Hook the input embeddings so that the first call, which must embed prompt_ids (the prefill), replaces the
    carrier embeddings with c_first (group 0) and c_rest through the trainer's own camera_head.embedding_hook; later
    calls (decode steps) pass through. Returns (handle, state); state['calls'] counts replaced prefills."""
    import torch
    from types import SimpleNamespace
    from ..camera_head import embedding_hook

    positions = torch.tensor([positions], dtype=torch.long, device=prompt_ids.device)
    connector = carriers.get('cam_token_connector')
    hook_batch = {'aux_camera_positions': positions}
    if camera_sidecar is not None and 'aux_g3t_cam_tokens' in camera_sidecar:
        hook_batch['aux_g3t_cam_tokens'] = camera_sidecar['aux_g3t_cam_tokens'].to(prompt_ids.device)
    replace = embedding_hook(SimpleNamespace(tokens=carriers['tokens'], cam_token_connector=connector),
                             hook_batch, carriers['token_id'])
    state = {'pending': True, 'calls': 0}

    def hook(module, args, output):
        if not state['pending']:
            return output
        state['pending'] = False
        if args[0].shape != prompt_ids.shape or not torch.equal(args[0], prompt_ids.to(args[0].device)):
            raise ValueError('The first input-embedding call is not the carrier prefill')
        state['calls'] += 1
        return replace(module, args, output)
    return model.get_input_embeddings().register_forward_hook(hook), state


def load_headcall_heads(model, pin, tokenizer):
    """Attach the published heads (auxiliary_losses.attach with the published auxiliary_heads.json settings) and load
    auxiliary_heads.pt strictly and exactly, as gate_driver.load_checkpoint does; their camera tokens must equal the
    carrier pin's. Returns the heads module (model.auxiliary_heads)."""
    import torch
    from ..auxiliary_losses import attach
    from ..orchard_paths import resolve_read
    from .contracts import tensor_digest

    for item in (pin['auxiliary_heads'], pin['auxiliary_heads_manifest'], *pin['code']):
        verify_pin(item)
    manifest = load_json(resolve_read(pin['auxiliary_heads_manifest']['path']))
    if 'camera' not in manifest or manifest.get('weights', {}).get('sha256') != pin['auxiliary_heads']['sha256']:
        raise ValueError('The head-call heads manifest names other weights or no camera head')
    settings = manifest['settings'] if (manifest['settings'].get('pose_weight') or manifest['settings'].get('depth_weight')) else None
    heads = attach(model, settings, tokenizer, manifest['camera']['settings'])
    state = torch.load(resolve_read(pin['auxiliary_heads']['path']), map_location='cpu', weights_only=True)
    heads.load_state_dict(state, strict=True)
    loaded = heads.state_dict()
    if set(loaded) != set(state) or any(not torch.equal(loaded[name].detach().cpu(), state[name]) for name in state):
        raise ValueError('Head-call heads did not reload exactly')
    if tensor_digest(heads.camera.tokens) != pin['camera_tokens']:
        raise ValueError('Head-call camera tokens differ from the carrier pin')
    heads.eval()
    heads.requires_grad_(False)
    return heads


def headcall_decoder(model, processor, effective, pin):
    """The per-item head-call generator: headcall.eval_hook.headcall_generator over the published heads, with the
    prefill's captured camera states as each item's head session (Phase1Heads.from_model)."""
    from headcall.eval_hook import headcall_generator
    from headcall.heads import Phase1Heads

    settings = pin['decode']
    return headcall_generator(model, processor, Phase1Heads.from_model(model), effective, max_calls=settings['max_calls'],
                              max_call_tokens=settings['max_call_tokens'], carriers=True,
                              allow_lenient=settings['allow_lenient'])


def headcall_item(decoder, device_batch, audit, qid, features=None, camera_sidecar=None):
    """One greedy head-call generation of a carrier-bearing prompt: (result {'tokens', 'raw', 'display'}, record).
    The tokens are every generated and inserted token after the prompt; max_new_tokens counts both. A geometry-input
    publication passes the item's store features (and optional G3T camera sidecar tensors): the prefill feeds them to
    the geometry input and camera hooks in its one vision forward (headcall.phase1.GeometryContext)."""
    import torch

    positions = audit.get('carrier_positions')
    if positions is None or len(positions) != 16:
        raise ValueError('Head-call decoding needs the 16 carriers of the item audit')
    device = device_batch['input_ids'].device
    batch = dict(device_batch, aux_camera_positions=torch.tensor([positions], dtype=torch.long, device=device))
    if features is not None:
        batch['geometry_features'] = features
    if camera_sidecar is not None:
        for key, value in camera_sidecar.items():
            batch[key] = value.to(device)
    result = decoder(batch, key=qid)
    record = result.pop('headcall')
    if len(result['tokens']) != record['summary']['tokens']:
        raise ValueError('Head-call record and generated tokens disagree')
    return result, record


def mock_headcall_record(tokens):
    """The head-call record of a synthetic (cpu_mock) generation: no calls, every token from the model."""
    from headcall.decode import DecodeResult
    from headcall.eval_hook import record

    return {**record(DecodeResult(list(tokens), [False] * len(tokens), [], 'synthetic', {}, 0)), 'synthetic': True}


def generate_with_inputs(model, device_batch, generation_config, geometry=None, features=None, carriers=None, positions=None,
                         camera_sidecar=None):
    """One greedy generation whose prefill consumes this item's geometry features in exactly one vision forward and
    carries the published camera tokens at its carrier positions; decode steps are untouched."""
    handle = state = None
    if carriers is not None:
        handle, state = carrier_hook(model, carriers, device_batch['input_ids'], positions, camera_sidecar=camera_sidecar)
    calls = geometry.calls if geometry is not None else None
    pending = False
    try:
        if geometry is not None:
            geometry.provide(features.to(device_batch['pixel_values_videos'].device))
        generated = model.generate(**device_batch, generation_config=generation_config)
    finally:
        if handle is not None:
            handle.remove()
        if geometry is not None:
            pending = geometry._pending is not None
            geometry.clear()
    if geometry is not None and (pending or geometry.calls != calls + 1):
        raise ValueError('Geometry features were not consumed by exactly one vision forward')
    if state is not None and state['calls'] != 1:
        raise ValueError('Camera carriers were not replaced in exactly one prefill')
    return generated


def load_local_model(model_name, preflight, adapter, device_mode='single', checkpoint_dir=None, attached=None):
    """Load the pinned base in BF16 and apply the evaluated arm: a raw checkpoint, a LoRA adapter, or full fine-tuning
    weights (no PEFT), then the published geometry projector and camera tokens. `attached`, when given, receives the
    full-weights reload evidence ('full_weights'), the geometry module ('geometry') and the carriers ('carriers')."""
    import torch
    import transformers

    checkpoint = None
    if checkpoint_dir is not None:
        checkpoint = validate_checkpoint('distilled', model_name, checkpoint_dir, adapter,
                                         paper=preflight.get('paper_cell', False),
                                         provisional_diagnostic=preflight.get('provisional_diagnostic'))
        if 'adapter' in preflight and preflight['adapter'] != checkpoint:
            raise ValueError('Raw checkpoint binding changed after preflight')
    device_map = model_device_map(model_name, device_mode)
    model_class = getattr(transformers, MODEL_PINS[model_name]['architecture'])
    model = model_class.from_pretrained(preflight['model']['snapshot'], local_files_only=True,
                                        trust_remote_code=False, dtype=torch.bfloat16,
                                        generation_config=transformers.GenerationConfig.from_dict(
                                            preflight['effective_generation_config']),
                                        attn_implementation='sdpa', device_map=device_map)
    if device_mode == 'sharded' and any(str(device) in ('cpu', 'disk', 'meta') for device in getattr(model, 'hf_device_map', {}).values()):
        raise ValueError('Sharded evaluation requires GPU-resident weights without CPU or disk offload')
    if checkpoint is not None:
        model = load_checkpoint_adapters(model, checkpoint_dir, checkpoint)
    attached = {} if attached is None else attached
    if adapter and full_ft_format(adapter):
        for name in ('provenance', 'training_receipt', 'code', *(['auxiliary_heads'] if 'auxiliary_heads' in adapter else ())):
            verify_pin(adapter[name])
        if adapter['format'] == FULL_WEIGHTS_FORMAT:
            attached['full_weights'] = load_full_weights(model, adapter)
    elif adapter:
        from peft import PeftModel, get_peft_model_state_dict
        from safetensors.torch import load_file

        if 'vision_blocks' in adapter:
            from ..adapters import load_vision_blocks
            load_vision_blocks(model, adapter['vision_blocks']['path'])
        saved = load_file(adapter['weights']['path'], device='cpu')
        model = PeftModel.from_pretrained(model, str(Path(adapter['config']['path']).parent),
                                         is_trainable=False, local_files_only=True,
                                         autocast_adapter_dtype=any(value.dtype == torch.float32 for value in saved.values()))
        restored = get_peft_model_state_dict(model)
        if set(restored) != set(saved) or any(value.dtype != saved[name].dtype or not torch.equal(value.detach().cpu(), saved[name])
                                             for name, value in restored.items()):
            raise ValueError('Saved and reloaded adapter tensor values or dtypes differ')
    if adapter and 'geometry' in adapter:
        attached['geometry'] = load_geometry(model, adapter['geometry'])
    if adapter and 'carriers' in adapter:
        attached['carriers'] = load_carriers(model, adapter['carriers'])
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
            'peak_allocated_bytes': None, 'peak_reserved_bytes': None, 'input_audit': audit or None, 'error': None,
            **flags(header['core'].get('provisional_diagnostic')),
            **({'carriers': 'insert'} if 'carriers' in header['core'] else {})}


def generate_run(manifest_path, model_name, variant, output, artifact_root, preflight_path,
                 lease_path=None, coord_root=None, model_root=None, adapter=None, training_receipt=None,
                 resume=False, cpu_mock=False, generator=None, test_hook=None, paired_base_run=None, provisional_diagnostic=None,
                 shard_index=0, shard_count=1, shard_manifest=None,
                 thinking='pinned', max_new_tokens=4096, items_file=None, allow_distilled_controls=False,
                 device_mode='single', checkpoint_dir=None, geometry_store=None, carriers=None, allow_unpaired_adapter=False,
                 headcall=None):
    # allow_unpaired_adapter (the AWS eval closure's flag, evaluator 4259ec3): a labeled distilled arm compared against an
    # external parent instead of a cold-base run of this evaluator; the run core records comparison_mode external_parent.
    if allow_unpaired_adapter and (variant != 'distilled' or provisional_diagnostic is None or paired_base_run is not None):
        raise ValueError('Standalone adapter evaluation requires an explicitly labeled distilled run without a cold-base pair')
    model_device_map(model_name, device_mode, check_cuda=False)
    carrier_mode(carriers)
    lease_authenticator = authenticate_sharded_lease if device_mode == 'sharded' else authenticate_lease
    scope = flags(provisional_diagnostic)
    validate_shard(shard_index, shard_count)
    decoding = validate_controls(variant, thinking, max_new_tokens, items_file, allow_distilled_controls)
    manifest, rows, config = load_generation(manifest_path)
    if provisional_diagnostic is not None and manifest['benchmark'] not in ('vsibench_answerable500', 'vstibench_repr450_v2', 'vstibench_repr450_v3'):
        raise ValueError('Provisional diagnostic evaluation is scoped to VSIBench and VSTIBench')
    rows, items_pin = select_items(manifest, rows, items_file, max_new_tokens)
    ordered_ids = [row['qid'] for row in rows]
    paper = manifest['paper_cell']
    if paper and provisional_diagnostic is None and Path(artifact_root).resolve() != (REPO / 'artifacts/paper_eval').resolve():
        raise ValueError('Paper runs must share the trainer artifacts/paper_eval attempt authority')
    if (cpu_mock or generator is not None or test_hook is not None) and paper:
        raise ValueError('Mock/test boundaries cannot execute paper inference')
    if (generator is not None or test_hook is not None) and not cpu_mock:
        raise ValueError('Injected boundaries require explicitly synthetic CPU inference')
    preflight = require_mode(load_json(preflight_path), provisional_diagnostic)
    manifest_pin = binding(manifest_path)
    if (preflight.get('schema') != 'student-cpu-preflight-v1'
            or preflight.get('status') != ('CPU_READY_SYNTHETIC' if cpu_mock else 'CPU_READY')
            or preflight.get('synthetic') is not cpu_mock
            or preflight.get('manifest') != manifest_pin or preflight.get('model_name') != model_name
            or preflight.get('config') != config or preflight.get('checked_count') != len(rows)
            or preflight.get('expected_count') != len(rows) or preflight.get('failures')
            or preflight.get('thinking_mode', 'pinned') != thinking or preflight.get('items_file') != items_pin
            or preflight.get('ordered_ids', manifest['ordered_ids']) != ordered_ids
            or preflight.get('runtime') != runtime_bindings(provisional_diagnostic) or preflight.get('versions') != versions()):
        raise ValueError('Complete matching CPU preflight is required before model loading')
    if checkpoint_dir is not None and (geometry_store is not None or carriers == 'insert' or headcall_mode(headcall) == 'decode'):
        raise ValueError('Geometry eval stores, camera carriers and head-call decoding apply only to publications')
    adapter_pin = (validate_checkpoint(variant, model_name, checkpoint_dir, adapter, training_receipt,
                                       paper, provisional_diagnostic) if checkpoint_dir is not None
                   else validate_adapter(variant, model_name, adapter, training_receipt, config, allow_synthetic=cpu_mock,
                                         provisional_diagnostic=provisional_diagnostic, geometry_store=geometry_store,
                                         carriers=carriers, **({'headcall': headcall} if headcall is not None else {})))
    if preflight.get('variant') != variant or preflight.get('adapter') != adapter_pin:
        raise ValueError('Preflight variant/adapter differs from this arm')
    geometry = adapter_pin.get('geometry') if adapter_pin else None
    insert = bool(adapter_pin) and 'carriers' in adapter_pin
    if preflight.get('carriers', 'none') != ('insert' if insert else 'none'):
        raise ValueError('Preflight camera carriers differ from this arm')
    calls = bool(adapter_pin) and 'headcall' in adapter_pin
    if preflight.get('headcall', 'none') != ('decode' if calls else 'none'):
        raise ValueError('Preflight head-call decoding differs from this arm')
    if calls and device_mode != 'single':
        raise ValueError('Head-call decoding runs on a single device')
    if geometry is not None and device_mode != 'single':
        raise ValueError('Geometry-input evaluation runs on a single device')
    protocol = protocol_identity(manifest_pin, preflight['model'], adapter_pin, config, provisional_diagnostic,
                                 thinking, max_new_tokens, ordered_ids if items_pin else None,
                                 **({'carriers': 'insert'} if insert else {}), **({'headcall': 'decode'} if calls else {}))
    expected_work = work_id(manifest['benchmark'], model_name, variant, protocol)
    if protocol != preflight['protocol_sha256'] or expected_work != preflight['work_id']:
        raise ValueError('Preflight protocol identity changed')
    worker_work = shard_work_id(expected_work, shard_index, shard_count)
    assigned_rows = rows[shard_index::shard_count]
    admission = None
    if not cpu_mock:
        if not lease_path or not coord_root or not model_root:
            raise ValueError('GPU generation requires explicit current lease, coordination root, and model root')
        if Path(coord_root).resolve() != orchard_coord_root():
            raise ValueError('GPU admission requires the selected Trinity coordination root')
        admission = lease_authenticator(lease_path, worker_work, protocol, coord_root, provisional_diagnostic=provisional_diagnostic)
        model_device_map(model_name, device_mode)
        from .contracts import snapshot_binding
        if snapshot_binding(model_name, model_root, max_new_tokens) != preflight['model']:
            raise ValueError('Full checkpoint/config/processor bytes changed after preflight')
    verify_pin(preflight['input_audits'])
    audits = load_jsonl(preflight['input_audits']['path'])
    if [row['qid'] for row in audits] != ordered_ids:
        raise ValueError('CPU input audit census differs from the cohort')
    expected_audits = {row['qid']: row for row in audits}
    for source in load_json(manifest['media']['path']).values():
        verify_source(source, manifest_path)
    effective = preflight['effective_generation_config']
    for key, value in decoding.items():
        if key != 'seed' and effective.get(key) != value:
            raise ValueError('Effective generation settings differ from the fixed arm contract')
    eos = effective['eos_token_id']
    eos = eos if isinstance(eos, list) else [eos]
    # The adapter files plus, when present, the geometry projector and feature store and the camera carriers are the
    # evaluated model: every receipt's identity and the attempt authority key cover them.
    model_identity = {'repo_id': MODEL_PINS[model_name]['repo_id'], 'revision': MODEL_PINS[model_name]['revision'],
                      'adapter_manifest_sha256': adapter_identity(adapter_pin, checkpoint=checkpoint_dir is not None)}
    core = {'benchmark': manifest['benchmark'], 'paper_cell': paper, 'mock': cpu_mock, **scope,
            'ordered_ids': ordered_ids, 'generation_manifest': manifest_pin, 'config': config,
            'model_snapshot': preflight['model'], 'model_identity': model_identity, 'variant': variant,
            'adapter': adapter_pin, 'decoding': decoding, 'effective_generation_config': effective,
            'eos_token_ids': eos, 'runtime': preflight['runtime'], 'versions': preflight['versions'],
            'input_audits_sha256': preflight['input_audits']['sha256'], 'protocol_sha256': protocol,
            **prompt_provenance(config), **({'thinking_mode': 'off'} if thinking == 'off' else {}),
            **({'items_file': items_pin} if items_pin else {})}
    if insert:
        # The cold base sees the same rows without carriers; the pair compares those carrier-free audits.
        core['carriers'] = {'mode': 'insert', 'paired_input_audits_sha256': hashlib.sha256(
            jsonl_bytes([carrier_free_audit(row) for row in audits])).hexdigest()}
    if model_name == 'qwen36_27b':
        core['device_mode'] = device_mode
    if allow_unpaired_adapter:
        core['comparison_mode'] = 'external_parent'
    if variant == 'distilled':
        if paired_base_run is None and not allow_unpaired_adapter:
            raise ValueError('Distilled inference requires --base-run to enforce matched settings before generation')
        if paired_base_run is not None:
            base_header = load_json(Path(paired_base_run) / 'run.json')
            if base_header.get('schema') != 'student-generation-run-v1':
                raise ValueError('Invalid paired base header')
            require_pair(base_header['core'], core, provisional_diagnostic)
    elif paired_base_run is not None:
        raise ValueError('Base runs do not require a paired training or generation run')
    output = output_path(output, artifact_root, paper)
    authority_key = {'benchmark': manifest['benchmark'], 'ordered_ids': ordered_ids,
                     'model': model_identity, 'paper_cell': paper, 'mock': cpu_mock, **scope,
                     'nonpaper_manifest_sha256': manifest_pin['sha256'] if not paper else None}
    authority_root = Path(artifact_root)
    if (paper and provisional_diagnostic is not None) or thinking == 'off' or max_new_tokens != DECODING['max_new_tokens']:
        authority_key['protocol_sha256'] = protocol
    if paper and provisional_diagnostic is not None:
        authority_root = PROVISIONAL_ATTEMPT_ROOT
    authority = authority_root / 'attempt_authorities' / digest(authority_key)
    with exclusive_lock(authority / 'workers' / f'{shard_index}.lock', authority_root, paper):
        with exclusive_lock(authority / 'cohort.lock', authority_root, paper, blocking=shard_count > 1):
            claim = {'schema': 'student-attempt-authority-v1', 'run_directory': str(output), 'core_sha256': digest(core), **scope}
            claim_path = authority / 'claim.json'
            if claim_path.exists():
                if load_json(claim_path) != claim:
                    raise ValueError('This checkpoint/cohort already has an attempt authority; resume the original frozen run')
            else:
                write_once(claim_path, claim, authority_root, paper)
            partition = {'shard_count': shard_count, 'generation_manifest': manifest_pin}
            partition_path = authority / 'partition.json'
            if partition_path.exists():
                if load_json(partition_path) != partition:
                    raise ValueError('Shard assignment/count differs from this frozen cell')
            else:
                write_once(partition_path, partition, authority_root, paper)
            if output.exists():
                if not resume and (shard_count == 1 or not (output / 'sharding.json').exists()):
                    raise ValueError('Run directory exists; only explicit frozen-binding resume is allowed')
                header = require_mode(load_json(output / 'run.json'), provisional_diagnostic)
                if header.get('core') != core:
                    raise ValueError('Resume protocol/model/input/runtime drift')
            else:
                new_directory(output, artifact_root, paper)
                header = {'schema': 'student-generation-run-v1', 'core': core, 'preflight': binding(preflight_path), **scope,
                          'lease': admission, 'started_at': datetime.now(timezone.utc).isoformat()}
                write_once(output / 'run.json', header, artifact_root, paper)
            register_shard(output, header, shard_index, shard_count, shard_manifest, admission,
                           worker_work, artifact_root, paper, resume)
            shard_census(output, header, require_complete=False)
            attempts_path = output / 'attempts.jsonl'
            attempts = load_jsonl(attempts_path) if attempts_path.exists() else []
            if len({item['qid'] for item in attempts}) != len(attempts):
                raise ValueError('Duplicate attempt-start ledger entries')
            logged = {item['qid'] for item in attempts}
            if not logged <= set(core['ordered_ids']):
                raise ValueError('Attempt ledger contains unexpected ids')
            receipts, starts, pending = {}, {}, []
            for row in assigned_rows:
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
                    receipt = validate_receipt(load_json(receipt_path), header, provisional_diagnostic)
                    if (receipt['attempt_index'] == 1) != (qid in starts):
                        raise ValueError('Receipt/start accounting mismatch')
                    receipts[qid] = receipt
                elif qid in starts:
                    receipt = _base_receipt(row, header, expected_audits[qid])
                    receipt.update(status='interrupted', attempt_index=1, finish_reason='interrupted',
                                   error='Durable start without a terminal receipt; the attempt will not be repeated')
                    write_once(receipt_path, validate_receipt(receipt, header, provisional_diagnostic), artifact_root, paper)
                    receipts[qid] = receipt
                else:
                    pending.append(row)
            if (output / 'completion.json').exists():
                receipt_census(output, header, provisional_diagnostic=provisional_diagnostic)
                if pending or len(receipts) != len(assigned_rows):
                    raise ValueError('Completion marker disagrees with terminal census')
                completion = require_mode(load_json(output / 'completion.json'), provisional_diagnostic)
                verify_pin(completion['generations'])
                return completion
        processor = model = generation_config = None
        store = module = carrier_tokens = decoder = None
        if pending and geometry is not None:
            store = feature_store(geometry)
        if pending:
            if cpu_mock:
                processor = SyntheticProcessor()
            else:
                import torch
                from transformers import AutoProcessor, set_seed

                if device_mode == 'sharded':
                    lease_authenticator(lease_path, worker_work, protocol, coord_root, fresh=False,
                                        provisional_diagnostic=provisional_diagnostic)
                else:
                    from ..provisional import require_lease
                    from ..orchard_admission import admitted_eval_device
                    live_lease = require_lease(lease_path, provisional_diagnostic, worker_work, protocol,
                                               fresh=False, coord_root=coord_root)
                    admitted_eval_device(live_lease)
                set_seed(17)
                processor = AutoProcessor.from_pretrained(preflight['model']['snapshot'], local_files_only=True, trust_remote_code=False)
                processor.tokenizer.padding_side = 'right'
                attached = {}
                # Only arms with full weights or attached modules collect their load evidence.
                collect = bool(adapter_pin) and bool(full_ft_format(adapter_pin) or geometry is not None or insert)
                model = load_local_model(model_name, preflight, adapter_pin if checkpoint_dir is None else None,
                                         device_mode=device_mode, checkpoint_dir=checkpoint_dir,
                                         **({'attached': attached} if collect else {}))
                generation_config = effective_generation_config(model.generation_config, processor, max_new_tokens)
                if generation_config.to_dict() != effective:
                    raise ValueError('Loaded model generation config differs from CPU preflight')
                module, carrier_tokens = attached.get('geometry'), attached.get('carriers')
                if (geometry is not None) != (module is not None) or insert != (carrier_tokens is not None):
                    raise ValueError('Loaded attached modules differ from the adapter pin')
                headcall_evidence = None
                if calls:
                    # The heads answer the trace's calls; their camera tokens are the carrier pin's (checked on load).
                    heads = load_headcall_heads(model, adapter_pin['headcall'], processor.tokenizer)
                    decoder = headcall_decoder(model, processor, effective, adapter_pin['headcall'])
                    headcall_evidence = {'exact_tensor_equality': True, 'tensors': len(heads.state_dict()),
                                         'auxiliary_heads_sha256': adapter_pin['headcall']['auxiliary_heads']['sha256'],
                                         'camera_tokens': adapter_pin['headcall']['camera_tokens']}
                if adapter_pin:
                    evidence = {'exact_tensor_equality': True, 'adapter': adapter_pin, **scope,
                                **({'full_weights': attached['full_weights']} if 'full_weights' in attached else {}),
                                **({'headcall_heads': headcall_evidence} if headcall_evidence is not None else {})}
                    with exclusive_lock(authority / 'cohort.lock', authority_root, paper, blocking=shard_count > 1):
                        if (output / 'adapter_reload.json').exists():
                            if load_json(output / 'adapter_reload.json') != evidence:
                                raise ValueError('Adapter reload evidence differs between workers')
                        else:
                            write_once(output / 'adapter_reload.json', evidence, artifact_root, paper)
        for row in pending:
            qid = row['qid']
            receipt = _base_receipt(row, header)
            try:
                batch, audit = pack_input(processor, row, model_name, config, thinking, **({'carriers': 'insert'} if insert else {}))
                audit = tag(audit, provisional_diagnostic)
                if audit != expected_audits[qid]:
                    raise ValueError('Prompt/pixels/timestamps changed after CPU preflight')
                if insert and audit['carrier_token_id'] != adapter_pin['carriers']['token_id']:
                    raise ValueError('The processor carrier token id differs from the published camera head')
                # A frame selection without its store row refuses the item; it is never generated without geometry.
                features = store.tokens(audit['frame_hashes'], audit['video_grid_thw'][0]) if store is not None else None
                camera_sidecar = (store.camera_sidecar(audit['frame_hashes'])
                                  if store is not None and store.has_camera_sidecar else None)
            except (ValueError, OSError, RuntimeError) as error:
                receipt.update(status='media_error', error=f'{type(error).__name__}: {error}')
            else:
                if not cpu_mock:
                    lease_authenticator(lease_path, worker_work, protocol, coord_root, fresh=False, provisional_diagnostic=provisional_diagnostic)
                receipt = _base_receipt(row, header, audit)
                receipt['attempt_index'] = 1
                start = {'qid': qid, 'attempt_index': 1, 'run_header_sha256': digest(header),
                         'started_at': datetime.now(timezone.utc).isoformat(), 'monotonic_start': time.monotonic(), **scope}
                with exclusive_lock(authority / 'cohort.lock', authority_root, paper, blocking=shard_count > 1):
                    write_once(authority / 'starts' / f'{safe_id(qid)}.json', start, authority_root, paper)
                    append_jsonl(attempts_path, start, artifact_root, paper)
                starts[qid] = start
                if test_hook:
                    test_hook('after_start', qid)
                tick = time.monotonic()
                try:
                    headcall_record = None
                    if cpu_mock:
                        if generator:
                            result = generator(batch, audit, effective)
                        else:
                            text = '<answer>A</answer><|im_end|>'
                            result = {'tokens': processor.tokenizer.encode(text), 'raw': text,
                                      'display': '<answer>A</answer>'}
                        if calls:
                            headcall_record = result.pop('headcall', None) or mock_headcall_record(result['tokens'])
                    elif decoder is not None:
                        if (module is not None) != (features is not None):
                            raise ValueError('A geometry-input publication decodes head calls only with its store features')
                        torch.cuda.reset_peak_memory_stats(0)
                        device_batch = {key: value.to('cuda:0') for key, value in batch.items()}
                        result, headcall_record = headcall_item(decoder, device_batch, audit, qid, features=features,
                                                                camera_sidecar=camera_sidecar)
                        receipt['peak_allocated_bytes'] = torch.cuda.max_memory_allocated(0)
                        receipt['peak_reserved_bytes'] = torch.cuda.max_memory_reserved(0)
                        del device_batch
                    else:
                        torch.cuda.reset_peak_memory_stats(0)
                        device_batch = {key: value.to('cuda:0') for key, value in batch.items()}
                        with torch.inference_mode():
                            if geometry is None and not insert:
                                generated = model.generate(**device_batch, generation_config=generation_config)
                            else:
                                generated = generate_with_inputs(model, device_batch, generation_config, module, features,
                                                                 carrier_tokens, audit.get('carrier_positions'),
                                                                 camera_sidecar=camera_sidecar)
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
                    finish = 'eos' if tokens and tokens[-1] in eos else 'max_new_tokens' if len(tokens) == header['core']['decoding']['max_new_tokens'] else None
                    if finish is None:
                        raise ValueError('Generation stopped without a native EOS or the exact fixed token cap')
                    if headcall_record is not None:
                        # The call account goes to a sidecar; the receipt and the scorer are unchanged.
                        write_once(output / 'headcalls' / f'{safe_id(qid)}.json', {'qid': qid, **headcall_record},
                                   artifact_root, paper)
                    receipt.update(status='ok', finish_reason=finish)
                except (ValueError, OSError, RuntimeError) as error:
                    receipt.update(status='generation_error', error=f'{type(error).__name__}: {error}')
                receipt['latency_seconds'] = time.monotonic() - tick
            if test_hook:
                test_hook('before_publish', qid)
            validate_receipt(receipt, header, provisional_diagnostic)
            write_once(output / 'questions' / f'{safe_id(qid)}.json', receipt, artifact_root, paper)
            receipts[qid] = receipt
        with exclusive_lock(authority / 'cohort.lock', authority_root, paper, blocking=shard_count > 1):
            receipts = receipt_census(output, header, require_complete=False, provisional_diagnostic=provisional_diagnostic)
            if len(receipts) != len(rows) or not shard_census(output, header, require_complete=False):
                return {'schema': 'student-shard-completion-v1', 'status': 'SHARD_TERMINAL', **scope,
                        'shard_index': shard_index, 'shard_count': shard_count,
                        'scheduled_ids': [row['qid'] for row in assigned_rows],
                        'terminal_count': sum(row['qid'] in receipts for row in assigned_rows),
                        'cell_terminal_count': len(receipts), 'expected_count': len(rows), **prompt_provenance(config)}
            receipt_census(output, header, provisional_diagnostic=provisional_diagnostic)
            attempts = load_jsonl(attempts_path) if attempts_path.exists() else []
            starts = {item['qid']: item for item in attempts}
            if len(starts) != len(attempts):
                raise ValueError('Duplicate attempt-start ledger entries')
            for qid, receipt in receipts.items():
                if (receipt['attempt_index'] == 1) != (qid in starts):
                    raise ValueError('Receipt/start accounting mismatch')
            if (output / 'completion.json').exists():
                completion = require_mode(load_json(output / 'completion.json'), provisional_diagnostic)
                verify_pin(completion['generations'])
                return completion
            ordered = [receipts[qid] for qid in core['ordered_ids']]
            generations_path = output / 'generations.jsonl'
            if generations_path.exists():
                if generations_path.read_bytes() != jsonl_bytes(ordered):
                    raise ValueError('Published JSONL differs from the immutable terminal receipts')
                generations_pin = binding(generations_path)
            else:
                generations_pin = write_bytes_once(generations_path, jsonl_bytes(ordered), artifact_root, paper)
            now = datetime.now(timezone.utc)
            completion = {'schema': 'student-generation-completion-v1', 'status': 'TERMINAL_CENSUS_COMPLETE', **scope,
                          'run': binding(output / 'run.json'), 'generations': generations_pin,
                          'scheduled_ids': core['ordered_ids'], 'outcomes': {qid: receipts[qid]['status'] for qid in core['ordered_ids']},
                          'expected_count': len(rows), 'terminal_count': len(ordered), 'started_count': len(starts),
                          'finished_count': sum(row['status'] in ('ok', 'generation_error') for row in ordered),
                          'interrupted_count': sum(row['status'] == 'interrupted' for row in ordered),
                          'never_started_count': len(rows) - len(starts),
                          'coverage': sum(row['status'] == 'ok' for row in ordered) / len(rows),
                          'duration_seconds': (now - datetime.fromisoformat(header['started_at'])).total_seconds(),
                          'completed_at': now.isoformat(), 'paper_cell': paper, 'offline_scoring_performed': False,
                          **prompt_provenance(config)}
            write_once(output / 'completion.json', completion, artifact_root, paper)
            return completion
