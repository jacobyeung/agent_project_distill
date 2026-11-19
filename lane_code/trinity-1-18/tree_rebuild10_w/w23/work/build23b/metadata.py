from pathlib import Path
import ast,datetime,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23b';A=L/'attic/build23b';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
old=J.load(A/'UPLOADS.json');new=J.load(B/'UPLOADS.json');before={x['opaque_name']:x for x in old['files']};after={x['opaque_name']:x for x in new['files']}
known={v['sha256'] for v in old['files']};changes=[];uploads=[]
for name in sorted(set(before)|set(after)):
 a=before.get(name);b=after.get(name)
 if a and b and (a['sha256'],a['bytes'])==(b['sha256'],b['bytes']):continue
 changes.append(dict(name=name,before={k:a[k] for k in ('bytes','sha256')} if a else None,after={k:b[k] for k in ('bytes','sha256')} if b else None))
 if b:
  p=Path(b['local_path']);assert p.stat().st_size==b['bytes'] and J.sha(p)==b['sha256']
  assert b['sha256'] in known or b['bytes']<10_000_000
  uploads.append(dict(name=name,bytes=b['bytes'],sha256=b['sha256'],local_path=str(p)))
J.write(D/'UPLOAD_DIFF.json',dict(baseline_kit='bb04241ca4a7ad1a1873991b722fa64e29b01af86373529f0dd074aa0749b200',changes=changes,new_uploads=uploads))
J.write(L/'out/UPLOADS_NEW_23B.json',uploads)
cfg=J.load(K/'k/n.json');prior=J.load(A/'q/k/n.json')
for key in ('remove_files','routing_opener_init','r2_identity','scene_division','benchmark_scene_exclusions','dev_scene_exclusions','s1_routing','streams'):
 assert cfg.get(key)==prior.get(key),key
for key in ('wording_exclusion','room_authority','registry','component_rows'):
 assert cfg['r1_training'].get(key)==prior['r1_training'].get(key),key
baseline=J.load(A/'PACKAGE_MANIFEST.json')['files'];changed=[]
for name,v in baseline.items():
 if name.startswith('work/tree_r1/') and J.sha(L/name)!=v['sha256']:changed.append(name.removeprefix('work/tree_r1/'))
assert len(changed)==7,changed
for name in ('b/z.py','job.sh','b/a.py'):assert (K/name).read_bytes()==(A/'q'/name).read_bytes()
# Kit code copies the unchanged resolver implementation.
assert (K/'b/z.py').read_bytes()==(B/'joblib.py').read_bytes()
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import pinned
paths={x['sha256']:x['local_path'] for x in new['files']}
with scope(paths):
 new_audit=J.load(pinned(cfg['r1_training']['room_audit']))
 old_audit=J.load(pinned(prior['r1_training']['room_audit']))
 assert new_audit['store']==old_audit['store'] and new_audit['authority']==old_audit['authority']
 assert new_audit['remove_files']==old_audit['remove_files'] and new_audit['slices']=={}
package=L/'out/tree_rebuild_b23_40abf77b.tar';delivery=J.load(L/'work/build23/DELIVERY.json')
assert J.sha(package)==delivery['sha256']
J.write(D/'INTEGRITY.json',dict(status='PASS',GO=False,tree_changed_files=sorted(changed),resolver_bytes_unchanged=True,base_package_sha256=delivery['sha256'],base_package_bytes=package.stat().st_size,base_package_unchanged=True,removals_lineage_opener_and_identity_unchanged=True,store_room_certification_unchanged=True,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
print(json.dumps(dict(new_upload_files=len(uploads),new_upload_bytes=sum(x['bytes'] for x in uploads),largest=max(x['bytes'] for x in uploads))))
