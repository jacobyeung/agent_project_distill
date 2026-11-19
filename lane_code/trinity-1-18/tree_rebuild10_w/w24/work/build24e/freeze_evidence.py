from pathlib import Path
import gzip,json,hashlib,sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";record=json.loads((D/"COMPRESSED_EVIDENCE.json").read_text())
folders=[D/"proofs",D/"resolver",D/"sequence",L/"attic/build24e/generated_order",L/"attic/build24e/generated_pretraining",L/"attic/build24e/generated_before_extended",L/"attic/build24e/sequence_q_p",L/"attic/build24e/sequence_n_p"]
if len(sys.argv)>1:folders.extend([D/"sequence_final",D/"go",D/"generated"])
selected=[p for folder in folders for p in folder.rglob("*") if p.is_file() and not p.is_symlink()]
selected += [D/"PATH_INVENTORY.json"]
if len(sys.argv)>1:selected += list(D.glob("SCAN_*.json"))
for p in selected:
 if not p.exists() or p.stat().st_size<50000 or p.suffix==".gz":continue
 raw=p.read_bytes();z=gzip.compress(raw,6,mtime=0)
 if len(z)>=len(raw):continue
 target=p.with_name(p.name+".gz");assert not target.exists();p.write_bytes(z);p.rename(target)
 record.append(dict(path=str(p.relative_to(L)),compressed=str(target.relative_to(L)),bytes=len(raw),gzip_bytes=len(z),sha256=hashlib.sha256(raw).hexdigest()))
(D/"COMPRESSED_EVIDENCE.json").write_text(json.dumps(record,indent=2)+"\n")
print("lossless fixture evidence",len(record),"saved",sum(r["bytes"]-r["gzip_bytes"] for r in record),flush=True)
