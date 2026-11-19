"""Record unchanged delivery state for the mandatory sealed-tree stop."""
from pathlib import Path
import datetime,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21h'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
delivery=J.load(L/'work/build21g/DELIVERY.json')
manifest=J.load(B/'PACKAGE_MANIFEST.json');n=0
for name,entry in manifest['files'].items():
    if name.startswith('work/tree_r1/'):
        p=L/name
        assert p.stat().st_size==entry['bytes'] and J.sha(p)==entry['sha256'],name
        n+=1
for name in ('work/build21/joblib.py','work/build21/kit.py','work/build21/naming21.py',
             'work/build21/environment21f.py','work/build21/UPLOADS.json'):
    assert J.sha(L/name)==manifest['files'][name]['sha256'],name
kit=J.seal(B/'kits/q');assert kit==delivery['kit_seal_after']
package=L/delivery['package'];assert J.sha(package)==delivery['sha256']
assert J.load(D/'LOOKAHEAD_BEFORE.json')['result']['refusal']=='ValueError:R1_PROOF_NATIVE_ROUTING_REQUIRED'
assert J.load(D/'HOST_FLAG_BLOCKER.json')['tree_change_required'] is True
state=dict(status='STOP_SEALED_TREE_REQUIRED',GO=False,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    tree_seal=delivery['tree_seal'],tree_files_verified=n,kit_seal=kit,kit_changed=False,upload_diff=[],
    generator_resolver_scanner_upload_inventory_unchanged=True,base_package=delivery['package'],
    base_package_sha256=delivery['sha256'],new_package=None,
    earlier_package_sizes_unchanged=all((L/x['path']).stat().st_size==x['bytes'] for x in delivery['bases']),
    earlier_packages_note='No earlier archive was opened for writing; only the immediate base is rehashed here.',
    tmp_bytes=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()),
    report_lines=len((L/'out/BUILD21H_REPORT.md').read_text().splitlines()))
assert state['report_lines']<90 and state['tmp_bytes']<=200_000_000
J.write(D/'FINAL_STATE.json',state)
(D/'STATUS.md').write_text('STOP: the sealed full-intake reader lacks an opaque frame-host flag alias. GO=false.\n'
    'The report records the exact required source change. Kit, tree and upload inventory remain unchanged.\n'
    'Evidence: HOST_FLAG_BLOCKER.json, LOOKAHEAD_BEFORE.json and FINAL_STATE.json.\n')
print(json.dumps(state,indent=2))
