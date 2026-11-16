from __future__ import annotations
import argparse
from pathlib import Path


def prepare(args):
    if args.dataset == 'arkitscenes':
        if args.sequence_dir is None or args.correspondence is None:
            raise ValueError('ARKitScenes requires --sequence-dir and --correspondence')
        from prepare_arkit_scene import prepare as prepare_arkit
        return prepare_arkit(args)
    if args.dataset == 'scannetppv2':
        if args.obb_lengths not in ('full', 'half'):
            raise ValueError('ScanNet++ requires its verified --obb-lengths convention')
        from prepare_gt_scene import prepare as prepare_scannetpp
        return prepare_scannetpp(args)
    raise ValueError('unsupported corpus; no implicit preparer fallback')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare',))
    parser.add_argument('--dataset', required=True, choices=('arkitscenes', 'scannetppv2'))
    parser.add_argument('--scene', required=True)
    parser.add_argument('--frames-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sequence-dir', type=Path)
    parser.add_argument('--correspondence', type=Path)
    parser.add_argument('--obb-lengths', choices=('full', 'half'))
    return prepare(parser.parse_args())


if __name__ == '__main__':
    main()
