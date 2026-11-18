from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
s=(B/'proof_r1_edges9.py').read_text().replace("O=L/'work/merge11/proofs/n1/r1_edges'","O=L/'work/merge11/proofs/n1/contract_closure'")
s=s.replace("('sampler',sampler),('admitted_identity',admitted_identity),",'')
s=s.replace("    assert R.row_check({},'pose')=={}", "    assert R.row_check({},'pose')=={}\n    assert R.scale_init({}, {}, enabled=False)==set()")
s=s.replace('Synthetic metadata and a bounded real admitted-row identity check; no production sampler or model inference qualification.',
            'Synthetic metadata refusal cases only; no production sampler or model inference qualification.')
(B/'proof_contract_closure.py').write_text(s)
s=(B/'proof_extra.py').read_text().replace("O=L/'work/merge11/proofs/n1/contracts'","O=L/'work/merge11/proofs/n1/registry_closure'")
s=s.replace(";case('real_kit_producer_reader',kit)",'')
(B/'proof_registry_closure.py').write_text(s)
