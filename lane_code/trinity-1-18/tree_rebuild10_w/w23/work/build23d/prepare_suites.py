from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build23d'
text=(L/'work/build23c/suites.py').read_text().replace("D=L/'work/build23c'","D=L/'work/build23d'").replace("B/'test21g.py'","D/'test_wrapper.py'").replace("'b23c_'","'b23d_'")
(D/'suites.py').write_text(text)
text=(L/'work/build23c/check.py').read_text().replace("D=L/'work/build23c'","D=L/'work/build23d'")
(D/'check.py').write_text(text)
