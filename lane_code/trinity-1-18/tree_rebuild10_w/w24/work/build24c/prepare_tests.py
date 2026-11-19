from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24c';B=L/'work/build24b'
for name in ('q','n'):
 for kind in ('new','legacy'):
  s=(B/f'guard_{name}_{kind}.py').read_text().replace(f"D=L/'work/build24b/guard_{name}'",f"D=L/'work/build24c/guard_{name}'")
  (D/f'guard_{name}').mkdir(exist_ok=True);(D/f'guard_{name}_{kind}.py').write_text(s)
s=(B/'lookahead.py').read_text().replace("D=L/'work/build24b'","D=L/'work/build24c'").replace("directory='b24b_'","directory='b24c_'")
(D/'lookahead.py').write_text(s)
s=(L/'work/build24/kit_tests.py').read_text()
s=s.replace("str(D/'scanners/n/environment21f.py')","str(L/'work/build24c/scanners/n/environment21f.py')")
s=s.replace("L/'work/build24b/naming24_q.py'","L/'work/build24c/naming24c_q.py'")
s=s.replace("J.write(D/'KIT_TESTS.json'","J.write(L/'work/build24c/KIT_TESTS.json'")
(D/'kit_tests.py').write_text(s)
# Keep original test results intact; these adapters change only evidence paths.
s=(L/'work/build24/resolver_tests.py').read_text().replace("O=L/'work/build24b/proofs/resolver600'","O=L/'work/build24c/proofs/resolver600'")
s=s.replace("J.write(D/'RESOLVER_TESTS.json'","J.write(L/'work/build24c/RESOLVER_TESTS.json'")
(D/'resolver_tests.py').write_text(s)
s=(L/'work/build24/resolver23_tests.py').read_text().replace("D=L/'work/build24/proofs/resolver23'","D=L/'work/build24c/proofs/resolver23'")
(D/'resolver23_tests.py').write_text(s)
