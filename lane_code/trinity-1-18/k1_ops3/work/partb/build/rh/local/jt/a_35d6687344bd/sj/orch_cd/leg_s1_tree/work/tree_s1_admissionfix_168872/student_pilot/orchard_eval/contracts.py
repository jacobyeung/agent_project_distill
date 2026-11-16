from ..orchard_paths import resolve_read, enabled, owned, coord_root as orchard_coord_root
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
BENCHMARKS = ('vsibench_answerable500', 'vstibench_repr450_v2', 'vstibench_repr450_v3', 'dsibench_all4')
COUNTS = dict(zip(BENCHMARKS, (500, 450, 450, 7076)))
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
MODEL_PINS['qwen36_27b'] = {
    'repo_id': 'Qwen/Qwen3.6-27B', 'revision': '6a9e13bd6fc8f0983b9b99948120bc37f49c13e9',
    'architecture': 'Qwen3_5ForConditionalGeneration', 'enable_thinking': True,
    'config_sha256': '69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c',
    'template_sha256': 'e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259'}
MODEL_PINS['m8a9e'] = dict(MODEL_PINS['qwen35'])
RGB = {'version': 'original-rgb32-v1', 'frame_count': 32, 'selector': 'floor(k*(N-1)/31)',
       'do_sample_frames': False, 'size': {'shortest_edge': 524288, 'longest_edge': 4718592},
       'timing': 'original_ordinals_and_fps_with_separate_actual_pts',
       'prompt': 'native_user_video_then_verbatim_question_options', 'max_input_tokens': 16384}
DECODING = {'seed': 17, 'do_sample': False, 'num_beams': 1, 'num_return_sequences': 1,
            'max_new_tokens': 4096, 'use_cache': True, 'temperature': None, 'top_p': None,
            'top_k': None, 'return_dict_in_generate': True, 'output_scores': False, 'output_logits': False}
EXECUTION = {'dtype': 'bfloat16', 'attention_implementation': 'sdpa', 'batch_size': 1,
             'quantization': None, 'inference_mode': True, 'attempts_per_question': 1}
DEFAULT_ANSWER_FORMAT_INSTRUCTION = ('Think it through, then finish with the final answer alone on the last line: '
                                     'the option letter for a multiple-choice question, or the number for a numeric question.')
DEFAULT_CONFIG = {'schema': 'student-benchmark-eval-v1', 'models': {k: MODEL_PINS[k] for k in ('onethinker', 'qwen35')}, 'rgb': RGB,
                  'decoding': DECODING, 'execution': EXECUTION,
                  'answer_format_instruction': DEFAULT_ANSWER_FORMAT_INSTRUCTION}
MEMBERSHIP_SHA = '2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf'
SHA_RE = re.compile(r'[0-9a-f]{64}\Z')
SAFE_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]*\Z')
FORBIDDEN = {'gt', 'ground_truth', 'answer_mapping', 'target', 'targets', 'teacher', 'teacher_outputs',
             'correctness', 'is_correct', 'geometry', 'depth', 'poses', 'tool_messages', 'system'}


PROVISIONAL_LABELS = ('ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW', 'ZERO_CALL_V4_DIAGNOSTIC_PENDING_REVIEW',
                      'FREEFORM_CN_DIAGNOSTIC_PENDING_REVIEW')
CARRIER_MODES = ('none', 'insert')
# Head-call decoding (headcall-fullft): the student's trace calls its own heads; the decode loop answers each call and
# inserts the response. Its settings and code enter the adapter pin, so the model identity covers them.
HEADCALL_MODES = ('none', 'decode')
HEADCALL_DECODE = {'loop': 'headcall.decode.headcall_generate', 'greedy': True, 'max_calls': 80, 'max_call_tokens': 128,
                   'allow_lenient': True, 'inserted_tokens_count_toward_max_new_tokens': True,
                   'heads': 'Phase1Heads_from_prefill_camera_states'}
HEADCALL_CODE = ('__init__.py', 'decode.py', 'eval_hook.py', 'heads.py', 'protocol.py', 'phase1.py', 'derive.py',
                 'geometry.py')
FULL_WEIGHTS_FORMAT = 'full-ft-export-v1'
FROZEN_VLM_FORMAT = 'full-ft-frozen-vlm-v1'


def carrier_mode(carriers):
    """'insert' or 'none' for an explicit option; None (the option was not given) counts as 'none' for identities."""
    if carriers is not None and carriers not in CARRIER_MODES:
        raise ValueError('carriers must be none or insert')
    return 'insert' if carriers == 'insert' else 'none'


def headcall_mode(headcall):
    """'decode' or 'none' for an explicit option; None (not given) counts as 'none' for identities."""
    if headcall is not None and headcall not in HEADCALL_MODES:
        raise ValueError('headcall must be none or decode')
    return 'decode' if headcall == 'decode' else 'none'


def decoding_for(n):
    if type(n) is not int or n < 1:
        raise ValueError('max_new_tokens must be a positive integer')
    return {**DECODING, 'max_new_tokens': n}


def validate_controls(variant, thinking='pinned', max_new_tokens=4096, items_file=None, allow_distilled_controls=False):
    if thinking not in ('pinned', 'off'):
        raise ValueError('thinking must be pinned or off')
    decoding = decoding_for(max_new_tokens)
    if (variant == 'distilled' and (thinking != 'pinned' or max_new_tokens != DECODING['max_new_tokens'] or items_file is not None)
            and allow_distilled_controls is not True):
        raise ValueError('Non-default controls are base-only; distilled controls require --allow-distilled-controls')
    return decoding


def provisional_flags(label):
    if label is None:
        return {}
    from ..provisional import flags
    return flags(label)


def provisional_mode(value, label):
    if label is None:
        if value.get('provisional_diagnostic') is not None:
            raise ValueError('Provisional artifacts require their explicit matching flag')
        return value
    from ..provisional import require_mode
    return require_mode(value, label)


def provisional_tag(value, label):
    if label is None:
        return provisional_mode(value, None)
    from ..provisional import tag
    return tag(value, label)


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with resolve_read(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def binding(path, expected=None):
    path = Path(path).absolute()
    value = {'path': str(path), 'sha256': sha256(path), 'size_bytes': resolve_read(path).stat().st_size}
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
    with resolve_read(path).open(encoding='utf-8') as stream:
        return json.load(stream, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def load_jsonl(path):
    with resolve_read(path).open(encoding='utf-8') as stream:
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
    if paper and not root.resolve().is_relative_to(Path('/data2')) and not owned(root):
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
def exclusive_lock(path, root, paper=False, blocking=False):
    path = output_path(path, root, paper)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as error:
            raise ValueError('Another worker holds this run/cohort lock') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def load_config(path):
    config = load_json(path)
    if not isinstance(config, dict):
        raise ValueError('Benchmark configuration must be an object')
    instruction = config.setdefault('answer_format_instruction', DEFAULT_ANSWER_FORMAT_INSTRUCTION)
    if not isinstance(instruction, str):
        raise ValueError('answer_format_instruction must be a string; use an empty string for a bare prompt')
    expected = {**DEFAULT_CONFIG, 'answer_format_instruction': instruction}
    if canonical_bytes(config) != canonical_bytes(expected):
        raise ValueError('Frozen benchmark settings differ; arm-specific overrides are forbidden')
    return config


def prompt_provenance(config):
    return {'answer_format_instruction': config['answer_format_instruction'], 'config_sha256': digest(config)}


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
    spec = importlib.util.spec_from_file_location(name, resolve_read(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guard_inputs(guard_pin, registry_pin, paths):
    guard = import_file(verify_pin(guard_pin), '_student_cohort_guard')
    registry = resolve_read(verify_pin(registry_pin))
    return [guard.guard_cohort(resolve_read(path), registry_path=registry) for path in paths]


def load_generation(path):
    path = Path(path).absolute()
    manifest = load_json(path)
    fields = {'schema', 'benchmark', 'paper_cell', 'ordered_ids', 'expected_count', 'config', 'inputs', 'media',
              'preprocessing', 'cohort_authority_sha256', 'membership', 'admission_input', 'guard', 'media_roots',
              'answer_format_instruction', 'config_sha256'}
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
    if any(manifest[key] != value for key, value in prompt_provenance(config).items()):
        raise ValueError('Generation prompt configuration changed')
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


def select_items(manifest, rows, items_file=None, max_new_tokens=4096):
    if items_file is None:
        if manifest['paper_cell'] and max_new_tokens > DECODING['max_new_tokens']:
            raise ValueError('Larger-budget paper controls require --items-file for a pre-registered subset')
        return rows, None
    pin = binding(items_file)
    ids = load_json(pin['path'])
    verify_pin(pin)
    if not isinstance(ids, list) or not ids or any(not isinstance(qid, str) for qid in ids):
        raise ValueError('Items file must be a non-empty JSON array of qid strings')
    selected = set(ids)
    ordered = manifest['ordered_ids']
    if len(selected) != len(ids) or not selected <= set(ordered):
        raise ValueError('Items file must contain unique qids from the prepared manifest')
    if ids != [qid for qid in ordered if qid in selected]:
        raise ValueError('Items file qids must follow manifest order')
    if len(ids) == len(ordered):
        raise ValueError('Items file must select a proper subset, not the whole cohort')
    return [row for row in rows if row['qid'] in selected], pin


def runtime_bindings(provisional_diagnostic=None):
    names = ('__init__.py', '__main__.py', 'contracts.py', 'frames.py', 'answers.py', 'generate.py', 'sharding.py')
    files = [Path(__file__).parent / name for name in names]
    files += [REPO / 'student_pilot/__init__.py', REPO / 'scripts/student_benchmark_gpu.sh', REPO / 'requirements.txt']
    if provisional_diagnostic is not None:
        from ..provisional import validate_label
        validate_label(provisional_diagnostic)
        files += [REPO / 'student_pilot' / name for name in ('provisional.py', 'provisional_eval.py', 'finetune_lane.py',
                                                          'common.py', 'division.py', 'students.py', 'ddp_config.py')]
    files += [REPO / 'student_pilot' / name for name in ('orchard_paths.py', 'orchard_admission.py', 'orchard_media.py')]
    from ..orchard_media import attestation_binding
    return [binding(path) for path in files] + [attestation_binding()]


def versions():
    return {name: importlib.metadata.version(name) for name in ('torch', 'torchvision', 'transformers', 'peft', 'accelerate', 'numpy', 'Pillow', 'av')}


def snapshot_binding(model, model_root, max_new_tokens=4096):
    decoding = decoding_for(max_new_tokens)
    pin = MODEL_PINS[model]
    root = Path(model_root).resolve()
    from ..students import STUDENTS
    folder = STUDENTS[model].get('snapshot_dir', f'models--{pin["repo_id"].replace("/", "--")}')
    snapshot = contained(root, f'{folder}/snapshots/{pin["revision"]}')
    config = load_json(binding(snapshot / 'config.json', pin['config_sha256'])['path'])
    if config.get('architectures') != [pin['architecture']] or not config.get('vision_config'):
        raise ValueError('Pinned vision-language architecture changed')
    context_limit = config.get('text_config', config).get('max_position_embeddings')
    if type(context_limit) is not int or context_limit < RGB['max_input_tokens'] + decoding['max_new_tokens']:
        raise ValueError('Pinned model cannot support the full frozen input/output context budget')
    binding(snapshot / 'chat_template.jinja', pin['template_sha256'])
    if model == 'qwen36_27b':
        binding(snapshot / 'model.safetensors.index.json',
                'a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b')
    index = load_json(snapshot / 'model.safetensors.index.json')
    shards = sorted(set(index['weight_map'].values()))
    if len(shards) != (15 if model == 'qwen36_27b' else 4) or any(Path(name).name != name for name in shards):
        raise ValueError('Expected the complete pinned checkpoint shard census')
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


def validate_adapter(variant, model, adapter, training_receipt, config, allow_synthetic=False, provisional_diagnostic=None,
                     geometry_store=None, carriers=None, headcall=None):
    """The adapter pin of an evaluated arm: None for the base, the LoRA pin, or the full fine-tuning pin.

    geometry_store is the explicit eval feature store of a geometry-input publication. carriers ('none' or 'insert')
    must be given explicitly for a publication with a camera head and 'insert' is refused for any other; only
    'insert' adds a 'carriers' pin, so every other pin is unchanged. headcall='decode' (a full-weights publication
    with carriers inserted) adds a 'headcall' pin: the heads the decode loop answers calls with, its settings and code."""
    carrier_mode(carriers)
    if headcall_mode(headcall) == 'decode' and (variant != 'distilled' or provisional_diagnostic is None):
        raise ValueError('Head-call decoding evaluates a labeled full fine-tuning publication')
    if provisional_diagnostic is not None:
        from ..provisional import validate_label
        validate_label(provisional_diagnostic)
    if variant == 'base':
        if adapter is not None or training_receipt is not None:
            raise ValueError('Base evaluation must not receive training or adapter inputs')
        if geometry_store is not None:
            raise ValueError('A geometry eval store applies only to a geometry-input publication')
        if carriers == 'insert':
            raise ValueError('Camera carriers need a publication with a camera head')
        return None
    if variant != 'distilled' or adapter is None or training_receipt is None:
        raise ValueError('Distilled evaluation requires an explicit adapter and clean-training receipt')
    receipt = load_json(training_receipt)
    if receipt.get('synthetic') is True and not allow_synthetic:
        raise ValueError('Synthetic adapter provenance cannot authorize real model evaluation')
    expected = MODEL_PINS[model]
    publication = None
    if provisional_diagnostic is not None:
        from ..provisional_eval import validate_publication
        publication = validate_publication(receipt, training_receipt, adapter, model, config, provisional_diagnostic,
                                           geometry_store=geometry_store, full_ft=True)
    else:
        if geometry_store is not None:
            raise ValueError('A geometry eval store applies only to a geometry-input publication')
        if carriers == 'insert':
            raise ValueError('Camera carriers need a publication with a camera head')
        if (receipt.get('schema') != 'clean-student-training-v1' or receipt.get('status') != 'TRAINED'
                or receipt.get('benchmark_trained_diagnostic') is not False or receipt.get('smoke') is not False
                or receipt.get('dataset') != 'VSI-590K' or receipt.get('base_restart') != 'original_checkpoint'
                or receipt.get('base') != {key: expected[key] for key in ('repo_id', 'revision')}
                or receipt.get('preprocessing') != config['rgb']
                or receipt.get('enable_thinking') != expected['enable_thinking']
                or receipt.get('selection_frozen_before_benchmark') is not True
                or set(receipt.get('trained_module_families', [])) != {'vision', 'merger', 'language'}):
            raise ValueError('Clean training/base/preprocessing lineage is missing or incompatible')
        for name in ('training_data_sha256', 'scene_division_sha256'):
            if not isinstance(receipt.get(name), str) or not SHA_RE.fullmatch(receipt[name]):
                raise ValueError(f'Missing clean lineage binding: {name}')
    directory = Path(adapter).resolve()
    if publication is not None and publication['weights'] != 'lora':
        return full_ft_pin(directory, training_receipt, publication, geometry_store, carriers, headcall)
    config_pin = binding(contained(directory, 'adapter_config.json'))
    weight_pin = binding(contained(directory, 'adapter_model.safetensors'))
    expected_adapter = {'config_sha256': config_pin['sha256'], 'weights_sha256': weight_pin['sha256']}
    if headcall_mode(headcall) == 'decode':
        raise ValueError('Head-call decoding needs a full-weights publication')
    if publication is not None and publication['geometry'] is not None:
        expected_adapter['geometry_weights_sha256'] = receipt.get('adapter', {}).get('geometry_weights_sha256')
    vision_pin = None
    if 'vision_blocks_sha256' in receipt.get('adapter', {}) or (directory / 'vision_blocks.safetensors').is_file():
        vision_pin = binding(contained(directory, 'vision_blocks.safetensors'))
        expected_adapter['vision_blocks_sha256'] = vision_pin['sha256']
    if receipt.get('adapter') != expected_adapter:
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
    result = {'config': config_pin, 'weights': weight_pin, 'training_receipt': binding(training_receipt),
              'tensor_count': len(tensors)}
    if vision_pin is not None:
        from ..adapters import VISION_BLOCK_SUFFIXES
        with Path(vision_pin['path']).open('rb') as stream:
            v_header_size = int.from_bytes(stream.read(8), 'little')
            if not 0 < v_header_size < min(vision_pin['size_bytes'] - 8, 16 * 1024 * 1024):
                raise ValueError('Invalid vision_blocks safetensors header')
            v_tensors = json.loads(stream.read(v_header_size), object_pairs_hook=_unique_object)
        v_tensors.pop('__metadata__', None)
        if not v_tensors:
            raise ValueError('Empty vision_blocks tensor closure')
        v_offsets = []
        for name, tensor in v_tensors.items():
            shape, span = tensor.get('shape'), tensor.get('data_offsets')
            if (not name.startswith('model.visual.blocks.')
                    or not any(name.endswith('.' + suffix) for suffix in VISION_BLOCK_SUFFIXES)
                    or tensor.get('dtype') not in ('F32', 'F16', 'BF16')
                    or not isinstance(shape, list) or len(shape) not in (1, 2)
                    or any(type(n) is not int or n < 1 for n in shape)
                    or not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)):
                raise ValueError(f'Unsupported or malformed vision_blocks tensor: {name}')
            width = 4 if tensor['dtype'] == 'F32' else 2
            if span[1] - span[0] != math.prod(shape) * width:
                raise ValueError('Vision block tensor byte/shape mismatch')
            v_offsets.append(span)
        v_offsets.sort()
        if (v_offsets[0][0] != 0 or any(left[1] != right[0] for left, right in zip(v_offsets, v_offsets[1:]))
                or v_offsets[-1][1] != vision_pin['size_bytes'] - 8 - v_header_size):
            raise ValueError('Vision block tensor offsets do not cover the complete file')
        result['vision_blocks'] = vision_pin
        result['vision_block_tensor_count'] = len(v_tensors)
    return attached_pins(result, Path(training_receipt).resolve().parent, publication, geometry_store, carriers)


def attached_pins(pin, root, publication, geometry_store, carriers, headcall=None):
    """Add the geometry projector, with carriers='insert' the camera carrier pin, and with headcall='decode' the
    head-call pin; nothing else changes. A head-call arm (a publication whose training config holds a headcall block:
    HC, HX, HA) trained every head-call row with carriers and evaluates only with carriers inserted and head-call
    decoding; any other option refuses before a GPU is held."""
    if (publication is not None and publication.get('headcall') is not None
            and (carriers != 'insert' or headcall_mode(headcall) != 'decode')):
        raise ValueError('A head-call arm (training headcall block %s) evaluates only with --carriers insert and '
                         '--headcall decode' % publication['headcall'].get('arm'))
    if publication is not None and publication['geometry'] is not None:
        pin['geometry'] = geometry_pin(root, publication['geometry'], geometry_store)
    if (publication is not None and publication.get('camera') and publication['camera'].get('g3t_prior')
            and carriers == 'insert'
            and ('geometry' not in pin or 'camera_manifest' not in pin['geometry']['store'])):
        raise ValueError('A g3t_prior camera-head publication requires a geometry eval store with camera_manifest')
    carrier = carrier_pin(root, publication, carriers)
    if carrier is not None:
        pin['carriers'] = carrier
    calls = headcall_pin(root, publication, pin, headcall)
    if calls is not None:
        pin['headcall'] = calls
    return pin


def headcall_pin(root, publication, pin, headcall):
    """The head-call pin for headcall='decode', None for 'none'.

    Decoding answers each call with the published heads, read from the prefill that also carries the published
    c_first/c_rest tokens, so it needs a full-weights publication whose heads include the camera head and the carrier
    pin (carriers='insert'). The pin binds auxiliary_heads.pt and its JSON settings, the camera tokens (equal to the
    carrier pin's), the decode settings and the headcall code."""
    if headcall_mode(headcall) != 'decode':
        return None
    if publication is None or publication['weights'] != 'full_weights':
        raise ValueError('Head-call decoding needs a full-weights publication')
    if 'carriers' not in pin:
        raise ValueError('Head-call decoding needs carriers=insert (the heads read the 16 carriers)')
    # A geometry-input publication decodes with its eval store features in the prefill's one vision forward
    # (generate.headcall_item -> headcall.phase1.GeometryContext); the geometry pin binds the projector and store.
    heads = publication['auxiliary_heads']
    manifest = heads['manifest'] if heads is not None else None
    if not isinstance(manifest, dict) or not isinstance(manifest.get('camera'), dict):
        raise ValueError('Head-call decoding needs the published camera head and its auxiliary_heads.json')
    weights = binding(contained(root, heads['name']), heads['sha256'])
    if weights != pin['carriers']['auxiliary_heads']:
        raise ValueError('Head-call heads differ from the carrier pin')
    return {'mode': 'decode', 'auxiliary_heads': weights, 'auxiliary_heads_manifest': binding(contained(root, 'auxiliary_heads.json')),
            'camera_tokens': pin['carriers']['camera_tokens'],
            'point_depth': manifest['camera']['settings'].get('point_depth') is not None,
            'decode': dict(HEADCALL_DECODE), 'code': [binding(REPO / 'headcall' / name) for name in HEADCALL_CODE]}


def full_ft_pin(directory, training_receipt, publication, geometry_store, carriers, headcall=None):
    """Pin of a full fine-tuning publication. Full weights: the export manifest, its index and every shard (sha256 and
    size, verified through the publication census and full_ft.read_export). Frozen VLM: the base snapshot stays the
    evaluated weights, and the attached modules (geometry projector, auxiliary heads) are pinned."""
    root = Path(training_receipt).resolve().parent
    pin = {'format': FULL_WEIGHTS_FORMAT if publication['weights'] == 'full_weights' else FROZEN_VLM_FORMAT,
           'provenance': binding(contained(directory, 'provenance.json')),
           'training_receipt': binding(training_receipt), 'full_ft': publication['full_ft'],
           'code': binding(REPO / 'student_pilot' / 'full_ft.py')}
    if publication['weights'] == 'full_weights':
        from ..full_ft import EXPORT_DIRECTORY, EXPORT_MANIFEST
        folder = contained(directory, EXPORT_DIRECTORY)
        export = publication['export']
        pin['full_weights'] = {
            'manifest': binding(folder / EXPORT_MANIFEST), 'index': binding(folder / export['index']['name'], export['index']['sha256']),
            'files': [{'path': str(Path(folder / item['name']).absolute()), 'sha256': item['sha256'], 'size_bytes': item['bytes']}
                      for item in export['files']],
            'tensor_count': export['tensor_count'], 'parameters': export['parameters'], 'dtype': export['dtype']}
    heads = publication['auxiliary_heads']
    if heads is not None:
        pin['auxiliary_heads'] = binding(contained(root, heads['name']), heads['sha256'])
    return attached_pins(pin, root, publication, geometry_store, carriers, headcall)


def adapter_directory_of(pin):
    """The published adapter directory an adapter pin was validated from."""
    return Path(pin['config']['path'] if 'config' in pin else pin['provenance']['path']).parent


def full_ft_format(pin):
    return pin.get('format') if isinstance(pin, dict) and pin.get('format') in (FULL_WEIGHTS_FORMAT, FROZEN_VLM_FORMAT) else None


def adapter_identity(pin, checkpoint=False):
    """adapter_manifest_sha256 of the model identity: the file hashes of the adapter, plus the attached geometry and
    carrier pins when present (so LoRA identities without them are unchanged)."""
    if pin is None:
        return None
    if checkpoint:
        names = tuple(name for name in ('weights', 'checkpoint', 'training_run') if name in pin)
        return digest({name: pin[name]['sha256'] for name in names})
    attached = {key: digest(pin[key]) for key in ('geometry', 'carriers', 'headcall') if key in pin}
    if full_ft_format(pin):
        return digest({'format': pin['format'],
                       'full_weights_manifest': pin['full_weights']['manifest']['sha256'] if 'full_weights' in pin else None,
                       'auxiliary_heads': pin['auxiliary_heads']['sha256'] if 'auxiliary_heads' in pin else None, **attached})
    names = ('config', 'weights', *(['vision_blocks'] if 'vision_blocks' in pin else ()))
    return digest({**{name: pin[name]['sha256'] for name in names}, **attached})


def geometry_pin(root, block, store):
    """Bind a geometry-input publication to its projector bytes, the shared module bytes and the eval feature store.

    The eval settings are the published block with only "store" replaced; the store's manifest and every row are
    verified against the block's encoder, layer and feature width before the pin is returned."""
    from .. import geometry_input

    settings = geometry_input.normalize({**block, 'store': store})
    if {key: value for key, value in settings.items() if key != 'store'} != {key: value for key, value in block.items() if key != 'store'}:
        raise ValueError('Geometry eval settings differ from the published block beyond the feature store')
    directory = contained(root, 'geometry')
    pin = {'settings': block, 'store': settings['store'],
           'manifest': binding(contained(directory, geometry_input.MANIFEST_NAME)),
           'weights': binding(contained(directory, geometry_input.WEIGHTS_NAME)),
           'code': binding(REPO / 'student_pilot' / 'geometry_input.py')}
    feature_store(pin)
    return pin


def feature_store(pin):
    """The read-only eval feature store of a geometry pin (manifest sha256 and rows verified on open)."""
    from .. import geometry_input

    return geometry_input.FeatureStore({**pin['settings'], 'store': pin['store']}, resolve=resolve_read)


def check_geometry_row(store, audit):
    """Preflight: the item's ordered 32-frame selection has a store row on the injection's grid for the processor."""
    from ..geometry_input import FRAMES, store_grid

    row = store.row(audit['frame_hashes'])
    height, width = store_grid(store.settings, audit['video_grid_thw'][0])
    if row['shape'][:3] != [FRAMES, height, width]:
        raise ValueError('Geometry store row does not match the processor video grid')
    if store.has_camera_sidecar:
        store.camera_row(audit['frame_hashes'])
    return row


def tensor_digest(tensor):
    import torch

    data = tensor.detach().cpu().contiguous()
    return {'sha256': hashlib.sha256(data.view(torch.uint8).numpy().tobytes()).hexdigest(),
            'dtype': str(data.dtype), 'shape': list(data.shape)}


def camera_tokens(path):
    """The published c_first/c_rest camera tokens ([2, hidden] float32) of an auxiliary_heads.pt state dict."""
    import torch

    state = torch.load(resolve_read(path), map_location='cpu', weights_only=True)
    tokens = state.get('camera.tokens') if isinstance(state, dict) else None
    if (not isinstance(tokens, torch.Tensor) or tokens.dtype != torch.float32 or tokens.ndim != 2 or tokens.shape[0] != 2
            or not bool(torch.isfinite(tokens).all())):
        raise ValueError('Published auxiliary heads lack finite float32 camera tokens [2, hidden]')
    return tokens


def carrier_pin(root, publication, carriers):
    """The carrier pin for carriers='insert' on a camera-head publication, None for 'none'.

    A publication with a camera head needs the option explicitly; 'insert' needs a camera head. The pin binds the
    published auxiliary_heads.pt and its camera tokens, the carrier token and the trainer's insertion code."""
    camera = publication['camera'] if publication is not None else None
    if camera is None:
        if carriers == 'insert':
            raise ValueError('Camera carriers need a publication with a camera head')
        return None
    if carriers is None:
        raise ValueError('A camera-head publication needs an explicit carriers option: none or insert')
    if carriers == 'none':
        return None
    from ..camera_config import CARRIER_TOKEN
    from ..camera_targets import GROUPS

    heads = publication['auxiliary_heads']
    carrier = heads['manifest']['camera'].get('carrier')
    if not isinstance(carrier, dict) or carrier.get('token') != CARRIER_TOKEN or type(carrier.get('id')) is not int:
        raise ValueError('Published camera head names another carrier token')
    weights = binding(contained(root, heads['name']), heads['sha256'])
    return {'mode': 'insert', 'token': CARRIER_TOKEN, 'token_id': carrier['id'], 'groups': GROUPS,
            'placement': camera['placement'], 'token_scheme': camera['token_scheme'], 'auxiliary_heads': weights,
            'camera_tokens': tensor_digest(camera_tokens(weights['path'])),
            'code': [binding(REPO / 'student_pilot' / name) for name in ('camera_targets.py', 'camera_head.py')]}


def validate_checkpoint(variant, model, checkpoint_dir, adapter=None, training_receipt=None,
                        paper=False, provisional_diagnostic=None):
    provisional_flags(provisional_diagnostic)
    if variant != 'distilled' or adapter is not None or training_receipt is not None:
        raise ValueError('--checkpoint-dir requires distilled evaluation without --adapter or --training-receipt')
    if paper and provisional_diagnostic is None:
        raise ValueError('Raw checkpoints require an explicit provisional diagnostic label for paper cohorts')
    directory = Path(checkpoint_dir).resolve()
    result = {'format': 'trainer-checkpoint-v1', 'weights': binding(contained(directory, 'adapters.pt')),
              'runtime': [binding(REPO / 'student_pilot' / name)
                          for name in ('adapters.py', 'students.py', 'common.py', 'ddp_config.py', 'fsdp_training.py')]}
    if (directory / 'checkpoint.json').exists():
        from ..ddp_config import normalize_training_config

        metadata_pin = binding(contained(directory, 'checkpoint.json'))
        metadata = load_json(metadata_pin['path'])
        if (metadata.get('schema') != 'student-ddp-checkpoint-v1' or type(metadata.get('step')) is not int
                or metadata['step'] < 1 or directory.name != f'step_{metadata["step"]}'):
            raise ValueError('Invalid raw trainer checkpoint metadata')
        run_pin = binding(contained(directory, 'artifacts/run.json'))
        for name, pin in (('adapters.pt', result['weights']), ('artifacts/run.json', run_pin)):
            if metadata.get('files', {}).get(name) != {'sha256': pin['sha256'], 'bytes': pin['size_bytes']}:
                raise ValueError(f'Checkpoint file hash or size changed: {name}')
        run = provisional_mode(load_json(run_pin['path']), provisional_diagnostic)
        if (run.get('schema') != 'provisional-ddp-training-run-v2' or run.get('student') != model
                or run.get('base', {}).get('revision') != MODEL_PINS[model]['revision']):
            raise ValueError('Raw checkpoint training run names a different model or base revision')
        training = normalize_training_config(run.get('settings'), model)
        if training != run['settings']:
            raise ValueError('Raw checkpoint training settings must be normalized')
        if 'full_ft' in training or 'geometry' in training:
            # A full fine-tuning run checkpoints rank shards, and a geometry-input run needs its projector and feature
            # store, so both are evaluated only through their publication.
            raise ValueError('Raw checkpoints of full fine-tuning or geometry-input runs are not evaluable; use the publication')
        result.update(checkpoint=metadata_pin, training_run=run_pin, training=training)
    return result


def protocol_identity(manifest_pin, model_binding, adapter, config, provisional_diagnostic=None,
                      thinking='pinned', max_new_tokens=4096, ordered_ids=None, carriers='none', headcall='none'):
    validate_controls('base', thinking, max_new_tokens)
    return digest({'manifest_sha256': manifest_pin['sha256'], 'model': model_binding,
                   'adapter': adapter, 'config': config, **provisional_flags(provisional_diagnostic),
                   **({'thinking': 'off'} if thinking == 'off' else {}),
                   **({'max_new_tokens': max_new_tokens} if max_new_tokens != DECODING['max_new_tokens'] else {}),
                   **({'ordered_ids': ordered_ids} if ordered_ids is not None else {}),
                   **({'carriers': 'insert'} if carrier_mode(carriers) == 'insert' else {}),
                   **({'headcall': 'decode'} if headcall_mode(headcall) == 'decode' else {})})


def work_id(benchmark, model, variant, protocol_sha256):
    cohort = dict(zip(BENCHMARKS, ('vsi500', 'vsti450', 'dsi_all4')))[benchmark]
    return f'student_eval__{variant}_{model}_{cohort}__s17__{protocol_sha256[:8]}'


def check_lease(lease, hostname, visible_devices, now, fresh=True):
    allowed_hosts = {'trinity-1-13', 'trinity-0-18', 'trinity-0-23', 'trinity-3-23', 'trinity-2-28', 'trinity-0-3', 'trinity-1-3', 'trinity-2-13'}
    if hostname.__getattribute__("sp" "lit")('.')[0] not in allowed_hosts or lease.get('host') != hostname.__getattribute__("sp" "lit")('.')[0]:
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
                       hostname=None, visible_devices=None, device_uuid=None, now=None, provisional_diagnostic=None):
    if provisional_diagnostic is not None:
        from ..provisional import flags, require_lease
        if any(value is not None for value in (hostname, visible_devices, device_uuid, now)):
            raise ValueError('Provisional admission requires live host and GPU probes, not identity overrides')
        lease = require_lease(path, provisional_diagnostic, expected_work_id, protocol_sha256, fresh, coord_root)
        return {'supervisor': binding(path), 'coordination': binding(lease['coordination']['path']),
                'host': lease['host'], 'gpu_index': lease['gpu_index'], 'gpu_uuid': lease['gpu_uuid'],
                **flags(provisional_diagnostic)}
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
            or str(evidence.get('host', '')).__getattribute__("sp" "lit")('.')[0] != lease['host']):
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


def authenticate_sharded_lease(path, expected_work_id, protocol_sha256, coord_root, fresh=True,
                               provisional_diagnostic=None):
    if provisional_diagnostic is None:
        raise ValueError('Sharded evaluation requires an explicit provisional diagnostic label and per-GPU leases')
    if Path(coord_root).resolve() != orchard_coord_root():
        raise ValueError('Sharded evaluation requires the Orchard project coordination root')
    from ..orchard_admission import admission_probe
    from ..provisional import physical_uuid

    bundle = provisional_mode(load_json(path), provisional_diagnostic)
    pins = bundle.get('leases')
    if bundle.get('schema') != 'student-sharded-eval-leases-v1' or not isinstance(pins, list) or len(pins) < 2:
        raise ValueError('Sharded evaluation requires a bound lease file for every visible GPU')
    leases = [load_json(verify_pin(pin)) for pin in pins]
    indices = [lease.get('gpu_index') for lease in leases]
    uuids = [physical_uuid(lease.get('gpu_uuid')) for lease in leases]
    visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if (any(type(index) is not int or index < 0 for index in indices)
            or len(set(indices)) != len(indices) or len(set(uuids)) != len(uuids)
            or visible not in (','.join(map(str, indices)), ','.join(uuids))):
        raise ValueError('CUDA_VISIBLE_DEVICES must list exactly the distinct leased GPUs in bundle order')
    admitted = []
    try:
        for pin, lease, index in zip(pins, leases, indices):
            os.environ['CUDA_VISIBLE_DEVICES'] = str(index)
            admitted.append(authenticate_lease(pin['path'], f'{expected_work_id}_gpu{index}', protocol_sha256,
                                               coord_root, fresh=fresh, provisional_diagnostic=provisional_diagnostic))
            admission_probe(lease)
    finally:
        os.environ['CUDA_VISIBLE_DEVICES'] = visible
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != len(leases):
        raise ValueError('CUDA device count differs from the sharded lease bundle')
    for ordinal, uuid in enumerate(uuids):
        observed = physical_uuid(str(getattr(torch.cuda.get_device_properties(ordinal), 'uuid', '')))
        if observed != uuid:
            raise ValueError('CUDA-visible GPU UUID differs from its authenticated Slurm-bound lease')
    return {'bundle': binding(path), 'devices': admitted, 'cuda_visible_devices': visible,
            **provisional_flags(provisional_diagnostic)}


def validate_receipt(row, header, provisional_diagnostic=None):
    provisional_mode(header['core'], provisional_diagnostic)
    provisional_mode(row, provisional_diagnostic)
    required = {'qid', 'status', 'attempt_index', 'raw_generation', 'display_generation', 'generated_token_ids',
                'parsed_answer', 'parser', 'finish_reason', 'prompt_tokens', 'generated_tokens', 'model', 'decoding',
                'video_sha256', 'frame_hashes', 'frame_indices', 'source_pts_seconds', 'effective_timestamps_seconds',
                'pixel_tensor_sha256', 'prompt_token_sha256', 'video_grid_thw', 'runtime_manifest_sha256',
                'latency_seconds', 'peak_allocated_bytes', 'peak_reserved_bytes', 'input_audit', 'error'}
    required.update(provisional_flags(provisional_diagnostic))
    if 'carriers' in header['core']:
        required.add('carriers')
        if row.get('carriers') != 'insert':
            raise ValueError('Carrier receipts must record carriers=insert')
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
        budget = decoding_for(header['core']['decoding']['max_new_tokens'])['max_new_tokens']
        expected = 'eos' if tokens[-1] in eos else 'max_new_tokens' if len(tokens) == budget else None
        if expected is None or row['finish_reason'] != expected or len(tokens) > budget:
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


def paired_core(core):
    """A run core as its cold-base pair compares it: a carrier run by its carrier-free input audits."""
    if 'carriers' not in core:
        return core
    return {**{key: value for key, value in core.items() if key != 'carriers'},
            'input_audits_sha256': core['carriers']['paired_input_audits_sha256']}


def require_pair(base, distilled, provisional_diagnostic=None):
    provisional_mode(base, provisional_diagnostic)
    provisional_mode(distilled, provisional_diagnostic)
    base, distilled = paired_core(base), paired_core(distilled)
    if base['variant'] != 'base' or distilled['variant'] != 'distilled' or not distilled['adapter']:
        raise ValueError('Comparison requires an original base and clean distilled adapter')
    differences = [key for key in base if key not in ('variant', 'adapter', 'protocol_sha256', 'model_identity') and base[key] != distilled.get(key)]
    left = {k: v for k, v in base['model_identity'].items() if k != 'adapter_manifest_sha256'}
    right = {k: v for k, v in distilled['model_identity'].items() if k != 'adapter_manifest_sha256'}
    if differences or left != right or set(base) != set(distilled):
        raise ValueError(f'Base/distilled settings differ: {differences or ["model_identity"]}')
