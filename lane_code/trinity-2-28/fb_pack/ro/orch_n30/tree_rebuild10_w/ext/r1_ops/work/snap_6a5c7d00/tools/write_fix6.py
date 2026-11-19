"""Write the bounded frozen-snapshot delta without Git or deletion."""
import difflib,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_782f303d')
EXCLUDED={'out/FIX6.md','out/FIX6.diff','out/SHA256SUMS'}
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
            if folder in ('configs','work/tree'):
                raise ValueError('Fix 6 must preserve config and trainer bytes: '+name)
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
    count=int(re.search(r'Ran (\d+) tests',(out/'logs/tests.log').read_text()).group(1))
    if not (out/'logs/tests.log').read_text().rstrip().endswith('OK'):raise ValueError('Tests failed')
    note=f'''The packaged deriver validates production-form evidence and reaches READY without a Slurm identity or persistent-run initialization. Config identity remains `{binding['config_identity']}`. All {count} packet tests pass.

Archive: `{op['archive']}`. SHA256: `{op['sha256']}`.

`tools/derive_deployment.py` uses inherited `g.read_pin`, `g.identity`, `g.digest` and `d.contract`. It checks the review verdict, reviewer, config/source identity, admission hash, contract and scope; staging status, config/source identity, missing inputs and write count; durable archive status, location, tree and archive hash; and mode-p authorization identity, source, contract and expiry. It does not call `g.check`, `persistent_launch` or `r8.main`. The inherited verifier has no complete evidence-only entry point, so the deriver composes its read-only helpers with these record predicates. The unchanged job path runs the full allocation-time verifier.

`tests/test_derivation_pre_submit.py` uses the read-only driver `evidence_body.py`, `fixture_h`, `fixture_b` and the construction in `test_local.py`. It exercises the packaged `d.py` with every Slurm environment variable removed. A call guard refuses allocation-time persistence, and an audit guard refuses writes outside the lane's test directory. The READY result retains `production_authorized=false` in the derivation receipt. Four wrong-identity records and fourteen malformed record/binding variants fail. Runtime files under `b/` and `job.sh` match the existing fixture derivation byte for byte.

The tests use observed H1 record schemas and raw native selection receipt/index bytes. Two absent data archives contain explicit local sentinels; review attestations are simulated. These fixtures prove control flow and evidence validation, not production data authenticity, independent approval or native preparation. `proof/PRE_SUBMISSION.json` and `logs/tests.log` record the scope and results. The operator archive rebuild is byte-deterministic, and two fixture derivations have identical manifest hashes. Existing four-rank OFF and first-batch results remain bound to the unchanged config and trainer tree.

`R1P_PACKET.md` sets `H=/project/community/jjyeung/okh7/x_3fdda0fb` and prints source manifest SHA256 `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3`. The fixture manifest value remains confined to local evidence. The archive, `OPERATOR.json`, `REPORT.md`, `R1P_PACKET.md`, `proof/GATES.json`, review request and checksums are resealed together. Independent final-packet review, content certification and the production CPU proof remain pending; no Orchard, Slurm, SSH, GPU or Git command ran.

`FIX6.diff` compares `tools`, `tests`, `configs`, `out` and `work/tree` against `{SNAPSHOT}`. Config and trainer files are byte-identical. The diff excludes itself, this note and `SHA256SUMS` to avoid recursive checksum dependencies; the final checksum manifest authenticates both FIX6 files. Binary changes carry before/after SHA256 values. No inherited `b/` file was edited. No files were deleted or edited outside this lane.

The report and packet instructions apply the no-archaeology writing rule. The snapshot comparison is retained because the brief explicitly requests a reviewable delta.

Changed files covered by the diff:

'''
    note+=''.join('- `'+name+'`\n' for name in changed)
    (out/'FIX6.md').write_text(note)
    (out/'FIX6.diff').write_text(''.join(patches))
    print(json.dumps(dict(changed_files=changed,binary_files=binary,diff='out/FIX6.diff')))

if __name__=='__main__':main()
