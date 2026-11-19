from pathlib import Path
import os,json,hashlib,gzip,io,tarfile
R=Path(__file__).resolve().parent;W=R.parent
H='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'
# Relocate copied fixture links without deleting anything.
for root,dirs,files in os.walk(R):
 for n in dirs+files:
  p=Path(root)/n
  if p.is_symlink() and '/out2/' in os.readlink(p):
   target=os.readlink(p).replace('/out2/','/out3/');p.rename(p.with_name(p.name+'.r2_link'));p.symlink_to(target)
# Localize executable gate fixtures, never production payload sources.
for root,dirs,files in os.walk(R/'gates'):
 dirs[:]=[d for d in dirs if d not in ('src','tmp','checks') and not (Path(root)/d).is_symlink()]
 for n in files:
  p=Path(root)/n
  if p.suffix in ('.py','.json') and not p.is_symlink():
   s=p.read_text();s=s.replace(str(W/'out2'),str(R));p.write_text(s)
for label in ('A','B'):
 d=R/label;p=d/'fill_export.py';s=p.read_text()
 s=s.replace("MEMBERS = dict", "REVIEWED_OBJECT = 'q8/8865619b/673bc60f_m200.tar'\nREVIEWED_ARCHIVE_BYTES = 21583032320\nREVIEWED_ARCHIVE_SHA256 = '"+H+"'\n\nMEMBERS = dict")
 s=s.replace("    return cfg['export_binding']", "    binding = dict(cfg['export_binding'])\n    binding.update(archive_bytes=REVIEWED_ARCHIVE_BYTES, archive_sha256=REVIEWED_ARCHIVE_SHA256)\n    return binding")
 s=s.replace("def bind_review(a, export, artifact, archive, prep, binding):\n", """def receipt_review(done):
    fields = Path(done).read_text().split()
    if fields != [REVIEWED_OBJECT, str(REVIEWED_ARCHIVE_BYTES), REVIEWED_ARCHIVE_SHA256]:
        raise ValueError('Reviewed whole-tar receipt differs')


def bind_review(a, export, artifact, archive, prep, binding):
    # These constants are sealed by the delivery manifest, independent of caller input.
    if (a.object != REVIEWED_OBJECT or archive.get('sha256') != REVIEWED_ARCHIVE_SHA256
            or sum(p['bytes'] for p in archive.get('parts', [])) != REVIEWED_ARCHIVE_BYTES):
        raise ValueError('Reviewed whole-tar identity differs')
    for key, expected in [('archive_bytes', REVIEWED_ARCHIVE_BYTES),
                          ('archive_sha256', REVIEWED_ARCHIVE_SHA256)]:
        if key in binding and binding[key] != expected:
            raise ValueError('Reviewed export binding differs: '+key)
""")
 s=s.replace("    binding=reviewed_binding()", "    binding=reviewed_binding()\n    receipt_review(a.done)")
 p.write_text(s);(d/'package/a/4.py').write_text(s)
 p=d/'READ_PLAN.json';v=json.loads(p.read_text());v['export_binding'].update(archive_bytes=21583032320,archive_sha256=H);v['export_identity_seal']='Delivery PACKAGE.json pins a/4.py; payload 9.json remains byte-identical.';p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
 p=d/'o_pullfill.sh';s=p.read_text()
 if label=='A':
  s=s.replace("f[2].startswith('795ef9ef')", "f[2]=='"+H+"'").replace('Completion receipt differs from the R2 handoff','Completion receipt differs from the reviewed export')
  s=s.replace('gsutil -q cp', 'gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp')
 p.write_text(s)
 p=d/'o_fetch.sh';s=p.read_text().replace('3.py fetch --return-token "$RET" --out "$P/a/f"','"$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"');p.write_text(s)
