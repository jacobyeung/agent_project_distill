"""Run the unmodified filter on explicit folders, without copying or writing manifests."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def root_gate(script, folder):
    # Read constants without importing the filter, whose top level walks the current tree.
    constants = {}
    for node in ast.parse(script.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ('MAXDIR', 'SUBSTR'):
                constants[name] = ast.literal_eval(node.value)
            elif name == 'DIRRE':
                constants[name] = re.compile(ast.literal_eval(node.value.args[0]))
    name = folder.name
    if name == '.git' or 'frames' in name or constants['DIRRE'].match(name):
        return 'directory name excluded at hourly tree root'
    if any(s in '/' + name + '/' for s in constants['SUBSTR']):
        return 'path substring excluded at hourly tree root'
    if len(os.listdir(folder)) > constants['MAXDIR']:
        return f"directory exceeds MAXDIR={constants['MAXDIR']} at hourly tree root"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path)
    args = parser.parse_args()
    if os.environ.get('LCS_ENABLE_DRY_COUNT') != '1':
        parser.error('disabled; set LCS_ENABLE_DRY_COUNT=1')
    base = Path(os.environ.get('LCS_B', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'))
    script = Path(os.environ.get('LCS_FILTER', str(base / 'tools' / 'lane_code_filter.py'))).resolve(strict=True)
    failures = 0
    for folder in args.folders:
        try:
            # Check the lexical path before resolve: hourly os.walk never enters symlinked lanes.
            folder = Path(os.path.abspath(str(folder)))
            if any(p.is_symlink() for p in (folder,) + tuple(folder.parents)):
                raise ValueError('symlinked folders or ancestors are refused')
            try:
                folder.relative_to('/scratch/jjyeung/orch_n30')
            except ValueError:
                raise ValueError('folders must be under /scratch/jjyeung/orch_n30/')
            folder = folder.resolve(strict=True)
            if not folder.is_dir():
                raise ValueError('folder must be an existing directory')
            # No manifest argument: the filter makes no output files.
            result = subprocess.run([sys.executable, '-I', '-s', '-B', str(script), folder.name],
                                    cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            if result.returncode:
                raise ValueError(f'filter exit {result.returncode}: {result.stderr.decode(errors="replace")}')
            paths = [os.fsdecode(x) for x in result.stdout.split(b'\0') if x]
            stats = result.stderr.decode(errors='replace').strip()
            nbytes = sum((folder / p).stat().st_size for p in paths)
            match = re.search(r'files=(\d+) bytes=(\d+)', stats)
            if not match or (int(match[1]), int(match[2])) != (len(paths), nbytes):
                raise ValueError('filter stats disagree with selected files; tree may be changing')
            gate = root_gate(script, folder)
            print(json.dumps(dict(folder=str(folder), files=len(paths), bytes=nbytes, filter_stats=stats,
                                  hourly_root_gate_reason=gate, hourly_files=0 if gate else len(paths),
                                  hourly_bytes=0 if gate else nbytes), sort_keys=True))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            print(f'REFUSED {folder}: {exc}', file=sys.stderr)
            failures += 1
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
