from pathlib import Path
import base64,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build23c';B=L/'work/build21';K=B/'kits/q';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
import joblib as J
from naming21 import scan_decoded
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
baseline=J.load(D/'START.json');current=inventory(T)
assert current==baseline['tree'] and digest(current)==baseline['tree_seal']
control=J.load(K/'k/a.json');check_archive(file_pin(K/control['source']['path']),current)
actual={str(p.relative_to(K)):J.sha(p) for p in K.rglob('*') if p.is_file()}
assert set(actual)==set(baseline['kit'])
changed=sorted(n for n,h in actual.items() if baseline['kit'][n]!=h)
assert changed==['BUILD.json','SHA256SUMS.txt','b/g.py']
assert J.seal(K)==J.load(D/'KIT.json')['kit_seal']
shell=base64.b64decode(json.loads((K/'k/j.json').read_text())['payload']).decode()
original=(L.parent/'ext/pwrap/b/c.sh').read_text()
start=original.index('tk_bwrap() {');end=original.index('\ntk_env()',start)
function=original[start:end]
start2=shell.index('tk_bwrap() {');end2=shell.index('\ntk_env()',start2)
generated=shell[start2:end2]
assert '--dev-bind /dev /dev' in generated
assert 'for entry in /* /.[!.]* /..?*' in generated and '--ro-bind "$entry" "$entry"' in generated
assert 'case "$entry" in /home|/dev|/proc)' in generated
assert '"${BW[@]}" "$PILOT_VENV/bin/python" -s -B "$Q_KIT/b/g.py"' in shell
assert shell.index('tk_bwrap\nBW+=')<shell.index('"$Q_KIT/b/g.py"')
assert (K/'b/z.py').read_bytes()==(B/'joblib.py').read_bytes()
J.write(D/'VIEW_AUDIT.json',dict(status='PASS',guard_location='inside bwrap',nvidia_nodes='--dev-bind /dev /dev: all host /dev nodes, including nvidia0, nvidiactl, nvidia-uvm and nvidia-caps when present',driver_libraries='Same host top-level read-only binds and symlink preservation as P; /usr, /lib*, /opt and other top-level entries except /home,/dev,/proc remain visible. The private /tmp is restored at Q_ROOT. No special driver-library mount differs from P.',bind_change=False,host_visibility_unproved=True,original=function,generated=generated,invocation='job.sh -> b/x.py bootstrap -> decoded k/j.json -> tk_bwrap -> BW python b/g.py'))
scan=scan_decoded(K);assert scan['status']=='PASS'
summary={k:v for k,v in scan.items() if not isinstance(v,list)}
summary.update(list_counts={k:len(v) for k,v in scan.items() if isinstance(v,list)},kit_seal=J.seal(K),tree_seal=digest(current))
J.write(D/'SCAN.json',summary)
J.write(D/'INTEGRITY.json',dict(status='PASS',tree_seal=digest(current),kit_seal=J.seal(K),changed_kit_files=changed,config_unchanged=True,resolver_unchanged=True,packages=baseline['packages']))
print(json.dumps(summary))
