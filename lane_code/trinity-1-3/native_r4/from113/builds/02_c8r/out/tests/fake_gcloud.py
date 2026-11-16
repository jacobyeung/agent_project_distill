"""Offline CLI fixture. Its backing store and command log stay in the build."""
import hashlib,json,os,sys
from pathlib import Path
root=Path(os.environ['C8R_CLOUD_STORE'])
root.mkdir(parents=True,exist_ok=True)
args=sys.argv[1:]
with (root/'calls.jsonl').open('a') as s:
 s.write(json.dumps(dict(argv=args,config=os.environ.get('CLOUDSDK_CONFIG')))+'\n')
def path(uri):
 assert uri.startswith('gs://cmu-gpucloud-jjyeung/q8/n2r/')
 name=uri.split('#')[0].split('/')[-2:]
 assert all(x and x not in ('.','..') for x in name)
 p=root/name[0]/name[1];p.parent.mkdir(parents=True,exist_ok=True)
 return p
if os.environ.get('C8R_CLOUD_FAIL'):raise SystemExit(7)
if args[:2]==['storage','cp']:
 path(args[3]).write_bytes(Path(args[2]).read_bytes())
elif args[:3]==['storage','objects','describe']:
 p=path(args[3]);print(json.dumps(dict(generation='invalid' if os.environ.get('C8R_CLOUD_BAD_META') else '73',size=p.stat().st_size)))
elif args[:2]==['storage','cat']:
 assert args[2].endswith('#73'), 'readback must be generation pinned'
 data=path(args[2]).read_bytes()
 if os.environ.get('C8R_CLOUD_CORRUPT'):data=b'x'+data[1:]
 sys.stdout.buffer.write(data)
else:raise SystemExit('Unsupported offline CLI invocation')
