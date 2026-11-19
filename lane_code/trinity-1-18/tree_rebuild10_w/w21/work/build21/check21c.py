from pathlib import Path
import sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c';A=L/'attic/build21c'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
delivery=J.load(C/'DELIVERY.json');old=J.load(A/'kit/k/p.json');new=J.load(B/'kits/q/k/p.json')
bad='k/benchmark_scene_exclusions.json';alias='k/3119aa4a.json';h=old['p_files'][bad]
assert new['p_files'][alias]==h and new['p_sources'][alias]=='u/'+h
assert {k:v for k,v in old['p_files'].items() if k!=bad}=={k:v for k,v in new['p_files'].items() if k!=alias}
assert (B/'kits/q/k/n.json').read_bytes()==(A/'kit/k/n.json').read_bytes()
assert new['pin_paths'][h]==new['namespace']+'/u/'+h
assert J.sha(L/delivery['base']['path'])==delivery['base']['sha256']
assert J.sha(L/delivery['package'])==delivery['sha256']
assert J.seal(B/'kits/q')==delivery['kit_seal']
manifest=J.load(B/'PACKAGE_MANIFEST.json')
assert hashlib.sha256(json.dumps(manifest['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==delivery['package_seal']
original=J.load(A/'PACKAGE_MANIFEST.json')['files'];changes=[]
for p in sorted((B/'kits/q').rglob('*')):
    if not p.is_file():continue
    name=str(p.relative_to(L));current=dict(bytes=p.stat().st_size,sha256=J.sha(p))
    assert manifest['files'][name]==current
    if original.get(name)!=current:changes.append(name)
result=dict(status='PASS',GO=False,base_unchanged=True,configuration_capsule_byte_identical=True,
    p_file_inventory_change=dict(before=bad,after=alias,sha256=h),other_p_pins_unchanged=True,
    kit_matches_package_manifest=True,kit_file_changes=changes,package=delivery['package'])
J.write(C/'PACKAGE_CHECK.json',result)
print(json.dumps(result,indent=2))
