from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix'
steps=[]
for name in ('pre_freeze_tests','requalify_final','proof_kit_scope','proof_contract_closure','proof_registry_closure','proof_gate_edges9',
             'proof_mix_checks9','proof_host_checks','mutations','inference_inventory','review_evidence',
             'legacy_guard_proof','compare','coverage_current','storage'):
    steps.append(dict(step=name,status='running'))
    (B/'FINAL_STEPS.json').write_text(json.dumps(steps,indent=2)+'\n')
    (B/'STATUS.md').write_text('# Build n1fix status\n\nFinal qualification is running '+name+'. GO=false. Evidence: FINAL_STEPS.json.\n')
    with (B/('finish_'+name+'.log')).open('w') as log:
        code=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'.py'))],cwd=L,
                            stdout=log,stderr=subprocess.STDOUT).returncode
    steps[-1].update(returncode=code,status='complete' if code==0 else 'failed')
    (B/'FINAL_STEPS.json').write_text(json.dumps(steps,indent=2)+'\n')
    print(name,code,flush=True)
    if code<0:raise SystemExit('A process was killed; stop without retry.')
    if code:raise SystemExit(code)
comparison=json.loads((B/'SUITE_COMPARISON.json').read_text())
gaps=json.loads((B/'GAPS.json').read_text())
unexpected=[r for r in comparison['failures'] if not r['preexisting'] and 'BF16' not in r['cause']]
(B/'FINAL_CHECK.json').write_text(json.dumps(dict(cpu_gaps=len(gaps),unexpected_regressions=len(unexpected),
    r2_failures=comparison['r2_failures'],complete=not gaps and not unexpected and not comparison['r2_failures']),indent=2)+'\n')
print(json.dumps(dict(cpu_gaps=len(gaps),unexpected_regressions=len(unexpected),r2_failures=comparison['r2_failures'])))
