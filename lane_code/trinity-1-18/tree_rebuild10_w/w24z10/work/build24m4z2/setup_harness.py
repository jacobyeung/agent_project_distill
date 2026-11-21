from pathlib import Path
import shutil
J=Path.cwd();W=J/'work/enospc2'
shutil.copytree(J/'out/kit_n_go',W/'kit')
for n in ('bin','tmp','mnt','node','logs','sink'):(W/n).mkdir(exist_ok=True)
(W/'bin/python3').write_text('#!/bin/bash\nexec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TEST_W/runtime.py" "$@"\n')
(W/'bin/python3').chmod(0o755)
(W/'j2_helper_new.py').write_text((J/'out/jn2.sh').read_text().split("<<'PYJ2'\n",1)[1].split('\nPYJ2',1)[0])
