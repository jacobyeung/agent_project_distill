from pathlib import Path
import hashlib,json,subprocess,tarfile,shutil
L=Path(__file__).resolve().parents[1];O=L/'out';root=L/'work/trees/r2_proof';target=root/'base'
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
stages=sorted(root.glob('.contracts-*'))
assert len(stages)==2 and all((p/'staged').is_dir() for p in stages)
before=inv(target)
for stage in stages:
    baseline={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (stage/'before').read_text().splitlines()}
    assert baseline==before
    staged=inv(stage/'staged')
    assert all(staged[n]==e['patched_sha256'] for n,e in M['files'].items())
    assert (stage/'before').read_bytes()==(stage/'recheck').read_bytes()
dry=dict(returncode=0,target_unchanged=True,transactions=[str(p) for p in stages],
    evidence='Both retained staging transactions passed patching, post hashes and target inventory recheck.')
for p in [target,*target.rglob('*')]:p.chmod(p.stat().st_mode|0o200)
applied=run(['bash',O/'apply_contract_patches_r2.sh',target]);assert applied['returncode']==0,applied
after=inv(target);assert all(after[n]==e['patched_sha256'] for n,e in M['files'].items())
assert all(after[n]==v for n,v in before.items() if n not in M['files'])
again=run(['bash',O/'apply_contract_patches_r2.sh',target]);assert again['returncode']!=0 and after==inv(target)
# Reuse the retained dry-run tree. Move extra source files aside, preserving every file.
snapshot=L/'work/trees/r2_snapshot';(stages[0]/'staged').rename(snapshot)
retained=L/'work/r2_retained_stage_files';retained.mkdir()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    members=t.getmembers();files={str(Path(*Path(m.name).parts[1:])):m for m in members if m.isfile()}
    for p in list(snapshot.rglob('*')):
        if p.is_file() and str(p.relative_to(snapshot)) not in files:
            dest=retained/p.relative_to(snapshot);dest.parent.mkdir(parents=True,exist_ok=True);p.rename(dest)
    snap_expected={}
    for rel,member in files.items():
        assert member.size<20_000_000 and not Path(rel).is_absolute() and '..' not in Path(rel).parts
        dest=snapshot/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256()
        with t.extractfile(member) as source,dest.open('wb') as sink:
            for block in iter(lambda:source.read(1048576),b''):sink.write(block);h.update(block)
        snap_expected[rel]=h.hexdigest()
assert inv(snapshot)==snap_expected
plan=run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-s','-B',O/'contract_hash_checks_r2.py','pre',snapshot]);assert plan['returncode']==0,plan
steps=[]
for name in plan['output'].splitlines():
    cmd=['patch','--batch','--forward','-p1','-F0','--no-backup-if-mismatch','-d',snapshot,'-i',O/name]
    dry_step=run(cmd+['--dry-run']);step=run(cmd)
    for result in (dry_step,step):
        assert result['returncode']==0 and not any(x in result['output'].lower() for x in ('offset','fuzz','reject')),result
    steps.append(dict(dry_run=dry_step,apply=step))
snap_after=inv(snapshot)
assert all(snap_after[n]==e.get('accepted_integration_bases',[e])[0]['patched_sha256'] for n,e in M['files'].items())
assert all(snap_after[n]==v for n,v in snap_expected.items() if n not in M['files'])
repeat=run(['bash',O/'apply_contract_patches_r2.sh',snapshot]);assert repeat['returncode']!=0 and snap_after==inv(snapshot)
proof=dict(source=str(O/'PATCH_MANIFEST_R2.json'),base_source=str(L/'work/base/work/base/tree_b01ce449'),
    ordered=dict(dry_run=dry,apply=applied,all_patched_hashes_match=True,untouched_files_equal=True),
    refusals=dict(reapplication=dict(again,unchanged=True),integration_reapplication=dict(repeat,unchanged=True)),
    integration=dict(tree=str(snapshot),source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'),
        exact_archive_inventory_before_apply=True,plan=plan,steps=steps,all_patched_hashes_match=True,untouched_files_equal=True),
    tree=str(target),full_tree_copies=4,
    retained_test_copy_permission_failure=dict(target_unchanged=True,reason='Read-only mode inherited from sealed base; only local copy modes changed.',
        retained_stages=[str(p) for p in stages]),
    reused_stage=dict(source=str(stages[0]/'staged'),snapshot=str(snapshot),extra_files_preserved=str(retained)))
(O/'APPLY_PROOF_R2.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Application and snapshot proofs passed; four full trees retained.')
