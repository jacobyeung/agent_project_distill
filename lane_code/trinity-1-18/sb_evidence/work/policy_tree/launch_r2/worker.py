"""Opaque worker adapter for the parent's distributed command."""
from pathlib import Path
import os
import sys


def main(root, mode, arm):
    if arm != '0':
        raise ValueError('Unknown worker arm')
    sys.path.insert(0,os.environ['K2'])
    from launch_r2.distributed import worker
    return worker(root,mode,arm)


if __name__=='__main__':
    main(*sys.argv[1:])
