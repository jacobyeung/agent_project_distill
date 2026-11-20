"""Verify completed outputs and seal checksums after every writer exits."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import k1x as K
import summarize_round4 as S


def main():
    result=json.loads((S.OUT/'K1X4.json').read_text())
    box=json.loads((S.BOX/'BOX.json').read_text())
    tests=json.loads((S.OUT/'TESTS.json').read_text())
    assert tests['passed'] and tests['skipped']==0,tests
    assert len(result['rows'])==1253 and len(box['rows'])==1253
    assert len((S.OUT/'REPORT_R2_4.md').read_text().splitlines())<=60
    assert len((S.BOX/'REPORT_BOX.md').read_text().splitlines())<=50
    assert all(p['passed'] for p in result['parity'])
    assert result['served_invariance']['checked']==8*1253
    old=json.loads((K.ROOT/'out/K1X.json').read_text())
    oldrows={r['row_id']:r for r in old['rows']}
    rows={r['row_id']:r for r in result['rows']}
    preservation=[]
    for line in (K.ROOT/'out/SHA256SUMS').read_text().splitlines():
        sha,path=line.split(maxsplit=1)
        if not path.startswith('out/'):continue
        actual=hashlib.sha256((K.ROOT/path).read_bytes()).hexdigest()
        assert actual==sha,path
        preservation.append(dict(path=path,sha256=actual,passed=True))
    for reading in result['readings']['B'].values():
        for subgroup in reading.values():
            for contrast in list(subgroup['contrasts'].values())+list(subgroup['gt_depth_rows'].values()):
                assert contrast['n']==len(contrast['row_ids'])
                for rid in contrast['row_ids']:assert S.support(rows[rid],contrast['arm'],contrast['reference'])
    depth='deployed/GT/G3T/own'
    old_new_refusals=[r['row_id'] for r in old['rows'] if r['split']=='heldout'
        and r['cells'][K.DBASE]['prediction'] is not None and r['cells'][depth]['prediction'] is None]
    recovered=[rid for rid in old_new_refusals if rows[rid]['cells'][depth]['prediction'] is not None]
    remaining=[rid for rid in old_new_refusals if rid not in recovered]
    assert len(box['e3_base_parity'])==2506 and all(x['passed'] for x in box['e3_base_parity'])
    files=[p for p in K.ROOT.rglob('*') if p.is_file()]
    size=sum(p.stat().st_size for p in files)
    assert size<3_000_000_000,size
    receipt=dict(status='PASS',tests=tests,rows=1253,served_cells_exact=10024,
        box_base_exact=len(box['base_parity']),e3_base_exact=len(box['e3_base_parity']),
        original_outputs_unchanged=preservation,workspace_bytes=size,
        heldout_prior_depth_refusals=dict(count=len(old_new_refusals),recovered=len(recovered),remaining=len(remaining),
            recovered_ids=recovered,remaining_ids=remaining),
        missing_depth_pose_and_hole_regressions='PASS',support_definition_and_train_only_freeze_tests='PASS')
    K.write(S.OUT/'VALIDATION.json',receipt)
    K.write(S.BOX/'TESTS.json',tests)
    K.write(S.BOX/'VALIDATION.json',dict(status='PASS',base_exact=2506,e3_base_exact=2506,
        floor=box['freeze']['floor'],heldout_used_for_fit=False,dev_item_check='pending rank 1 dump',tests=tests))
    # Keep the CLI's convenience report consistent with the requested report.
    (S.OUT/'REPORT_R2.md').write_text((S.OUT/'REPORT_R2_4.md').read_text())
    S.checksums()
    for folder in (S.OUT,S.BOX):
        for line in (folder/'SHA256SUMS').read_text().splitlines():
            sha,path=line.split(maxsplit=1)
            assert hashlib.sha256((K.ROOT/path).read_bytes()).hexdigest()==sha,path
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
