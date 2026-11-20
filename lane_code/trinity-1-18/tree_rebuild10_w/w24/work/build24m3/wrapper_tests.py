from common import *
import sqlite3,subprocess,shlex
F=D/'db_loop_fixture';F.mkdir();node=F/'node';out=F/'out';out.mkdir()
db=node/'dr/p/q/selection/rows.sqlite';db.parent.mkdir(parents=True)
with sqlite3.connect(db) as c:c.execute('create table rows(i integer)')
(out/'routing_selection.json').write_text('{}\n')
# Native helper hashes and searches a tiny real SQLite file, with a target differing only in the header.
raw=bytearray(db.read_bytes());raw[96:100]=(3040000).to_bytes(4,'big');target=hashlib.sha256(raw).hexdigest()
loop=(D/'db_loop.sh').read_text();script=F/'loop.sh'
script.write_text(loop+'\ntk_db_loop '+shlex.join([str(node),str(out),str(L/'out/dbb2.py')])+'\n')
env={**os.environ,'PATH':str(Path(sys.executable).parent)+':'+os.environ['PATH'],'DBB_TARGET':target}
r=subprocess.run(['/bin/bash',str(script)],capture_output=True,text=True,env=env,timeout=55)
(F/'native.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
value=J.load(out/'db_bytes.json');entry=value['files'][0]
assert entry['sha256']==J.sha(db) and entry['size']==db.stat().st_size
assert entry['head100_hex']==db.read_bytes()[:100].hex()
assert entry['body_sha256']==hashlib.sha256(db.read_bytes()[100:]).hexdigest()
assert entry['header_search']['found']==[dict(version=3040000,hex=(3040000).to_bytes(4,'big').hex())]
# Exercise the real shell loop with bounded stubs; no waiting in the fixture.
for name,body in [('retry','python3() { printf call\\n >> "$calls"; [[ $(wc -l < "$calls") -ge 3 ]]; }'),
                  ('cap','python3() { printf call\\n >> "$calls"; return 1; }'),
                  ('missing','python3() { return 99; }')]:
 calls=F/(name+'.calls');sleeps=F/(name+'.sleeps');calls.write_text('');sleeps.write_text('')
 missing=F/'missing';missing.mkdir(exist_ok=True)
 prefix='calls='+shlex.quote(str(calls))+'\nsleeps='+shlex.quote(str(sleeps))+'\n'+body+'\nsleep() { echo "$1" >> "$sleeps"; }\n'
 s=F/(name+'.sh');s.write_text(prefix+loop+'\ntk_db_loop '+shlex.join([str(node),str(missing if name=='missing' else out),'unused'])+'\n')
 r=subprocess.run(['/bin/bash',str(s)],capture_output=True,text=True)
 n=len(calls.read_text().splitlines());waits=sleeps.read_text().splitlines()
 if name=='retry':assert r.returncode==0 and n==3 and waits==['60']*2,(r.returncode,n,waits)
 else:assert r.returncode==1 and n==(180 if name=='cap' else 0) and waits==['60']*179
assert J.sha(L/'out/dbb2.py')=='a7cbfb9f3093ee50bf373838cd952405de190cb8b5dbcc29a0ab0aa1a48d06e5'
J.write(D/'WRAPPER_TESTS.json',dict(status='PASS',helper_unchanged=True,native_sqlite_hashes=True,native_header_search_processes=8,found=entry['header_search']['found'],retry_interval_seconds=60,max_attempts=180,fixture_waits='Stubbed; real loop body and native helper execute'))
print('Wrapper native db bytes, header search, retry, cap and missing selection PASS')
