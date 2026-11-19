from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23b';A=L/'attic/build23b'
p=B/'OPERATOR.md';(A/'OPERATOR.md').write_bytes(p.read_bytes())
kit=json.loads((D/'KIT.json').read_text());uploads=json.loads((B/'UPLOADS.json').read_text());s=p.read_text()
s=s.replace('No routing envelope may be supplied under this declaration.', 'The central MINIMAL check refuses every active routing-slice binding before native row readers run.\n`row_slice_inputs`, `routing_inputs`, routing entries in `row_sources`, nonempty membership,\nand nonzero deferred card cells refuse by field and slice name. Only the two non-routing\nroom audit entries and an empty membership catalog remain in the active source metadata.')
s=s.replace('../../out/UPLOADS_NEW.json','../../out/UPLOADS_NEW_23B.json').replace('../build23/SCAN.json','../build23b/SCAN.json').replace('../build23/UPLOAD_DIFF.json','../build23b/UPLOAD_DIFF.json')
s=s.replace('Upload total: 137121851 bytes in 167 files',f"Upload total: {uploads['total_bytes']} bytes in {len(uploads['files'])} files")
s=s.replace('b4edc4750df4a0f87b1143d2bf6c98155a64fd81fd7a50e98029be7c6147be0e',kit['tree_seal']).replace('bb04241ca4a7ad1a1873991b722fa64e29b01af86373529f0dd074aa0749b200',kit['kit_seal'])
s=s.replace('../build23/rebuild_kit.py','../build23b/kit.py').replace('../build23/metadata.py','../build23b/metadata.py')
s=s.replace('The capacity script is `../build23/native23.py`;\nit reconstructs its own synthetic databases and model payloads, which the package omits.', 'The capacity script is `../build23b/capacity.py`;\nit reconstructs synthetic databases and model payloads, which the package omits. Retain any\nexisting proof output under attic before a fresh reconstruction. The final-tree replay and\nits exact scope are recorded in `../build23b/capacity_final.py` and `../build23b/FIXTURE.json`.')
s=s.replace('../../out/BUILD23_REPORT.md','../../out/BUILD23B_REPORT.md');p.write_text(s)
