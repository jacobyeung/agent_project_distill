from pathlib import Path
import hashlib,json,shutil,subprocess
L=Path(__file__).resolve().parents[1];out=L/'out';base=L/'work/base/work/base/tree_b01ce449'
manifest=json.loads((out/'PATCH_MANIFEST.json').read_text())
def inventory(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def fresh(name):
    root=L/'work/trees'/name;shutil.copytree(base,root)
    for p in [root,*root.rglob('*')]:p.chmod(0o755 if p.is_dir() else 0o644)
    return root
def run(cmd):
    r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return dict(command=[str(c) for c in cmd],returncode=r.returncode,output=r.stdout)
proof=dict(source=str(out/'PATCH_MANIFEST.json'),individual={},ordered={},integration={},refusals={})
for group in ('geometry','candidates','box'):
    target=fresh('b2_alone_'+group)
    result=run(['patch','--batch','--forward','-p1','-F0','--no-backup-if-mismatch','-d',target,'-i',out/f'PATCH_{group}.diff'])
    assert result['returncode']==0 and not any(s in result['output'].lower() for s in ('offset','fuzz','reject'))
    inv=inventory(target)
    assert all(inv.get(n)==e['patched_sha256'] for n,e in manifest['files'].items() if e['patch']==group)
    result['patched_hashes_verified']=True;proof['individual'][group]=result
target=fresh('b2_ordered');before=inventory(target)
dry=run(['bash',out/'apply_contract_patches.sh',target,'--dry-run'])
assert dry['returncode']==0 and before==inventory(target)
result=run(['bash',out/'apply_contract_patches.sh',target]);assert result['returncode']==0
after=inventory(target)
assert all(after.get(n)==e['patched_sha256'] for n,e in manifest['files'].items())
assert all(after[n]==h for n,h in before.items() if n not in manifest['files'])
proof['ordered']=dict(dry_run=dry,apply=result,all_patched_hashes_match=True,untouched_files_equal=True)
again=run(['bash',out/'apply_contract_patches.sh',target]);assert again['returncode']!=0 and after==inventory(target)
proof['refusals']['reapplication']=dict(again,unchanged=True)
target=fresh('b2_mismatch');(target/'student_pilot/geometry_profiles.py').write_text('# mismatch\n')
before=inventory(target);bad=run(['bash',out/'apply_contract_patches.sh',target]);assert bad['returncode']!=0 and before==inventory(target)
assert 'student_pilot/geometry_profiles.py' in bad['output']
proof['refusals']['base_hash_mismatch']=dict(bad,unchanged=True)
tree=L/'work/trees/tree_r1_rehearsal';inv=inventory(tree)
for n,e in manifest['files'].items():
    expected=e.get('accepted_integration_bases',[e])[0]['patched_sha256'];assert inv[n]==expected,n
proof['integration']=dict(tree=str(tree),all_patched_hashes_match=True,merge_proof=str(out/'INTEGRATION_MERGE_PROOF.json'))
again=run(['bash',out/'apply_contract_patches.sh',tree]);assert again['returncode']!=0 and inv==inventory(tree)
proof['refusals']['integration_reapplication']=dict(again,unchanged=True)
(out/'APPLY_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Independent patches, dry run, ordered application, mismatch and repeat refusal passed.')
