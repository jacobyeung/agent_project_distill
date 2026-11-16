import argparse
import json
import os
from pathlib import Path
import shutil
import tarfile


MIN_FREE_BYTES = 200*1024**3
MEMBERS = ('run/request.json', 'run/BIND_STATUS.json', 'run/PROMPT_PINS.json',
           'run/kit/CODE_PINS.json', 'run/frames/0.json', 'run/results')


class SpaceFloor(RuntimeError):
    pass


def free_bytes(path):
    return shutil.disk_usage(path).free


def check_space(path):
    available = free_bytes(path)
    if available < MIN_FREE_BYTES:
        raise SpaceFloor('Project space below the 200 GiB floor: '+str(available)+' bytes available')
    return available


def save(source, output, slot):
    source, output = Path(source), Path(output)
    if slot not in (0, 1):
        raise ValueError('Rolling archive slot must be zero or one')
    check_space(output)
    target = output/('save_'+str(slot)+'.tar')
    temporary = output/('.save_'+str(slot)+'.partial')
    if target.is_symlink():
        raise ValueError('Archive destination must not be a symlink')
    with temporary.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w') as archive:
            for name in MEMBERS:
                path = source/name
                if not path.exists() or path.is_symlink():
                    raise ValueError('Missing or unsafe archive member: '+name)
                archive.add(str(path), arcname=name)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(target))
    check_space(output)
    return dict(path=str(target), bytes=target.stat().st_size, floor_bytes=MIN_FREE_BYTES)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--slot', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(save(args.source, args.output, args.slot)))
    except SpaceFloor as error:
        parser.exit(78, str(error)+'\n')
