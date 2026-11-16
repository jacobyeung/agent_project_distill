"""CPU namespace probe adapted from native_stage.namespace (C8r)."""
import os
from pathlib import Path


def namespace(root, config):
    root = Path(root)
    argv = ['/usr/bin/bwrap']
    for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc', 'opt', 'run', 'sys'):
        path = Path('/') / name
        if path.is_symlink():
            argv += ['--symlink', os.readlink(path), str(path)]
        elif path.exists():
            argv += ['--ro-bind', str(path), str(path)]
    # CPU rehearsal exposes no GPU devices and cannot open network connections.
    # Every persistent writable bind is a directory under the build workspace.
    argv += ['--dev', '/dev', '--proc', '/proc', '--unshare-net',
             '--dir', '/scratch', '--ro-bind', str(root / 'sj'), '/scratch/jjyeung',
             '--ro-bind', config['build'], config['build']]
    for path in config['runtime_paths']:
        argv += ['--ro-bind', path, path]
    argv += ['--bind', config['output'], config['output'],
             '--die-with-parent', '--chdir', config['output']]
    return argv
