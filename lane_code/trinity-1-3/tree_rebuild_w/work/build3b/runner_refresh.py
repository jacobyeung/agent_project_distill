"""Keep the storage checks exact while reducing repeated pathlib traversal overhead."""
from pathlib import Path
import json
import os
L=Path(__file__).resolve().parents[2]
source=(L/'work/build1/run_tests.py').read_text()
old="    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())"
new='''    total, pending = 0, [str(path)]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.is_file():
                    total += entry.stat().st_size
    return total'''
assert old in source
source=source.replace(old,new)
(L/'work/build3b/bounded_runner.py').write_text(source)
source=(L/'work/build2/run_tests.py').read_text().replace("work/build1/run_tests.py", "work/build3b/bounded_runner.py")
(L/'work/build3b/shared_runner.py').write_text(source)
source=(L/'work/build3/run_tests.py').read_text().replace("work/build2/run_tests.py", "work/build3b/shared_runner.py")
(L/'work/build3b/snapshot_runner.py').write_text(source)
source=(L/'work/build3b/run_tests.py').read_text().replace("work/build3/run_tests.py", "work/build3b/snapshot_runner.py")
(L/'work/build3b/run_tests.py').write_text(source)
namespace={'os':os}
exec('def size(path):\n'+new,namespace)
value={}
for path in (L/'work/tmp',L):
    before=sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
    after=namespace['size'](path)
    value[str(path)]=dict(pathlib_bytes=before,scandir_bytes=after)
    # A running test may write between measurements; equality is checked after the suite.
(L/'out/B3B_STORAGE_WALK.json').write_text(json.dumps(value,indent=2)+'\n')
