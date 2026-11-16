from pathlib import Path
import difflib, hashlib, json
L=Path(__file__).resolve().parents[1]
base=L/'work/base/work/base/tree_b01ce449'
src=L/'work/src'; out=L/'out'; tree=L/'work/trees/tree_r1_rehearsal'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
groups=json.loads((L/'work/patch_groups.json').read_text())
manifest=json.loads((out/'PATCH_MANIFEST.json').read_text())
def diff(rel,old,new):
    return ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
for group,files in groups.items():
    text=''
    for rel in files:
        text+=diff(rel,(base/rel).read_text() if (base/rel).exists() else '',(src/rel).read_text())
        manifest['files'][rel].update(base_sha256=sha(base/rel),patched_sha256=sha(src/rel))
    (out/f'PATCH_{group}.diff').write_text(text)
changed={p.relative_to(tree).as_posix() for p in tree.rglob('*') if p.is_file() and sha(p)!=sha(base/p.relative_to(tree))}
overlap=sorted(changed & manifest['files'].keys())
assert overlap==['student_pilot/carrier_c1_routing.py'],overlap
rel=overlap[0];a=(base/rel).read_text();b=(src/rel).read_text();c=(tree/rel).read_text()
merged=c
for op,i,j,k,n in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
    if op=='equal':continue
    old=''.join(a.splitlines(True)[i:j]);new=''.join(b.splitlines(True)[k:n])
    assert old and merged.count(old)==1
    merged=merged.replace(old,new,1)
variant=(out/'PATCH_geometry.diff').read_text().replace(diff(rel,a,b),diff(rel,c,merged))
(out/'PATCH_geometry_on_tree_r1.diff').write_text(variant)
merged_sha=hashlib.sha256(merged.encode()).hexdigest()
manifest['files'][rel]['accepted_integration_bases']=[dict(base_sha256=sha(tree/rel),patched_sha256=merged_sha,patch_file='PATCH_geometry_on_tree_r1.diff',source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'))]
manifest['patch_sha256']={p.name:sha(p) for p in out.glob('PATCH_*.diff')}
manifest['build2_defects']=[dict(source=str(out/'REAL_ROW_DEFECT_B1.json'),files=['student_pilot/phrases.py','student_pilot/training_contract.py'],fix='Use the runtime question-parser fallback when no manifest is configured; strip the distance unit suffix from the parsed operand. Explicit manifests still require each named row.')]
manifest['integration_overlap']=overlap
(out/'PATCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'INTEGRATION_MERGE_PROOF.json').write_text(json.dumps(dict(overlap=overlap,tree_changed_files=sorted(changed),contract_edits_present='if not recorded and not heading_available(geometry):' in merged,tree_edits_present="if row.get('trace_contract') == 'next-leg-r2-v1':" in merged,merged_sha256=merged_sha,source=str(tree/rel)),indent=2)+'\n')
print('Regenerated patch packet and exact integration variant.')
