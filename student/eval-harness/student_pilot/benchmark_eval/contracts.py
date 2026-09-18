import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import re
import socket
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


REPO = Path(__file__).resolve().parents[2]
BENCHMARKS = ('vsibench_answerable500', 'vstibench_repr450_v2', 'dsibench_all4')
COUNTS = dict(zip(BENCHMARKS, (500, 450, 7076)))
VARIANTS = ('std', 'reverse', 'hflip', 'reverse_hflip')
MODEL_PINS = {
    'onethinker': {'repo_id': 'OneThink/OneThinker-8B', 'revision': '2b7032f4179d8c032d2eac67b3692263f85be0fc',
                   'architecture': 'Qwen3VLForConditionalGeneration', 'enable_thinking': None,
                   'config_sha256': 'cc76a13b9e08a9548e177717d4e0b929142edcaf674d26dff5b2c586a8e28a35',
                   'template_sha256': '3636d0f0bd6bef02654cdffdc447b79cb2cef8ab02cc75267345946291a489e4'},
    'qwen35': {'repo_id': 'Qwen/Qwen3.5-9B', 'revision': 'c202236235762e1c871ad0ccb60c8ee5ba337b9a',
               'architecture': 'Qwen3_5ForConditionalGeneration', 'enable_thinking': True,
               'config_sha256': 'd0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05',
               'template_sha256': 'a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715'},
}
RGB = {'version': 'original-rgb32-v1', 'frame_count': 32, 'selector': 'floor(k*(N-1)/31)',
       'do_sample_frames': False, 'size': {'shortest_edge': 524288, 'longest_edge': 4718592},
       'timing': 'original_ordinals_and_fps_with_separate_actual_pts',
       'prompt': 'native_user_video_then_verbatim_question_options', 'max_input_tokens': 16384}
DECODING = {'seed': 17, 'do_sample': False, 'num_beams': 1, 'num_return_sequences': 1,
            'max_new_tokens': 16384, 'use_cache': True, 'temperature': None, 'top_p': None,
            'top_k': None, 'return_dict_in_generate': True, 'output_scores': False, 'output_logits': False}
EXECUTION = {'dtype': 'bfloat16', 'attention_implementation': 'sdpa', 'batch_size': 1,
             'quantization': None, 'inference_mode': True, 'attempts_per_question': 1}
DEFAULT_CONFIG = {'schema': 'student-benchmark-eval-v1', 'models': MODEL_PINS, 'rgb': RGB,
                  'decoding': DECODING, 'execution': EXECUTION}
MEMBERSHIP_SHA = '2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf'
SHA_RE = re.compile(r'[0-9a-f]{64}\Z')
SAFE_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]*\Z')
FORBIDDEN = {'gt', 'ground_truth', 'answer_mapping', 'target', 'targets', 'teacher', 'teacher_outputs',
             'correctness', 'is_correct', 'geometry', 'depth', 'poses', 'tool_messages', 'system'}


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def binding(path, expected=None):
    path = Path(path).absolute()
    value = {'path': str(path), 'sha256': sha256(path), 'size_bytes': path.stat().st_size}
    if expected is not None and value['sha256'] != expected:
        raise ValueError(f'Hash mismatch: {path}')
    return value


def verify_pin(pin):
    if not isinstance(pin, dict) or set(pin) != {'path', 'sha256', 'size_bytes'} or not SHA_RE.fullmatch(pin['sha256']):
        raise ValueError('Malformed file binding')
    if binding(pin['path'], pin['sha256']) != pin:
        raise ValueError(f'File binding changed: {pin["path"]}')
    return Path(pin['path'])


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f'Nonfinite JSON value: {value}')


def load_json(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def load_jsonl(path):
    with Path(path).open(encoding='utf-8') as stream:
        return [json.loads(line, object_pairs_hook=_unique_object, parse_constant=_invalid_constant) for line in stream if line.strip()]


def jsonl_bytes(rows):
    return b''.join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n').encode() for row in rows)


def safe_id(value):
    if not isinstance(value, str) or not SAFE_RE.fullmatch(value) or '..' in value:
        raise ValueError(f'Unsafe identifier: {value!r}')
    return value.replace(':', '_') + '_' + hashlib.sha256(value.encode()).hexdigest()[:12]


def contained(root, relative):
    root, relative = Path(root).resolve(), Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Expected a traversal-free relative path')
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError('Input symlink escapes its explicit root')
    return path


def output_path(path, root, paper=False):
    path, root = Path(path).absolute(), Path(root).absolute()
    if '..' in path.parts or '..' in root.parts:
        raise ValueError('Output traversal is forbidden')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output escapes the artifact root')
    if paper and not root.resolve().is_relative_to(Path('/data2')):
        raise ValueError('Paper artifacts must remain under an explicit /data2 root')
    return path


def new_directory(path, root, paper=False):
    path = output_path(path, root, paper)
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_bytes_once(path, payload, root, paper=False):
    path = output_path(path, root, paper)
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = output_path(path.parent / '_staging', root, paper)
    staging.mkdir(exist_ok=True)
    private = staging / uuid4().hex
    with private.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(private, path)
    except FileExistsError as error:
        raise ValueError(f'Refusing to overwrite immutable artifact: {path}') from error
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return binding(path)


def write_once(path, value, root, paper=False):
    return write_bytes_once(path, canonical_bytes(value), root, paper)


def append_jsonl(path, row, root, paper=False):
    path = output_path(path, root, paper)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as stream:
        stream.write(jsonl_bytes([row]))
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def exclusive_lock(path, root, paper=False):
    path = output_path(path, root, paper)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Another worker holds this run/cohort lock') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def load_config(path):
    config = load_json(path)
    if canonical_bytes(config) != canonical_bytes(DEFAULT_CONFIG):
        raise ValueError('Frozen benchmark settings differ; arm-specific overrides are forbidden')
    return config


def reject_forbidden(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN or key.lower().startswith(('teacher_', 'correctness_', 'ground_truth')):
                raise ValueError(f'Forbidden inference field: {key}')
            reject_forbidden(item)
    elif isinstance(value, list):
        for item in value:
            reject_forbidden(item)


def validate_input(row):
    reject_forbidden(row)
    if set(row) != {'qid', 'video_id', 'student_input'}:
        raise ValueError('Inference rows must contain only qid, video_id, student_input')
    safe_id(row['qid'])
    if not isinstance(row['video_id'], str) or not row['video_id']:
        raise ValueError('Dataset-qualified video identity is required')
    item = row['student_input']
    required = {'question', 'options', 'options_serialization', 'video_path', 'video_sha256', 'frame_receipt'}
    if not isinstance(item, dict) or set(item) != required:
        raise ValueError('Unexpected or missing student input fields')
    if not isinstance(item['question'], str) or not item['question'].strip():
        raise ValueError('Question must be a nonempty original string')
    options = item['options']
    if not isinstance(options, (list, str)) or isinstance(options, list) and not all(isinstance(x, str) for x in options):
        raise ValueError('Options must be original strings')
    serialized = '\n'.join(options) if isinstance(options, list) else options
    if item['options_serialization'] != serialized:
        raise ValueError('Options serialization changed')
    if not isinstance(item['video_path'], str) or not SHA_RE.fullmatch(item['video_sha256']):
        raise ValueError('Video path/hash are required')
    if set(item['frame_receipt']) != {'path', 'sha256', 'size_bytes'}:
        raise ValueError('Frame receipt must be a plain file binding')
    if any(token in item['question'] + serialized for token in ('<|im_start|>', '<|im_end|>', '<|video_pad|>', '<|image_pad|>')):
        raise ValueError('Conversation/media control tokens in source input')
    return row


def import_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guard_inputs(guard_pin, registry_pin, paths):
    guard = import_file(verify_pin(guard_pin), '_student_cohort_guard')
    registry = verify_pin(registry_pin)
    return [guard.guard_cohort(path, registry_path=registry) for path in paths]


def load_generation(path):
    path = Path(path).absolute()
    manifest = load_json(path)
    fields = {'schema', 'benchmark', 'paper_cell', 'ordered_ids', 'expected_count', 'config', 'inputs', 'media',
              'preprocessing', 'cohort_authority_sha256', 'membership', 'admission_input', 'guard', 'media_roots'}
    if set(manifest) != fields or manifest['schema'] != 'student-generation-manifest-v1':
        raise ValueError('Invalid answer-free generation manifest')
    if manifest['benchmark'] not in BENCHMARKS or type(manifest['paper_cell']) is not bool:
        raise ValueError('Unknown benchmark or paper scope')
    ids = manifest['ordered_ids']
    if not ids or len(set(ids)) != len(ids) or len(ids) != manifest['expected_count']:
        raise ValueError('Invalid ordered cohort census')
    if manifest['paper_cell'] and len(ids) != COUNTS[manifest['benchmark']]:
        raise ValueError('Paper cohort count changed')
    for field in ('config', 'inputs', 'media', 'membership', 'admission_input'):
        pin = manifest[field]
        if not Path(pin['path']).resolve().is_relative_to(path.parent.resolve()):
            raise ValueError('Generation package reference escapes its directory')
        verify_pin(pin)
    config = load_config(manifest['config']['path'])
    if manifest['preprocessing'] != config['rgb']:
        raise ValueError('Preprocessing contract changed')
    rows = load_jsonl(manifest['inputs']['path'])
    if [validate_input(row)['qid'] for row in rows] != ids:
        raise ValueError('Admission inputs do not exactly match ordered membership')
    if load_json(manifest['membership']['path']) != {'qids': ids} or load_json(manifest['admission_input']['path']) != rows:
        raise ValueError('Membership/admission projection changed')
    media = load_json(manifest['media']['path'])
    if set(media) != {row['video_id'] for row in rows}:
        raise ValueError('Media census mismatch')
    for row in rows:
        item, source = row['student_input'], media[row['video_id']]
        if source != {key: item[key] for key in ('video_path', 'video_sha256', 'frame_receipt')}:
            raise ValueError('Question media differs from shared video selection')
        if not any(Path(item['video_path']).resolve().is_relative_to(Path(root).resolve()) for root in manifest['media_roots']):
            raise ValueError('Video escapes the explicit media roots')
        if not Path(item['frame_receipt']['path']).resolve().is_relative_to(path.parent.resolve()):
            raise ValueError('Frame cache escapes the generation package')
        verify_pin(item['frame_receipt'])
    if manifest['benchmark'] == 'vsibench_answerable500':
        if manifest['paper_cell'] and manifest['cohort_authority_sha256'] != MEMBERSHIP_SHA:
            raise ValueError('VSIBench requires the answerable-500 authority')
        if not manifest['guard']:
            raise ValueError('VSIBench admission requires the cohort guard')
        guard_inputs(manifest['guard']['source'], manifest['guard']['registry'],
                     [manifest['membership']['path'], manifest['admission_input']['path']])
    return manifest, rows, config


def runtime_bindings():
    names = ('__init__.py', '__main__.py', 'contracts.py', 'frames.py', 'answers.py', 'generate.py')
    files = [Path(__file__).parent / name for name in names]
    files += [REPO / 'student_pilot/__init__.py', REPO / 'scripts/student_benchmark_gpu.sh', REPO / 'requirements.txt']
    return [binding(path) for path in files]


def versions():
    return {name: importlib.metadata.version(name) for name in ('torch', 'torchvision', 'transformers', 'peft', 'accelerate', 'numpy', 'Pillow', 'av')}


def snapshot_binding(model, model_root):
    pin = MODEL_PINS[model]
    root = Path(model_root).resolve()
    snapshot = contained(root, f'models--{pin["repo_id"].replace("/", "--")}/snapshots/{pin["revision"]}')
    config = load_json(binding(snapshot / 'config.json', pin['config_sha256'])['path'])
    if config.get('architectures') != [pin['architecture']] or not config.get('vision_config'):
        raise ValueError('Pinned vision-language architecture changed')
    context_limit = config.get('text_config', config).get('max_position_embeddings')
    if type(context_limit) is not int or context_limit < RGB['max_input_tokens'] + DECODING['max_new_tokens']:
        raise ValueError('Pinned model cannot support the full frozen input/output context budget')
    binding(snapshot / 'chat_template.jinja', pin['template_sha256'])
    index = load_json(snapshot / 'model.safetensors.index.json')
    shards = sorted(set(index['weight_map'].values()))
    if len(shards) != 4 or any(Path(name).name != name for name in shards):
        raise ValueError('Expected the complete four-shard checkpoint')
    required = {'config.json', 'model.safetensors.index.json', 'tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja'}
    optional = {'generation_config.json', 'preprocessor_config.json', 'video_preprocessor_config.json',
                'processor_config.json', 'chat_template.json', 'special_tokens_map.json', 'added_tokens.json', 'vocab.json', 'merges.txt'}
    names = sorted(required | {name for name in optional if (snapshot / name).is_file()})
    files = []
    for name in names + shards:
        file = contained(root, str(snapshot.relative_to(root) / name))
        files.append(binding(file))
    return {'repo_id': pin['repo_id'], 'revision': pin['revision'], 'architecture': pin['architecture'],
            'snapshot': str(snapshot), 'files': files, 'weight_shards': shards,
            'generation_config_source': 'generation_config.json' if 'generation_config.json' in names else 'model_config'}


def validate_adapter(variant, model, adapter, training_receipt, config, allow_synthetic=False):
    if variant == 'base':
        if adapter is not None or training_receipt is not None:
            raise ValueError('Base evaluation must not receive training or adapter inputs')
        return None
    if variant != 'distilled' or adapter is None or training_receipt is None:
        raise ValueError('Distilled evaluation requires an explicit adapter and clean-training receipt')
    receipt = load_json(training_receipt)
    if receipt.get('synthetic') is True and not allow_synthetic:
        raise ValueError('Synthetic adapter provenance cannot authorize real model evaluation')
    expected = MODEL_PINS[model]
    if (receipt.get('schema') != 'clean-student-training-v1' or receipt.get('status') != 'TRAINED'
            or receipt.get('benchmark_trained_diagnostic') is not False or receipt.get('smoke') is not False
            or receipt.get('dataset') != 'VSI-590K' or receipt.get('base_restart') != 'original_checkpoint'
            or receipt.get('base') != {key: expected[key] for key in ('repo_id', 'revision')}
            or receipt.get('preprocessing') != config['rgb']
            or receipt.get('enable_thinking') != expected['enable_thinking']
            or receipt.get('selection_frozen_before_benchmark') is not True
            or set(receipt.get('trained_module_families', [])) != {'vision', 'merger', 'language'}):
        raise ValueError('Clean training/base/preprocessing lineage is missing or incompatible')
    for name in ('training_data_sha256', 'scene_split_sha256'):
        if not isinstance(receipt.get(name), str) or not SHA_RE.fullmatch(receipt[name]):
            raise ValueError(f'Missing clean lineage binding: {name}')
    directory = Path(adapter).resolve()
    config_pin = binding(contained(directory, 'adapter_config.json'))
    weight_pin = binding(contained(directory, 'adapter_model.safetensors'))
    if receipt.get('adapter') != {'config_sha256': config_pin['sha256'], 'weights_sha256': weight_pin['sha256']}:
        raise ValueError('Adapter tensor/config bytes differ from the clean-training receipt')
    adapter_config = load_json(config_pin['path'])
    if adapter_config.get('peft_type') != 'LORA' or not adapter_config.get('target_modules'):
        raise ValueError('A declared LoRA module closure is required')
    base_path = str(adapter_config.get('base_model_name_or_path', ''))
    if base_path != expected['repo_id'] and Path(base_path).name != expected['revision']:
        raise ValueError('Adapter config names a different base checkpoint')
    with Path(weight_pin['path']).open('rb') as stream:
        header_size = int.from_bytes(stream.read(8), 'little')
        if not 0 < header_size < min(weight_pin['size_bytes'] - 8, 16 * 1024 * 1024):
            raise ValueError('Invalid adapter safetensors header')
        tensors = json.loads(stream.read(header_size), object_pairs_hook=_unique_object)
    tensors.pop('__metadata__', None)
    if not tensors:
        raise ValueError('Empty adapter tensor closure')
    offsets = []
    for name, tensor in tensors.items():
        shape, span = tensor.get('shape'), tensor.get('data_offsets')
        if (not name.endswith(('.lora_A.weight', '.lora_B.weight')) or tensor.get('dtype') not in ('F32', 'F16', 'BF16')
                or not isinstance(shape, list) or len(shape) != 2 or any(type(n) is not int or n < 1 for n in shape)
                or not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)):
            raise ValueError('Unsupported or malformed LoRA tensor')
        width = 4 if tensor['dtype'] == 'F32' else 2
        if span[1] - span[0] != math.prod(shape) * width:
            raise ValueError('Adapter tensor byte/shape mismatch')
        partner = name.replace('.lora_A.', '.lora_B.') if '.lora_A.' in name else name.replace('.lora_B.', '.lora_A.')
        if partner not in tensors:
            raise ValueError('Adapter tensor pair is incomplete')
        offsets.append(span)
    offsets.sort()
    if (offsets[0][0] != 0 or any(left[1] != right[0] for left, right in zip(offsets, offsets[1:]))
            or offsets[-1][1] != weight_pin['size_bytes'] - 8 - header_size):
        raise ValueError('Adapter tensor offsets do not cover the complete file')
    return {'config': config_pin, 'weights': weight_pin, 'training_receipt': binding(training_receipt),
            'tensor_count': len(tensors)}


def protocol_identity(manifest_pin, model_binding, adapter, config):
    return digest({'manifest_sha256': manifest_pin['sha256'], 'model': model_binding,
                   'adapter': adapter, 'config': config})


def work_id(benchmark, model, variant, protocol_sha256):
    cohort = dict(zip(BENCHMARKS, ('vsi500', 'vsti450', 'dsi_all4')))[benchmark]
    return f'student_eval__{variant}_{model}_{cohort}__s17__{protocol_sha256[:8]}'


def check_lease(lease, hostname, visible_devices, now, fresh=True):
    allowed_hosts = {'trinity-1-13', 'trinity-0-18', 'trinity-0-23', 'trinity-3-23', 'trinity-2-28'}
    if hostname.split('.')[0] not in allowed_hosts or lease.get('host') != hostname.split('.')[0]:
        raise ValueError('Supervisor lease must match an authorized evaluation host')
    index = lease.get('gpu_index')
    if type(index) is not int or not 0 <= index <= 7 or visible_devices != str(index):
        raise ValueError('Only the supervisor-leased physical GPU may be exposed')
    if lease['host'] == 'trinity-1-13' and index == 0:
        raise ValueError('trinity-1-13 GPU0 is reserved for SAM3')
    for key in ('ownership_check_passed', 'coordination_lease_passed', 'vnice_wrapped'):
        if lease.get(key) is not True:
            raise ValueError(f'Supervisor evidence must attest {key}=true')
    for key in ('owner', 'work_id', 'coordination_lease_evidence'):
        if not isinstance(lease.get(key), str) or not lease[key].strip():
            raise ValueError(f'Missing supervisor evidence: {key}')
    checked = datetime.fromisoformat(lease['ownership_checked_at'].replace('Z', '+00:00'))
    expires = datetime.fromisoformat(lease['expires_at'].replace('Z', '+00:00'))
    if checked.tzinfo is None or expires.tzinfo is None or checked > now or expires <= now or expires <= checked:
        raise ValueError('Lease timestamps are missing a timezone, future-dated, or expired')
    if fresh and (now - checked).total_seconds() > 300:
        raise ValueError('Supervisor ownership check is older than five minutes')
    return lease


def authenticate_lease(path, expected_work_id, protocol_sha256, coord_root, fresh=True,
                       hostname=None, visible_devices=None, device_uuid=None, now=None):
    now = now or datetime.now(timezone.utc)
    lease = check_lease(load_json(path), hostname or socket.gethostname(),
                        visible_devices if visible_devices is not None else os.environ.get('CUDA_VISIBLE_DEVICES'), now, fresh)
    if lease['work_id'] != expected_work_id or lease.get('protocol_sha256') != protocol_sha256:
        raise ValueError('Lease is not bound to this benchmark/model/protocol')
    evidence_path = contained(coord_root, f'LEASES/{expected_work_id}.lock/lease.json')
    if Path(lease['coordination_lease_evidence']).resolve() != evidence_path.resolve():
        raise ValueError('Evidence is not the current coordination lease')
    evidence = load_json(evidence_path)
    if (evidence.get('work_id') != expected_work_id or evidence.get('status') != 'running'
            or evidence.get('agent_id') != lease['owner']
            or str(evidence.get('host', '')).split('.')[0] != lease['host']):
        raise ValueError('Coordination lease owner/state/host mismatch')
    heartbeat = datetime.fromisoformat(evidence['last_heartbeat'].replace('Z', '+00:00'))
    if heartbeat.tzinfo is None or not 0 <= (now - heartbeat).total_seconds() <= 300:
        raise ValueError('Coordination heartbeat is stale or future-dated')
    if device_uuid is None:
        result = subprocess.run(['nvidia-smi', '-i', str(lease['gpu_index']), '--query-gpu=uuid', '--format=csv,noheader'],
                                check=True, capture_output=True, text=True, timeout=20)
        device_uuid = result.stdout.strip()
    if not device_uuid or lease.get('gpu_uuid') != device_uuid:
        raise ValueError('Physical GPU UUID does not match the admitted lease')
    return {'supervisor': binding(path), 'coordination': binding(evidence_path), 'gpu_uuid': device_uuid}


def validate_receipt(row, header):
    required = {'qid', 'status', 'attempt_index', 'raw_generation', 'display_generation', 'generated_token_ids',
                'parsed_answer', 'parser', 'finish_reason', 'prompt_tokens', 'generated_tokens', 'model', 'decoding',
                'video_sha256', 'frame_hashes', 'frame_indices', 'source_pts_seconds', 'effective_timestamps_seconds',
                'pixel_tensor_sha256', 'prompt_token_sha256', 'video_grid_thw', 'runtime_manifest_sha256',
                'latency_seconds', 'peak_allocated_bytes', 'peak_reserved_bytes', 'input_audit', 'error'}
    if set(row) != required or row['qid'] not in header['core']['ordered_ids']:
        raise ValueError('Invalid per-question JSON schema or membership')
    if row['runtime_manifest_sha256'] != digest(header):
        raise ValueError('Question receipt is bound to another run header')
    if row['model'] != header['core']['model_identity'] or row['decoding'] != header['core']['decoding']:
        raise ValueError('Question model or decoding contract changed')
    if row['status'] not in ('ok', 'generation_error', 'interrupted', 'media_error'):
        raise ValueError('Unknown question status')
    if row['status'] == 'ok':
        tokens = row['generated_token_ids']
        if not isinstance(tokens, list) or not tokens or any(type(token) is not int for token in tokens):
            raise ValueError('Native generated token ids are required')
        if row['generated_tokens'] != len(tokens) or row['attempt_index'] != 1:
            raise ValueError('Attempt/token census mismatch')
        eos = header['core']['eos_token_ids']
        expected = 'eos' if tokens[-1] in eos else 'max_new_tokens' if len(tokens) == DECODING['max_new_tokens'] else None
        if expected is None or row['finish_reason'] != expected or len(tokens) > DECODING['max_new_tokens']:
            raise ValueError('Native EOS/output-cap telemetry mismatch')
        if type(row['prompt_tokens']) is not int or not 0 < row['prompt_tokens'] <= RGB['max_input_tokens']:
            raise ValueError('Prompt token budget mismatch')
    elif row['finish_reason'] not in ('error', 'interrupted'):
        raise ValueError('Failed attempts require explicit error/interrupted termination')
    if row['generated_token_ids'] is not None:
        tokens = row['generated_token_ids']
        if (not isinstance(tokens, list) or any(type(token) is not int or token < 0 for token in tokens)
                or row['generated_tokens'] != len(tokens)
                or not isinstance(row['raw_generation'], str) or not isinstance(row['display_generation'], str)):
            raise ValueError('Native generation token/text telemetry is malformed')
    elif any(row[field] is not None for field in ('generated_tokens', 'raw_generation', 'display_generation', 'parsed_answer')):
        raise ValueError('Unavailable generation telemetry must use typed nulls')
    return row


def require_pair(base, distilled):
    if base['variant'] != 'base' or distilled['variant'] != 'distilled' or not distilled['adapter']:
        raise ValueError('Comparison requires an original base and clean distilled adapter')
    differences = [key for key in base if key not in ('variant', 'adapter', 'protocol_sha256', 'model_identity') and base[key] != distilled.get(key)]
    left = {k: v for k, v in base['model_identity'].items() if k != 'adapter_manifest_sha256'}
    right = {k: v for k, v in distilled['model_identity'].items() if k != 'adapter_manifest_sha256'}
    if differences or left != right or set(base) != set(distilled):
        raise ValueError(f'Base/distilled settings differ: {differences or ["model_identity"]}')
