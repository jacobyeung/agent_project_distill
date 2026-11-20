"""Audit completed test artifacts and the local workspace budget."""
import hashlib
import json
from pathlib import Path
import shlex
import sys

WORK = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = WORK / 'score_fov.py'
    selected = [WORK / 'tests' / name for name in (
        'REFUSAL_RESULTS_1795131491235408410.json',
        'OUTPUT_GUARD_RESULTS_1795131491623429217.json',
        'SYNTHETIC_RESULTS_1795133046128932626.json')]
    pins = {str(source): sha(source), str(Path(__file__).resolve()): sha(__file__)}
    for path in selected:
        result = json.loads(path.read_text())
        assert all(test['pass'] for test in result['tests'])
        assert result['input_sha256'][str(source)] == pins[str(source)]
        pins[str(path)] = sha(path)
        for script in ('test_refusals.py', 'test_output_guards.py', 'run_synthetic.py'):
            target = WORK / 'tests' / script
            if str(target) in result['input_sha256']:
                assert sha(target) == result['input_sha256'][str(target)]
                pins[str(target)] = sha(target)
    json_files = sorted((WORK / 'tests').rglob('*.json'))
    for path in json_files:
        result = json.loads(path.read_text())
        assert isinstance(result.get('input_sha256'), dict) and result['input_sha256'], path
        pins[str(path)] = sha(path)
    size = sum(path.stat().st_size for path in WORK.rglob('*') if path.is_file())
    assert size < 1_000_000_000, size
    real_root = Path('/scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov/native/probe')
    result = {'input_sha256': pins, 'command': shlex.join([sys.executable, '-B', str(Path(__file__).resolve())]),
              'status': 'PASS', 'test_json_files_with_input_sha256': len(json_files),
              'workspace_file_bytes_before_audit': size, 'workspace_limit_bytes': 1_000_000_000,
              'real_input': {'path': str(real_root), 'status': 'PRESENT, NOT SCORED' if real_root.is_dir() else 'MISSING'}}
    with (WORK / 'tests' / 'FINAL_AUDIT.json').open('x') as file:
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'input_sha256'}))


if __name__ == '__main__':
    main()
