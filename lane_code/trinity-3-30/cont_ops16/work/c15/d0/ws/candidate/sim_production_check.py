"""Run s1_warm_data_identity.check on the real mirrored donor preparation, config and three rebuilt
stream receipts, against a simulated fresh admission (every run-local pin relocated to a new run with
new SHAs) shaped as prepared() hands it to bind(). File reads are redirected to the off-node mirror."""
import copy
import json
from pathlib import Path
import sys
from unittest.mock import patch

W = Path(__file__).resolve().parent
sys.path.insert(0, '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
import student_pilot  # noqa: E402
student_pilot.__path__.insert(0, str(W / 'student_pilot'))
from student_pilot import s1_warm_data_identity as guard  # noqa: E402

P = Path('/scratch/jjyeung/orch_cd/orchard_cp2/out/admission_preparation_169097/prepare_dd26bb95f37a43789206c6e4d4cd94bd')
RUN = '/runs/469ddece/'
donor = json.loads((P / 'config.json').read_text())
before = json.loads((P / 'prepared/s1_receipt.json').read_text())
files = {}
for name in ('pointing', 'routing', 'vqa'):
    files[donor['streams'][name]['path']] = json.loads((P / name / 'receipt.json').read_text())
files[donor['streams']['pose']['path']] = {'schema': 'pose-mix-stand-in'}


def relocate(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'} and RUN + 'inputs/' in value['path']:
            return {'path': value['path'].replace(RUN, '/runs/fedcba98/'), 'sha256': 'd' * 64}
        return {k: relocate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v) for v in value]
    return value


cfg = copy.deepcopy(donor)
cfg['init_artifact'] = {'artifact': {'path': '/x/m200/artifact.json', 'sha256': '1' * 64}, 'lm': 'full',
                        'heads': ['pose', 'depth', 'frame_embeddings']}
new_receipt = relocate(before)
for name, pin in donor['streams'].items():
    if RUN + 'inputs/' in pin['path']:
        new = relocate(pin)
        files[new['path']] = relocate(files[pin['path']])
        cfg['streams'][name] = new
    assert new_receipt['streams'][name]['receipt'] == cfg['streams'][name], name
# prepared() final-mode transform (carrier_c1_run.py:669-672), applied to the new receipt only.
new_receipt = {**new_receipt, 'align': cfg.get('align'), 'init_artifact': cfg['init_artifact'],
               'frame_markers': cfg.get('frame_markers', False), 'pointing_weights': cfg.get('pointing_weights'),
               'camera': {**new_receipt['camera'], **cfg.get('camera_overrides', {})}}
with patch.object(guard, 'pinned', side_effect=lambda pin: pin['path']), \
     patch.object(guard, 'load', side_effect=lambda path: copy.deepcopy(files[path])):
    guard.check(before, donor, new_receipt, cfg)
    print('PASS: real mirrored schema, fresh-admission relocation binds')
    for label, mutate in (
            ('camera override not applied', lambda r: r.update(camera=before['camera'])),
            ('frame_markers flipped', lambda r: r.update(frame_markers=not r['frame_markers'])),
            ('pose frame_prefix', lambda r: r['streams']['pose']['sources'][0].update(frame_prefix='/other/')),
            ('vqa count', lambda r: r['streams']['vqa'].update(count=r['streams']['vqa']['count'] - 1)),
            ('pose source db sha', lambda r: r['streams']['pose']['sources'][1]['database'].update(sha256='e' * 64)),
            ('census db not equal stream db', lambda r: r['scene_filter_report']['expected']['vqa']['population']
             ['database'].update(sha256='c' * 64))):
        changed = copy.deepcopy(new_receipt)
        mutate(changed)
        try:
            guard.check(before, donor, changed, cfg)
            print('ACCEPTED (unexpected):', label)
        except ValueError as error:
            print('refused:', label, '->', str(error)[:90])
    routing = cfg['streams']['routing']['path']
    files[routing] = {**files[routing], 'policy_version': 'changed'}
    try:
        guard.check(before, donor, new_receipt, cfg)
        print('ACCEPTED (unexpected): routing receipt policy_version')
    except ValueError as error:
        print('refused: routing receipt policy_version ->', str(error)[:90])
