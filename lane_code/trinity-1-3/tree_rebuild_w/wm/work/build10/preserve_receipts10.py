from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10';F=L.parent/'w9f';records=[]
for variant in ('tree','base'):
    for group in ('generator','legacy','r2'):
        source=F/'work/build9fix/proofs'/('suite_'+variant)/group/'GROUP_RECEIPT.json'
        if not source.exists():continue
        target=L/'work/merge11/proofs/resume9fix'/variant/group/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
        receipt=json.loads(source.read_text())
        records.append(dict(source=str(source),copy=str(target.relative_to(L)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            eligible=False,reason='Current runner has relocated workspace bindings; its exact byte hash differs. Tree inputs additionally changed. No mismatching receipt is reused.'))
(B/'RESUME_AUDIT.json').write_text(json.dumps(records,indent=2)+'\n')
source=F/'work/build9fix/CHANGED_COVERAGE.json';(B/'B9F_COVERAGE.json').write_bytes(source.read_bytes())
out=L/'work/merge11/proofs/audit';out.mkdir(exist_ok=True)
(out/'INFERENCE_COMPONENTS.json').write_bytes((F/'work/build9fix/proofs/audit/INFERENCE_COMPONENTS.json').read_bytes())
