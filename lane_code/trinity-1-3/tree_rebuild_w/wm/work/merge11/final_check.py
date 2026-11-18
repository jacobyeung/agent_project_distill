from pathlib import Path
import hashlib,json,re,sys
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';T=L/'work/tree_r1'
def read(p):return json.loads((L/p).read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
seal=read('out/TREE_SEAL.json');actual=inventory(T)
assert actual==seal['files'] and digest(actual)==seal['tree_sha256']
delivery=read('work/n1fix2/DELIVERY.json');p=L/delivery['path']
assert p.stat().st_size==delivery['bytes']<150_000_000 and sha(p)==delivery['sha256']
assert not read('work/merge11/GAPS.json')
comparison=read('work/n1fix2/SUITE_COMPARISON.json')
assert comparison['r2_failures']==0
assert all(r['preexisting'] or r['cause'].startswith('BF16 cached/online') for r in comparison['failures'])
assert read('work/merge11/PROOF_EQUALITY.json')['all_equal']
# Apply each unified hunk in memory to the supplied clean harness.
lines=(L/'out/EAT1_FIXED_MATH.patch').read_text().splitlines(True)
checks=[];i=0;base=L.parent/'work/design/eat1_v7'
while i<len(lines):
    assert lines[i].startswith('--- a/'),lines[i]
    name=lines[i][6:].strip();i+=1
    assert lines[i].startswith('+++ b/');i+=1
    prior=base/name;old=prior.read_text().splitlines(True) if prior.exists() else []
    cursor=0;out=[]
    while i<len(lines) and not lines[i].startswith('--- a/'):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert m,lines[i]
        start=int(m[1]);count=int(m[2] or 1);index=start-1 if count else start
        assert index>=cursor
        out.extend(old[cursor:index]);cursor=index;i+=1
        while i<len(lines) and not lines[i].startswith(('@@ ','--- a/')):
            tag=lines[i][0];value=lines[i][1:]
            if tag in (' ','-'):assert old[cursor]==value;cursor+=1
            if tag in (' ','+'):out.append(value)
            assert tag in (' ','-','+'),lines[i]
            i+=1
    out.extend(old[cursor:]);expected=L/'work/build10'/name
    assert ''.join(out)==expected.read_text(),name
    checks.append(dict(file=name,sha256=sha(expected)))
record=dict(verified=True,tree_sha256=seal['tree_sha256'],package_sha256=delivery['sha256'],patch_files=checks,
    comparison='work/n1fix2/SUITE_COMPARISON.json',coverage='work/merge11/CHANGED_COVERAGE.json')
(B/'FINAL_INTEGRITY.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(verified=True,patch_files=len(checks),tree_sha256=seal['tree_sha256'])))
