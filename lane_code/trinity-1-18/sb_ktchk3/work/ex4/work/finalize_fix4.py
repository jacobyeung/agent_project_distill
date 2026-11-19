"""Run the unchanged finalizer with the new archive name."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
source=ROOT/'scripts/finalize_v3.py'
sha(__file__);sha(source)
text=source.read_text()
assert text.count('sb_ktfix3.tar')==5
text=text.replace('sb_ktfix3.tar','sb_ktfix4.tar')
exec(compile(text,str(source),'exec'),dict(__name__='__main__',__file__=str(source)))
