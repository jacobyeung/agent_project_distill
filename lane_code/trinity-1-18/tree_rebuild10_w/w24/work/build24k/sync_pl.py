from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
for k in (L/'work/build24/kits/q',L/'work/build24/kits/n',L/'out/kit_n_go'):(k/'b/pl.py').write_bytes((D/'pl.py').read_bytes())
p=D/'sequence_final.py';p.write_text(p.read_text().replace('sequence_sealed','sequence_delivery'))
p=D/'integration_tests.py';p.write_text(p.read_text().replace("D/'integration_verified'","D/'integration_delivery'"))
