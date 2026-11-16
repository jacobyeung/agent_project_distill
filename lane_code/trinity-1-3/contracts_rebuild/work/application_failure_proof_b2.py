from pathlib import Path
import hashlib,json,re,shutil,subprocess
L=Path(__file__).resolve().parents[1];out=L/'out';base=L/'work/base/work/base/tree_b01ce449'
def inventory(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
proof=json.loads((out/'APPLY_PROOF.json').read_text())
for case in ('post_hash_mismatch','offset_hunk'):
    packet=L/'work'/('b2_packet_'+case);packet.mkdir()
    for name in ['apply_contract_patches.sh','contract_hash_checks.py','PATCH_MANIFEST.json','PATCH_geometry.diff','PATCH_geometry_on_tree_r1.diff','PATCH_candidates.diff','PATCH_box.diff']:
        shutil.copyfile(out/name,packet/name)
    manifest=json.loads((packet/'PATCH_MANIFEST.json').read_text())
    if case=='post_hash_mismatch':manifest['files']['student_pilot/live_instances314.py']['patched_sha256']='0'*64
    else:
        patch=packet/'PATCH_box.diff';text=patch.read_text()
        text=re.sub(r'@@ -(\d+)',lambda m:'@@ -'+str(int(m[1])+1),text,count=1)
        patch.write_text(text);manifest['patch_sha256'][patch.name]=hashlib.sha256(patch.read_bytes()).hexdigest()
    (packet/'PATCH_MANIFEST.json').write_text(json.dumps(manifest))
    target=L/'work/trees'/('b2_failure_'+case);shutil.copytree(base,target)
    before=inventory(target)
    r=subprocess.run(['bash',packet/'apply_contract_patches.sh',target],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    assert r.returncode!=0 and inventory(target)==before
    assert ('Hash mismatch' if case=='post_hash_mismatch' else 'offset') in r.stdout,r.stdout
    proof['refusals'][case]=dict(returncode=r.returncode,output=r.stdout,unchanged=True,packet=str(packet),target=str(target))
(out/'APPLY_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Post-patch hash failure and offset rejection preserve the complete target.')
