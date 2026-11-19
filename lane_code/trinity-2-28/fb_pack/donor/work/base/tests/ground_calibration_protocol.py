"""Recompute tau and present-object miss rate from pinned native query exports.

Required input JSON contains continuation='native_single_token_v1', artifact
SHA, split='train', tau_slice=True, validation_used=False and the mdg_train
collect_outputs fields in records. This test refuses historical batched scores.
"""
import argparse,json
from pathlib import Path
import numpy as np
from student_pilot.mdg_train import choose_tau,metrics_at


def main():
    p=argparse.ArgumentParser();p.add_argument('--records',required=True);p.add_argument('--out',required=True)
    args=p.parse_args();source=Path(args.records)
    if not source.exists():
        result=dict(status='PENDING-INPUT',expected_path=str(source),
                    required='Native-query outputs on the frozen training tau slice, including point hits, positive labels and absent scores',
                    prohibition='Do not reuse tau 0.27 or its miss rate from a batched-suffix export')
    else:
        data=json.loads(source.read_text())
        assert data['continuation']=='native_single_token_v1'
        assert data['split']=='train' and data['tau_slice'] is True and data['validation_used'] is False
        assert len(data['artifact_sha256'])==64
        records=data['records'];tau,objective=choose_tau(records);metrics=metrics_at(records,tau)
        result=dict(status='PASS',continuation=data['continuation'],artifact_sha256=data['artifact_sha256'],
                    tau=tau,objective=objective,present_frame_miss_rate=1-metrics['presence_recall'],metrics=metrics,
                    note='Frame-presence miss rate; object-level not-seen requires grouped labels and geometry/admission outcomes')
        assert len(records['clips']) == 40, 'Require the complete frozen 40-clip tau slice'
        assert 'objects' in data, 'Require grouped object outcomes to derive the row miss rate'
        present=[o for o in data['objects'] if o['gt_present']]
        assert present
        assert all(len(o['prob']) == len(o['eligible']) == 32 for o in present)
        misses=[not any(float(p)>=tau and bool(ok) for p,ok in zip(o['prob'],o['eligible'])) for o in present]
        result.update(present_object_miss_rate=float(np.mean(misses)),present_objects=len(present))
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
