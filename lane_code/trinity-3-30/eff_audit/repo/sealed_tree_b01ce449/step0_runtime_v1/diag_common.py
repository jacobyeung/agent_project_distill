from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from tracecold_transport import LANE, CELLS, ROOT, contract_for, pin, digest
LANE_BULK = ROOT

CELL = os.environ.get('TRACECOLD_STEP0_CELL', '')
if CELL not in CELLS:
    raise ValueError('An explicit registered count9 scorer cell is required')
BULK = ROOT
OUT = ROOT / 'cells' / CELL

WORK = Path(__file__).resolve().parent
NATIVE = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/trinity_exec_20260930/eval/r1835_vsibench_answerable500_r2/checkout/91d47a0ee099df925ddcd1591e773430d71d3637')
NATIVE_COMMIT = '91d47a0ee099df925ddcd1591e773430d71d3637'
PARSER_ROOT = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_parser_sensitivity/work/harness')
VENV = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv')
COORD_ROOT = Path('/data2/jjyeung/agent_project/.coord')
COORD_TOOL = Path('/home/jjyeung/agent_project/agent/coord.py')
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'
ASSIGNMENTS = []
ROUTE_ROOT = OUT / 'inference'
CATEGORY = 'object_counting'
COUNT = 251 if CELL.startswith('bare_') else 269
ARMS = (CELL,)
NATIVE_FILES = ['student_pilot/' + name + '.py' for name in ('common', 'students', 'batches', 'diagnostic_data', 'diagnostic', 'runner', 'adapters', 'provisional')]
INPUT_FIELDS = {'question', 'options', 'frames', 'frame_indices', 'timestamps', 'fps', 'total_num_frames'}


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode()


def object_digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encode(value))
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return pin(path)


def verify(value):
    path = Path(value['path'])
    if digest(path) != value['sha256'] or 'bytes' in value and path.stat().st_size != value['bytes']:
        raise ValueError('Frozen file differs: ' + str(path))
    return path


def read_json(path):
    return json.loads(Path(path).read_text())


def validate_row(row):
    if set(row) != {'qid', 'dataset', 'scene', 'category', 'student_input'} or row['category'] != CATEGORY or not isinstance(row['qid'], str) or not re.fullmatch(r'[A-Za-z0-9_-]+', row['qid']):
        raise ValueError('Unexpected generation-row fields or question identity')
    inputs = row['student_input']
    if set(inputs) != INPUT_FIELDS or not isinstance(inputs['question'], str) or not isinstance(inputs['options'], list) or not all(isinstance(option, str) for option in inputs['options']):
        raise ValueError('Generation accepts only original RGB, question and options')
    if len(inputs['frames']) != 32 or len(inputs['frame_indices']) != 32 or len(inputs['timestamps']) != 32:
        raise ValueError('Exactly 32 original frames are required')
    if any(set(frame) != {'path', 'sha256'} for frame in inputs['frames']):
        raise ValueError('Frame bindings contain unexpected fields')
    return row


def load_rows(path):
    rows = [validate_row(json.loads(line)) for line in Path(path).open() if line.strip()]
    if len(rows) != COUNT or len({row['qid'] for row in rows}) != COUNT:
        raise ValueError(f'The counting gate requires exactly {COUNT} unique frozen questions')
    return rows


def tensor_digest(batch):
    import torch
    value = hashlib.sha256()
    for name, tensor in sorted(batch.items()):
        value.update(encode({'name': name, 'shape': list(tensor.shape), 'dtype': str(tensor.dtype)}))
        value.update(tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return value.hexdigest()


def emit(phase, **details):
    print(json.dumps({'checked_at_utc': now(), 'phase': phase, **details}, sort_keys=True), flush=True)


def contract():
    job, binding = contract_for(CELL)
    if job['assignments'] != ASSIGNMENTS:
        raise ValueError('The imported placement differs from the frozen job')
    return job, binding


if (OUT / 'EVAL_FROZEN.json').is_file():
    ASSIGNMENTS = read_json(OUT / 'EVAL_FROZEN.json')['assignments']
