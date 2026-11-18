#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,os,stat
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_6f8ed106');k=b.parent/'x_6f8ed106'
assert k.is_dir() and not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
raw=b'{"q8/8865619b/78d0a06c_m100.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_0", "q8/8865619b/78d0a06c_m100.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_1", "q8/8865619b/78d0a06c_m100.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_2", "q8/8865619b/78d0a06c_m100.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_3", "q8/8865619b/78d0a06c_m200.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_4", "q8/8865619b/78d0a06c_m200.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_5", "q8/8865619b/78d0a06c_m200.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_6", "q8/8865619b/78d0a06c_m200.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_7", "q8/8865619b/78d0a06c_mstop.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_8", "q8/8865619b/78d0a06c_mstop.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_9", "q8/8865619b/78d0a06c_mstop.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_10", "q8/8865619b/78d0a06c_mstop.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_11", "q8/8865619b/78d0a06c_mstopB.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_12", "q8/8865619b/78d0a06c_mstopB.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_13", "q8/8865619b/78d0a06c_mstopB.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_14", "q8/8865619b/78d0a06c_mstopB.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_15", "q8/8865619b/78d0a06c_mstopC.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_16", "q8/8865619b/78d0a06c_mstopC.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_17", "q8/8865619b/78d0a06c_mstopC.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_18", "q8/8865619b/78d0a06c_mstopC.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_19"}'
expected='d936bff0afdbdb6cac4ac4855c5ae8e12918ca02cc29cbdb68b8a3738b80fe92'
assert hashlib.sha256(raw).hexdigest()==expected
d=json.loads(raw);want=set((b/'e.txt').read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
with (k/'sess.json').open('xb') as f:f.write(raw)
(k/'sess.json').chmod(0o600)
assert hashlib.sha256((k/'sess.json').read_bytes()).hexdigest()==expected
print('PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld')
PYCODE
