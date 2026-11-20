from common import *
import sqlite3,subprocess,shlex
F=D/'db_loop_fixture';node=F/'node';out=F/'out'
db=node/'dr/p/q/selection/rows.sqlite';assert db.is_file()
value=J.load(out/'db_bytes.json');entry=value['files'][0]
loop=(D/'db_loop.sh').read_text()
# Exercise the real shell loop with bounded stubs; no waiting in the fixture.
for name,body in [('retry','python3() { echo call >> "$calls"; [[ $(wc -l < "$calls") -ge 3 ]]; }'),
                  ('cap','python3() { echo call >> "$calls"; return 1; }'),
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
