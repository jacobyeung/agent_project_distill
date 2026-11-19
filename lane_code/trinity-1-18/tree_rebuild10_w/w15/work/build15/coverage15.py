from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
s=(L/'work/build13/coverage13.py').read_text()
s=s.replace("B=L/'work/build13'","B=L/'work/build15'")
s=s.replace("(B/'proofs',L/'work/build12/proofs')","(B/'proofs',L/'work/build14/proofs',L/'work/build13/proofs',L/'work/build12/proofs')")
s=s.replace("q=B/'prior12'/name","q=L/'work/build13/prior12'/name")
exec(compile(s,str(B/'coverage15.py'),'exec'))
