import argparse
import hashlib
import os
import sys

from scripts import tracecold_step0_prepare as helper


io = helper.io


def guard_projection(contracts, manifest, inputs_pin, destination):
    values = list(io.rows(io.verify(inputs_pin)))
    admission = io.save(destination / 'admission_input.json', values)
    guard = manifest['guard']
    checked = contracts.guard_inputs(guard['source'], guard['registry'], [manifest['membership']['path'], admission['path']])
    io.verify(inputs_pin)
    return {'source': guard['source'], 'registry': guard['registry'], 'membership': manifest['membership'],
            'inputs': inputs_pin, 'admission_input': admission, 'results': checked}


def prepare(attempt):
    io.require(type(attempt) is int and attempt > 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '' and sys.dont_write_bytecode,
               'Bare-input preparation requires a CPU-only immutable attempt')
    staged = io.load(helper.STAGED)
    for value in staged['runtime_code'] + staged['source_code']:
        io.verify(value)
    helper.install_metadata_reader()
    os.environ['TRACECOLD_STEP0_CELL'] = 'bare_CS_s17'
    sys.path.insert(0, str(helper.RUNTIME))
    import diag_common
    from student_pilot.batches import load_processor
    from student_pilot.diagnostic_data import encode_prompt, versions
    import torch
    source_pin = io.pin(helper.SOURCE_READY)
    source = io.load(helper.SOURCE_READY)
    io.require(versions() == source['versions'], 'The native diagnostic environment differs')
    for value in source['native_files'] + source['base']['files']:
        io.verify(value)
    contracts, frames = helper.reference_modules()
    io.require(frames.DEFAULT_ANSWER_FORMAT_INSTRUCTION == helper.INSTRUCTION, 'The native instruction bytes differ')
    values, original, config, authority = helper.bare_inputs(contracts)
    io.require(len(values) == diag_common.COUNT == 251 and len({row['qid'] for row in values}) == 251,
               'The counting membership must remain complete and unique')
    for row in values:
        diag_common.validate_row(row)
    cohort = helper.ROOT / 'bare'
    destination = cohort / f'cpu_a{attempt}'
    io.require(not (cohort / 'READY.json').exists() and not destination.exists(), 'Preserve every input-preparation epoch')
    destination.mkdir(parents=True, exist_ok=False)
    inputs_pin = io.save_rows(destination / 'inputs.jsonl', values)
    cohort_guard = guard_projection(contracts, io.load(io.verify(authority[-1])), inputs_pin, destination)
    reference_config = io.save(destination / 'native_reference_config.json', config)
    config = contracts.load_config(reference_config['path'])
    processor = load_processor('qwen35')
    audits = []
    for index, row in enumerate(values, 1):
        batch, audit = encode_prompt(processor, row)
        public = original[row['qid']]
        reference, _ = frames.pack_input(processor, public, 'qwen35', config)
        prompt = processor.apply_chat_template(frames.prompt_messages(public, answer_format_instruction=''),
                                              tokenize=False, add_generation_prompt=True, enable_thinking=True)
        io.require(set(batch) == set(reference) and all(torch.equal(batch[key], reference[key]) for key in batch),
                   'Native prompt tokens, multimodal metadata or RGB tensors differ at ' + row['qid'])
        text = row['student_input']['question'] + ('\n' + '\n'.join(row['student_input']['options']) if row['student_input']['options'] else '')
        actual_prompt = processor.apply_chat_template([{'role': 'user', 'content': [{'type': 'video'}, {'type': 'text', 'text': text}]}],
                                                      tokenize=False, add_generation_prompt=True)
        io.require(actual_prompt.encode() == prompt.encode(), 'Native user/assistant boundary bytes differ')
        audits.append({'qid': row['qid'], 'input_sha256': diag_common.object_digest(row['student_input']),
                       'tensor_sha256': diag_common.tensor_digest(batch), 'audit': audit,
                       'native_prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'native_parity': True})
        if index == 1 or index % 20 == 0 or index == len(values):
            io.heartbeat('Verified ' + str(index) + ' Step-zero bare native inputs')
    io.require(source_pin == io.pin(helper.SOURCE_READY) and not torch.cuda.is_initialized(), 'Source readiness changed or CUDA initialized')
    result = {key: source[key] for key in ('schema', 'native_commit', 'native_files', 'base', 'versions', 'rgb', 'seed',
                                         'max_new_tokens', 'do_sample', 'num_beams', 'attempts')}
    result.update(status='CPU_READY_NOT_GPU_ADMITTED', at_utc=io.now(), inputs=inputs_pin, ordered_qids=[row['qid'] for row in values],
                  input_audits=io.save(destination / 'input_audits.json', audits), effective_generation_config=source['effective_generation_config'],
                  expected_count=251, checked_count=len(audits), failures=[], source_ready=source_pin, source_authority=authority,
                  builder=io.pin(__file__), helpers=io.pin(helper.__file__), transport=io.pin(helper.STAGED), source_commit_bound_by_review=True,
                  answer_format_instruction='', native_prompt_parity=True, native_RGB_parity=True,
                  reference_code=[io.pin(frames.__file__), io.pin(contracts.__file__)], reference_config=reference_config,
                  supports_decisions=False, score_nomination_allowed=False, labels_loaded_by_preparation=False, GPU_used=False,
                  cpu_attempt=attempt, cohort_guard=cohort_guard)
    io.verify(result['effective_generation_config'])
    return io.save(cohort / 'READY.json', result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=int, required=True)
    args = parser.parse_args()
    print(io.canonical({'output': prepare(args.attempt)}), flush=True)


if __name__ == '__main__':
    main()
