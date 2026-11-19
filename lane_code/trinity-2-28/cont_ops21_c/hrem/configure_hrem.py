"""Write parameterized scripts for timeout 300 bash ossh.sh 'bash -s' < script."""
import argparse
import shlex
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for n in ('parent','stage','step','out'):p.add_argument('--'+n,required=True)
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
header='export '+ ' '.join(n.upper()+'='+shlex.quote(getattr(a,n)) for n in ('parent','stage','step'))+'\n'
for action in ('build','place_fill','cpu','sub','fetch'):
    name='o_'+action+'_hrem.sh'
    (out/name).write_text(header+(Path(__file__).resolve().parent/name).read_text())
