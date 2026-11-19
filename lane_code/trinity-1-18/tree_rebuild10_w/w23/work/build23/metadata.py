from pathlib import Path
import ast,datetime,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23';K=B/'kits/q';A=L/'attic/build23'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
old=J.load(A/'UPLOADS.json');new=J.load(B/'UPLOADS.json')
before={x['opaque_name']:x for x in old['files']};after={x['opaque_name']:x for x in new['files']}
known={x['sha256'] for x in old['files']};changes=[];uploads=[]
for name in sorted(set(before)|set(after)):
    a=before.get(name);b=after.get(name)
    if a and b and (a['sha256'],a['bytes'])==(b['sha256'],b['bytes']):continue
    changes.append(dict(name=name,before={k:a[k] for k in ('bytes','sha256')} if a else None,after={k:b[k] for k in ('bytes','sha256')} if b else None))
    if b:
        path=Path(b['local_path']);assert path.stat().st_size==b['bytes'] and J.sha(path)==b['sha256']
        available='same bytes in build21g upload inventory' if b['sha256'] in known else 'new small local upload'
        assert b['sha256'] in known or b['bytes']<10_000_000
        uploads.append(dict(name=name,bytes=b['bytes'],sha256=b['sha256'],local_path=str(path),availability=available))
J.write(D/'UPLOAD_DIFF.json',dict(baseline='../w21/out/tree_rebuild_b21g_2f9a23be.tar:work/build21/UPLOADS.json',before_bytes=old['total_bytes'],after_bytes=new['total_bytes'],changes=changes,new_uploads=uploads))
J.write(L/'out/UPLOADS_NEW.json',uploads)
cfg=J.load(K/'k/n.json');prior=J.load(A/'q/k/n.json')
assert cfg['remove_files']==prior['remove_files']
assert cfg['routing_opener_init']==prior['routing_opener_init']=='keep'
assert cfg['r2_identity']['init']['step']==544
assert cfg['r1_training']['wording_exclusion']==prior['r1_training']['wording_exclusion']
def functions(p):
    s=p.read_text();lines=s.splitlines(True)
    return {n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
old_functions=functions(A/'joblib.py');new_functions=functions(B/'joblib.py')
identities=['small_archive','metadata_at','metadata_closure','export_identity','identities']
assert all(old_functions[n]==new_functions[n] for n in identities)
def scanner_rules(path):
    tree=ast.parse(path.read_text())
    tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='SOURCE_SEALS' for t in n.targets))]
    return ast.dump(tree,include_attributes=False)
assert scanner_rules(A/'naming21.py')==scanner_rules(B/'naming21.py')
base_manifest=J.load(A/'PACKAGE_MANIFEST.json')['files']
unchanged=['student_pilot/job_env.py','student_pilot/r2_intake.py','student_pilot/r2_materialize.py','student_pilot/r1_components.py','student_pilot/r1_handover.py','student_pilot/r1_persisted.py','student_pilot/r2_openers.py']
for name in unchanged:assert J.sha(L/'work/tree_r1'/name)==base_manifest['work/tree_r1/'+name]['sha256']
J.write(D/'INTEGRITY.json',dict(status='PASS',GO=False,kit_seal=J.seal(K),tree=J.load(L/'out/TREE_SEAL.json'),
    unchanged_tree_files=unchanged,resolver_identity_functions_unchanged=identities,scanner_rules_unchanged=True,
    removal_order_and_pins_unchanged=True,wording_exclusion_unchanged=True,lineage_step=544,opener='keep',timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
J.write(B/'FINAL_KITS.json',dict(status='PASS',GO=False,tree_seal=J.load(L/'out/TREE_SEAL.json')['tree_sha256'],kits={'q':J.load(K/'BUILD.json')},
    decoded_scan=J.load(D/'SCAN.json'),upload_bytes=new['total_bytes'],upload_files=len(new['files']),
    inherited_kit_note='The inherited r1 kit retains its build-21g source seal; build 23 certifies kit q only.'))
J.write(D/'STATUS.json',dict(GO=False,phase='capacity fixture and final validation',new_upload_files=len(uploads),new_upload_bytes=sum(x['bytes'] for x in uploads),kit_seal=J.seal(K)))
print(json.dumps(dict(new_upload_files=len(uploads),new_upload_bytes=sum(x['bytes'] for x in uploads),largest_new_upload=max(x['bytes'] for x in uploads),kit_seal=J.seal(K))))
