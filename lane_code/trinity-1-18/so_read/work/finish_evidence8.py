from pathlib import Path
import hashlib,json
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
p=L/'work/gate_integration8.py';s=p.read_text().replace('from pathlib import Path','from pathlib import Path\nimport torch\ntorch.set_num_threads(8)');p.write_text(s)
p=L/'work/write_report8.py';s=p.read_text().replace('based on about 32.6 GB of expanded inputs plus tar headers.','based on **32,606,120,583 expanded bytes read from the six archives declared in the supplied a10b_pins/1.json**, plus tar headers ([source pin](checks/ARCHIVE_ESTIMATE8.json)).')
s=s.replace("work/share_storage8_more.py  # two bounded passes','storage8.txt')", "work/share_storage8_more.py  # first additional pass\\nbash work/cpu.sh work/share_storage8_more.py  # second additional pass\\nbash work/cpu.sh work/share_known8.py','storage8.txt')")
p.write_text(s)
provenance=json.loads((O/'operations/DEFAULT_EXPORT_PROVENANCE.json').read_text());source=Path(provenance['source'])/'1.json';raw=source.read_bytes();value=json.loads(raw)
record=dict(source=str(source),sha256=hashlib.sha256(raw).hexdigest(),archive_count=len(value['archives']),declared_expanded_bytes=sum(a['expanded_bytes'] for a in value['archives']),estimated_tar_bytes=33_000_000_000,basis='Declared expanded inputs plus tar headers; admitted symlinks remain links. Metadata total is read, archive size is estimated; no production archive measured.')
(O/'checks/ARCHIVE_ESTIMATE8.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print('Pinned expanded-input metadata and labelled archive estimate.')
