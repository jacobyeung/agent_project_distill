from pathlib import Path
import sys,types,inspect
sys.path.insert(0,sys.argv[1])
from common228 import install_imports
root=Path(sys.argv[1]);install_imports(root/'A4/src')
from e2e_reader import parity
from h1eval.h10 import launch,parity_adapter
from observe228 import install
original=parity.make_real
state=install(parity,launch,None,None,None,None,enabled=True)
for i in range(2):
    result=launch.reader_factory(root/'A4/src/b')
    assert result is parity_adapter.make_capped_real
    assert Path(inspect.getsourcefile(result)).name=='parity_adapter.py'
assert parity.make_real is not original
state['restore']()
assert parity.make_real is original
print('sealed resolver and maker binding unchanged')
