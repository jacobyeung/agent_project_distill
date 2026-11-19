from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
for name in ('mutations','storage'):
    s=(L/f'work/build14/{name}14.py').read_text().replace('work/build14','work/build15').replace('test14.py','test15.py').replace('B14_PROOF','B15_PROOF')
    (B/f'{name}15.py').write_text(s)
s=(L/'work/build14/coverage14.py').read_text().replace("B=L/'work/build14'","B=L/'work/build15'")
s=s.replace('"B=L/\'work/build14\'"','"B=L/\'work/build15\'"')
s=s.replace("(B/'proofs',L/'work/build13/proofs',L/'work/build12/proofs')","(B/'proofs',L/'work/build14/proofs',L/'work/build13/proofs',L/'work/build12/proofs')")
s=s.replace("str(B/'coverage14.py')","str(B/'coverage15.py')")
(B/'coverage15.py').write_text(s)
