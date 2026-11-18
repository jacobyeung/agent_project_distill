"""Report the complete continuation packet and its sealed resource authority."""
import difflib
import json
import re
import subprocess
import sys
import tempfile
import tarfile
import hashlib
from pathlib import Path
from rebind import ROOT,load,sha,write


def main():
    out=ROOT/'out';baseline=load(out/'CONT4_BASELINE.json');base=Path(baseline['snapshot'])
    b=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    log=(out/'logs/tests.log').read_text()
    assert log.rstrip().endswith('OK')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    assert 'test_full_store_build_stream_division_with_and_without_remove' in log
    for name in ('FIRST_BATCH','DERIVATION','PRE_SUBMISSION','SWITCH_GUARDS','UNIT_REAL'):
        record=load(out/'proof'/(name+'.json'))
        assert record['status']=='PASS' and record['config_identity']==b['config_identity'],name
    for name,digest in baseline['archives'].items():assert sha(out/name)==digest,name
    assert op['archive'] not in baseline['archives'] and sha(out/op['archive'])==op['sha256']
    assert sha(out/'config.json')==baseline['config']
    assert sha(out/'BINDING.json')==baseline['binding']
    assert sha(out/'r1p_code.tar')==baseline['code']
    ready=Path(load(out/'proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    from r4 import validate
    auth=load(ready/'k/4.json');validate(auth)
    before={str(p.relative_to(ready)):sha(p) for p in (ready/'k').rglob('*') if p.is_file()}
    # This local certificate exercises inventory verification only. It is not
    # an independent content scan and cannot serve as production evidence.
    write(ready/'ANON_OK.json',dict(status='CLEAN',hits=0,fixture=True,
        manifest_sha256=sha(ready/'SHA256SUMS.txt'),scope='Local inventory fixture only'))
    subprocess.run([sys.executable,'-B',str(ready/'b/a.py'),str(ready)],check=True)
    seals={};sealroot=Path(tempfile.mkdtemp(prefix='cont4_seal_',dir=ROOT/'work'))
    for partition in ('general','bootstrap'):
        dest=sealroot/(partition+'.json')
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/seal_proof.py'),'--kit',str(ready),
            '--bundle',str(out/'operator'),'--binding',str(out/'BINDING.json'),
            '--partition',partition,'--out',str(dest)],check=True)
        authority=load(dest)
        assert authority['runtime']['k/4.json']==sha(ready/'k/4.json')
        seals[partition]=dict(path=str(dest),sha256=sha(dest))
    assert before=={str(p.relative_to(ready)):sha(p) for p in (ready/'k').rglob('*') if p.is_file()}
    subprocess.run([sys.executable,'-B',str(ready/'b/a.py'),str(ready)],check=True)
    write(out/'proof/CONT4_RESEAL.json',dict(status='PASS',authorities=seals,
        kit_files_unchanged=True,inventory_before_and_after='PASS',
        authority_sha256=sha(ready/'k/4.json'),scope='Local fixture only; no independent content scan'))
    old=load(base/'out/OPERATOR.json')
    def members(path):
        with tarfile.open(path) as archive:
            return {m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),
                bytes=m.size,mode=oct(m.mode)) for m in archive if m.isfile()}
    oldmembers=members(base/'out'/old['archive']);newmembers=members(out/op['archive'])
    changes={name:dict(before=oldmembers.get(name),after=newmembers.get(name))
        for name in sorted(set(oldmembers)|set(newmembers)) if oldmembers.get(name)!=newmembers.get(name)}
    assert set(changes)=={op['proof_script'],'s.sh','sums.txt'},changes.keys()
    rows=['| Archive member | Before SHA256 | After SHA256 | Change |',
          '|---|---|---|---|']
    for name,change in changes.items():
        reason={'s.sh':'Pinned C canary exception; unchanged PASS branch.',op['proof_script']:'Verify trainer before audit import; isolated proof-tail rehearsal.','sums.txt':'Pin the changed script bytes.'}[name]
        rows.append(f"| `{name}` | `{change['before']['sha256']}` | `{change['after']['sha256']}` | {reason} |")
    table='\n'.join(rows)+'\n'
    oldkit=Path(load(base/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    def kit_inventory(root):
        return {str(p.relative_to(root)):dict(sha256=sha(p),mode=oct(p.stat().st_mode&0o777)) for p in root.rglob('*') if p.is_file()}
    old_inventory=kit_inventory(oldkit);new_inventory=kit_inventory(ready)
    kit_changes={n:dict(before=old_inventory.get(n),after=new_inventory.get(n)) for n in sorted(set(old_inventory)|set(new_inventory)) if old_inventory.get(n)!=new_inventory.get(n)}
    kit_note=f'\nAll {len(newmembers)-len(changes)} other archive members retain their bytes and modes. Derived kit: {len(kit_changes)}/{len(new_inventory)} members changed.\n'
    assert set(kit_changes)<= {'k/selection_equality.json','SHA256SUMS.txt','ANON_OK.json'},kit_changes.keys()
    kit_note+='\nAll derived runtime code, config, staged-input pins and resource authority retain their bytes and modes. The equality record binds a fresh local native-fixture receipt path/hash; SHA256SUMS binds that record, and ANON_OK binds the resulting fixture manifest. These three evidence changes do not change the staged archives or C identity.\n'
    for name,change in kit_changes.items():kit_note+='\n'+name+': '+json.dumps(change,sort_keys=True)+'\n'
    for name in ('KIT_DIFF4.md','KIT_DIFF.md'):(out/name).write_text(table+kit_note)
    write(out/'KIT_DIFF4.json',dict(archive_changes=changes,kit_changes=kit_changes,kit_members=len(new_inventory)))
    write(out/'KIT_DIFF_CONT4.json',dict(baseline=old['archive'],archive=op['archive'],changes=changes,
        unchanged_members=len(newmembers)-len(changes)))
    replay=load(out/'proof/CONT4_LOADER_REPLAY.json')
    assert replay['status']=='PASS' and replay['proof_sha256']==sha(out/'proof/p.py')
    outer=load(out/'proof/CONT4_OUTER_NAMESPACE.json')
    assert outer['status']=='PASS' and outer['proof_sha256']==sha(out/'proof/p.py')
    text=(base/'out/CONT3.md').read_text().replace(old['archive'],op['archive']).replace(old['sha256'],op['sha256'])
    start=text.index('The CPU proof retains');end=text.index('Validation:',start)
    text=text[:start]+'''The CPU proof authenticates the trainer with the same `v.tree(record_pin, TRAINER, commit)` call as `b/w.py`, then inserts `TRAINER` at the front of `sys.path` before importing `student_pilot.loader_audit.main`. `tk_pythonpath p` retains its existing composition. The config, trainer archive, training wrapper, run, bundle and kit identities remain unchanged.

The post-admission audit found no further production defects. The rehearsal also rejects empty staged-root arguments and records namespace failures separately from trainer/import failures. The local shell fixture places `student_pilot` only in the sealed epoch tree. This test arrangement detects the missing import path instead of masking it with a package under `b/`. Its relocated Python launcher preserves the permitted CPU virtual environment and its dependencies.

| Post-admission boundary | Verification and result |
|---|---|
| Runtime record and trainer | The shell checks the staged record SHA. The heredoc reads `k/0.json`; `v.tree` checks its record pin, schema, commit, complete file inventory and tree digest before import. A changed trainer refuses before executing it. |
| Environment and Python path | The real `c.sh` establishes `TRAINER`, runtime record aliases, closure, optional NumPy overlay, CPU visibility and private cache paths. The fixture tests both overlay branches with no trainer on the initial PYTHONPATH. |
| Run directory | `TK_RUNS_DIR=$NR`; the inner namespace binds `$NR` to `$X/runs`. `d.effective` reads the authenticated preparation from that logical run path. |
| Audit writes and mounts | The real loader writes `inputs/l.json` and `inputs/a.json` inside a real local bubblewrap namespace. Trainer and staged inputs remain read-only; runs and the proof job directory are writable. The outer proof maps the same run to its physical work directory. |
| Data authentication | The replay executes the real `d.effective`, pinned preparation reads, SQLite population scan, sampler, disk plan, routing selection and required-family checks on synthetic prepared data. No loader or validator body is mocked. |
| Report pins | The loader pins `l.json` in `a.json`. The outer proof requires the original config identity and checks the physical `l.json` SHA before merging checks. Changed identities and loader bytes refuse. |
| Check aggregation | The outer proof adds the resume fixture, audit checks and directory-mode check. Missing reports, missing required checks and failed checks refuse. The additional staged-binary inventory is retained. |
| Status and return code | A loader exception or failed prepared-data verification cannot produce PASS. Negative tests cover execution failure, verification failure, missing audit, wrong pin, wrong identity, failed check, missing required check, failed resume fixture and nonprivate directory. |
| Resume fixture | The unchanged verifier extracts a four-rank fixture slot and checks the exact step-200 pointer, binding and shard pins. The final proof requires `resume_pointer=PASS`; this fixture does not attest a future real A slot. |

KIT_DIFF compares the final archive with `snap_6a5c7d00`:

'''+table+'\n'+text[end:]
    start=text.index('Validation:');end=text.index('Reviewer checks:',start)
    text=text[:start]+f'''Validation: all {count} packet tests pass, including all three tests in `tests/test_fix10.py`, its full-store division regression, 17 C canary gate tests and five audit/rehearsal tests. `tools/run_local_checks.py --share-fixture-bytes` passes deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and the full test suite. The new coverage includes a changed-trainer refusal, real loader success and failure inside bubblewrap, and nine outer-proof failure cases. `out/proof/CONT4_LOADER_REPLAY.json` pins the real loader reports. A separate native outer-bubblewrap check passes and is recorded in `out/proof/CONT4_OUTER_NAMESPACE.json`. `out/proof/CONT4_RESEAL.json` records successful general/bootstrap fixture seals with unchanged kit inventory.

'''+text[end:]
    start=text.index('Reviewer checks:')
    text=text[:start]+'''Reviewer checks: verify the archive SHA256, `KIT_DIFF4.md` and `CONT4.diff` against `snap_6a5c7d00`. Review the fixed two-path admission allowlist, byte pins, five checks, staged-input equality, general queue predicate, exclusive canary marker, distinct rehearsal name and non-PASS receipts. Confirm the PASS branch and training sbatch argv remain byte-identical. The proof script, launch gate and checksum file change in the archive. Compare the generated heredoc's tree check and import order with `b/w.py`; inspect the real loader replay and the negative cases. Reseal the proof against the final deployed bundle and certified kit, run the production CPU proof and verify every required check plus its receipt pins. The delta review must cover these final proof and gate bytes before deployment. The PASS branch retains every predicate. The canary branch requires the pinned admission evidence, an active new proof and identity-bound GO under the written ORCH ruling.

Local evidence does not certify Orchard's namespace configuration, production prepared rows, filesystem capacity, full routing regeneration, the real A checkpoint or GPU/FSDP behavior. The local replay uses synthetic SQLite rows and preparation receipts with the byte-identical sealed trainer; it executes the actual nested kit namespace, and a native outer-namespace fixture verifies that the retained staged root is read-only while the fresh run is writable. C continues from A's full step-200 optimizer checkpoint to step 600; the resume fixture is not a substitute for runtime donor verification.

No SSH, Orchard access, Git, GPU launch, external write or independent review occurred. `out/REVIEW_REQUEST.json` is the local handoff. The general/bootstrap proof seals are local fixtures, not production approval. All existing packet archives remain checksum-identical. `CONT4.diff` covers local code, tests, reports and derived kit differences from `snap_6a5c7d00`. No cleanup was attempted.
'''
    text=text.replace('The launch gate accepts only a completed PASS CPU proof and separate written GO. No canary is needed.', 'The launch gate accepts a completed PASS CPU proof or the pinned canary exception, with separate identity-bound GO.')
    text=text.replace('The submitter still requires a completed PASS CPU proof and separate identity-bound `go.json`.', 'The submitter requires a completed PASS proof or the pinned canary exception, plus separate identity-bound `go.json`.')
    extra="""
The binding ORCH ruling is `events/r1_ops/20261118T0842Z_ORCH_RULING_C_canary_and_general_order.md`, SHA256 `31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89`. It authorizes the boundary canary subject to its ordering, real step-200 checkpoint/population checks and kill rules; this packet does not replace those conditions.

The C canary gate requires `canary=true`, `ADMISSION_JOB=172180`, and `PROOF_JOB` equal to the new bundle's `job.id`. It authenticates admission receipt SHA256 `ed9aad679a1d9dd6302970dcb82d02d5b92fd6bf219fca405f8d21` and log SHA256 `0658f1614ad94ff6141b66ba1523b37d2ea60d28c074929ac6e6f2307b1d58a3`. All five admission checks must PASS; the resume pointer must be the step-200 A fixture. The receipt's config/contract, old manifest and current staged hashes must match. The pinned log must show exactly one `exit rc=0`. The new proof must be PENDING or RUNNING under `a15_cot_ap05b8ac69` on general; held PENDING is accepted. The gate exclusively creates `KH/o/<PROOF_JOB>.canary.json` after kit validation. It marks gate acceptance, not successful training allocation.

`ADMISSION_KIT` accepts exactly `/project/community/jjyeung/okh7/x_7f1589c1` (the default) or `/project/community/jjyeung/okh7/x_7f1589c1.f172180`. Retain the old receipt, log, manifest and authenticated config/staging files together. If deriving the new kit changes its manifest, use the moved-aside old kit as ADMISSION_KIT; the current-kit location works only while its receipt-authenticated manifest and files remain intact. Moving the old kit aside and deriving the new kit at its original name preserves the unchanged bundle/kit identities. PASS mode does not consult admission evidence or write a canary marker.

The proof's `--rehearsal STAGED_ROOT` switch reuses the production tail and both namespaces, with fresh writable run/job paths and a read-only existing staged root. It performs `tk_env`, `tk_pythonpath p`, the trainer-tree verification, native imports, a pinned VQA descriptor read and a read-only SQLite schema query. The native loader starts and reaches `d.effective`; only a FileNotFoundError for the exact absent `data_receipt.json` is expected. Other exceptions fail. It does not stage archives, run admission, restore a checkpoint or certify populations. The rehearsal job name is `a15_cot_ap05b8ac6a`, which the canary queue predicate refuses. Receipts are `<job>.rehearsal.json` and logs are `<job>.rehearsal.log`; terminal status is exclusively REHEARSAL_OK or REHEARSAL_FAIL and cannot satisfy the launch gate. Each step is reported; the first uncompleted step fails when execution fails.

The operator must first retain the staged root on `orchard-community-0` and reseal the final certified kit for general into `BUN/a4.json`. Seal the deployed authority with `/usr/bin/python3 -I -B /project/community/jjyeung/okh7/i_7f1589c1/p.py --kit /project/community/jjyeung/okh7/x_7f1589c1 --bundle /project/community/jjyeung/okh7/i_7f1589c1 --binding /project/community/jjyeung/okh7/i_7f1589c1/BINDING.json --partition general --out /project/community/jjyeung/okh7/i_7f1589c1/a4.json`. The sealer exclusively creates this path; choose a fresh authority filename if it already exists and use the same filename in sbatch.

Run this exact argv after the general-slot ordering permits the short rehearsal:

```bash
sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:30:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.out --error=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.err /project/community/jjyeung/okh7/i_7f1589c1/p_05b8ac69.sh /project/community/jjyeung/okh7/i_7f1589c1/a4.json --rehearsal /tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/root
```

The root is from the pinned 172180 receipt and is node-local. A missing root produces REHEARSAL_FAIL; do not restage or rerun admission under this switch. `out/proof/CONT4_REHEARSAL.json` records the local native-loader boundary test. The operator must inspect the Orchard rehearsal before submitting the full proof, then follow the ruling's held-proof/general ordering and real A step-200 checkpoint/population checks. A rehearsal job must never be written to the bundle's `job.id` as the parallel full proof. The canary gate checks for a rehearsal receipt and refuses it.

"""
    extra=extra.replace('ed9aad679a1d9dd6302970dcb82d02d5b92fd6bf219fca405f8d21','ed9aad679a1d9dd6302970dcb82d02d5b92fd6f3a53aede6bf219fca405f8d21')
    text=text.replace('Reviewer checks:',extra+'Reviewer checks:',1)
    for name in ('CONT4.md','REPORT.md','R1P_PACKET.md'):(out/name).write_text(text)
    result=dict(status='BUILT_FOR_INDEPENDENT_REVIEW',identity=b['config_identity'],run=b['run_key'],
        bundle=op['bundle'],kit=op['kit'],archive=op['archive'],sha256=op['sha256'],tests=count,
        full_suite=True,production_authorized=False,review='REQUIRED',further_production_defects=[],
        changed_archive_members=sorted(changes),fixture=str(ready),manifest_sha256=sha(ready/'SHA256SUMS.txt'))
    for name in ('CONT4_RESULT.json','REVIEW_REQUEST.json','proof/GATES.json'):write(out/name,result)
    write(out/'proof/CONT4_TEST_LEDGER.json',dict(status='PASS',tests=count,full_suite=True,
        suite_log='out/logs/tests.log',deferred=[],fix10_tests=3,cont4_tests=5,canary_c_tests=17,
        trainer_refusal_tests=1,outer_failure_cases=9))
    (ROOT/'STATUS.md').write_text(f"{result['status']}. C {b['config_identity']}, run {b['run_key']}, {op['archive']} SHA256 {op['sha256']}. All {count} tests pass. Read out/CONT4.md and out/CONT4.diff. Review, production proof and written GO remain required.\n")
    patches=[];inventory={}
    def compare(left,right,name):
        a=left.read_bytes() if left.is_file() else b'';z=right.read_bytes() if right.is_file() else b''
        if a==z:return
        inventory[name]=dict(before=sha(left) if left.is_file() else None,after=sha(right) if right.is_file() else None)
        try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='C3/'+name,tofile='C4/'+name))
        except UnicodeDecodeError:patches.append('Binary content differs: '+name+'\n')
    paths={'STATUS.md'}
    for folder in ('tools','tests','configs','out'):
        for root in (base,ROOT):
            paths.update(str(p.relative_to(root)) for p in (root/folder).rglob('*') if p.is_file()
                and p.stat().st_size<1_000_000 and p.suffix not in ('.diff','.tar','.pyc')
                and p.name not in ('CONT4_INVENTORY.json','finalize.log','cont4_local_checks.log','SHA256SUMS'))
    for name in sorted(paths):compare(base/name,ROOT/name,name)
    oldkit=Path(load(base/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    for path in sorted(ready.rglob('*')):
        rel=path.relative_to(ready);oldpath=oldkit/rel
        if path.is_dir():
            if oldpath.exists() and oldpath.stat().st_mode&0o777!=path.stat().st_mode&0o777:
                patches.append(f'Mode kit/{rel}: {oldpath.stat().st_mode&0o777:04o} -> {path.stat().st_mode&0o777:04o}\n')
        elif path.is_file() and path.stat().st_size<1_000_000:compare(oldpath,path,'kit/'+str(rel))
    (out/'CONT4.diff').write_text(''.join(patches));write(out/'CONT4_INVENTORY.json',inventory)
    print(json.dumps({k:result[k] for k in ('status','identity','run','archive','sha256','tests')}))


if __name__=='__main__':main()
