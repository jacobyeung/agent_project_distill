"""Pinned benchmark membership, official prompts, and lossless trainer rows."""
import hashlib
import fcntl
import json
import math
from pathlib import Path
from types import SimpleNamespace

from .official import build_prompt_context

MEMBERSHIP_SHA256 = '2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf'
TRINITY_DATA = '/data2/jjyeung/agent_project_data'
AWS_DATA = ('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'
            'distill/orch/data2root/jjyeung/agent_project_data')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def pinned(pin):
    path = Path(pin['path'])
    if sha256(path) != pin['sha256']:
        raise ValueError(f'Input pin changed: {path}')
    return path


def read_rows(pin):
    path = pinned(pin)
    if path.suffix == '.jsonl':
        with path.open() as f:
            return [json.loads(line) for line in f if line.strip()]
    value = json.loads(path.read_text())
    return value if isinstance(value, list) else value['items']


def item_id(row):
    for key in ('example_id', 'qid', 'id'):
        if key in row:
            return str(row[key])
    raise ValueError('Missing item id')


def index_rows(rows):
    result = {}
    for row in rows:
        key = item_id(row)
        if key in result:
            raise ValueError(f'Duplicate item id: {key}')
        result[key] = row
    return result


def load_items(spec, roots):
    """roots: {video_root, optional data2_root/path_map}; no media is read here.

    VSI needs membership + canonical rows. VSTI needs pinned v3 rows (or prepared
    generation inputs + scoring labels) and a pinned v3 ID list when available.
    Labels stay in task records and never enter a trainer row.
    """
    from .kit_inputs import resolve_spec, official_rows
    spec = resolve_spec(spec, roots)
    benchmark = spec['benchmark']
    if benchmark == 'routed_dev':
        from .routed_dev import load_tasks
        return load_tasks(spec, roots)
    if benchmark == 'official5130':
        return official_rows(spec, roots)
    rows = index_rows(read_rows(spec['rows']))
    if benchmark == 'vsi500':
        if spec['membership']['sha256'] != MEMBERSHIP_SHA256:
            raise ValueError('VSI requires the official answerable-500 membership')
        members = index_rows(read_rows(spec['membership']))
        if len(members) != 500 or not set(members) <= set(rows):
            raise ValueError('Missing answerable-500 canonical rows')
        rows = {key: rows[key] for key in members}
        for key, member in members.items():
            row = rows[key]
            if (row['dataset'] != member['dataset'] or
                    row.get('scene_name', row.get('scene')) != member['scene'] or
                    row['question_type'] != member['category']):
                raise ValueError('VSI canonical/membership scene or type differs')
    elif benchmark == 'vstiv3':
        if spec.get('version') != 'v3' or len(rows) != 450:
            raise ValueError('Only the pinned VSTI-450 v3 release is accepted')
        if spec.get('labels'):
            labels = index_rows(read_rows(spec['labels']))
            if set(labels) != set(rows):
                raise ValueError('VSTI input/label membership differs')
            for key, row in rows.items():
                for field in ('question', 'options'):
                    source = row.get(field, row.get('student_input', {}).get(field))
                    if source is not None and field in labels[key] and source != labels[key][field]:
                        raise ValueError('VSTI generation prompt differs from its scoring labels')
            rows = {key: {**row, **labels[key]} for key, row in rows.items()}
        if spec.get('ids'):
            expected = json.loads(pinned(spec['ids']).read_text())
            if set(map(str, expected)) != set(rows):
                raise ValueError('VSTI v3 membership differs')
    else:
        raise ValueError('benchmark must be vsi500 or vstiv3')
    result = []
    for key in sorted(rows):
        raw = rows[key]
        si = raw.get('student_input') or {}
        task = {**raw, 'example_id': key, 'benchmark': benchmark,
                'scene_name': raw.get('scene_name', raw.get('scene')),
                'question': raw.get('question', si.get('question')),
                'options': raw.get('options', si.get('options')) or []}
        if not isinstance(task['question'], str) or 'ground_truth' not in task:
            raise ValueError('Missing unchanged question or ground truth')
        video = raw.get('video_path') or si.get('video_path')
        if video:
            for old, new in roots.get('path_map', {}).items():
                if video.startswith(old):
                    video = new + video[len(old):]
                    break
            if video.startswith('/data2/') and roots.get('data2_root'):
                video = roots['data2_root'].rstrip('/') + '/' + video[len('/data2/'):]
            if not Path(video).is_absolute():
                video = str(Path(roots['video_root']) / video)
        else:
            video = str(Path(roots['video_root']) / task['dataset'] / (task['scene_name'] + '.mp4'))
        task['video_path'] = video
        task['video_sha256'] = raw.get('video_sha256') or si.get('video_sha256') or ''
        build_prompt_context(task, 'ours')  # Reject a prepared row with changed text.
        result.append(task)
    return result


def assert_prompt_equal(processor, row):
    """Capture the actual user message passed by the trainer to its chat template."""
    from student_pilot.batches import training_text
    from student_pilot.carrier_c1_data import READOUT_TARGET
    captured = []

    class Capture:
        tokenizer = processor.tokenizer

        def __getattr__(self, key):
            return getattr(processor, key)

        def apply_chat_template(self, messages, **kwargs):
            captured.append(messages[0]['content'][1]['text'])
            return processor.apply_chat_template(messages, **kwargs)

    si = row.get('student_input', row)
    training_text(Capture(), si['question'], si.get('options') or [], READOUT_TARGET)
    expected = build_prompt_context(si, 'ours')
    if not captured or any(text.encode() != expected.encode() for text in captured):
        raise AssertionError('Trainer user text differs from official ours')
    return expected


def trainer_row(task, cache):
    """Serialize shared-video cache fills across GPU workers."""
    directory = Path(cache)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / (digest(task['video_path']) + '.lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _trainer_row(task, cache)


def _trainer_row(task, cache):
    """Decode with the official Qwen3.5 PyAV branch (prepare_q35_visual) and pin its exact RGB arrays as PNGs."""
    from PIL import Image
    from .sampling import sample_video
    # One directory per video path/version. Cached rows bind video stat + PNG bytes.
    video = Path(task['video_path'])
    stat = video.stat()
    identity = dict(path=str(video), size=stat.st_size, mtime_ns=stat.st_mtime_ns,
                    video_sha256=task.get('video_sha256', ''), backend='pyav-floor-uniform-32')
    directory = Path(cache) / digest(identity)
    receipt = directory / 'frames.json'
    if receipt.exists():
        si = json.loads(receipt.read_text())
        for pin in si['frames']:
            pinned(pin)
    else:
        if identity['video_sha256'] and sha256(video) != identity['video_sha256']:
            raise ValueError('Video SHA differs')
        arrays, indices, fps, total = sample_video(task, SimpleNamespace(max_frames_num=32))
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError('Video has no positive original FPS')
        directory.mkdir(parents=True, exist_ok=True)
        pins = []
        for i, array in enumerate(arrays):
            path = directory / f'{i:02}.png'
            # Existing files from an interrupted decode must match the new PNG bytes.
            import io
            buffer = io.BytesIO()
            Image.fromarray(array).save(buffer, format='PNG')
            payload = buffer.getvalue()
            if path.exists():
                if path.read_bytes() != payload:
                    raise ValueError('Cached sampled pixels changed')
            else:
                with path.open('xb') as f:
                    f.write(payload)
            pins.append(dict(path=str(path.resolve()), sha256=sha256(path)))
        si = dict(frames=pins, frame_indices=indices, timestamps=[i / fps for i in indices],
                  fps=fps, total_num_frames=total, video_identity=identity)
        with receipt.open('x') as f:
            json.dump(si, f)
    return dict(qid=task['example_id'], dataset=task['dataset'], scene=task['scene_name'],
                student_input={**si, 'question': task['question'], 'options': task['options']})
