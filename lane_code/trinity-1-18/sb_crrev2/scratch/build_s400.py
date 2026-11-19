"""Build synthetic step-400/600 packages+returns (complete and partial) from A4 and rob/t2, under this scratch."""
import glob, json, os, shutil
from pathlib import Path
IN = Path('/scratch/jjyeung/orch_n30/sb_callrate/in')
PKG = IN / 'cont_ops16/work/c15/r1route/out3s/A'
A4 = IN / 'cont_ops/work/r1route/out3/A4'
T2 = Path('/scratch/jjyeung/orch_n30/sb_crrev/scratch/rob/t2/ret')
HERE = Path(__file__).absolute().parent / 'steps'


def build(name, step, source):
    root = HERE / name
    if root.exists():
        raise SystemExit('exists: ' + str(root))
    root.mkdir(parents=True)
    plan = json.loads((PKG / 'READ_PLAN.json').read_text())
    plan['export_binding']['step'] = step
    (root / 'READ_PLAN.json').write_text(json.dumps(plan))
    shutil.copy2(PKG / 'tower_sequence.py', root / 'tower_sequence.py')
    os.symlink(A4 / 'package', root / 'package')
    os.symlink(A4 / 'src', root / 'src')
    shutil.copytree(source, root / 'ret', symlinks=True)
    pin = root / 'ret/metadata/EXPORT_PIN.json'
    data = json.loads(pin.read_text()); data['step'] = step; pin.write_text(json.dumps(data))
    for env in glob.glob(str(root / 'ret/metadata/reads/*/metadata/journals/*/*/environment.json')):
        data = json.loads(Path(env).read_text())
        data['binding']['step'] = step
        Path(env).write_text(json.dumps(data))


build('p400', 400, A4 / 'ret')
build('p600', 600, A4 / 'ret')
build('p400partial', 400, T2)
build('p600partial', 600, T2)
print('built', sorted(os.listdir(HERE)))
