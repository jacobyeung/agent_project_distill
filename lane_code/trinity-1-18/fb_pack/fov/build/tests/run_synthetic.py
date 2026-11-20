"""Run all three full-population CLI cases serially, or verify completed runs."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import time

WORK = Path(__file__).resolve().parents[1]
CASES = [('full_1_1', ('1.0', '1.0'), 'V2'),
         ('full_1_1p02', ('1.0', '1.02'), 'V1'),
         ('full_1p02_1p02', ('1.02', '1.02'), 'NONE')]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--prefix', default='')
    args = parser.parse_args()
    outcomes = []
    pins = {str(WORK / 'score_fov.py'): sha(WORK / 'score_fov.py'), str(Path(__file__).resolve()): sha(__file__)}
    baseline_path = Path('/scratch/jjyeung/orch_n30/sb_own400/out/real400_score_n/SCORE_RESULT.json')
    baseline = json.loads(baseline_path.read_text())
    pins[str(baseline_path)] = sha(baseline_path)
    for name, factors, expected in CASES:
        out = WORK / 'tests' / (args.prefix + name)
        command = ['env', 'OMP_NUM_THREADS=8', 'MKL_NUM_THREADS=8', 'OPENBLAS_NUM_THREADS=8',
                   'CUDA_VISIBLE_DEVICES=', 'nice', '-n', '10', sys.executable, '-B', str(WORK / 'score_fov.py'),
                   '--synthetic', *factors, '--out', str(out)]
        if not args.verify_only:
            with (WORK / 'tests' / (args.prefix + name + '.log')).open('x') as log:
                subprocess.run(command, cwd=WORK, stdout=log, stderr=log, check=True)
        path = out / 'FOV_RESULT.json'
        value = json.loads(path.read_text())
        pins[str(path)] = sha(path)
        assert value['input_sha256'][str(WORK / 'score_fov.py')] == pins[str(WORK / 'score_fov.py')]
        assert value['synthetic'] is True and value['decision_usable'] is False
        assert value['choice'] == expected, (name, value['choice'])
        assert value['captures'] == 239 and len(value['missing']) == 3
        assert value['pairs'] == baseline['pairs']
        for metric in ('displacement', 'routed_distance'):
            assert value[metric]['combined']['A'] == baseline[metric]['combined']['A']
            for observed, frozen in zip(value[metric]['folds'], baseline[metric]['folds']):
                assert observed['name'] == frozen['name'] and observed['A'] == frozen['A']
        if expected == 'V2':
            assert all(value['criteria'][arm]['acceptable'] for arm in ('V1', 'V2'))
        elif expected == 'V1':
            assert value['criteria']['V1']['acceptable'] and not value['criteria']['V2']['D1']['pass']
        else:
            assert not any(value['criteria'][arm]['acceptable'] for arm in ('V1', 'V2'))
        outcomes.append({'name': name, 'pass': True, 'choice': expected, 'seconds': value['seconds'],
                         'baseline_arm_A_parity': 'EXACT: both folds and combined, both metrics',
                         'command': shlex.join(command), 'V1-A': value['displacement']['combined']['V1-A'],
                         'V2-A': value['displacement']['combined']['V2-A']})
    report = {'input_sha256': pins, 'synthetic': True, 'decision_usable': False,
              'command': shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]]), 'tests': outcomes}
    dest = WORK / 'tests' / (args.prefix + 'SYNTHETIC_RESULTS_' + str(time.time_ns()) + '.json')
    dest.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'pass': True, 'tests': len(outcomes), 'result': str(dest)}), flush=True)


if __name__ == '__main__':
    main()
