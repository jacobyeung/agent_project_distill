from pathlib import Path
import hashlib,json,subprocess,tarfile
L=Path(__file__).resolve().parents[1];O=L/'out';root=L/'work/trees/r2_proof';target=root/'base';snapshot=L/'work/trees/r2_snapshot'
M=json.loads((O/'PATCH_MANIFEST_R2.json').read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def inv(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def run(cmd):
    r=subprocess.run(list(map(str,cmd)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return dict(command=list(map(str,cmd)),returncode=r.returncode,output=r.stdout)
stages=sorted(root.glob('.contracts-*'),key=lambda p:(p/'before').stat().st_mtime_ns)
assert len(stages)==3
applied_stage=next(p for p in stages if (p/'original').is_dir())
before=inv(applied_stage/'original');after=inv(target)
assert all(after[n]==e['patched_sha256'] for n,e in M['files'].items())
assert all(after[n]==v for n,v in before.items() if n not in M['files'])
for stage in stages:
    baseline={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (stage/'before').read_text().splitlines()}
    assert baseline==before and (stage/'before').read_bytes()==(stage/'recheck').read_bytes()
again=run(['bash',O/'apply_contract_patches_r2.sh',target]);assert again['returncode']!=0 and after==inv(target)
snap_expected={}
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    for m in t:
        if m.isfile():
            h=hashlib.sha256()
            with t.extractfile(m) as f:
                for block in iter(lambda:f.read(1048576),b''):h.update(block)
            snap_expected[str(Path(*Path(m.name).parts[1:]))]=h.hexdigest()
assert inv(snapshot)==snap_expected
plan=run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-s','-B',O/'contract_hash_checks_r2.py','pre',snapshot]);assert plan['returncode']==0,plan
steps=[]
for name in plan['output'].splitlines():
    cmd=['patch','--batch','--forward','-p1','-F0','--no-backup-if-mismatch','-d',snapshot,'-i',O/name]
    dry=run(cmd+['--dry-run']);step=run(cmd)
    for result in (dry,step):
        assert result['returncode']==0 and not any(x in result['output'].lower() for x in ('offset','fuzz','reject')),result
    steps.append(dict(dry_run=dry,apply=step))
snap_after=inv(snapshot)
assert all(snap_after[n]==e.get('accepted_integration_bases',[e])[0]['patched_sha256'] for n,e in M['files'].items())
assert all(snap_after[n]==v for n,v in snap_expected.items() if n not in M['files'])
repeat=run(['bash',O/'apply_contract_patches_r2.sh',snapshot]);assert repeat['returncode']!=0 and snap_after==inv(snapshot)
transactions=[]
for stage in stages:
    transactions.append(dict(path=str(stage),plan=(stage/'plan').read_text().splitlines(),
        target_inventory_unchanged=True,patch_logs={p.name:p.read_text() for p in stage.glob('*.log')}))
proof=dict(source=str(O/'PATCH_MANIFEST_R2.json'),base_source=str(L/'work/base/work/base/tree_b01ce449'),
    ordered=dict(dry_run=dict(command=['bash',str(O/'apply_contract_patches_r2.sh'),str(target),'--dry-run'],
        returncode_asserted_zero_by=str(L/'work/apply_proof_r2.py'),transaction=str(stages[0]),target_unchanged=True),
        apply=dict(command=['bash',str(O/'apply_contract_patches_r2.sh'),str(target)],
            returncode_asserted_zero_by=str(L/'work/resume_apply_proof_r2.py'),transaction=str(applied_stage),
            retained_original=str(applied_stage/'original')),all_patched_hashes_match=True,untouched_files_equal=True),
    transactions=transactions,refusals=dict(reapplication=dict(again,unchanged=True),integration_reapplication=dict(repeat,unchanged=True)),
    integration=dict(tree=str(snapshot),source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'),
        exact_archive_inventory_before_apply=True,plan=plan,steps=steps,all_patched_hashes_match=True,untouched_files_equal=True),
    tree=str(target),full_tree_copies=4,
    test_copy_modes='The fresh base copy must be writable for directory replacement. Only local test-copy modes were changed.',
    stage_reuse='A retained staging tree was repopulated from the snapshot archive; extra files were moved to work/r2_retained_stage_files. No files were discarded.')
(O/'APPLY_PROOF_R2.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Base and integration snapshot proofs passed; both reject reapplication.')
