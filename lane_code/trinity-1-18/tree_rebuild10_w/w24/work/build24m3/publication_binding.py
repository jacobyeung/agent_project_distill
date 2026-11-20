from common import *
s=(D/'cs.py').read_text()
s=s.replace("            write(Path(root)/('c5.json' if phase=='final' else 'd6.json'),output)","            (Path(root)/('c5.json' if phase=='final' else 'd6.json')).write_bytes(encoded(output))")
s=s.replace("    pin=write(Path(root)/('c5.json' if phase=='final' else 'd6.json'),output)","    path=Path(root)/('c5.json' if phase=='final' else 'd6.json')\n    path.write_bytes(encoded(output));pin=file_pin(path)")
s=s.replace("    live,_=location(Path(kit),root,os.environ['SLURM_JOB_ID'])\n    for stream in STREAMS:", "    live,_=location(Path(kit),root,os.environ['SLURM_JOB_ID'])\n    checked(live/'c4.json',file_pin(path)['sha256'])\n    for stream in STREAMS:")
replace(D/'cs.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/cs.py',s)
 for p in ('BUILD.json','SHA256SUMS.txt'):replace(k/p,(k/p).read_bytes())
 print(name,reseal(k))
