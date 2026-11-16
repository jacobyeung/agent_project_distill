import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'vendor/r5'))
import adapter as A

PAYLOADS = {'camera': ROOT/'payload'}
CODE = ('direct.py', 'vendor/r3/adapter.py', 'vendor/r4/adapter.py',
        'vendor/r5/adapter.py', 'vendor/r5/dev_scoring.py', 'vendor/r5/report.py')


def code_pins():
    return {name: A.sha(ROOT/name) for name in CODE}


def validate(cfg):
    expected = dict(schema='devs1-camera-direct-v1', family='camera',
                    cohort_sha256=A.R4.CAMERA_COHORT_SHA256, tasks_sha256=A.R4.CAMERA_TASKS_SHA256,
                    code_pins=code_pins())
    if cfg.get('camera') != expected:
        raise ValueError('Camera reader identity changed')
    if Path(cfg['devs1']['payload']).resolve() != PAYLOADS['camera']:
        raise ValueError('Camera payload path differs')
    if len(cfg['cells']) != 1 or cfg['cells'][0]['model'] not in ('cp1m200', 'f17'):
        raise ValueError('Camera baseline model differs')
    A.R4.validate_cell(cfg['cells'][0], cfg['cells'][0]['model'], PAYLOADS['camera'])
    if cfg['devs1']['pins'].get('TASKS.jsonl') != A.R4.CAMERA_TASKS_SHA256:
        raise ValueError('Frozen camera tasks differ')
    request = {k: v for k, v in cfg.items() if k not in ('binding', 'output')}
    if hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest() != cfg['binding']:
        raise ValueError('Camera request binding differs')


def bind(args):
    args.payload = str(PAYLOADS[args.family])
    A.bind(args)
    path = Path(args.dest)/'request.json'
    cfg = json.loads(path.read_text())
    cfg['camera'] = dict(schema='devs1-camera-direct-v1', family=args.family,
        cohort_sha256=A.R4.CAMERA_COHORT_SHA256, tasks_sha256=A.R4.CAMERA_TASKS_SHA256,
        code_pins=code_pins())
    request = {k: v for k, v in cfg.items() if k not in ('binding', 'output')}
    cfg['binding'] = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    validate(cfg)
    rebind_frames(args.dest, cfg['binding'])
    A.dump(path, cfg)
    print(json.dumps(dict(camera_binding=cfg['binding'], cell=args.cell, dry=args.dry)))


def rebind_frames(dest, binding):
    dest = Path(dest)
    path = dest/'frames/0.json'
    if not path.exists():
        return
    frames = json.loads(path.read_text())
    frames['binding'] = binding
    A.dump(path, frames)
    status = json.loads((dest/'BIND_STATUS.json').read_text())
    status['frames_sha256'] = A.sha(path)
    A.dump(dest/'BIND_STATUS.json', status)


def launch(args):
    validate(json.loads((Path(args.dest)/'request.json').read_text()))
    A.launch(args)


def merge(args):
    validate(json.loads((Path(args.source)/'request.json').read_text()))
    A.merge_existing(args)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    q = sub.add_parser('bind')
    q.add_argument('--family', choices=PAYLOADS, default='camera')
    q.add_argument('--cell', choices=('cp1m200', 'f17'), required=True)
    for name in ('kit', 'dest', 'models', 'frames-root'):
        q.add_argument('--'+name, required=True)
    q.add_argument('--dry', action='store_true')
    q = sub.add_parser('launch')
    q.add_argument('--dest', required=True)
    q.add_argument('--attempt', required=True)
    q = sub.add_parser('merge')
    for name in ('source', 'dest', 'kit', 'attempt'):
        q.add_argument('--'+name, required=True)
    q.add_argument('--tokenizer-dir')
    q.add_argument('--tokenizer-manifest')
    args = parser.parse_args()
    {'bind': bind, 'launch': launch, 'merge': merge}[args.command](args)


if __name__ == '__main__':
    main()
