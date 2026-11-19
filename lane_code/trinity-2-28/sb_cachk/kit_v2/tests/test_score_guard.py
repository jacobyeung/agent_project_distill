"""CPU-only refusal tests: each public scoring entry must fail before writing."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import mc_score_guard as G


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'directory'
            for p in root.rglob('*')}


def prepare(root, case, output):
    bars = root/'out/v2'
    bars.mkdir(parents=True)
    if case != 'missing':
        raw = (KIT.parent/'out/v2/BARS_FROZEN.json').read_bytes()
        (bars/'BARS_FROZEN.json').write_bytes(raw + (b' ' if case == 'tampered' else b''))
    if case == 'existing':
        output.mkdir(parents=True, exist_ok=True)
        (output/'PER_ITEM.jsonl').write_text('existing score bytes\n')
    return bars


ENTRIES = [
    ('mc_price', "m.main()", "['mc_price.py','S_A0_D64',str(o/'price')] ", 'price'),
    ('mc_summary', 'm.dry()', "['mc_summary.py','dry']", 'dry'),
    ('mc_summary', 'm.final()', "['mc_summary.py','final']", ''),
    ('mc_step0', 'm.main()', "['mc_step0.py','all']", 'dry'),
    ('mc_seeds', 'm.main()', "['mc_seeds.py','all']", 'seeds'),
    ('mc_stubs', 'm.main()', "['mc_stubs.py','seed']", 'dry'),
    ('mc_dryrun_report', 'm.main()', "['mc_dryrun_report.py']", ''),
    ('mc_track_pass', "sys.exit(m.main(['--device','cpu','--out',str(o/'track')]))", "['mc_track_pass.py']", 'track'),
]


@pytest.mark.parametrize('case', ['missing', 'tampered', 'existing'])
@pytest.mark.parametrize('module,call,argv,subdir', ENTRIES)
def test_scoring_entry_refuses_without_writes(tmp_path, case, module, call, argv, subdir):
    out = tmp_path/'out/v2'
    prepare(tmp_path, case, out/subdir)
    before = snapshot(tmp_path)
    code = (f'import sys; from pathlib import Path; sys.path.insert(0,{str(KIT)!r}); '
            f'import mc_common as C; o=Path({str(out)!r}); C.OUT=o; '
            f'import {module} as m; sys.argv={argv}; {call}')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', CUDA_VISIBLE_DEVICES='')
    ret = subprocess.run([sys.executable, '-B', '-c', code], env=env, capture_output=True, text=True)
    assert ret.returncode != 0 and 'BARS_FIRST:' in ret.stderr, ret.stderr
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('case', ['missing', 'tampered', 'existing'])
@pytest.mark.parametrize('script', ['launch_gpu.sh', 'post_gpu.sh'])
def test_shell_entry_refuses_without_writes(tmp_path, case, script):
    kit = tmp_path/'kit_v2'; kit.mkdir()
    for name in (script, 'mc_score_guard.py'):
        shutil.copy2(KIT/name, kit/name)
    out = tmp_path/'out/v2'
    prepare(tmp_path, case, out)
    before = snapshot(tmp_path)
    env = dict(os.environ, MC_DRY_LAUNCH='1', MC_SKIP_PREFLIGHT='1', MC_HOST='trinity-1-18', MC_WAIT_SECONDS='0',
               MC_NVIDIA_SMI='/missing/mock-smi-must-never-be-reached', PYTHONDONTWRITEBYTECODE='1')
    ret = subprocess.run(['bash', str(kit/script)], env=env, capture_output=True, text=True)
    assert ret.returncode != 0 and 'BARS_FIRST:' in ret.stderr, ret.stderr
    assert snapshot(tmp_path) == before


def test_capture_price_existing_file_refused(tmp_path):
    bars = prepare(tmp_path, 'valid', tmp_path/'scores')
    target = tmp_path/'scores'; target.mkdir()
    (target/'scannet__capture.json.gz').write_bytes(b'existing per-capture scores')
    before = snapshot(tmp_path)
    with pytest.raises(SystemExit, match='already exists'):
        G.check(bars, [target], capture_scores=True)
    assert snapshot(tmp_path) == before


def test_valid_freeze_returns_pin_without_writes(tmp_path):
    bars = prepare(tmp_path, 'valid', tmp_path/'scores')
    before = snapshot(tmp_path)
    assert G.check(bars, [tmp_path/'scores']) == {str(bars/'BARS_FROZEN.json'): G.FROZEN_SHA256}
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('case', ['missing', 'tampered', 'existing'])
def test_cpu_runner_refuses_before_cache_creation(tmp_path, case):
    kit = tmp_path/'kit_v2'; kit.mkdir()
    for name in ('run_cpu.sh', 'mc_score_guard.py'):
        shutil.copy2(KIT/name, kit/name)
    out = tmp_path/'out/v2'
    prepare(tmp_path, case, out/'price')
    before = snapshot(tmp_path)
    ret = subprocess.run(['bash', str(kit/'run_cpu.sh'), 'p1cpu', 'mc_price.py', 'S_A0_D64', str(out/'price')],
                         capture_output=True, text=True)
    assert ret.returncode != 0 and 'BARS_FIRST:' in ret.stderr, ret.stderr
    assert snapshot(tmp_path) == before
