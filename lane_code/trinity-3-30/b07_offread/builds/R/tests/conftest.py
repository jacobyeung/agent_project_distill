
# Every test process and child uses a fresh, synthetic build secret.
import os, tempfile
from pathlib import Path
Path('/dev/shm/b07_n7').mkdir(exist_ok=True)
_fixture_root=Path(tempfile.mkdtemp(prefix='a',dir='/dev/shm/b07_n7'))
_fixture_secret=_fixture_root/'secret'
_fixture_secret.write_text('37'*32)
_fixture_secret.chmod(0o600)
os.environ['A0_BUILD_SECRET_FILE']=str(_fixture_secret)
