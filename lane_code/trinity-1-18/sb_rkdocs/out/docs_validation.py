"""CPU verification for the documentation delivery; shipped kit code is unchanged."""
import json, runpy, sys
from pathlib import Path
from unittest.mock import patch
import common
from common import W, sha, read, write
SOURCE = '/scratch/jjyeung/orch_n30/sb_rkfix2'
raw_read = read

def mapped(path):
    value = raw_read(path)
    if isinstance(value, dict) and isinstance(value.get('input_sha256'), dict):
        value = dict(value, input_sha256={
            (str(W) + p[len(SOURCE):] if p.startswith(SOURCE + '/') else p): h
            for p, h in value['input_sha256'].items()})
    return value

if sys.argv[1] == 'tests':
    # S0 retains its original bytes. Translate only its input path keys in memory,
    # as the review probe does for an extracted copy. Every digest is preserved.
    def relocated_s0(path):
        return mapped(path) if Path(path) == W/'out/S0.json' else raw_read(path)
    with patch.object(common, 'read', relocated_s0):
        runpy.run_path(str(W/'tests/test_roomkit.py'), run_name='__main__')
elif sys.argv[1] == 'probe':
    import gates, gpu_run
    original = W/'configs/KERNEL_PROVENANCE.json'
    frozen = W/'configs/KERNEL_FROZEN.json'
    hashes = {str(p):sha(p) for p in [original, frozen]}
    approved = dict(read(original), authorized_by='SIMULATED approval: CPU documentation probe only')
    target = W/'tmp/docs_probe/KERNEL_PROVENANCE_APPROVED.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(approved, indent=2)+'\n')
    assert [k for k in approved if approved[k] != read(original)[k]] == ['authorized_by']
    args = ['gpu_run.py','--run-id','docs-probe','--go-file','configs/GO_docs-probe.json',
            '--provenance','configs/KERNEL_PROVENANCE_APPROVED.json',
            '--reader-receipt','configs/READER_RECEIPT.json']
    with patch.object(sys, 'argv', args), patch.object(gpu_run, 'run') as runner:
        gpu_run.main()
        assert runner.call_args.args[0].provenance == 'configs/KERNEL_PROVENANCE_APPROVED.json'
    verified = {}
    verify = gates.verify_inputs
    def capture(records):
        verify(records)
        verified.update(records)
    with patch.object(gates, 'read', mapped), patch.object(gates, 'verify_inputs', capture):
        try:
            gates.prerequisites(original,W/'configs/READER_RECEIPT.json')
        except ValueError as exc:
            assert 'clean held-out provenance' in str(exc)
        else:
            raise AssertionError('pending authorization accepted')
        gates.prerequisites(target,W/'configs/READER_RECEIPT.json')
    assert hashes == {str(p):sha(p) for p in [original,frozen]}
    inputs={**verified,**hashes}
    for p in [Path(__file__),target,W/'scripts/gpu_run.py',W/'scripts/gates.py',
              W/'out/TESTS.json',W/'review/rkrev3_approve.py',W/'review/rkrev3_REVIEW_VERDICT.md']:
        inputs[str(p)]=sha(p)
    write(W/'out/DOCS_PROBE.json',dict(verdict='PASS',cli_accepts_provenance=True,
          pending_rejected=True,approved_copy_prerequisites='PASS',verified_inputs=len(verified),
          original_and_frozen_unchanged=True,gpu_execution=False,
          path_translation='Only source-root input path keys are mapped to the copied root in memory; digests are unchanged.',
          command='bash scripts/cpu.sh out/docs_validation.py probe'),inputs)
    print('PASS: CLI parsed; pending refused; approved copy passed;',len(verified),'input hashes verified; no CUDA execution')
else:
    raise SystemExit('expected tests or probe')
