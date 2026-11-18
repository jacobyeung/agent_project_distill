"""Record the reviewable continuation identity and bounded local evidence."""
import difflib,json,re,subprocess,sys,tarfile,tempfile
from pathlib import Path
from rebind import ROOT,load,sha,write,diff
from build_cont1 import SNAP

def main():
    out=ROOT/'out';b=load(out/'BINDING.json');cfg=load(out/'config.json');op=load(out/'OPERATOR.json')
    log=(out/'logs/tests.log').read_text();assert log.rstrip().endswith('OK')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    rechecks=count
    ledger=load(out/'proof/CONT1_TEST_LEDGER.json') if (out/'proof/CONT1_TEST_LEDGER.json').exists() else None
    if ledger:
        assert ledger['status']=='PASS';count=ledger['unique_tests']
    assert 'Continuation.test_' in log
    for n in ('FIRST_BATCH','DERIVATION','PRE_SUBMISSION','SWITCH_GUARDS','UNIT_REAL'):
        r=load(out/'proof'/(n+'.json'));assert r['status']=='PASS' and r['config_identity']==b['config_identity'],n
    for n in ('CONT1_ROWS','CONT1_STATE','OFF_IDENTITY'):assert load(out/'proof'/(n+'.json'))['status']=='PASS'
    assert sha(out/op['archive'])==op['sha256']
    protected={p.name:sha(p) for p in (SNAP/'out').glob('p_*.tar')}
    for n,h in protected.items():assert sha(out/n)==h,n
    write(out/'CONT1_PROTECTED_ARCHIVES.json',protected)
    ready=Path(load(out/'proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    destination=Path(tempfile.mkdtemp(prefix='cont1_seal_',dir=ROOT/'work'))/'authority.json'
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/seal_proof.py'),'--kit',str(ready),'--bundle',str(out/'operator'),
        '--binding',str(out/'BINDING.json'),'--partition','general','--out',str(destination)],check=True)
    authority=load(destination)
    assert {'b/c0.py','b/w.py','b/r8.py','job.sh'}<=set(authority['runtime'])
    assert {'c0.py','a0.json'}<=set(authority['bundle_files'])
    write(out/'proof/CONT1_RESEAL.json',dict(status='PASS',authority=str(destination),sha256=sha(destination),
        identity=b['config_identity'],scope='Local production-form fixture; deployed evidence remains external'))
    changes=diff(load(SNAP/'out/config.json'),cfg)
    rows='\n'.join('| '+x['field']+' | `'+json.dumps(x['before'])+'` | `'+json.dumps(x['after'])+'` |' for x in changes)
    manifest={}
    for line in (ready/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1);manifest[n]=h
    text=f'''BUILT_FOR_INDEPENDENT_REVIEW. C resumes A at absolute step 200 and stops at 600. The launch gate accepts only a completed PASS CPU proof and separate written GO. No canary is needed.

| Identity | Value |
|---|---|
| Config identity | `{b['config_identity']}` |
| Config file SHA256 | `{sha(out/'config.json')}` |
| Run key | `{b['run_key']}` |
| Job name | `{b['job_name']}` |
| Bundle | `{op['bundle']}` |
| Kit | `{op['kit']}` |
| Persistent slots | `/project/community/jjyeung/okh7/r/{b['run_key']}` |
| Archive | `{op['archive']}` |
| Archive SHA256 | `{op['sha256']}` |
| Proof script | `{op['proof_script']}` (general, CPU only) |
| Training time limit | `24:00:00` (advanced, four GPUs) |

The estimate is `(400 × 0.153 + 11) / 4 = 18.05` wall hours. The 24-hour allocation leaves 5.95 hours for restore, exports and variation. The existing trainer budget remains 86,400 seconds with a 3,600-second stop reserve. The wrapper's GCS fallback deadline also uses 86,400 seconds.

The complete config delta from frozen A is below. Tree, code archive, stores, REMOVE lists, selection, units, reader pins, S2=true, S1=false, both max_own probabilities, 1,000-step LR horizon, seed, row offset and default cells are equal to A.

| Field | A | C |
|---|---|---|
{rows}

`configs/cont1_cells.json` exposes every family's requested cents. `tools/build_cont1.py --cells FILE` puts those values directly into `type_mix.streams.<stream>.cells`, which the unchanged sampler consumes. A changed parameter set produces a distinct identity; it needs new admission, proof and GO. Unit allowlists and row/store pins remain explicit existing config parameters. This sealed C enforces identical admitted populations at its default boundary. The explicit `continuation.rows=rebind` config mode permits an intentional change to newly admitted cells and input pins. `--mix FILE` also accepts the existing unit allowlist and mix policy. The builder selects rebind mode when the requested mix changes; a source-pin rebind still needs matching store, selection and packaging records. Rebind mode preserves optimizer and absolute step, while rebuilding the requested sampler at that step; it does not claim equality with A's draws.

The bundle and kit tokens differ from A; `record_key=69d2930d` retains A's immutable data-record paths. All new writable run, slot, log, export-session and bundle/kit paths use C's opaque token. A's `r/673bc60f` is read only. Existing packet archives are checksum-verified and retained.

`b/c0.py` is the sealed runtime bridge. The wrapper first restores any C slot through its inherited A/B restore path. For the first C leg, `job.sh` verifies A's run marker, binding mirror and digest, selects only a verified step-200 A/B record, checks its archive size and SHA256, safely streams its regular members into C's private `d/`, and verifies the pinned `complete.json` plus every shard, replicated payload and rank RNG file. It retains A's checkpoint and binding bytes unchanged. The donor pointer records A's run, launch identity, exact step, archive digest and manifest digest.

A's checkpoint binds its admitted effective configuration. The bridge reconstructs that configuration from the frozen A template and authenticated admission/preparation pins, requires its identity to equal the checkpoint binding, and checks the sealed trainer revision. In C's default exact mode, it compares C's regenerated stream counts, database/indices hashes, mix populations, effective quotas and policy before restoring. A mismatched population or source refuses.

`b/r8.py` returns mode `u` for the verified donor and initializes only C's persistent marker. `b/w.py` installs the bridge only for a continuation config in mode `u`. The first native restore receives A's original binding and restores parameters, Adam state, buffers, trained-group state and RNG. The native loop receives start_step=200; it computes LR and row plans from absolute step 201. The first new output binding belongs to C. Later C checkpoints use the inherited native resume path. Empty or malformed optimizer state refuses before an update. The sealed trainer tree is byte-identical to A.

H1's `C1_INIT_LOCAL` path loads the pinned m544 full-weight/head export before optimizer construction. That warm start alone cannot preserve Adam or absolute step. C retains that initialization for compatibility, then restores A's full checkpoint. A's GCS `m200` and `mstop*` objects are weight exports, not substitutes for the verified slot. If A uses its separate GCS slot fallback, an operator must restore and verify a normal A/B slot before C can start; C does not fetch network objects.

The CPU proof retains A's admission, namespace, loader-audit and fix-11 environment setup. It additionally exercises the actual slot extraction and pointer verifier against a four-rank fixture. PASS requires `checks.resume_pointer.status=PASS`; the launch gate refuses CANARY. The proof fixture does not attest a future real A slot, which is verified at runtime.

Validation: {count} unique packet tests have passing results. The initial full run executed 77 tests; its single stale generated-diff failure is covered by the final {rechecks}-test recheck. `CONT1_TEST_LEDGER.json` records each result and both logs. Passing tests of unchanged code, including the 1.79 GB division fixture and historical A CANARY gate, are retained to respect the scratch cap. The runner checks deterministic archives, two byte-equal fixture kit derivations, production-form review/staging/archive evidence, four-rank D0 OFF optimizer identity, native unit regeneration, the CPU first batch and fix-11 nounset replay. Large immutable local fixture files share hardlinks; source snapshots remain untouched. The continuation tests compare default step-201–600 plans, check wrong run/step/config/checksums and missing optimizer state, exercise the adapter and resume chooser, and execute the PASS-only gate. The native small-model test compares 206 uninterrupted updates with 200 plus six resumed updates: parameters, Adam state, RNG, LR and rows are bit-exact. It uses native shard serialization/restore with mocked single-rank collectives. Other sampler populations are synthetic; the VQA check also uses the real local admitted population.

Reviewer checks: inspect the A launch-to-effective-config authentication chain, slot extraction and checksum checks, native restore adapter, new-output binding, row-population equality, independent writable namespaces, PASS-only gate, fix-11 replay, 24-hour limits and exact archive/derived-kit inventory. Confirm the real step-200 slot exists with full optimizer state. Independently scan the new runtime/proof text and seal the final deployed kit. Confirm the operator's written boundary GO and normal monitoring rules before submission.

Local tests do not prove Orchard namespaces, filesystem capacity, real A checkpoint availability, GPU/FSDP bit-exactness, production RGB admission, full routing regeneration or throughput. Regenerated database or population hashes may differ in production; C then refuses and needs investigation. No Orchard access, SSH, Git, GPU launch, external write, mirror or independent review occurred. The brief forbids those actions here; `out/REVIEW_REQUEST.json` is the local handoff. `out/proof/CONT1_RESEAL.json` is a fixture seal, not production approval. The explicit snapshot comparison in this report identifies the requested authority baseline.
'''
    (out/'CONT1.md').write_text(text)
    for name in ('REPORT.md','R1P_PACKET.md'):(out/name).write_text(text)
    paths=set()
    for folder in ('tools','tests','configs'):
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).glob('*') if p.is_file())
    paths.update('out/'+n for n in ('config.json','BINDING.json','a0.json','proof/inputs.json','proof/p.py'))
    for root in (ROOT,SNAP):
        sums=root/'out/operator/sums.txt'
        paths.update('out/operator/'+line.split('  ',1)[1] for line in sums.read_text().splitlines())
    patches=[];inventory={}
    for name in sorted(paths):
        left=SNAP/name;right=ROOT/name
        a=left.read_bytes() if left.is_file() else b'';z=right.read_bytes() if right.is_file() else b''
        if a==z:continue
        inventory[name]=dict(before=sha(left) if left.is_file() else None,after=sha(right) if right.is_file() else None)
        try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='snap_9dd2fbb7/'+name,tofile='C/'+name))
        except UnicodeDecodeError:patches.append('Binary content differs: '+name+'\n')
    old_evidence=load(SNAP/'out/proof/DERIVATION.json');old_kit=Path(old_evidence['fixture_paths'][0])
    assert sha(old_kit/'SHA256SUMS.txt')==old_evidence['manifest_sha256']
    old_manifest=dict(reversed(line.split('  ',1)) for line in (old_kit/'SHA256SUMS.txt').read_text().splitlines())
    kit_changes={}
    for name in sorted(set(old_manifest)|set(manifest)):
        if old_manifest.get(name)==manifest.get(name):continue
        kit_changes[name]=dict(before=old_manifest.get(name),after=manifest.get(name))
        left=old_kit/name;right=ready/name
        a=left.read_bytes() if left.is_file() else b'';z=right.read_bytes() if right.is_file() else b''
        try:patches.extend(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='A_fixture_kit/'+name,tofile='C_fixture_kit/'+name))
        except UnicodeDecodeError:patches.append('Binary content differs: kit/'+name+'\n')
    (out/'CONT1.diff').write_text(''.join(patches))
    write(out/'CONT1_INVENTORY.json',dict(changed=inventory,derived_manifest=manifest,derived_kit_changes=kit_changes,
        old_fixture_manifest=old_evidence['manifest_sha256'],new_fixture_manifest=sha(ready/'SHA256SUMS.txt')))
    result=dict(status='BUILT_FOR_INDEPENDENT_REVIEW',identity=b['config_identity'],config_file_sha256=sha(out/'config.json'),
        run=b['run_key'],job=b['job_name'],bundle=op['bundle'],kit=op['kit'],archive=op['archive'],sha256=op['sha256'],
        tests=count,config_delta=changes,production_authorized=False,review='REQUIRED',time_limit='24:00:00')
    write(out/'CONT1_RESULT.json',result);write(out/'REVIEW_REQUEST.json',result)
    write(out/'proof/GATES.json',dict(status='BUILT_FOR_INDEPENDENT_REVIEW',config_identity=b['config_identity'],
        tests=count,local_checks='PASS',production_authorized=False,production_cpu_proof='NOT_RUN',
        real_slot='NOT_AVAILABLE_LOCALLY',independent_review='REQUIRED',fixture_reseal=sha(destination)))
    (ROOT/'STATUS.md').write_text(f"BUILT_FOR_INDEPENDENT_REVIEW. C {b['config_identity']}, run {b['run_key']}, {op['archive']} SHA256 {op['sha256']}. {count} tests and local checks pass. Read out/CONT1.md and out/CONT1.diff. Independent review, deployed proof/seal, real A slot verification and written GO remain required.\n")
    print(json.dumps(result))
if __name__=='__main__':main()
