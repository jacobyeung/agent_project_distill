"""Write the bounded frozen-snapshot delta without Git or deletion."""
import difflib,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_f719b05f')
EXCLUDED={'out/FIX7.md','out/FIX7.diff','out/SHA256SUMS'}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def load(path):return json.loads(path.read_text())

def main():
    patches=[];changed=[];binary=[]
    for folder in ('tools','tests','configs','out','work/tree'):
        left=SNAPSHOT/folder;right=ROOT/folder
        paths={p.relative_to(left) for p in left.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        paths|={p.relative_to(right) for p in right.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        for rel in sorted(paths):
            name=folder+'/'+str(rel)
            if name in EXCLUDED:continue
            a=left/rel;b=right/rel
            before_sha=sha(a) if a.is_file() else None;after_sha=sha(b) if b.is_file() else None
            if before_sha==after_sha:continue
            changed.append(name)
            if folder=='work/tree' and name!='work/tree/student_pilot/loader_audit.py':
                raise ValueError('Unexpected trainer change: '+name)
            if '/b/' in name:raise ValueError('Inherited b/ member changed: '+name)
            before=a.read_bytes() if a.is_file() else b'';after=b.read_bytes() if b.is_file() else b''
            try:
                if b'\0' in before or b'\0' in after:raise UnicodeError()
                old=before.decode();new=after.decode()
            except UnicodeError:
                patches.append('Binary files a/'+name+' and b/'+name+' differ\n')
                patches.append('# SHA256 before='+str(before_sha)+' after='+str(after_sha)+'\n')
                binary.append(name);continue
            patches.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),
                                               fromfile='a/'+name,tofile='b/'+name))
    out=ROOT/'out';binding=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    frozen=load(SNAPSHOT/'out/BINDING.json')
    for key in ('receipt_sha256','database_sha256','mix','orchard_store','proof_partition','unit_binding','traced_room_receipt'):
        if binding[key]!=frozen[key]:raise ValueError('V7 binding changed: '+key)
    previous=load(SNAPSHOT/'out/proof/selection/r.json');current=load(out/'proof/selection/r.json')
    before=previous.pop('implementation');after=current.pop('implementation')
    if previous!=current:raise ValueError('Source selections changed')
    if {k for k in set(before)|set(after) if before.get(k)!=after.get(k)}!={'student_pilot/loader_audit.py'}:
        raise ValueError('Unexpected selection fingerprint changes')
    count=int(re.search(r'Ran (\d+) tests',(out/'logs/tests.log').read_text()).group(1))
    if not (out/'logs/tests.log').read_text().rstrip().endswith('OK'):raise ValueError('Tests failed')
    note=f'''The routing absolute-distance census reads `routing.canonical` first, then nested and top-level provenance fallbacks. It counts `scannetpp/`, `scannetppv2/`, `scannet/` and `arkitscenes/` separately. More than 1% unknown eligible distance rows makes the loader audit and its production check FAIL, with unknown and total counts. Exactly 1% passes.

All {count} packet tests pass. Fixtures run through the frozen `c1_row` converter and classify all four canonical prefixes without unknowns. Real SQLite loader checks cover 0/100, 1/100, 2/100, 1/99 and 4/4 unknown rows, including propagation through `loader_audit.main` to its admission report. The packaged submit gate rejects invalid GO under PYTHONOPTIMIZE=1 and 2; it runs with `-I` and PYTHONOPTIMIZE unset. `proof/ROUTING_PREFIX.json` and `logs/tests.log` record the evidence.

V7 retains its producer receipt, database, mix and source selections. The selection implementation fingerprint binds the changed loader code. Config identity: `{binding['config_identity']}`. Run key: `{binding['run_key']}`. Archive: `{op['archive']}`. Archive SHA256: `{op['sha256']}`.

Pre-submission fixtures verify the current packaged config identity before building simulated evidence, reject malformed records and compare inherited runtime bytes. The operator archive rebuild is byte-deterministic; two fixture deployments have identical manifests. Four-rank OFF identity and the final-config first batch pass. The packet, report, gate records and checksums bind this identity. Production routing, native preparation and independent review remain pending; these fixtures do not certify production data or grant launch authorization.

`FIX7.diff` compares tools, tests, configs, out and work/tree against `{SNAPSHOT}` (fix-6 archive f719b05f). The diff excludes itself, this note and SHA256SUMS to avoid recursion. The checksum manifest authenticates both FIX7 files. Binary changes include before/after hashes. Only loader_audit.py changes in the trainer tree; no inherited b/ file changes. All writes stay in this lane; no SSH, Orchard, Git, GPU or deletion command ran.

The reports apply the no-archaeology writing rule. The frozen-snapshot comparison is retained because the brief explicitly requests a reviewable delta.

Changed files covered by the diff:

'''
    note+=''.join('- `'+name+'`\n' for name in changed)
    (out/'FIX7.md').write_text(note)
    (out/'FIX7.diff').write_text(''.join(patches))
    print(json.dumps(dict(changed_files=changed,binary_files=binary,diff='out/FIX7.diff')))

if __name__=='__main__':main()
