from pathlib import Path
from tests import test_r1_export17 as prior
from student_pilot import r1_persisted as P
from student_pilot.p3_provenance import load

class HashTwin(prior.Export17):
    def test_same_size_shard_refuses(self):
        root,cfg,run,_,_=self.fixture();cfg=self.export_only(root,cfg,run)
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        label=next(k for k in receipt['pins'] if k.startswith('export/') and k.endswith('.safetensors'))
        sha=receipt['pins'][label]['sha256'];path=Path(r['persisted_files'][sha])
        raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'HANDOVER_FILE_MISMATCH:export/'):
            P.admission(cfg,weights=True)
