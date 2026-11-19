"""Contrast: the same FoV mutants with the fixture's nonzero FiLM removed (zero-initialized FoV path)."""
import json, shutil, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
FILM = ("        film.weight.copy_(torch.randn(film.weight.shape, generator=torch.Generator().manual_seed(5)) * .5)\n")
results = {}
for name in ('mut_live_private_fov', 'mut_pose_head_fov'):
    tree = W / (name + '_film0')
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(W / name, tree, ignore=shutil.ignore_patterns('__pycache__'))
    p = tree / 'tests/test_scale_donor.py'; s = p.read_text(); assert s.count(FILM) == 1
    p.write_text(s.replace(FILM, "        pass\n"))
    tests = ['tests.test_scale_donor.ScaleDonorTests.test_both_variants_are_frozen_and_use_pinned_checkpoint',
             'tests.test_scale_donor.ScaleDonorTests.test_tower_scales_once_and_own_depth_stays_live']
    r = subprocess.run(['nice', '-n', '10', PY, '-B', str(W / 'run_unit.py'), tree.name, *tests], capture_output=True, text=True)
    (W / f'{tree.name}.unit.log').write_text(r.stdout + r.stderr)
    results[tree.name] = dict(rc=r.returncode, escaped=r.returncode == 0)
    print(tree.name, results[tree.name], flush=True)
(W / 'MUTANTS_FILM0.json').write_text(json.dumps(results, indent=1))
