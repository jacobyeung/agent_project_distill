import argparse
import json
import os
from pathlib import Path
import shutil
import tarfile
import uuid


MIN_FREE = 200*1024**3
ARCHIVE_LIMIT = 89999999
PROJECT_LIMIT = 20000000000
DIRECT_FILES = ('request.json', 'BIND_STATUS.json', 'PROMPT_PINS.json', 'LAYOUT_ADMISSION.json', 'kit/CODE_PINS.json',
                'frames/0.json', 'results')
TOP_FILES = ('PLAN.json', 'SPEC.json', 'AUTHORIZATION.json', 'RELEASE.json', 'HARDWARE.json',
             'START.json', 'COMPLETE.json', 'FAILED.json', 'STEPS.jsonl', 'CODE_PINS.json',
             'FRAME_PLAN.json', 'PARITY.json', 'TRACE.json.gz')


class BudgetError(RuntimeError):
    pass


def atomic_json(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Status destination must not be a symlink')
    temporary = path.parent/(path.name+'.'+uuid.uuid4().hex+'.partial')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def local_output(path):
    path = Path(path)
    resolved = path.resolve()
    if not path.is_absolute() or not any(
            resolved.is_relative_to(root) for root in (Path('/scratch'), Path('/tmp'), Path('/dev/shm'))):
        raise ValueError('Rolling read archives require a node-local output directory')
    return resolved


class LimitedWriter:
    def __init__(self, stream, limit):
        self.stream = stream
        self.limit = limit
        self.written = 0

    def write(self, data):
        if self.written+len(data) > self.limit:
            raise BudgetError('Compressed archive exceeds the transfer-safe file limit')
        result = self.stream.write(data)
        self.written += result
        return result

    def __getattr__(self, name):
        return getattr(self.stream, name)


def regular_files(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refuse a symlink in read results: '+str(path))
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in sorted(path.iterdir()):
            yield from regular_files(child)
    elif path.exists():
        raise ValueError('Refuse a special file in read results: '+str(path))


def members(source):
    source = Path(source)
    selected = [source/name for name in TOP_FILES]
    selected.extend(source/name for name in ('ITEMS.jsonl','SUMMARY.json','metadata','logs'))
    for family in ('main','away','forward','camera'):
        selected.extend(source/family/name for name in ('ITEMS.jsonl','COMPLETE.json','report'))
        for name in ('request.json','BIND_STATUS.json','PROMPT_PINS.json','kit/CODE_PINS.json','frames/0.json'):
            selected.append(source/family/'a0'/name)
        for rel in ('0','budget_2048/0','budget_4096/0'):
            selected.append(source/family/'a0/results'/rel/'summary_a0.json')
    result = {}
    for path in selected:
        for item in regular_files(path):
            result[str(item.relative_to(source))] = item
    if sum(p.stat().st_size for p in result.values()) > 512*1024**2:
        raise BudgetError('Expanded return exceeds its allowance')
    return result


def save(source, output, slot, persisted_input_bytes=0):
    source, output = Path(source), local_output(output)
    if slot not in (0, 1) or not 0 <= persisted_input_bytes <= PROJECT_LIMIT:
        raise ValueError('Invalid archive slot or persistent input accounting')
    if not output.is_dir():
        raise ValueError('Archive output directory must exist')
    used = sum(p.stat().st_size for p in regular_files(output))
    if used+persisted_input_bytes+ARCHIVE_LIMIT > PROJECT_LIMIT:
        raise BudgetError('The read would exceed its 20 GB project-write allowance')
    if shutil.disk_usage(output).free < MIN_FREE+ARCHIVE_LIMIT:
        raise BudgetError('The archive would breach the 200 GiB project floor')
    paths = members(source)
    target = output/f'save_{slot}.tar.gz'
    temporary = output/f'.save_{slot}.{uuid.uuid4().hex}.partial'
    if target.is_symlink():
        raise ValueError('Archive destination must not be a symlink')
    with temporary.open('xb') as raw:
        limited = LimitedWriter(raw, ARCHIVE_LIMIT)
        with tarfile.open(fileobj=limited, mode='w:gz', compresslevel=1) as archive:
            for relative, path in sorted(paths.items()):
                archive.add(str(path), arcname=relative, recursive=False)
        raw.flush()
        os.fsync(raw.fileno())
    os.replace(temporary, target)
    if shutil.disk_usage(output).free < MIN_FREE:
        raise BudgetError('Project free space fell below the 200 GiB floor')
    return dict(path=str(target), bytes=target.stat().st_size, files=len(paths),
                project_limit_bytes=PROJECT_LIMIT, archive_limit_bytes=ARCHIVE_LIMIT)


def main():
    parser = argparse.ArgumentParser()
    for name in ('source', 'output'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--slot', type=int, choices=(0, 1), required=True)
    parser.add_argument('--persisted-input-bytes', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(save(args.source, args.output, args.slot, args.persisted_input_bytes)))


if __name__ == '__main__':
    main()
