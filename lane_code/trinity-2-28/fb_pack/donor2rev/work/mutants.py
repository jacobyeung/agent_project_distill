"""Build leak mutants of work/new; each must make donor2's own tests fail (M1 negative controls)."""
import json, shutil, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'

MUTANTS = {
    # V1 reads the live private FoV module instead of its checkpoint copy.
    'mut_live_private_fov': [
        ('student_pilot/scale_donor.py',
         "            self.fov = copy.deepcopy(depth.fov)\n",
         "            self.fov = copy.deepcopy(depth.fov)\n            self._live_fov = weakref.ref(depth.fov)\n"),
        ('student_pilot/scale_donor.py',
         "fov = (1e-4 + (math.pi - 2e-4) * self.fov(captured.states.float()).sigmoid())[0]",
         "fov = (1e-4 + (math.pi - 2e-4) * self._live_fov()(captured.states.float()).sigmoid())[0]"),
    ],
    # The tower bridge feeds the live pose-head FoV (own pose9) to the donor encoder.
    'mut_pose_head_fov': [
        ('student_pilot/scale_donor.py',
         "    def forward(self, batch, tower_state=None):\n",
         "    def forward(self, batch, tower_state=None, live_fov=None):\n"),
        ('student_pilot/scale_donor.py',
         "        if fov.shape != (32, 2)",
         "        if live_fov is not None:\n            fov = live_fov.to(fov)\n        if fov.shape != (32, 2)"),
        ('student_pilot/tower_read.py',
         "if scale_donor is None else scale_donor(batch, state).double().cpu().numpy())",
         "if scale_donor is None else scale_donor(batch, state, live_fov=torch.as_tensor(np.asarray(heads.pose9)[:, 7:9].copy())).double().cpu().numpy())"),
    ],
    # The donor reads the live frame queries instead of its frozen checkpoint copy.
    'mut_live_queries': [
        ('student_pilot/scale_donor.py',
         "        self.config = copy.deepcopy(depth.config)\n",
         "        self.config = copy.deepcopy(depth.config)\n        self._live_depth = weakref.ref(depth)\n"),
        ('student_pilot/scale_donor.py',
         "                                frame_queries=self.frame_queries)",
         "                                frame_queries=self._live_depth().auxiliary_heads.frame_queries)"),
    ],
}

results = {}
for name, edits in MUTANTS.items():
    tree = W / name
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(W / 'new', tree, ignore=shutil.ignore_patterns('__pycache__'))
    for rel, old, new in edits:
        p = tree / rel; s = p.read_text(); assert s.count(old) == 1, (name, rel, old); p.write_text(s.replace(old, new))
    log = W / f'{name}.unit.log'
    r = subprocess.run(['nice', '-n', '10', PY, '-B', str(W / 'run_unit.py'), name], capture_output=True, text=True)
    log.write_text(r.stdout + r.stderr)
    failed = [l.split(' (')[0].replace('FAIL: ', '').replace('ERROR: ', '') for l in (r.stdout + r.stderr).splitlines()
              if l.startswith(('FAIL: ', 'ERROR: '))]
    results[name] = dict(rc=r.returncode, failed_tests=failed, caught=r.returncode != 0)
    print(name, results[name], flush=True)
(W / 'MUTANTS_UNIT.json').write_text(json.dumps(results, indent=1))
