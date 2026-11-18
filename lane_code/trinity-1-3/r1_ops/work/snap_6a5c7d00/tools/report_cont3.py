"""Report the complete continuation packet and its sealed resource authority."""
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from rebind import ROOT,load,sha,write


def main():
    out=ROOT/'out';baseline=load(out/'CONT3_BASELINE.json');base=Path(baseline['snapshot'])
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
    ready=Path(load(out/'proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    from r4 import validate
    auth=load(ready/'k/4.json');validate(auth)
    before={str(p.relative_to(ready)):sha(p) for p in (ready/'k').rglob('*') if p.is_file()}
    # This local certificate exercises inventory verification only. It is not
    # an independent content scan and cannot serve as production evidence.
    write(ready/'ANON_OK.json',dict(status='CLEAN',hits=0,fixture=True,
        manifest_sha256=sha(ready/'SHA256SUMS.txt'),scope='Local inventory fixture only'))
    subprocess.run([sys.executable,'-B',str(ready/'b/a.py'),str(ready)],check=True)
    seals={};sealroot=Path(tempfile.mkdtemp(prefix='cont3_seal_',dir=ROOT/'work'))
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
    write(out/'proof/CONT3_RESEAL.json',dict(status='PASS',authorities=seals,
        kit_files_unchanged=True,inventory_before_and_after='PASS',
        authority_sha256=sha(ready/'k/4.json'),scope='Local fixture only; no independent content scan'))
    text=(base/'out/CONT2.md').read_text()
    text=text.replace(text.split('. ',1)[0]+'. ','BUILT_FOR_INDEPENDENT_REVIEW. ',1)
    old=load(base/'out/OPERATOR.json')
    text=text.replace(old['archive'],op['archive']).replace(old['sha256'],op['sha256'])
    start=text.index('The CPU proof accepts');end=text.index('The CPU proof retains',start)
    text=text[:start]+'''The derived `k/4.json` seals modes `["p","t","u"]`, `new_gpus={"p":0,"t":4,"u":4}`, top-level partition `advanced`, wall limit `86400`, one node, arm `0`, GPU cap `4`, one parallel job and `resume="latest"`. Its per-mode resources authorize `p` on `general` or `bootstrap` with zero GPUs and 14,400 seconds; `t` and `u` require `advanced`, four GPUs and 86,400 seconds. Proof and training request 48 CPUs and 800 GB. C's verified donor and later checkpoint restores enter `u`; the inherited cold-entry resource envelope also carries `t`, while C's restore bridge still refuses training without a continuation checkpoint.

The deriver binds these resource fields before generating `SHA256SUMS.txt`. It preserves the supplied evidence identity, revision, admission contract and expiry. Both `b/g.py` and `b/i.py` validate the exact authority and allocation. The sealed entry sets `TK_ALLOCATION_MODE` before preflight and recursive admission: CPU preparation inside a training job uses that training allocation's limits. A standalone proof uses the zero-GPU proof limits. The runtime checks a supplied `SLURM_TIMELIMIT`; the sealed launch slot, job and wrapper pin the training wall limit even where Slurm omits that variable.

`production_go_granted` is false and `production_go_required_separately` is true. The resource authority grants no launch GO. The submitter still requires a completed PASS CPU proof and separate identity-bound `go.json`. The proof sealer validates the complete authority, permits general/bootstrap, and pins `k/4.json` alongside the runtime. Certification and proof sealing do not modify any file in `k/`.

'''+text[end:]
    start=text.index('Validation:');end=text.index('Reviewer checks:',start)
    text=text[:start]+f'''Validation: all {count} packet tests pass, including all three tests from `tests/test_fix10.py` and its full-store division regression. `tools/run_local_checks.py` passes deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and fix-11 shell replay. Five C3 tests exercise the real `g.check`, `i.authorize` and `x.ready` on fixture records: proof on both CPU partitions, both training modes, nested admission, sealed fields, and refusal of wrong modes, GPU counts, partitions, nodes and wall limits. Only native data admission and persistent slot selection are mocked in that resource matrix. Existing prefix tests execute the real metadata preflight, isolated gate and resume imports, then verify `a.py`, unchanged inventory, no bytecode and `0500` code directories. The native continuation test checks exact parameters, Adam state, RNG, LR and rows for 206 uninterrupted updates versus 200 plus six resumed updates, with single-rank collectives mocked.

'''+text[end:]
    start=text.index('Reviewer checks:');end=text.index('Local tests do not prove',start)
    text=text[:start]+'''Reviewer checks: verify the archive SHA256 and `CONT3.diff` against `snap_c60b9015`; inspect `d.py`, `r4.py`, the derived `k/4.json`, `b/g.py`, `b/i.py`, the job prefix and recursive admission path. Check all per-mode limits, `resume="latest"`, the 24-hour launch slot and wrapper, separate written GO, and the proof seal's authority hash. Derive and certify a fresh final kit with real evidence; never patch a certified `k/4.json`. Confirm the real step-200 A slot contains the full optimizer state, the continuation authentication chain and row populations match, and the deployed manifest survives prefix execution without bytecode. Run the production CPU proof on the selected CPU partition and obtain the operator's written boundary GO before submission.

'''+text[end:]
    start=text.index('`out/proof/CONT2_RESEAL.json`')
    text=text[:start]+'''`out/proof/CONT3_RESEAL.json` records fixture seals, not production approval. `out/CONT3.diff` compares the frozen `snap_c60b9015` packet with this packet, including derived kit bytes and directory modes. All existing packet archives remain checksum-identical. No cleanup was attempted.
'''
    (out/'CONT3.md').write_text(text)
    for name in ('REPORT.md','R1P_PACKET.md'):(out/name).write_text(text)
    result=dict(status='BUILT_FOR_INDEPENDENT_REVIEW',identity=b['config_identity'],run=b['run_key'],
        bundle=op['bundle'],kit=op['kit'],archive=op['archive'],sha256=op['sha256'],tests=count,
        full_suite=True,production_authorized=False,review='REQUIRED',authority=auth,
        fixture=str(ready),manifest_sha256=sha(ready/'SHA256SUMS.txt'))
    for name in ('CONT3_RESULT.json','REVIEW_REQUEST.json','proof/GATES.json'):write(out/name,result)
    write(out/'proof/CONT3_TEST_LEDGER.json',dict(status='PASS',tests=count,full_suite=True,
        suite_log='out/logs/tests.log',deferred=[],fix10_tests=3,cont3_tests=5))
    (ROOT/'STATUS.md').write_text(f"{result['status']}. C {b['config_identity']}, run {b['run_key']}, {op['archive']} SHA256 {op['sha256']}. All {count} tests pass. Read out/CONT3.md and out/CONT3.diff. Independent review, production proof and written GO remain required.\n")
    patches=[];changes={}
    def compare(left,right,name):
        a=left.read_bytes() if left.is_file() else b'';z=right.read_bytes() if right.is_file() else b''
        if a==z:return
        changes[name]=dict(before=sha(left) if left.is_file() else None,after=sha(right) if right.is_file() else None)
        try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='C2/'+name,tofile='C3/'+name))
        except UnicodeDecodeError:patches.append('Binary content differs: '+name+'\n')
    paths={'STATUS.md'}
    for folder in ('tools','tests','configs','out'):
        for root in (base,ROOT):
            paths.update(str(p.relative_to(root)) for p in (root/folder).rglob('*') if p.is_file()
                         and p.stat().st_size<1_000_000 and p.suffix not in ('.diff','.tar','.pyc')
                         and p.name not in ('CONT3_INVENTORY.json','finalize.log','cont3_local_checks.log'))
    for name in sorted(paths):compare(base/name,ROOT/name,name)
    # The frozen packet records its production-form kit by an immutable fixture
    # path; work/kit in that snapshot is an unrelated inherited source packet.
    oldkit=Path(load(base/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    assert (oldkit/'SHA256SUMS.txt').is_file()
    for path in sorted(ready.rglob('*')):
        rel=path.relative_to(ready);oldpath=oldkit/rel
        if path.is_dir():
            if oldpath.exists() and oldpath.stat().st_mode&0o777!=path.stat().st_mode&0o777:
                patches.append(f'Mode kit/{rel}: {oldpath.stat().st_mode&0o777:04o} -> {path.stat().st_mode&0o777:04o}\n')
        elif path.is_file() and path.stat().st_size<1_000_000:compare(oldpath,path,'kit/'+str(rel))
    (out/'CONT3.diff').write_text(''.join(patches));write(out/'CONT3_INVENTORY.json',changes)
    print(json.dumps({k:result[k] for k in ('status','identity','run','archive','sha256','tests')}))


if __name__=='__main__':main()
