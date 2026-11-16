from pathlib import Path
import difflib, hashlib, json, tarfile
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r2';B=L/'work/base/work/base/tree_b01ce449'
def sha(p):
    if not p.exists():return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def diff(rel,a,b):return ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
groups=json.loads((L/'work/patch_groups.json').read_text())
groups['geometry']+=['trace_format/calculator.py','student_pilot/p3_printed_calculator.py','student_pilot/carrier_c1_run.py']
manifest=json.loads((O/'PATCH_MANIFEST.json').read_text())
manifest.pop('build2_proofs',None);manifest.pop('integration_seal',None)
for group,rels in groups.items():
    changes=[]
    for rel in rels:
        a=(B/rel).read_text() if (B/rel).exists() else '';b=(S/rel).read_text()
        changes.append(diff(rel,a,b))
        manifest['files'][rel]=dict(base_sha256=sha(B/rel),patched_sha256=sha(S/rel),patch=group)
    (O/f'PATCH_{group}_r2.diff').write_text(''.join(changes))
rel='student_pilot/carrier_c1_routing.py';a=(B/rel).read_text();b=(S/rel).read_text()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    c=t.extractfile('tree_r1/'+rel).read().decode()
anchor="    if row.get('form') in ground_rows.FORMS.values():\n"
addition="        if row.get('trace_contract') == 'next-leg-r2-v1':\n            from .r2_contract import event_row\n            return event_row(row)\n"
assert a.count(anchor)==b.count(anchor)==1
assert c==a.replace(anchor,anchor+addition)
merged=b.replace(anchor,anchor+addition)
variant=(O/'PATCH_geometry_r2.diff').read_text().replace(diff(rel,a,b),diff(rel,c,merged))
manifest['files'][rel]['accepted_integration_bases']=[dict(base_sha256=hashlib.sha256(c.encode()).hexdigest(),
    patched_sha256=hashlib.sha256(merged.encode()).hexdigest(),patch_file='PATCH_geometry_on_tree_r1_r2.diff',
    source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'))]
rel='student_pilot/carrier_c1_run.py';a=(B/rel).read_text();b=(S/rel).read_text()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    c=t.extractfile('tree_r1/'+rel).read().decode()
def identity_block(text):return text[text.index('def identity(cfg):'):text.index('def readout_identity(cfg):')]
assert identity_block(a)==identity_block(c)
merged=c.replace(identity_block(a),identity_block(b),1)
variant=variant.replace(diff(rel,a,b),diff(rel,c,merged))
manifest['files'][rel]['accepted_integration_bases']=[dict(base_sha256=hashlib.sha256(c.encode()).hexdigest(),
    patched_sha256=hashlib.sha256(merged.encode()).hexdigest(),patch_file='PATCH_geometry_on_tree_r1_r2.diff',
    source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'))]
(O/'PATCH_geometry_on_tree_r1_r2.diff').write_text(variant)
manifest['integration_overlap']=['student_pilot/carrier_c1_routing.py','student_pilot/carrier_c1_run.py']
manifest['patch_sha256']={p.name:sha(p) for p in O.glob('PATCH_*_r2.diff')}
manifest['r2_contract']=dict(heading_plane_min_default=.3,source=str(S/'trace_format/contracts.py'),
    guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),
    field_table=str(O/'HEADING_DEPENDENCE_R2.md'))
(O/'PATCH_MANIFEST_R2.json').write_text(json.dumps(manifest,indent=2)+'\n')
(L/'work/patch_groups_r2.json').write_text(json.dumps(groups,indent=2)+'\n')
script=(O/'apply_contract_patches.sh').read_text().replace('apply_contract_patches.sh','apply_contract_patches_r2.sh').replace('contract_hash_checks.py','contract_hash_checks_r2.py')
(O/'apply_contract_patches_r2.sh').write_text(script)
helper=(O/'contract_hash_checks.py').read_text().replace('PATCH_MANIFEST.json','PATCH_MANIFEST_R2.json').replace("f'PATCH_{g}.diff'","f'PATCH_{g}_r2.diff'")
(O/'contract_hash_checks_r2.py').write_text(helper)
(O/'PACKET_HELPER_PARITY_R2.json').write_text(json.dumps(dict(source=str(O/'apply_contract_patches.sh'),
    script_identical_except_names=script.replace('apply_contract_patches_r2.sh','apply_contract_patches.sh').replace('contract_hash_checks_r2.py','contract_hash_checks.py')==(O/'apply_contract_patches.sh').read_text(),
    helper_identical_except_names=helper.replace('PATCH_MANIFEST_R2.json','PATCH_MANIFEST.json').replace("f'PATCH_{g}_r2.diff'","f'PATCH_{g}.diff'")==(O/'contract_hash_checks.py').read_text()),indent=2)+'\n')
print('r2 patch packet generated.')
