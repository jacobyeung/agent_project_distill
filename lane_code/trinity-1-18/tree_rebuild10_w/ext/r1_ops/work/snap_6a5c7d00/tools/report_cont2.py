"""Report the current continuation packet and its local evidence."""
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from rebind import ROOT, load, sha, write


def main():
    out=ROOT/'out';base=ROOT/'work/cont2_baseline'
    b=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    log=(out/'logs/tests.log').read_text()
    assert log.rstrip().endswith('OK')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    full='Fix10.test_full_store_build_stream_division_with_and_without_remove' in log
    heavy=out/'logs/cont2_heavy.log'
    if not full and heavy.exists() and heavy.read_text().rstrip().endswith('OK'):
        count+=1;full=True
    for name in ('FIRST_BATCH','DERIVATION','PRE_SUBMISSION','SWITCH_GUARDS','UNIT_REAL'):
        record=load(out/'proof'/(name+'.json'))
        assert record['status']=='PASS' and record['config_identity']==b['config_identity'],name
    for name,digest in load(base/'archives.json').items():assert sha(out/name)==digest,name
    assert sha(out/op['archive'])==op['sha256']
    assert op['archive'] not in load(base/'archives.json')
    ready=Path(load(out/'proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    seals={};sealroot=Path(tempfile.mkdtemp(prefix='cont2_seal_',dir=ROOT/'work'))
    for partition in ('general','bootstrap'):
        dest=sealroot/(partition+'.json')
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/seal_proof.py'),'--kit',str(ready),
            '--bundle',str(out/'operator'),'--binding',str(out/'BINDING.json'),
            '--partition',partition,'--out',str(dest)],check=True)
        seals[partition]=dict(path=str(dest),sha256=sha(dest))
    write(out/'proof/CONT2_RESEAL.json',dict(status='PASS',authorities=seals,scope='Local fixture only'))
    text=(base/'out/CONT1.md').read_text()
    old=load(base/'out/OPERATOR.json')
    if not full:text=text.replace('BUILT_FOR_INDEPENDENT_REVIEW.','LOCAL_CHECKS_PENDING_HEAVY_TEST.',1)
    text=text.replace(old['archive'],op['archive']).replace(old['sha256'],op['sha256'])
    text=text.replace('(general, CPU only)','(general or bootstrap, CPU only; 48 CPUs, 800 GB, four hours)')
    insertion="""The deriver seals `b/` and every code subdirectory at `0500` after inventory generation and evidence validation. Isolated job-prefix imports cannot create bytecode in the kit. The resume chooser explicitly includes its sealed code directory so `python -I` can import the donor verifier. `tk_nx` uses `rsync --chmod=D700` to create private node-local directories at `0700`. `b/z.py` refuses in-place redeployment of a sealed kit. Operators must derive a fresh kit; changing permissions to redeploy is unsupported.

The CPU proof accepts `general` and `bootstrap`. Seal with `p.py --partition bootstrap` and submit the packaged proof script with `sbatch -p bootstrap`; the selected partition must match the authority. The default script selects `general`. Both use 48 CPUs, 800 GB, no GPUs and `04:00:00`. The kit authorization lists the two proof partitions and `advanced`; training stays on `advanced` with four GPUs and `24:00:00`. These partition fields do not grant submission GO.

"""
    text=text.replace('The CPU proof retains',insertion+'The CPU proof retains')
    validation=f"Validation: {count} packet tests pass on this build. "
    validation+=('The complete suite ran, including the full-store division regression. ' if full else
                 'The 1.79 GB full-store regression awaits the required heavy-I/O authorization; all other tests ran. ')
    validation+='''`tools/run_local_checks.py` checks deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and fix-11 shell replay. Five mode/partition regressions verify `0500` code directories, isolated cold and donor prefix execution without bytecode, inventory preservation, real `tk_nx` copies with the proof directory-mode checker, sealed-kit redeploy refusal, and both partition authorities. The native continuation test checks bit-exact parameters, Adam state, RNG, LR and rows for 206 uninterrupted updates versus 200 plus six resumed updates, with single-rank collectives mocked. Production RGB and other absent populations remain fixture boundaries.

'''
    start=text.index('Validation:');end=text.index('Reviewer checks:',start)
    text=text[:start]+validation+text[end:]
    text=text.replace('Reviewer checks: inspect','Reviewer checks: verify the archived deriver seals all code directories, `tk_nx` copies them at `0700`, the isolated prefix preserves inventory, and the selected proof partition matches both authority and submission. Verify training still selects advanced and inspect')
    start=text.index('The explicit snapshot comparison in this report')
    text=text[:start]+'''`out/CONT2.diff` compares the C1 baseline with this packet, including derived kit bytes and directory modes. `out/CONT2_STORAGE.json` records new local storage. No cleanup was attempted.\n'''
    text=text.replace('out/proof/CONT1_RESEAL.json','out/proof/CONT2_RESEAL.json')
    (out/'CONT2.md').write_text(text)
    (out/'CONT1.md').write_text(text)
    for name in ('REPORT.md','R1P_PACKET.md'):(out/name).write_text(text)
    paths={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p.parts[len(base.parts)] in ('tools','tests','configs','out')}
    paths.update(str(p.relative_to(ROOT)) for d in ('tools','tests','configs') for p in (ROOT/d).glob('*') if p.is_file())
    patches=[];changes={}
    for name in sorted(paths):
        left=base/name;right=ROOT/name
        a=left.read_bytes() if left.is_file() else b'';z=right.read_bytes() if right.is_file() else b''
        if a==z:continue
        changes[name]=dict(before=sha(left) if left.exists() else None,after=sha(right) if right.exists() else None)
        try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='C1/'+name,tofile='C2/'+name))
        except UnicodeDecodeError:patches.append('Binary content differs: '+name+'\n')
    oldkit=Path(load(base/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    for path in sorted(ready.rglob('*')):
        if path.is_dir():
            oldpath=oldkit/path.relative_to(ready)
            if oldpath.exists() and oldpath.stat().st_mode & 0o777 != path.stat().st_mode & 0o777:
                patches.append(f"Mode kit/{path.relative_to(ready)}: {oldpath.stat().st_mode & 0o777:04o} -> {path.stat().st_mode & 0o777:04o}\n")
        elif path.is_file() and path.stat().st_size<1_000_000:
            oldpath=oldkit/path.relative_to(ready)
            a=oldpath.read_bytes() if oldpath.exists() else b'';z=path.read_bytes()
            if a==z:continue
            try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='C1/kit/'+str(path.relative_to(ready)),tofile='C2/kit/'+str(path.relative_to(ready))))
            except UnicodeDecodeError:pass
    (out/'CONT2.diff').write_text(''.join(patches))
    write(out/'CONT2_INVENTORY.json',changes)
    result=dict(status='BUILT_FOR_INDEPENDENT_REVIEW' if full else 'LOCAL_CHECKS_PENDING_HEAVY_TEST',
        identity=b['config_identity'],run=b['run_key'],bundle=op['bundle'],kit=op['kit'],
        archive=op['archive'],sha256=op['sha256'],tests=count,full_suite=full,
        production_authorized=False,review='REQUIRED',proof_partitions=['general','bootstrap'])
    write(out/'proof/CONT2_TEST_LEDGER.json',dict(tests=count,full_suite=full,
        suite_log='out/logs/tests.log',heavy_log='out/logs/cont2_heavy.log' if heavy.exists() else None,
        deferred=[] if full else ['Fix10.test_full_store_build_stream_division_with_and_without_remove'],
        reason=None if full else 'Trinity heavy-I/O permission requested; answer pending.'))
    write(out/'CONT2_RESULT.json',result);write(out/'REVIEW_REQUEST.json',result)
    write(out/'proof/GATES.json',result)
    (ROOT/'STATUS.md').write_text(f"{result['status']}. C {b['config_identity']}, run {b['run_key']}, {op['archive']} SHA256 {op['sha256']}. {count} tests pass. Read out/CONT2.md and out/CONT2.diff. Independent review, production proof and written GO remain required.\n")
    print(json.dumps(result))


if __name__=='__main__':main()
