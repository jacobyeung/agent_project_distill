"""A comment-only edit to a FEATURE_FILES member in the reader tree vs an export from the patched tree; strict runtime load."""
import json, os, sys, tempfile, types
from pathlib import Path
import torch
W = Path(__file__).resolve().parent; T = W / sys.argv[1]
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
out = W / 'brittle'; out.mkdir(exist_ok=True); os.environ['LANE_TEST_OUTPUT'] = str(out); tempfile.tempdir = str(out)
torch.set_num_threads(8)
from tests.test_carrier_c1_final import final_fixture
from student_pilot import scale_donor as D, carrier_c1_run as run
from student_pilot.p3_provenance import digest, file_pin
exports = sorted((W / 'export').glob('e_*/artifact.json'), key=lambda p: p.stat().st_mtime)[-2:]
for art in exports:
    a = json.loads(art.read_text()); binding = a['scale_donor']['settings']
    m, _, _ = final_fixture(); m.auxiliary_heads.depth.model.visual.requires_grad_(False)
    try:
        D.attach(m, binding); print(sys.argv[1], binding['fov_source'], 'attach with N binding: accepted')
    except ValueError as e:
        print(sys.argv[1], binding['fov_source'], 'attach with N binding: REFUSED', e)
        m, _, _ = final_fixture(); m.auxiliary_heads.depth.model.visual.requires_grad_(False)
        D.attach(m, dict(binding, feature_contract_sha256=digest(D.feature_contract(m.auxiliary_heads.depth))))
        try:
            run.load_artifact(m, file_pin(art)); print('   repinned reader: export accepted')
        except ValueError as e2:
            print('   repinned reader: export REFUSED', e2)
    if sys.argv[1] == 'new':
        m, _, _ = final_fixture(); D.attach(m, binding) if False else None
        m.auxiliary_heads.depth.model.visual.requires_grad_(False); D.attach(m, binding)
        heads = torch.load(Path(a['heads']['path']), weights_only=True)
        try:
            m.auxiliary_heads.load_state_dict(heads, strict=True); print('   strict runtime-style load after attach: accepted')
        except Exception as e3:
            print('   strict runtime-style load after attach: REFUSED', str(e3)[:160])
