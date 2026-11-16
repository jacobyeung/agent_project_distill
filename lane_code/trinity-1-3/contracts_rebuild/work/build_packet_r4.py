from pathlib import Path
import difflib, hashlib, json, tarfile
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r4';B=L/'work/base/work/base/tree_b01ce449'
def sha(p):
    if not p.exists():return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def diff(rel,a,b):return ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
groups=json.loads((L/'work/patch_groups.json').read_text())
groups['geometry']+=['generator/derivgen_v7/derivgen/calculator.py', 'generator/derivgen_v7/derivgen/trace.py', 'trace_format/point_events.py']
groups['geometry']+=['trace_format/calculator.py','student_pilot/p3_printed_calculator.py','student_pilot/carrier_c1_run.py']
manifest=json.loads((O/'PATCH_MANIFEST.json').read_text())
manifest.pop('build2_proofs',None);manifest.pop('integration_seal',None)
for group,rels in groups.items():
    changes=[]
    for rel in rels:
        a=(B/rel).read_text() if (B/rel).exists() else '';b=(S/rel).read_text()
        changes.append(diff(rel,a,b))
        manifest['files'][rel]=dict(base_sha256=sha(B/rel),patched_sha256=sha(S/rel),patch=group)
    (O/f'PATCH_{group}_r4.diff').write_text(''.join(changes))
rel='student_pilot/carrier_c1_routing.py';a=(B/rel).read_text();b=(S/rel).read_text()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    c=t.extractfile('tree_r1/'+rel).read().decode()
anchor="    if row.get('form') in ground_rows.FORMS.values():\n"
addition="        if row.get('trace_contract') == 'next-leg-r2-v1':\n            from .r2_contract import event_row\n            return event_row(row)\n"
assert a.count(anchor)==b.count(anchor)==1
assert c==a.replace(anchor,anchor+addition)
merged=b.replace(anchor,anchor+addition)
variant=(O/'PATCH_geometry_r4.diff').read_text().replace(diff(rel,a,b),diff(rel,c,merged))
manifest['files'][rel]['accepted_integration_bases']=[dict(base_sha256=hashlib.sha256(c.encode()).hexdigest(),
    patched_sha256=hashlib.sha256(merged.encode()).hexdigest(),patch_file='PATCH_geometry_on_tree_r1_r4.diff',
    source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'))]
rel='student_pilot/carrier_c1_run.py';a=(B/rel).read_text();b=(S/rel).read_text()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    c=t.extractfile('tree_r1/'+rel).read().decode()
def identity_block(text):return text[text.index('def identity(cfg):'):text.index('def readout_identity(cfg):')]
assert identity_block(a)==identity_block(c)
merged=c.replace(identity_block(a),identity_block(b),1)
variant=variant.replace(diff(rel,a,b),diff(rel,c,merged))
manifest['files'][rel]['accepted_integration_bases']=[dict(base_sha256=hashlib.sha256(c.encode()).hexdigest(),
    patched_sha256=hashlib.sha256(merged.encode()).hexdigest(),patch_file='PATCH_geometry_on_tree_r1_r4.diff',
    source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar'))]
(O/'PATCH_geometry_on_tree_r1_r4.diff').write_text(variant)
manifest['integration_overlap']=['student_pilot/carrier_c1_routing.py','student_pilot/carrier_c1_run.py']
manifest['patch_sha256']={p.name:sha(p) for p in O.glob('PATCH_*_r4.diff')}
manifest['r4_contract']=dict(heading_plane_min_default=.3,source=str(S/'trace_format/contracts.py'),
    guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),
    field_table=str(O/'HEADING_DEPENDENCE_R4.md'))
(O/'PATCH_MANIFEST_R4.json').write_text(json.dumps(manifest,indent=2)+'\n')
(L/'work/patch_groups_r4.json').write_text(json.dumps(groups,indent=2)+'\n')
script=(O/'apply_contract_patches.sh').read_text().replace('apply_contract_patches.sh','apply_contract_patches_r4.sh').replace('contract_hash_checks.py','contract_hash_checks_r4.py')
script=script.replace('# All validation precedes installation.', '''# Check permissions before any validation inventory or staging copy.
"$py" -I -s -B "$packet/contract_hash_checks_r4.py" writable "$target"
# All validation precedes installation.''')
script=script.replace('cp -a -- "$target" "$transaction/staged"', '''if [[ ${2:-} == --dry-run ]]; then
    "$py" -I -s -B "$packet/contract_hash_checks_r4.py" stage-changed "$target" "$transaction/staged"
else
    cp -a -- "$target" "$transaction/staged"
fi''')
(O/'apply_contract_patches_r4.sh').write_text(script)
helper=(O/'contract_hash_checks.py').read_text().replace('PATCH_MANIFEST.json','PATCH_MANIFEST_R4.json').replace("f'PATCH_{g}.diff'","f'PATCH_{g}_r4.diff'")
helper=helper.replace("if sys.argv[1]=='pre':", '''if sys.argv[1]=='writable':
    import os, stat
    for p in (root, root.parent):
        if not stat.S_IMODE(p.stat().st_mode) & 0o222 or not os.access(p, os.W_OK | os.X_OK):
            raise SystemExit('target_not_writable: '+str(p)+'; staging not created')
    for p in root.rglob('*'):
        if p.is_symlink():
            raise SystemExit('target_symbolic_link: '+str(p)+'; staging not created')
        if not stat.S_IMODE(p.stat().st_mode) & 0o222 or not os.access(p, os.W_OK):
            raise SystemExit('target_not_writable: '+str(p)+'; staging not created')
elif sys.argv[1]=='pre':''')
helper=helper.replace("elif sys.argv[1]=='post':", '''elif sys.argv[1]=='stage-changed':
    import shutil
    stage=Path(sys.argv[3]); stage.mkdir()
    for rel in manifest['files']:
        source=root/rel
        if source.exists():
            dest=stage/rel; dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
elif sys.argv[1]=='post':''')
(O/'contract_hash_checks_r4.py').write_text(helper)
(O/'PACKET_HELPER_PARITY_R4.json').write_text(json.dumps(dict(source=str(O/'apply_contract_patches.sh'),
    script_identical_except_names=script.replace('apply_contract_patches_r4.sh','apply_contract_patches.sh').replace('contract_hash_checks_r4.py','contract_hash_checks.py')==(O/'apply_contract_patches.sh').read_text(),
    helper_identical_except_names=helper.replace('PATCH_MANIFEST_R4.json','PATCH_MANIFEST.json').replace("f'PATCH_{g}_r4.diff'","f'PATCH_{g}.diff'")==(O/'contract_hash_checks.py').read_text()),indent=2)+'\n')
print('r4 patch packet generated.')
