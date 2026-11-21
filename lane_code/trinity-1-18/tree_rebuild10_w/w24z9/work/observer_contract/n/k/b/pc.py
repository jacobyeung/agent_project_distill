import subprocess,sys
from pathlib import Path
p=Path(__file__).with_name('gc.py')
r=subprocess.run([sys.executable,'-I','-s','-B',str(p)],check=True)
