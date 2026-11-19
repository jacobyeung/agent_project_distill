from pathlib import Path
import runpy
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
s=(D/'lookahead_run.py').read_text().replace('minimal23b','minimal23bf')
(D/'lookahead_run_final.py').write_text(s);runpy.run_path(str(D/'lookahead_run_final.py'),run_name='__main__')
