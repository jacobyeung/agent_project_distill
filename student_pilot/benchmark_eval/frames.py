import hashlib
import io
import math
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

from .contracts import (MODEL_PINS, RGB, binding, canonical_bytes, digest, load_generation, load_json,
                        new_directory, protocol_identity, runtime_bindings, sha256, snapshot_binding,
                        validate_adapter, validate_input, verify_pin, versions, work_id,
                        write_bytes_once, write_once, jsonl_bytes)


def sample_indices(total):
    if type(total) is not int or total < 32:
        raise ValueError('RGB32 requires at least 32 actually decoded frames')
    return [k * (total - 1) // 31 for k in range(32)]


def decoder_identity():
    import av

    return {'av': av.__version__, 'libraries': {key: list(value) for key, value in av.library_versions.items()}}


def timing_audit(indices, fps, pts, temporal_patch_size=2):
    if not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('Original positive FPS is required; no default FPS')
    if len(pts) != len(indices) or any(not math.isfinite(x) for x in pts):
        raise ValueError('Actual presentation timestamps are required')
    if any(a >= b for a, b in zip(pts, pts[1:])):
        raise ValueError('Presentation timestamps must increase')
    effective_frames = [index / fps for index in indices]
    effective = [sum(effective_frames[i:i + temporal_patch_size]) / temporal_patch_size
                 for i in range(0, len(indices), temporal_patch_size)]
    actual = [sum(pts[i:i + temporal_patch_size]) / temporal_patch_size
              for i in range(0, len(indices), temporal_patch_size)]
    return {'source_pts_seconds': pts, 'effective_frame_timestamps_seconds': effective_frames,
            'effective_timestamps_seconds': effective,
            'max_frame_timestamp_discrepancy_seconds': max(abs(x - y) for x, y in zip(pts, effective_frames)),
            'max_patch_timestamp_discrepancy_seconds': max(abs(x - y) for x, y in zip(actual, effective)),
            'max_displayed_timestamp_discrepancy_seconds': max(abs(x - float(f'{y:.1f}')) for x, y in zip(actual, effective)),
            'processor_timestamp_precision_seconds': 0.1,
            'constant_rate_timing_exact': all(math.isclose(x, y, abs_tol=1e-6, rel_tol=0) for x, y in zip(pts, effective_frames))}


def cache_selection(video_path, cache_root, artifact_root, paper=False):
    import av
    from PIL import Image

    source_hash = sha256(video_path)
    cache_contract = {'video_sha256': source_hash, 'decoder': decoder_identity(), 'preprocessing': RGB}
    cache_id = digest(cache_contract)
    directory = Path(cache_root) / cache_id
    receipt_path = directory / 'selection.json'
    if directory.exists():
        receipt_pin = binding(receipt_path)
        load_selection(receipt_pin)
        if load_json(receipt_path)['cache_contract'] != cache_contract:
            raise ValueError('Stale frame cache')
        return receipt_pin
    timestamps, sizes = [], []
    with av.open(str(video_path)) as container:
        if not container.streams.video:
            raise ValueError('Source has no video stream')
        stream = container.streams.video[0]
        fps = stream.average_rate
        if fps is None or float(fps) <= 0:
            raise ValueError('Source video has no original FPS')
        rational = Fraction(fps)
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('A decoded source frame lacks PTS/time base')
            timestamps.append(float(frame.pts * frame.time_base))
            sizes.append((frame.width, frame.height))
    indices = sample_indices(len(timestamps))
    if len(set(sizes)) != 1:
        raise ValueError('Source video changes resolution')
    selected_pts = [timestamps[i] for i in indices]
    timing_audit(indices, float(fps), selected_pts)
    new_directory(directory, artifact_root, paper)
    selected = set(indices)
    records = []
    with av.open(str(video_path)) as container:
        for ordinal, frame in enumerate(container.decode(video=0)):
            if ordinal not in selected:
                continue
            if float(frame.pts * frame.time_base) != timestamps[ordinal]:
                raise ValueError('Two sequential decodes disagree on source timing')
            array = frame.to_ndarray(format='rgb24')
            encoded = io.BytesIO()
            Image.fromarray(array).save(encoded, format='PNG', optimize=False)
            frame_pin = write_bytes_once(directory / f'frame_{ordinal:08d}.png', encoded.getvalue(), artifact_root, paper)
            records.append({'index': ordinal, 'pts_seconds': timestamps[ordinal], 'width': frame.width,
                            'height': frame.height, 'png': frame_pin,
                            'rgb_sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()})
    if [row['index'] for row in records] != indices or sha256(video_path) != source_hash:
        raise ValueError('Video changed or selected frames were lost during decode')
    selection = [{'index': row['index'], 'pts_seconds': row['pts_seconds'], 'png_sha256': row['png']['sha256'],
                  'rgb_sha256': row['rgb_sha256']} for row in records]
    receipt = {'schema': 'rgb32-selection-v1', 'cache_contract': cache_contract, 'cache_id': cache_id,
               'total_num_frames': len(timestamps), 'fps': float(fps),
               'fps_rational': {'numerator': rational.numerator, 'denominator': rational.denominator},
               'frame_indices': indices, 'frames': records, 'ordered_selection_sha256': digest(selection)}
    return write_once(receipt_path, receipt, artifact_root, paper)


def load_selection(pin):
    import numpy as np
    from PIL import Image

    path = verify_pin(pin)
    receipt = load_json(path)
    contract = receipt['cache_contract']
    if (receipt['schema'] != 'rgb32-selection-v1' or receipt['cache_id'] != digest(contract)
            or contract['preprocessing'] != RGB or contract['decoder'] != decoder_identity()):
        raise ValueError('Stale or malformed RGB cache contract')
    indices = sample_indices(receipt['total_num_frames'])
    if indices != receipt['frame_indices'] or [row['index'] for row in receipt['frames']] != indices:
        raise ValueError('Cache selection is not the exact floor-uniform RGB32')
    rational = receipt['fps_rational']
    if float(Fraction(rational['numerator'], rational['denominator'])) != receipt['fps']:
        raise ValueError('FPS rational changed')
    arrays, selection = [], []
    for row in receipt['frames']:
        frame_path = Path(row['png']['path'])
        if not frame_path.resolve().is_relative_to(path.parent.resolve()):
            raise ValueError('Frame cache path escapes its selection directory')
        verify_pin(row['png'])
        with Image.open(frame_path) as image:
            if image.mode != 'RGB' or list(image.size) != [row['width'], row['height']]:
                raise ValueError('Cached RGB dimensions/mode changed')
            array = np.asarray(image).copy()
        if hashlib.sha256(array.tobytes(order='C')).hexdigest() != row['rgb_sha256']:
            raise ValueError('Cached RGB pixels changed')
        arrays.append(array)
        selection.append({'index': row['index'], 'pts_seconds': row['pts_seconds'],
                          'png_sha256': row['png']['sha256'], 'rgb_sha256': row['rgb_sha256']})
    if digest(selection) != receipt['ordered_selection_sha256']:
        raise ValueError('Ordered RGB selection hash mismatch')
    if len({array.shape for array in arrays}) != 1:
        raise ValueError('Inconsistent cached frame dimensions')
    timing_audit(indices, receipt['fps'], [row['pts_seconds'] for row in receipt['frames']])
    return np.stack(arrays), receipt


def tensor_audit(tensor):
    import torch

    data = tensor.detach().cpu().contiguous()
    payload = data.view(torch.uint8).numpy().tobytes()
    return {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload),
            'dtype': str(data.dtype), 'shape': list(data.shape)}


def prompt_messages(row):
    item = validate_input(row)['student_input']
    text = item['question'] + ('\n' + item['options_serialization'] if item['options_serialization'] else '')
    return [{'role': 'user', 'content': [{'type': 'video'}, {'type': 'text', 'text': text}]}]


def pack_input(processor, row, model, config):
    from transformers.video_utils import VideoMetadata

    arrays, receipt = load_selection(row['student_input']['frame_receipt'])
    if receipt['cache_contract']['video_sha256'] != row['student_input']['video_sha256']:
        raise ValueError('Frame cache does not belong to the admitted source video')
    height, width = arrays.shape[1:3]
    metadata = VideoMetadata(total_num_frames=receipt['total_num_frames'], fps=receipt['fps'],
                             frames_indices=receipt['frame_indices'], width=width, height=height)
    kwargs = {'enable_thinking': True} if MODEL_PINS[model]['enable_thinking'] is True else {}
    prompt = processor.apply_chat_template(prompt_messages(row), tokenize=False, add_generation_prompt=True, **kwargs)
    batch = processor(text=[prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                      size=config['rgb']['size'], return_tensors='pt', return_metadata=True,
                      truncation=False, padding=False)
    returned = batch.pop('video_metadata', None)
    if returned is None or len(returned) != 1 or (list(returned[0].frames_indices) != receipt['frame_indices']
                                                or returned[0].fps != receipt['fps']):
        raise ValueError('Processor changed or omitted original video metadata')
    allowed = {'input_ids', 'attention_mask', 'mm_token_type_ids', 'pixel_values_videos', 'video_grid_thw'}
    if set(batch) - allowed or not {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'} <= set(batch):
        raise ValueError('Unexpected or missing answer-free processor tensors')
    grid = batch['video_grid_thw']
    temporal = processor.video_processor.temporal_patch_size
    if tuple(grid.shape) != (1, 3) or int(grid[0, 0]) * temporal != 32:
        raise ValueError('Processor changed the RGB32 temporal grid')
    visual_tokens = int((batch['input_ids'] == processor.video_token_id).sum())
    if visual_tokens != int(grid.prod()) // processor.video_processor.merge_size ** 2:
        raise ValueError('Visual token/grid mismatch')
    if batch['input_ids'].ndim != 2 or batch['input_ids'].shape[0] != 1:
        raise ValueError('Only one untruncated prompt per batch is allowed')
    length = int(batch['input_ids'].shape[1])
    if not 0 < length <= config['rgb']['max_input_tokens'] or not bool((batch['attention_mask'] == 1).all()):
        raise ValueError('Input token cap exceeded or processor truncated/padded the prompt')
    timing = timing_audit(receipt['frame_indices'], receipt['fps'], [row['pts_seconds'] for row in receipt['frames']], temporal)
    decoded = processor.tokenizer.decode(batch['input_ids'][0], skip_special_tokens=False)
    if any(f'<{timestamp:.1f} seconds>' not in decoded for timestamp in timing['effective_timestamps_seconds']):
        raise ValueError('Native temporal-patch timestamps are absent from the prompt')
    pixel, tokens = tensor_audit(batch['pixel_values_videos']), tensor_audit(batch['input_ids'])
    patch_size = processor.video_processor.patch_size
    audit = {'qid': row['qid'], 'prompt': prompt, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
             'prompt_tokens': length, 'input_token_ids': batch['input_ids'][0].tolist(),
             'prompt_token_sha256': tokens['sha256'], 'prompt_tensor': tokens, 'pixel_tensor': pixel,
             'pixel_tensor_sha256': pixel['sha256'], 'video_grid_thw': grid.tolist(), 'visual_tokens': visual_tokens,
             'processed_height_width': [int(grid[0, 1]) * patch_size, int(grid[0, 2]) * patch_size],
             'original_width_height': [width, height], 'video_sha256': row['student_input']['video_sha256'],
             'frame_indices': receipt['frame_indices'], 'frame_hashes': [item['png']['sha256'] for item in receipt['frames']],
             'frame_rgb_hashes': [item['rgb_sha256'] for item in receipt['frames']],
             'ordered_selection_sha256': receipt['ordered_selection_sha256'], 'fps': receipt['fps'],
             'fps_rational': receipt['fps_rational'], 'do_sample_frames': False, 'truncation': False, **timing}
    return dict(batch), audit


def cpu_check(manifest_path, model, output, artifact_root, model_root=None, synthetic=False,
              variant='base', adapter=None, training_receipt=None):
    from .generate import effective_generation_config

    manifest, rows, config = load_generation(manifest_path)
    if synthetic and manifest['paper_cell']:
        raise ValueError('Synthetic processors cannot preflight a paper cell')
    adapter_pin = validate_adapter(variant, model, adapter, training_receipt, config, allow_synthetic=synthetic)
    if synthetic:
        processor = SyntheticProcessor()
        model_pin = {key: MODEL_PINS[model][key] for key in ('repo_id', 'revision', 'architecture')}
        model_pin['synthetic'] = True
        from transformers import GenerationConfig
        native = GenerationConfig(eos_token_id=10, pad_token_id=12, use_cache=False)
    else:
        from transformers import AutoConfig, AutoProcessor, GenerationConfig

        if model_root is None:
            raise ValueError('An explicit local model cache root is required')
        model_pin = snapshot_binding(model, model_root)
        snapshot = model_pin['snapshot']
        processor = AutoProcessor.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
        processor.tokenizer.padding_side = 'right'
        native = (GenerationConfig.from_pretrained(snapshot, local_files_only=True)
                  if model_pin['generation_config_source'] == 'generation_config.json'
                  else GenerationConfig.from_model_config(AutoConfig.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)))
    effective = effective_generation_config(native, processor)
    output = new_directory(output, artifact_root, manifest['paper_cell'])
    audits, failures = [], []
    checked_videos = set()
    for row in rows:
        try:
            item = row['student_input']
            if item['video_path'] not in checked_videos:
                binding(item['video_path'], item['video_sha256'])
                checked_videos.add(item['video_path'])
            _, audit = pack_input(processor, row, model, config)
            audits.append(audit)
        except (ValueError, OSError, RuntimeError) as error:
            failures.append({'qid': row['qid'], 'error': str(error), 'type': type(error).__name__})
    audits_pin = write_bytes_once(output / 'input_audits.jsonl', jsonl_bytes(audits), artifact_root, manifest['paper_cell'])
    manifest_pin = binding(manifest_path)
    protocol = protocol_identity(manifest_pin, model_pin, adapter_pin, config)
    report = {'schema': 'student-cpu-preflight-v1', 'status': 'BLOCKED' if failures else 'CPU_READY_SYNTHETIC' if synthetic else 'CPU_READY',
              'paper_cell': manifest['paper_cell'], 'synthetic': synthetic, 'manifest': manifest_pin, 'model_name': model,
              'model': model_pin, 'variant': variant, 'adapter': adapter_pin, 'config': config,
              'effective_generation_config': effective.to_dict(), 'input_audits': audits_pin,
              'runtime': runtime_bindings(), 'versions': versions(), 'failures': failures,
              'protocol_sha256': protocol, 'work_id': work_id(manifest['benchmark'], model, variant, protocol),
              'expected_count': len(rows), 'checked_count': len(audits)}
    write_once(output / 'preflight.json', report, artifact_root, manifest['paper_cell'])
    if failures:
        raise ValueError(f'CPU preflight failed for {len(failures)} questions; see {output / "preflight.json"}')
    return report


class SyntheticTokenizer:
    eos_token, eos_token_id, pad_token_id = '<|im_end|>', 10, 12
    padding_side = 'right'
    special = {'<|im_end|>': 10, '<|video_pad|>': 11}

    def encode(self, text, add_special_tokens=False):
        values = []
        while text:
            token = next((token for token in self.special if text.startswith(token)), None)
            if token:
                values.append(self.special[token])
                text = text[len(token):]
            else:
                values.append(ord(text[0]) + 256)
                text = text[1:]
        return values

    def decode(self, tokens, skip_special_tokens=False):
        inverse = {value: key for key, value in self.special.items()}
        return ''.join(('' if skip_special_tokens else inverse[int(value)]) if int(value) in inverse else chr(int(value) - 256)
                       for value in tokens)


class SyntheticProcessor:
    video_token_id = 11
    video_processor = SimpleNamespace(temporal_patch_size=2, merge_size=2, patch_size=16)

    def __init__(self):
        self.tokenizer = SyntheticTokenizer()

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=None):
        content = messages[0]['content']
        if messages[0]['role'] != 'user' or [item['type'] for item in content] != ['video', 'text']:
            raise ValueError('Synthetic template expects the native video/text user order')
        prompt = '<|im_start|>user\n<|video_pad|>' + content[1]['text'] + '<|im_end|>\n<|im_start|>assistant\n'
        if enable_thinking:
            prompt += '<think>\n'
        if len(messages) == 2:
            return prompt + messages[1]['content'] + self.tokenizer.eos_token + '\n'
        return prompt

    def __call__(self, text, videos, video_metadata, do_sample_frames, size, return_tensors, return_metadata, **kwargs):
        import torch

        if do_sample_frames or size != RGB['size'] or kwargs.get('truncation') is True:
            raise ValueError('Synthetic processor saw altered preprocessing')
        metadata = video_metadata[0]
        h, w = videos[0].shape[1:3]
        gh, gw = max(2, h // 32 * 2), max(2, w // 32 * 2)
        grid = torch.tensor([[16, gh, gw]], dtype=torch.long)
        stamps = [(metadata.frames_indices[i] + metadata.frames_indices[i + 1]) / (2 * metadata.fps) for i in range(0, 32, 2)]
        video = ''.join(f'<{stamp:.1f} seconds>' + '<|video_pad|>' * (gh * gw // 4) for stamp in stamps)
        ids = torch.tensor([self.tokenizer.encode(text[0].replace('<|video_pad|>', video))], dtype=torch.long)
        return {'input_ids': ids, 'attention_mask': torch.ones_like(ids),
                'pixel_values_videos': torch.from_numpy(videos[0].copy()).float(),
                'video_grid_thw': grid, 'video_metadata': video_metadata}
