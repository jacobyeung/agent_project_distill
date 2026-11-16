import argparse
import hashlib
from pathlib import Path

import torch
from transformers.video_utils import VideoMetadata

from student_pilot import batches
from student_pilot.trace_io import canonical, load, pin, require, rows, save, verify
from tests.test_tracecold import native_frames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows-ready', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ready_pin = pin(args.rows_ready)
    ready = load(args.rows_ready)
    processor = batches.load_processor('qwen35')
    reference = native_frames()
    records = []
    for arm in ('TR', 'AO'):
        source = ready['arms'][arm]['training']
        row = next(rows(verify(source)))
        print(canonical({'phase': 'RGB_and_native_encoding', 'arm': arm, 'qid': row['qid']}), flush=True)
        inputs = row['student_input']
        arrays, sizes = batches.load_rgb(inputs)
        metadata = VideoMetadata(total_num_frames=inputs['total_num_frames'], fps=inputs['fps'],
                                 frames_indices=inputs['frame_indices'], width=sizes[0][0], height=sizes[0][1])
        public = {'qid': row['qid'], 'video_id': row['dataset'] + '/' + row['scene'], 'student_input': {
            'question': inputs['question'], 'options': inputs['options'], 'options_serialization': '\n'.join(inputs['options']),
            'video_path': '/unused/parity.mp4', 'video_sha256': '0' * 64,
            'frame_receipt': {'path': '/unused/parity.json', 'sha256': '0' * 64, 'size_bytes': 0}}}
        native_prompt = processor.apply_chat_template(reference.prompt_messages(public), tokenize=False,
                                                     add_generation_prompt=True, enable_thinking=True)
        prompt, suffix = batches.training_text(processor, inputs['question'], inputs['options'], row['target'])
        require(prompt.encode() == native_prompt.encode(), 'Training and frozen native prompt bytes differ')
        batch, audit = batches.encode_arrays(processor, inputs['question'], inputs['options'], arrays, metadata, row['target'])
        native = processor(text=[native_prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                           size=reference.RGB['size'], return_tensors='pt', return_metadata=True, truncation=False, padding=False)
        length = audit['prompt_tokens']
        require(torch.equal(batch['input_ids'][:, :length], native['input_ids']), 'Expanded video prompt token IDs differ')
        require(torch.equal(batch['pixel_values_videos'], native['pixel_values_videos'])
                and torch.equal(batch['video_grid_thw'], native['video_grid_thw']), 'RGB tensors or video grid differ')
        labels = batch['labels'][batch['labels'] != -100].tolist()
        require(labels[-2:] == [248046, 248044] and labels.count(248069) == 1, 'The supervised think close or terminator differs')
        require(torch.all(batch['labels'][:, :length] == -100).item()
                and torch.all(batch['labels'][batch['attention_mask'] == 0] == -100).item(), 'The prompt or padding is supervised')
        close = labels.index(248069)
        require(processor.tokenizer.encode('<think>\n', add_special_tokens=False) == [248068, 198], 'The think-open token boundary changed')
        decoded = processor.tokenizer.decode(batch['input_ids'][0, :length], skip_special_tokens=False)
        records.append({'arm': arm, 'qid': row['qid'], 'source': source, 'target': row['target'],
                        'prompt': prompt, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                        'decoded_expanded_prompt_sha256': hashlib.sha256(decoded.encode()).hexdigest(),
                        'prompt_final_ids': batch['input_ids'][0, max(0, length - 12):length].tolist(),
                        'supervised_ids': labels, 'think_close_context_ids': labels[max(0, close - 8):close + 8],
                        'terminator_ids': labels[-2:], 'supervised_text': processor.tokenizer.decode(labels, skip_special_tokens=False),
                        'native_prompt_bytes_equal': True, 'native_expanded_prompt_tokens_equal': True,
                        'native_RGB_tensors_equal': True, 'prompt_and_padding_masked': True, 'audit': audit})
    require(ready_pin == pin(args.rows_ready) and not torch.cuda.is_initialized(), 'The source changed or CPU proof touched CUDA')
    result = {'schema': 'tracecold-native-prompt-and-token-proof-v1', 'status': 'PASS', 'rows_ready': ready_pin,
              'samples': records, 'sampling_rule': 'The first frozen source row, identically selected in each matched arm.',
              'evaluator_frames': pin(reference.__file__), 'training_batches': pin(batches.__file__), 'code': pin(__file__),
              'GPU_used': False, 'model_weights_loaded': False}
    print(canonical({'output': save(args.output, result)}), flush=True)


if __name__ == '__main__':
    main()
