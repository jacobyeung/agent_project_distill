# Adapted from tools/vstigen/io.py at e2f387e (vstigen-membership-v4-20260922).
import hashlib
import json
from pathlib import Path
import subprocess


OUTPUT_ROOT = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def pin(path, rows=None):
    path = Path(path).resolve()
    value = {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}
    if rows is not None:
        value['rows'] = rows
    return value


def verify_pin(spec):
    path = Path(spec['path'])
    size = spec.get('size_bytes', spec.get('bytes'))
    if path.is_symlink() or not path.is_file() or size is not None and path.stat().st_size != size:
        raise ValueError(f'missing, symlinked, or size-drifted input: {path}')
    if sha(path) != spec['sha256']:
        raise ValueError(f'input digest mismatch: {path}')
    return path


def output_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(OUTPUT_ROOT) or path == OUTPUT_ROOT:
        raise ValueError(f'outputs must live below {OUTPUT_ROOT}')
    return path


def write_json(path, value):
    with output_path(path).open('x') as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    with output_path(path).open('x') as handle:
        for row in rows:
            handle.write(canonical(row) + '\n')


def read_jsonl(path):
    with Path(path).open() as handle:
        for line in handle:
            yield json.loads(line)


def new_output(path):
    path = output_path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def source_commit():
    root = Path(__file__).resolve().parents[2]
    status = subprocess.check_output(['git', '--no-optional-locks', 'status', '--porcelain'], cwd=root, text=True)
    if status.strip():
        raise ValueError('generation and mixing require a clean committed worktree')
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
