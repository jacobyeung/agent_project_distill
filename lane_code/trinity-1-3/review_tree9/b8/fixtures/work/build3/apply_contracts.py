"""Apply authenticated contract patches with a fail-closed, documented envelope."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

L = Path(__file__).resolve().parents[2]
T = L/'work/tree_r1'


def apply_text(source, patch):
    old = source.splitlines(keepends=True)
    result, cursor = [], 0
    lines = patch.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        header = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[index])
        if not header:
            raise ValueError('Expected a unified patch hunk')
        start = int(header[1])-1
        if start < cursor:
            raise ValueError('Overlapping patch hunks')
        result.extend(old[cursor:start]); cursor = start; index += 1
        consumed = emitted = 0
        while index < len(lines) and not lines[index].startswith('@@ '):
            line = lines[index]; index += 1
            if line.startswith('\\'):
                raise ValueError('Patch needs newline-terminated source')
            if line[:1] in (' ', '-'):
                if cursor >= len(old) or old[cursor] != line[1:]:
                    raise ValueError('Patch context differs')
                cursor += 1; consumed += 1
            if line[:1] in (' ', '+'):
                result.append(line[1:]); emitted += 1
            if line[:1] not in (' ', '+', '-'):
                raise ValueError('Unknown patch line')
        if consumed != int(header[2] or 1) or emitted != int(header[4] or 1):
            raise ValueError('Patch hunk count differs')
    result.extend(old[cursor:])
    return ''.join(result)


def plan(folder, tree):
    changes, tests = {}, []
    patches = sorted(Path(folder).glob('PATCH_*_r2.diff'))
    if not patches:
        raise ValueError('Contract patches absent; no changes applied')
    for patch in patches:
        meta = json.loads(patch.with_suffix('.json').read_text())
        raw = patch.read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta['sha256'] or not meta.get('report'):
            raise ValueError('Patch hash or report absent')
        report = Path(folder)/meta['report']['path']
        if not report.resolve().is_relative_to(Path(folder).resolve()) or hashlib.sha256(report.read_bytes()).hexdigest() != meta['report']['sha256']:
            raise ValueError('Patch report hash differs')
        if 'level_basis' in raw.decode():
            raise ValueError('Heading switch is forbidden')
        blocks = re.split(r'(?m)^--- ', raw.decode())[1:]
        for block in blocks:
            first, second, body = block.split('\n', 2)
            name = first.split('\t')[0].removeprefix('a/')
            new = second.removeprefix('+++ ').split('\t')[0].removeprefix('b/')
            path = Path(tree)/name
            if name != new or not path.resolve().is_relative_to(Path(tree).resolve()) or name in changes:
                raise ValueError('Patch target is unsafe or repeated')
            source = path.read_bytes()
            if hashlib.sha256(source).hexdigest() != meta['base_hashes'][name]:
                raise ValueError('Patch base hash differs: '+name)
            changes[name] = apply_text(source.decode(), body)
        tests.extend(meta['tests'])
    if not tests or any(not re.fullmatch(r'tests\.test_[a-zA-Z0-9_]+', name) for name in tests):
        raise ValueError('Patch must name bounded unittest modules')
    return changes, tests


def main():
    folder = L/'work/contracts'
    changes, tests = plan(folder, T)
    for name, source in changes.items():
        (T/name).write_text(source)
    subprocess.run([sys.executable, '-I', '-s', '-B', str(L/'work/build3/run_tests.py'), *tests], check=True)
    print(json.dumps(dict(status='applied and tested', files=sorted(changes), tests=tests)))


if __name__ == '__main__':
    main()
