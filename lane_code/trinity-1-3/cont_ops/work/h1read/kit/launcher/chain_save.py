import argparse
from collections import Counter
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import uuid
import time


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
    for family in ('main','away','forward','camera','a7'):
        selected.extend(source/family/name for name in ('ITEMS.jsonl','COMPLETE.json','ASSET_CHECK.json','report'))
        for name in ('request.json','BIND_STATUS.json','PROMPT_PINS.json','kit/CODE_PINS.json','frames/0.json'):
            selected.append(source/family/'a0'/name)
        for rel in ('0','budget_2048/0','budget_4096/0'):
            selected.append(source/family/'a0/results'/rel/'summary_a0.json')
            selected.append(source/family/'a0/results'/rel/'items_a0.jsonl')
    result = {}
    for path in selected:
        for item in regular_files(path):
            result[str(item.relative_to(source))] = item
    if sum(p.stat().st_size for p in result.values()) > 512*1024**2:
        raise BudgetError('Expanded return exceeds its allowance')
    return result


def pack_partial(source, target, config, limit):
    """Pack bounded prefixes once; count all finished records, never infer scores.

    The raw tar budget conservatively bounds even incompressible gzip output.
    Each journal retains a valid JSONL prefix, never a torn or malformed line.
    Counts deduplicate IDs within a journal; arms are never added together.
    """
    started = time.monotonic()
    source, target = Path(source), Path(target)
    report = dict(complete=False, status='PARTIAL', plan_sha256=config['plan_sha256'],
                  step=config['spec']['step'], families={}, journals={}, omitted={}, malformed_summaries={}, truncated=False)
    if 'types' in config['spec']:
        report['types'] = config['spec']['types']
        report['excluded'] = {f:p['excluded'] for f,p in config['spec'].get('population', {}).items()}
    # Reserve space for status, tar headers/padding and worst-case deflate growth.
    budget = max(0, limit - max(262144, limit//100))
    entries = {}
    summaries = {}
    def retain(name, path, size):
        nonlocal budget
        cost = size + 2048
        if cost > budget:
            report['omitted'][name] = dict(bytes=size, reason='archive cap')
            report['truncated'] = True
            return False
        entries[name] = (path, size)
        budget -= cost
        return True

    # Identity and diagnostics precede optional bulk logs/reports.
    for name in ('FAILED.json', 'TRACE.json.gz'):
        path = source/name
        if path.is_file() and not path.is_symlink():
            retain(name, path, path.stat().st_size)
    for family in config['families']:
        detail = dict(complete=False, finished_items=0, types={}, rooms_with_finished_items=0,
                      population=config['spec'].get('population', {}).get(family, {}))
        detail['types'] = dict.fromkeys(detail['population'].get('types', {}), 0)
        report['families'][family] = detail
        marker = source/family/'COMPLETE.json'
        if marker.is_file() and not marker.is_symlink():
            try:
                value = json.loads(marker.read_text())
                if not isinstance(value, dict): raise ValueError('Invalid family marker')
                detail['population'] = value.get('population', detail['population'])
                detail['family_checks_passed'] = True
            except (ValueError, UnicodeError) as error:
                report['malformed_summaries'][str(marker.relative_to(source))] = str(error)
        results = source/family/'a0/results'
        for arm in ('0', 'budget_2048/0', 'budget_4096/0'):
            for filename in ('g0.jsonl', 'items_a0.jsonl', 'summary_a0.json'):
                path = results/arm/filename
                if path.is_symlink():
                    raise ValueError('Symlink in partial results')
                if not path.is_file():
                    continue
                name = str(path.relative_to(source))
                if filename.endswith('.json'):
                    if path.stat().st_size <= 65536:
                        try:
                            value = json.loads(path.read_text())
                            if not isinstance(value, dict): raise ValueError('Invalid summary')
                        except (ValueError, UnicodeError) as error:
                            report['malformed_summaries'][name] = str(error)
                            retain(name, path, path.stat().st_size)
                            continue
                        value.update(complete=False, provisional=True)
                        data = (json.dumps(value, sort_keys=True)+'\n').encode()
                        if len(data)+2048 <= budget:
                            summaries[name] = value
                            budget -= len(data)+2048
                        else:
                            report['omitted'][name] = dict(bytes=len(data), reason='archive cap')
                            report['truncated'] = True
                    else:
                        retain(name, path, path.stat().st_size)
                    continue
                counts, kept_counts, seen, rooms = Counter(), Counter(), set(), set()
                size = lines = kept_lines = invalid = 0
                prefix = True
                with path.open('rb') as stream:
                    for line in stream:
                        lines += 1
                        try:
                            row = json.loads(line)
                            if not line.endswith(b'\n') or not isinstance(row, dict):
                                raise ValueError('Torn line')
                        except (ValueError, UnicodeError):
                            invalid += 1
                            prefix = False
                            continue
                        finished = row.get('status') == 'complete'
                        key = row.get('key', row.get('id'))
                        task = row.get('question_type', row.get('task_type', 'unknown'))
                        fresh = finished and key is not None and key not in seen
                        if fresh:
                            seen.add(key); counts[task] += 1
                            rooms.add(row.get('room', row.get('scene')))
                        if prefix and size + len(line) + 2048 <= budget:
                            size += len(line); kept_lines += 1
                            if fresh: kept_counts[task] += 1
                        else:
                            prefix = False
                retain(name, path, size)
                truncated = kept_lines != lines
                report['truncated'] |= truncated
                report['journals'][name] = dict(lines=lines, retained_lines=kept_lines,
                    retained_bytes=size, invalid_lines=invalid, truncated=truncated,
                    finished_items=sum(counts.values()), types=dict(counts),
                    retained_finished_items=sum(kept_counts.values()), retained_types=dict(kept_counts))
                # Prefer ON16k generation; merged rows are a fallback, not extra items.
                if arm == '0' and (filename == 'g0.jsonl' or 'count_source' not in detail):
                    detail.update(finished_items=sum(counts.values()), types={**detail['types'], **dict(counts)},
                                  rooms_with_finished_items=len(rooms-{None}), count_source=name)
        asset_check = source/family/'ASSET_CHECK.json'
        if asset_check.is_file() and not asset_check.is_symlink():
            retain(str(asset_check.relative_to(source)), asset_check, asset_check.stat().st_size)
        for filename in ('request.json', 'BIND_STATUS.json', 'PROMPT_PINS.json', 'kit/CODE_PINS.json', 'frames/0.json'):
            path = source/family/'a0'/filename
            if path.is_file() and not path.is_symlink():
                retain(str(path.relative_to(source)), path, path.stat().st_size)
    for path in regular_files(source/'metadata'):
        retain(str(path.relative_to(source)), path, path.stat().st_size)
    report['packing_seconds_before_compression'] = time.monotonic()-started
    spec = dict(config['spec'])
    # Raw journal scores are provisional; only this top-level summary is a read report.
    generated = {**summaries, 'SUMMARY.json': report, 'PARTIAL.json': report, 'SPEC.json': spec}
    with Path(target).open('xb') as raw:
        with tarfile.open(fileobj=LimitedWriter(raw, limit), mode='w:gz', compresslevel=1,
                          format=tarfile.USTAR_FORMAT) as archive:
            for name, (path, size) in sorted(entries.items()):
                info = tarfile.TarInfo(name); info.size = size; info.mode = 0o600
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
            for name, value in generated.items():
                data = (json.dumps(value, sort_keys=True)+'\n').encode()
                info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600
                archive.addfile(info, io.BytesIO(data))
        raw.flush(); os.fsync(raw.fileno())
    return dict(seconds=time.monotonic()-started, bytes=Path(target).stat().st_size, **report)


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
        with tarfile.open(fileobj=limited, mode='w:gz', compresslevel=6) as archive:
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
