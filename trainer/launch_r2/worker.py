"""Opaque worker adapter for the parent's distributed command."""
from pathlib import Path
import sys


def main(root, mode, arm):
    sys.path.insert(0,str(Path(root).resolve()/'o/ee000001'))
    from launch_r2.distributed import worker
    return worker(root,mode,arm)


if __name__=='__main__':
    main(*sys.argv[1:])
