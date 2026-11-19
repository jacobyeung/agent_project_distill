from pathlib import Path
import runpy
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
s=(L/'work/build23/suites.py').read_text().replace("D=L/'work/build23'", "D=L/'work/build23b'").replace("'b23_'+name", "'b23b_'+name")
(D/'suites.py').write_text(s);runpy.run_path(str(D/'suites.py'),run_name='__main__')
