"""Exercise the carried patch on local bundle copies and reject divergent inputs."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1]
out=H/'evidence/fix5_patch';out.mkdir(mode=0o700)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={}
def fixture(label):
    o=out/label;o.mkdir(mode=0o700);b=o/'i_1be16f28';b.mkdir(mode=0o700)
    for p in (H/'payload').iterdir():
        if p.is_file():
            source=H/'evidence/fix5_before/payload'/p.name if p.name in ('g.sh','sums.txt') else p
            # Only the two patch targets are mutable in this fixture.
            if p.name in ('g.sh','sums.txt'): (b/p.name).write_bytes(source.read_bytes())
            else:os.link(source,b/p.name)
    (b/'p').mkdir();(b/'p/evidence').write_text('prepared')
    (b/'e').mkdir();(b/'e/evidence').write_text('reproduced')
    (b/'e.json').write_text('{"status":"PASS"}')
    script=(H/'build/g_patch.sh').read_text().replace('/project/community/jjyeung/okh7/i_1be16f28',str(b))
    sh=o/'patch.sh';sh.write_text(script)
    return b,sh

def snapshot(b):return {str(p.relative_to(b)):sha(p) for p in b.rglob('*') if p.is_file()}
def run(b,sh,label,expected):
    p=subprocess.run(['/bin/bash',str(sh)],capture_output=True,text=True)
    (out/(label+'.log')).write_text(p.stdout+p.stderr)
    assert (p.returncode==0)==expected,(label,p.stderr)
    records[label]=p.returncode

b,sh=fixture('good');before=snapshot(b);run(b,sh,'valid_old_bytes',True);after=snapshot(b)
assert {n for n in before if before[n]!=after[n]}=={'g.sh','sums.txt'}
assert set(after)-set(before)=={'g.sh.r4','sums.txt.r4'}
for name in ('g.sh','sums.txt'):
    assert after[name]==sha(H/'payload'/name) and after[name+'.r4']==before[name]
run(b,sh,'repeat_refused',False);assert snapshot(b)==after
for name in ('g.sh','sums.txt'):
    b,sh=fixture('bad_'+name);(b/name).write_bytes(b'altered')
    before=snapshot(b);run(b,sh,'altered_'+name,False);assert snapshot(b)==before
b,sh=fixture('backup');(b/'sums.txt.r4').write_text('retained')
before=snapshot(b);run(b,sh,'backup_refused',False);assert snapshot(b)==before
b,sh=fixture('gate');(b/'gate.json').write_text('{}')
before=snapshot(b);run(b,sh,'existing_gate_refused',False);assert snapshot(b)==before
b,sh=fixture('corrupt');s=sh.read_text();needle="'data': '";i=s.index(needle)+len(needle);sh.write_text(s[:i]+('A' if s[i]!='A' else 'B')+s[i+1:])
before=snapshot(b);run(b,sh,'embedded_corruption_refused',False);assert snapshot(b)==before
# Downstream entrypoints use the patched sums and derive their external records from it.
sums={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (H/'payload/sums.txt').read_text().splitlines()}
assert sums['g.sh']==sha(H/'payload/g.sh')
for n in ('z.sh','s.sh'):
    text=(H/'payload'/n).read_text();assert text.index('sha256sum -c sums.txt')<text.index('python3')
r=(H/'payload/r.py').read_text()
assert "(B/'sums.txt').read_text()" in r and "sha256=dk.sha(B/n)" in r
assert "for p in cert['external']:assert dk.sha(p['path'])==p['sha256']" in r
assert "'g.sh'" not in (H/'payload/over.json').read_text()
(out/'results.json').write_text(json.dumps(dict(status='PASS',cases=records,only_two_active_files_changed=True,prepared_evidence_unchanged=True,backups_exact=True,downstream_checksum_and_external_binding='PASS',full_reupload_required=False),indent=2)+'\n')
print(json.dumps(records,indent=2))
