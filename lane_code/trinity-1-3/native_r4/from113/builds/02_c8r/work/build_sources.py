from pathlib import Path
import hashlib,json,re
B=Path(__file__).resolve().parents[1]
R=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'
old=B.parent/'01_c8/out/c8/sources/sj/orch_cd/evalx/work/milestone'
accepted=(B/'in/launcher/orchard_results.py').read_text()
upload=accepted[accepted.index('class UploadError'):accepted.index('\ndef publish')]
upload=upload.replace("def upload(local,token,names=('result.tar.gz','EXIT.json')):",
                      "def upload(local,token,names=('result.tar.gz','EXIT.json'),cloud_config=None):")
upload=upload.replace('CLOUDSDK_CONFIG=CLOUD_CONFIG','CLOUDSDK_CONFIG=cloud_config or CLOUD_CONFIG')
base=(old/'orchard_results.py').read_text()
verify=base[base.index('def verify('):]
verify=verify.replace('archive.stat().st_size > ARCHIVE_LIMIT',
                      "archive.stat().st_size > mode_limit(receipt.get('mode', 'pilot'))-EXIT_RESERVE")
header='''"""Bounded independent returns, ported from the accepted lane transport."""
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_save as S

AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/n2r')
GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/n2r'
CLOUD_CONFIG = '/project/community/jjyeung/gcloud'
READ_LIMIT = 300_000_000
POOL_LIMIT = 1024**3
EXIT_RESERVE = 16*1024
ARCHIVE_LIMIT = READ_LIMIT-EXIT_RESERVE

'''
common=base[base.index('def sha('):base.index('def publish(')]
(R/'orchard_results.py').write_text(header+common+upload+'\n'+verify+'\n'+(B/'work/transport_body.py').read_text())
p=R/'orchard_launcher.py';text=(old/'orchard_launcher.py').read_text()
start,end=text.index('def fetch('),text.index('\ndef main():')
text=text[:start]+'''def fetch(destination):
    import orchard_results as R
    destination = Path(destination)
    config = json.loads((destination/'CONFIG.json').read_text())
    submission = json.loads((destination/'SUBMISSION.json').read_text())
    return R.fetch_return(config, submission, destination, remote)

'''+text[end:];p.write_text(text)
p=R/'orchard_native/native_job.py';text=(old/'orchard_native/native_job.py').read_text()
text=text.replace('    try:\n        context(root, config)',
    '    try:\n        evidence["pool_write_test"] = R.write_test(R.AUTHORIZED_POOL, config["token"])\n        context(root, config)')
text=text.replace('config["plan_sha256"], code)',
    'config["plan_sha256"], code,\n                               mode=config["mode"], cloud_config=config["assets"]["gcloud_config"])')
p.write_text(text)
p=R/'orchard_native/native_metrics.py'
text=(old/'orchard_native/native_metrics.py').read_text().replace('RETURN_LIMIT = 256*1024**2-16*1024','RETURN_LIMIT = 300_000_000-16*1024');p.write_text(text)
p=R/'orchard_native/native_local_check.py';text=(old/'orchard_native/native_local_check.py').read_text()
text=text.replace('SCHEMA = "evalx-native-local-input-check-v2"',
    'PACKAGING |= {str(C.LOGICAL_ROOT / name) for name in ("orchard_results.py", "orchard_launcher.py")}\nSCHEMA = "evalx-native-local-input-check-v2"')
p.write_text(text)
core=('orchard_launcher.py','orchard_job.py','orchard_stage.py','orchard_results.py','chain_save.py','stdout_transfer.py','ORCHARD_ASSETS.json')
pins={str(Path('/scratch/jjyeung/orch_cd/evalx/work/milestone')/n):hashlib.sha256((R/n).read_bytes()).hexdigest() for n in core}
digest=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()
p=R/'orchard_native/native_launcher.py';text=(old/'orchard_native/native_launcher.py').read_text()
text=re.sub(r'DIRECT_DIGEST = "[a-f0-9]+"','DIRECT_DIGEST = "'+digest+'"',text)
text=text.replace('return_bytes=256*1024**2, pool_bytes=1024**3','return_bytes=100_000_000 if mode == "pilot" else 300_000_000, pool_bytes=1024**3')
p.write_text(text)
print(json.dumps(dict(direct_launcher_digest=digest)))
