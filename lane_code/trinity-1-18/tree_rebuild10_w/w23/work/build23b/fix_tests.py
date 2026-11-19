from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
p=D/'tests.py';s=p.read_text().replace("def pin(name,v):return write(R/(name+'.json'),v) or file_pin(R/(name+'.json'))","def pin(name,v):\n (R/(name+'.json')).write_text(json.dumps(v));return file_pin(R/(name+'.json'))")
s=s.replace("build.build(p,B/'inputs'", "build.build(p['path'],B/'inputs'")
p.write_text(s)
(D/'unit').rename(L/'attic/build23b/unit_first')
