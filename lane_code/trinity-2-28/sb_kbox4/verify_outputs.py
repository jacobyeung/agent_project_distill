"""Check artifact claims, input hashes, row-set membership, and archive contents."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    out=ROOT/'out';ladder=out/'box_ladder'
    dry=json.loads((out/'DRYRUN.json').read_text())
    assert dry['tests']['stage1_replay']['matched']==4 and dry['tests']['stage1_replay']['total']==5
    assert dry['tests']['A0_deployed_row_reproduction']['matched']==4
    assert dry['tests']['reference_row_equality']['matched']==4
    assert not dry['full_train_started'] and not dry['heldout_evaluated'] and not dry['passed']
    inputs={};json_files=[out/'DRYRUN.json']+list(ladder.glob('*.json'))
    for p in json_files:
        obj=json.loads(p.read_text());assert obj.get('input_sha256'),p
        for path,digest in obj['input_sha256'].items():
            if path in inputs:assert inputs[path]==digest,(path,'inconsistent provenance')
            inputs[path]=digest
    # Hash local file inputs once, with bounded streaming memory. No NFS reads.
    mismatch=[]
    for name,want in inputs.items():
        p=Path(name)
        if not p.resolve().is_relative_to('/scratch'):
            continue
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        if h.hexdigest()!=want:mismatch.append(name)
    assert not mismatch,mismatch
    rows=[json.loads(s) for s in (ladder/'PER_ITEM.jsonl').read_text().splitlines()]
    assert len(rows)==92 and all(r['split']=='train' and r['stage']=='dry_run' for r in rows)
    assert all(r.get('input_sha256') for r in rows)
    pinned=json.loads((ladder/'ROW_SETS.json').read_text())
    assert len(pinned['train'])==1037 and len(pinned['predicted_train'])==883
    assert set(r['row_id'] for r in pinned['predicted_train'])<=set(r['row_id'] for r in pinned['train'])
    decisions=json.loads((ladder/'DECISION.json').read_text())
    assert not decisions['choices_frozen'] and all(v['verdict']=='MISSING' for v in decisions['bars'].values())
    assert len((out/'REPORT.md').read_text().splitlines())<=80
    archive=out/'sb_kbox2.tar';want=(out/'sb_kbox2.tar.sha256').read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==want
    with tarfile.open(archive) as t:
        names=t.getnames()
        assert len(names)==len(set(names))
        assert 'out/REPORT.md' in names and 'out/DRYRUN.json' in names
        assert not any('inherited' in n or n.endswith('.npz') or n.endswith('.tar') for n in names)
    print(json.dumps(dict(status='PASS',verified_input_files=len(inputs),output_json_files=len(json_files),records=len(rows),archive_sha256=want)))
if __name__=='__main__':main()
