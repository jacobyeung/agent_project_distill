from pathlib import Path
import tarfile,hashlib,json
root=Path(__file__).resolve().parents[1]; archive=root/'out/sb_cafix.tar'; sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
with tarfile.open(archive) as t:
 for m in t.getmembers():
  if not m.isfile() or Path(m.name).parts[0] not in ('kit_v2','in','out'):continue
  p=root/m.name
  ah=sha(t.extractfile(m).read()); wh=sha(p.read_bytes()) if p.is_file() else None
  rows.append(dict(path=m.name,archive_sha256=ah,workspace_sha256=wh,equal=ah==wh))
result=dict(command='python -B work/verify_archive.py',files=rows,mismatches=[x['path'] for x in rows if not x['equal']],input_sha256={str(archive):sha(archive.read_bytes()),str(Path(__file__)):sha(Path(__file__).read_bytes())})
(root/'out/check/ARCHIVE_ALL.json').write_text(json.dumps(result,indent=2)+'\n')
print(len(rows),'archive files compared; mismatches:',result['mismatches'])
