from common import *
s=(L/'work/build24m4k/package_k.py').read_text()
s=s.replace('build24m4k','build24m4n').replace('24M4K','24M4N').replace('b24m4k','b24m4l')
s=s.replace("source=W/'w24j/out/tree_rebuild_b24m4j_6a1635a0.tar'", "source=W/'w24k/out/tree_rebuild_b24m4k_2cd5a46f.tar'")
s=s.replace('b85621108f1f77772731c3a38b19672621fe73f139adc5d81613d9dd03a2e386','9e4d59ef5a75de02fb2ad9cc21616f833b96e677a9c57c0be7ad566cfa4ef918')
start=s.index('inner=dict(');end=s.index('\nmanifest=',start)
s=s[:start]+'''inner=dict(schema='build24m4n-delivery-v1',status='LOCAL_BUILD_AND_FIXTURES_PASS',
 tree_patch='out/TREE_CHANGE_24M4K.patch',tree_patch_applied=True,production_executed=False,
 qualification=validation['qualification'],package='out/'+name,package_seal=seal,
 base_archive=dict(path=str(source),sha256=expected_source),tree_sha256=validation['tree_sha256'],
 kits=validation['kits'],n_go_identity=validation['n_go_identity'],validation='work/build24m4n/VALIDATION.json',
 report='out/BUILD24M4N_REPORT.md',CPU_usage='out/RCJ_USAGE.md',uploads='out/UPLOADS_24M4N.json',
 upload_list='out/UPLOADS_24M4N.list',GO_delta='out/UPLOADS_24M4N_GO.json',GO=False,GO_template='out/kit_n_go',
 uploaded=False,launched=False,local_upload_files=up['total_files'],local_upload_bytes=up['total_bytes'],
 original_members=len(original),original_members_unchanged=same,preserved_originals=preserved,
 archive_compression='xz; tar auto-detects despite .tar suffix',
 archive_hash_record='External delivery adds archive checksum, verified member count and final storage.',disk_cap_bytes=LIMIT)'''+s[end:]
s=s.replace("'w:xz',preset=6","'w:xz',preset=3")
(D/'package_l.py').write_text(s)
print('Package script prepared; all base members and original bytes must be retained')
