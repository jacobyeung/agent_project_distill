"""Exercise scan1 against the existing local READY kit, without copying any kit."""
import hashlib
import subprocess
import sys
from pathlib import Path
from packet_config import PINS, fixture, render

w = Path(__file__).resolve().parent
ready = Path(sys.argv[1]).resolve()
assert ready.is_relative_to(w) and ready.name == 'derived_ready'
body = render((w/'scan_body.py').read_text())
body = body.replace("B=Path('"+PINS['bundle']+"');K=B.parent/'x_"+PINS['store']+"';H=B.parent/'x_3fdda0fb'",
                    'B=Path('+repr(str(fixture()))+');K=Path('+repr(str(ready))+');H=Path('+repr(str(w/'fixture_h'))+')')
result = subprocess.run([sys.executable, '-B', '-c', body], capture_output=True, text=True)
assert result.returncode == 0, result.stderr
(ready.parent/'scan_fixture.out').write_text(result.stdout)
assert 'PACKET '+PINS['identity']+' ARCHIVE '+PINS['outer']+' RUN '+PINS['run'] in result.stdout
assert 'MANIFEST '+hashlib.sha256((ready/'SHA256SUMS.txt').read_bytes()).hexdigest() in result.stdout
assert '-p general ' in result.stdout and '-p advanced ' in result.stdout
assert 'PENDING independent complete content scan' in result.stdout
assert 'https://storage.googleapis.com/upload/' not in result.stdout
print('PASS scan1 inventory: exact S2 packet, final manifest, both partitions, no session contents, independent scan remains required')
