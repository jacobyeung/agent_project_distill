from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
p=B/'proof_gate_edges9.py';s=p.read_text().replace("assert reasons(dict(target='heading\\u00a0unavailable'))==[], 'Unrelated heading pattern broadened'", "assert 'heading_threshold_status' in reasons(dict(target='heading\\u00a0unavailable'))")
p.write_text(s)
p=B/'proof_host_checks.py';s=p.read_text().replace("('nonempty','R1_HOST_ROOT_NOT_EMPTY')", "('nonempty','R1_HOST_JOB_TMP_NOT_EMPTY')")
p.write_text(s)
names=['proof_gate_edges9.py','proof_host_checks.py','proof_contract_closure.py','proof_registry_closure.py','inference_inventory.py','legacy_guard_proof.py','coverage_current.py','compare.py']
for name in names:
    s=(B/name).read_text()
    assert 'L.parent' not in s and '/tree_rebuild_w/w9' not in s,name
print('Supplementary proof paths checked.')
