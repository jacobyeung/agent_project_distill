#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
python3 -B - <<'PYCODE'
import hashlib,json,os,stat
from pathlib import Path
b=Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/builders_p5_x65quotl/remote/i_7f1589c1');k=b.parent/'x_7f1589c1'
assert hashlib.sha256((b/'p.tar').read_bytes()).hexdigest()=='6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888'
assert json.loads((b/'BINDING.json').read_text())['config_identity']=='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74'
assert k.is_dir() and not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
raw=b'{"q8/8865619b/05b8ac69_m400.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_0", "q8/8865619b/05b8ac69_m400.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_1", "q8/8865619b/05b8ac69_m400.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_2", "q8/8865619b/05b8ac69_m400.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_3", "q8/8865619b/05b8ac69_m600.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_4", "q8/8865619b/05b8ac69_m600.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_5", "q8/8865619b/05b8ac69_m600.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_6", "q8/8865619b/05b8ac69_m600.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_7", "q8/8865619b/05b8ac69_mstop.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_8", "q8/8865619b/05b8ac69_mstop.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_9", "q8/8865619b/05b8ac69_mstop.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_10", "q8/8865619b/05b8ac69_mstop.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_11", "q8/8865619b/05b8ac69_mstopB.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_12", "q8/8865619b/05b8ac69_mstopB.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_13", "q8/8865619b/05b8ac69_mstopB.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_14", "q8/8865619b/05b8ac69_mstopB.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_15", "q8/8865619b/05b8ac69_mstopC.tar.part00-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_16", "q8/8865619b/05b8ac69_mstopC.tar.part01-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_17", "q8/8865619b/05b8ac69_mstopC.tar.part02-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_18", "q8/8865619b/05b8ac69_mstopC.tar.part03-of-04": "https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_19"}'
expected='7a249e1ca10687e8c9804d6d00311989ab8d05208129d28ad13b5151a035fbbf'
assert hashlib.sha256(raw).hexdigest()==expected
d=json.loads(raw);want=set((b/'e.txt').read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
with (k/'sess.json').open('xb') as f:f.write(raw)
(k/'sess.json').chmod(0o600)
assert hashlib.sha256((k/'sess.json').read_bytes()).hexdigest()==expected
print('PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld')
PYCODE
