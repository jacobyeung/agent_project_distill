from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[1];O=L/'out';B=L/'work/base/work/base/tree_b01ce449'
M=json.loads((O/'PATCH_MANIFEST_R5.json').read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def inv(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def run(cmd):
    r=subprocess.run(list(map(str,cmd)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return dict(command=list(map(str,cmd)),returncode=r.returncode,output=r.stdout)
def clean(result):
    assert result['returncode']==0,result
    assert not any(x in result['output'].lower() for x in ('offset','fuzz','reject')),result
root=L/'work/trees/r5_proof';root.mkdir(exist_ok=True);target=root/'base';assert inv(target)==inv(B)
before=inv(target)
stages_before=sorted(str(p) for p in root.glob('.contracts-*'))
readonly=run(['bash',O/'apply_contract_patches_r5.sh',target])
assert readonly['returncode']!=0 and 'target_not_writable' in readonly['output'],readonly
assert stages_before==sorted(str(p) for p in root.glob('.contracts-*')) and inv(target)==before
for p in [target,*target.rglob('*')]:p.chmod(p.stat().st_mode | 0o200)
dry=run(['bash',O/'apply_contract_patches_r5.sh',target,'--dry-run']);assert dry['returncode']==0,dry
assert inv(target)==before
applied=run(['bash',O/'apply_contract_patches_r5.sh',target]);assert applied['returncode']==0,applied
after=inv(target);assert all(after[n]==e['patched_sha256'] for n,e in M['files'].items())
assert all(after[n]==h for n,h in before.items() if n not in M['files'])
again=run(['bash',O/'apply_contract_patches_r5.sh',target]);assert again['returncode']!=0 and after==inv(target)
# The retained dry-run stage is also verified by the unmodified staging operator.
snapshot=L/'work/trees/r5_snapshot';snapshot.mkdir()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    for member in t:
        parts=Path(member.name).parts
        if len(parts)==1:continue
        rel=Path(*parts[1:]);assert not rel.is_absolute() and '..' not in rel.parts
        dest=snapshot/rel
        if member.isdir():dest.mkdir(parents=True,exist_ok=True)
        else:
            assert member.isfile() and member.size<20_000_000,member.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(member) as source,dest.open('wb') as sink:shutil.copyfileobj(source,sink,1048576)
snap_before=inv(snapshot)
plan=run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-s','-B',O/'contract_hash_checks_r5.py','pre',snapshot]);assert plan['returncode']==0,plan
steps=[]
for name in plan['output'].splitlines():
    cmd=['patch','--batch','--forward','-p1','-F0','--no-backup-if-mismatch','-d',snapshot,'-i',O/name]
    dry_step=run(cmd+['--dry-run']);clean(dry_step)
    step=run(cmd);clean(step);steps.append(dict(dry_run=dry_step,apply=step))
snap_after=inv(snapshot)
assert all(snap_after[n]==e.get('accepted_integration_bases',[e])[0]['patched_sha256'] for n,e in M['files'].items())
assert all(snap_after[n]==v for n,v in snap_before.items() if n not in M['files'])
repeat=run(['bash',O/'apply_contract_patches_r5.sh',snapshot]);assert repeat['returncode']!=0 and snap_after==inv(snapshot)
proof=dict(source=str(O/'PATCH_MANIFEST_R5.json'),base_source=str(B),ordered=dict(dry_run=dry,apply=applied,
    all_patched_hashes_match=True,untouched_files_equal=True,dry_run_target_unchanged=True),
    refusals=dict(readonly=dict(readonly,no_staging_created=True,unchanged=True),reapplication=dict(again,unchanged=True),integration_reapplication=dict(repeat,unchanged=True)),
    integration=dict(tree=str(snapshot),source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'),plan=plan,steps=steps,
        all_patched_hashes_match=True,untouched_files_equal=True),tree=str(target),full_tree_copies=4)
(O/'APPLY_PROOF_R5.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Application proof passed.')
