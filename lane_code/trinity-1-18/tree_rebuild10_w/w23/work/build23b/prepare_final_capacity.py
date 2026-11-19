from pathlib import Path
import gzip,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';A=L/'attic/build23b/capacity_first'
(D/'proofs').rename(A)
(D/'CAPACITY.json').rename(L/'attic/build23b/CAPACITY_FIRST.json')
records=[]
for p in sorted(A.glob('400/q/p/prepare_*/*/rows.sqlite')):
 raw=p.read_bytes();encoded=gzip.compress(raw,compresslevel=6,mtime=0);assert gzip.decompress(encoded)==raw
 original=hashlib.sha256(raw).hexdigest();p.write_bytes(encoded);target=p.with_suffix('.sqlite.gz');p.rename(target)
 records.append(dict(retained_path=str(target),sha256=original,bytes=len(raw),compressed_bytes=len(encoded)))
(D/'RETAINED_CAPACITY.json').write_text(json.dumps(records,indent=2)+'\n')
p=D/'capacity_final.py';s=p.read_text()
s=s.replace("config=N.write(root/'request_config.json',cfg)","selection=load(pinned(cfg['s1_routing']['selection']))\nN.s1_pool.prepare(selection['manifest'],D/'selected',cfg['remove_files'])\ncfg['s1_routing']['selection']=file_pin(D/'selected/receipt.json')\nconfig=N.write(root/'request_config.json',cfg)")
s=s.replace("donor=load(A/'600/h/config.json')", "donor=load(O/'600/request_config.json')")
p.write_text(s)
