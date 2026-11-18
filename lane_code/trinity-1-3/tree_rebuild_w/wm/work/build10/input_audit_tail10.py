from pathlib import Path
import hashlib,json,tarfile
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
p=N/'work/build7/proofs/responses/INVENTORY.json';raw=p.read_bytes();value=json.loads(raw)
record=dict(source=str(p),sha256=hashlib.sha256(raw).hexdigest(),keys=sorted(value),
    example_fields=sorted({k for r in value.get('examples',[]) for k in r}),
    interpretation='This is a printed-response inventory. It does not contain producer pose, depth, FoV, camera/reference transforms or raw provider inputs. Original tiny-reader weights and frame inputs are separately replayed in proofs/parity_build7/RESULT.json.')
(L/'work/merge11/proofs/parity/BUILD7_INPUT_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
archive=N/'work/design/eat1_v7/b03_e2etest_eat1_v7.tar';root=N/'work/design/eat1_v7/eat1';rows=[]
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        parts=Path(member.name).parts
        if not member.isfile() or 'eat1' not in parts or not member.name.endswith(('.py','.json')):continue
        name=Path(*parts[parts.index('eat1')+1:]);path=root/name
        if not path.is_file():continue
        expected=hashlib.sha256(tar.extractfile(member).read()).hexdigest();actual=hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(dict(file=str(name),archive_sha256=expected,source_sha256=actual,match=expected==actual))
assert rows and all(r['match'] for r in rows)
(B/'HARNESS_BASELINE.json').write_text(json.dumps(dict(archive=str(archive),files=rows,status='PASS'),indent=2)+'\n')
print(json.dumps(dict(harness_files_verified=len(rows),build7_inventory='printed responses only')))
