import sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root))
source=root/'verify_c600.py'
code=source.read_text().replace("W=H/'rehearsal';V=W/'verify';V.mkdir()", "W=H/'rehearsal';V=H/'rehearsal/link/fix2b/verify_p1cpu';V.mkdir()")
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
