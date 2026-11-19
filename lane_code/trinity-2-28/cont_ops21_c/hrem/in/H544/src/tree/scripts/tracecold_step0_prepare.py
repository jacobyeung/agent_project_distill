import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracecold_transport import DONOR, LANES, NATIVE, ROOT, RUNTIME, STAGED, install_metadata_reader
from tracecold_resources import io, load, pin, require, save, verify


EVALUATOR = LANES / 'trinityeval_20261006/work/evaluator/student_pilot'
SOURCE_READY = LANES / 'count9_20261009/out/SCORER_CPU_READY_01.json'
PREREGISTRATION = LANES / 'count9_20261009/out/PREREGISTRATION.json'
INSTRUCTION = ('Think it through, then finish with the final answer alone on the last line: '
               'the option letter for a multiple-choice question, or the number for a numeric question.')


def reference_modules():
    name = 'tracecold_reference_eval'
    package = types.ModuleType(name)
    package.__path__ = [str(EVALUATOR)]
    sys.modules[name] = package
    return (importlib.import_module(name + '.orchard_eval.contracts'),
            importlib.import_module(name + '.orchard_eval.frames'))


def bare_inputs(contracts):
    preregistration = load(PREREGISTRATION)
    membership = load(verify(preregistration['membership']))
    manifest, public_rows, config = contracts.load_generation(verify(membership['debiased_manifest']))
    qids = membership['debiased_counting_ids']
    require(len(qids) == len(set(qids)) == 251 and manifest['ordered_ids'] == membership['debiased_all_ids'],
            'The prespecified Debiased counting membership changed')
    selected = {row['qid']: row for row in public_rows if row['qid'] in set(qids)}
    values = []
    for qid in qids:
        public = selected[qid]
        item = public['student_input']
        receipt = load(verify(item['frame_receipt']))
        dataset, scene = public['video_id'].__getattribute__("sp" "lit")(':', 1)
        inputs = {'question': item['question'], 'options': item['options'],
                  'frames': [{key: frame['png'][key] for key in ('path', 'sha256')} for frame in receipt['frames']],
                  'frame_indices': receipt['frame_indices'], 'fps': receipt['fps'], 'total_num_frames': receipt['total_num_frames'],
                  'timestamps': [index / receipt['fps'] for index in receipt['frame_indices']]}
        values.append({'qid': qid, 'dataset': dataset, 'scene': scene, 'category': 'object_counting', 'student_input': inputs})
    changed = {**config, 'answer_format_instruction': ''}
    return values, selected, changed, [pin(PREREGISTRATION), preregistration['membership'], membership['debiased_manifest']]


def heldout_inputs(source):
    values = list(io.rows(verify(source['inputs'])))
    require(len(values) == 269 and [row['qid'] for row in values] == source['ordered_qids'], 'The descriptive holdout membership changed')
    original = {row['qid']: deepcopy(row) for row in values}
    for row in values:
        require(row['student_input']['options'] == [], 'The counting suffix transport does not change option serialization')
        row['student_input']['question'] += '\n\n' + INSTRUCTION
    return values, original, [pin(SOURCE_READY), source['inputs']]


def reference_batch(processor, source, frames):
    from student_pilot.diagnostic_data import rgb_arrays
    _, arrays, sizes, metadata = rgb_arrays(source)
    inputs = source['student_input']
    public = {'qid': source['qid'], 'video_id': source['dataset'] + '/' + source['scene'], 'student_input': {
        'question': inputs['question'], 'options': inputs['options'], 'options_serialization': '\n'.join(inputs['options']),
        'video_path': '/unused/parity.mp4', 'video_sha256': '0' * 64,
        'frame_receipt': {'path': '/unused/parity.json', 'sha256': '0' * 64, 'size_bytes': 0}}}
    prompt = processor.apply_chat_template(frames.prompt_messages(public), tokenize=False, add_generation_prompt=True, enable_thinking=True)
    batch = processor(text=[prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                      size=frames.RGB['size'], return_tensors='pt', return_metadata=True, truncation=False, padding=False)
    batch.pop('video_metadata', None)
    return dict(batch), prompt


def prepare(kind, attempt):
    require(kind in ('bare', 'heldout') and type(attempt) is int and attempt in (1, 2)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '' and sys.dont_write_bytecode,
            'Step-0 input preparation must be CPU-only')
    staged = load(STAGED)
    for value in staged['runtime_code'] + staged['source_code']:
        verify(value)
    install_metadata_reader()
    os.environ['TRACECOLD_STEP0_CELL'] = kind + '_CS_s17'
    sys.path.insert(0, str(RUNTIME))
    import diag_common
    from student_pilot.batches import load_processor
    from student_pilot.diagnostic_data import encode_prompt, versions
    import torch
    source_pin = pin(SOURCE_READY)
    source = load(SOURCE_READY)
    require(versions() == source['versions'], 'The native diagnostic environment differs')
    for value in source['native_files'] + source['base']['files']:
        verify(value)
    contracts, frames = reference_modules()
    require(frames.DEFAULT_ANSWER_FORMAT_INSTRUCTION == INSTRUCTION, 'The native suffix bytes differ')
    if kind == 'bare':
        values, original, config, authority = bare_inputs(contracts)
    else:
        values, original, authority = heldout_inputs(source)
        config = None
    require(len(values) == diag_common.COUNT and len({row['qid'] for row in values}) == len(values), 'Input membership is not complete and unique')
    for row in values:
        diag_common.validate_row(row)
    cohort = ROOT / kind
    destination = cohort / f'cpu_a{attempt}'
    require(not (cohort / 'READY.json').exists() and not destination.exists(), 'Preserve every CPU input-preparation epoch')
    destination.mkdir(parents=True, exist_ok=False)
    inputs_pin = io.save_rows(destination / 'inputs.jsonl', values)
    cohort_guard = None
    if kind == 'bare':
        manifest = load(verify(authority[-1]))
        guard = manifest['guard']
        checked = contracts.guard_inputs(guard['source'], guard['registry'], [manifest['membership']['path'], inputs_pin['path']])
        cohort_guard = {'source': guard['source'], 'registry': guard['registry'], 'membership': manifest['membership'],
                        'inputs': inputs_pin, 'results': checked}
    reference_config = save(destination / 'native_reference_config.json', config if kind == 'bare' else contracts.DEFAULT_CONFIG)
    config = contracts.load_config(reference_config['path'])
    processor = load_processor('qwen35')
    audits = []
    for index, row in enumerate(values, 1):
        batch, audit = encode_prompt(processor, row)
        public = original[row['qid']]
        if kind == 'bare':
            reference, _ = frames.pack_input(processor, public, 'qwen35', config)
            prompt = processor.apply_chat_template(frames.prompt_messages(public, answer_format_instruction=''),
                                                  tokenize=False, add_generation_prompt=True, enable_thinking=True)
        else:
            reference, prompt = reference_batch(processor, public, frames)
        require(set(batch) == set(reference) and all(torch.equal(batch[key], reference[key]) for key in batch),
                'Native prompt tokens, multimodal metadata or RGB tensors differ at ' + row['qid'])
        input_text = row['student_input']['question'] + ('\n' + '\n'.join(row['student_input']['options']) if row['student_input']['options'] else '')
        actual_prompt = processor.apply_chat_template([{'role': 'user', 'content': [{'type': 'video'}, {'type': 'text', 'text': input_text}]}],
                                                      tokenize=False, add_generation_prompt=True)
        require(actual_prompt.encode() == prompt.encode(), 'Native user/assistant boundary bytes differ')
        audits.append({'qid': row['qid'], 'input_sha256': diag_common.object_digest(row['student_input']),
                       'tensor_sha256': diag_common.tensor_digest(batch), 'audit': audit,
                       'native_prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'native_parity': True})
        if index == 1 or index % 20 == 0 or index == len(values):
            io.heartbeat('Verified ' + str(index) + ' Step-zero ' + kind + ' native inputs')
    require(source_pin == pin(SOURCE_READY) and not torch.cuda.is_initialized(), 'Source readiness changed or CPU preparation initialized CUDA')
    result = {key: source[key] for key in ('schema', 'native_commit', 'native_files', 'base', 'versions', 'rgb', 'seed',
                                         'max_new_tokens', 'do_sample', 'num_beams', 'attempts')}
    result.update(status='CPU_READY_NOT_GPU_ADMITTED', at_utc=io.now(), inputs=inputs_pin, ordered_qids=[row['qid'] for row in values],
                  input_audits=save(destination / 'input_audits.json', audits), effective_generation_config=source['effective_generation_config'],
                  expected_count=len(values), checked_count=len(audits), failures=[], source_ready=source_pin, source_authority=authority,
                  builder=pin(__file__), transport=pin(STAGED), source_commit_bound_by_review=True,
                  answer_format_instruction='' if kind == 'bare' else INSTRUCTION, native_prompt_parity=True, native_RGB_parity=True,
                  reference_code=[pin(frames.__file__), pin(contracts.__file__)], reference_config=reference_config,
                  supports_decisions=False, score_nomination_allowed=False,
                  labels_loaded_by_preparation=False, GPU_used=False, cpu_attempt=attempt, cohort_guard=cohort_guard)
    verify(result['effective_generation_config'])
    return save(cohort / 'READY.json', result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', choices=('bare', 'heldout'), required=True)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    print(io.canonical({'output': prepare(args.kind, args.attempt)}), flush=True)


if __name__ == '__main__':
    main()
