from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24'
s=(L.parent/'w23/work/build23/resolver_tests.py').read_text().replace("D=L/'work/build23'","D=L/'work/build24/proofs/resolver23'")
s=s.replace("sys.path[:0]=[str(B),str(L/'work/tree_r1')]","sys.path[:0]=[str(L/'work/build24'),str(B),str(L/'work/tree_r1')]")
s=s.replace('import joblib as J',"import joblib as J\nD.mkdir(parents=True,exist_ok=True)\nR.K=L/'work/build24/kits/q';R.D=D/'f';R.D.mkdir(exist_ok=True)")
s=s.replace("L/'attic/build23/joblib.py'","L/'work/build22/joblib.py'")
s=s.replace('import resolver21e as R\nimport joblib as J','import joblib as J\nimport resolver21e as R')
(D/'resolver23_tests.py').write_text(s)
