from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
p=L/'work/integrity8.py';s=p.read_text().replace("(C/'gate_integration7.txt').read_text()", "(C/'gate_integration8.txt').read_text()");p.write_text(s)
p=L/'work/gate_integration8.py';s=p.read_text().replace("assert kit.kit_hashes()==config['adoption_kit']", "assert kit.kit_hashes()==config['adoption_kit']\ntry:kit.validate_environment(config)\nexcept ValueError:pass\nelse:raise AssertionError('CPU-only fixture environment authorized GPU execution')\nprint('PASS: actual CPU fixture environment refuses before synthetic GPU receipt serialization.')")
p.write_text(s)
p=L/'work/write_report8.py';s=p.read_text().replace("('bash work/cpu.sh work/share_storage8.py','storage8.txt')", "('bash work/cpu.sh work/share_storage8.py\\nbash work/cpu.sh work/share_storage8_more.py  # two bounded passes','storage8.txt')");p.write_text(s)
p=L/'out/FRAMEWORK_EVIDENCE.md';s=p.read_text().replace('were reread on 2026-11-19 for round 7.','were checked on 2026-11-19.').replace('on 2026-11-19 during this round.','on 2026-11-19.');p.write_text(s)
print('Aligned seal/integration/report references with current evidence and explicit CPU-environment refusal.')
