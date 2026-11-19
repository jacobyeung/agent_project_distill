"""H1 read configuration over the reader lane's single generator."""
import json
import os
import sys
from pathlib import Path

K = Path(__file__).resolve().parents[1]
READER = K/'h1eval/reader_core'
for path in (str(READER), str(K/'tree')):
    if path not in sys.path:sys.path.insert(0, path)

# The reserve checker imports student_pilot modules. Select the reviewed native
# tree before that happens, so a real parity run never mixes two trainer trees.
settings_path = os.environ.get('H10_SETTINGS')
for i, arg in enumerate(sys.argv):
    if arg == '--settings' and i+1 < len(sys.argv):settings_path = sys.argv[i+1]
    elif arg.startswith('--settings='):settings_path = arg.split('=',1)[1]
if settings_path is None and '--reader-root' in sys.argv:
    settings_path = '/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/settings_bw.json'
if settings_path and Path(settings_path).is_file():
    settings = json.loads(Path(settings_path).read_text())
    if settings.get('tree'):
        tree = Path(settings['tree']).resolve()
        if not (tree.is_relative_to('/scratch') or tree.is_relative_to('/dev/shm')):
            raise ValueError('Stage the native tree on /scratch or /dev/shm')
        sys.path.insert(0, str(tree))
        import student_pilot
        if not Path(student_pilot.__file__).resolve().is_relative_to(tree):
            raise ValueError('Native tree already imported from another root')
        # Only kit-specific modules absent from the sealed tree (h1_r0) use this fallback.
        student_pilot.__path__.append(str(K/'tree/student_pilot'))
