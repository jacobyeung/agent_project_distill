"""Audit the six copied producer examples without reopening NFS or evaluation data."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK))
import score_fov as f
import json


def main():
    inputs = f.Inputs()
    for p in (f.__file__, __file__, sys.executable, f.KIT/'core.py', f.KIT/'score_400.py'):
        inputs.check(p)
    inputs.read(f.AMENDMENT, f.AMENDMENT_SHA)
    files = sorted(WORK.glob('k1fwd2_example_*'))
    assert len(files) == 6
    for p in files:
        inputs.check(p)
    receipt = inputs.read(WORK/'k1fwd2_example_FOV_RECEIPT.json.input')
    phase = inputs.read(WORK/'k1fwd2_example_PHASE_COMPLETE.json.input')
    parity = inputs.read(WORK/'k1fwd2_example_fov_check_canary.json.input')
    assert receipt['boundaries_sha256'] == f.BOUNDARIES_SHA
    inputs.check(WORK/'k1fwd2_example_boundaries_454e9b27.py.txt', f.BOUNDARIES_SHA)
    inputs.check(WORK/'k1fwd2_example_fov_check_03319000.py.txt', '0331900005077792da9920a97b37902aebe7aaa8122947b7a86daf8cdb4fc780')
    assert receipt['sources']['V1'] == f.V1_SOURCE
    assert receipt['checks']['second_pass_pose_fov_bit_identical'] is True
    assert receipt['checks']['second_pass_pose_fov_max_abs'] == 0.0
    assert receipt['checkpoint']['sha256'] == phase['checkpoint']['sha256'] == f.CHECKPOINT_SHA
    assert receipt['capture_sha256'] == phase['capture_sha256']
    assert 'depth' not in receipt['keys'] and list(phase['files']) == ['own.npz']
    assert parity['summary']['passed'] is False
    rows = []
    for row in parity['rows']:
        if row['scored']:
            # No anchors are fabricated: absence is checked before comparison.
            try:
                f.anchor_grid(row, {'key':row['key']}, 'FOV_CHECK.json')
            except f.core.Refusal as exc:
                reason = str(exc)
                assert reason.startswith('P3_ANCHOR_INDICES_MISSING:'), reason
            else:
                raise AssertionError('canary unexpectedly supplies P3')
            rows.append({'key':row['key'], 'status':'MISSING', 'reason':reason,
                         'missing_fields':['anchor_indices', 'grid_uv or grid_uv_sha256']})
    result = {'input_sha256':inputs.pins, 'command':f.shlex.join([sys.executable,'-B',str(Path(__file__).resolve())]),
              'tests':[{'name':'producer code, receipt mapping, and named P3 absence verified','pass':True}],
              'canary_is_complete_provenance':False, 'P3':rows,
              'original_NFS_copies':{str(p): '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/fb_pack/' + p.name.removesuffix('.input') for p in files}}
    (WORK/'tests'/'PRODUCER_EXAMPLES.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass':True, 'P3':'MISSING', 'scored_canary_rows':len(rows)}))


if __name__ == '__main__':
    main()
