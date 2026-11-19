"""Seal the reviewed row packet and verify every archive member by digest."""
import collections as C, hashlib, json, tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'out'
def pin(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
    return dict(path=str(p),sha256=h.hexdigest(),bytes=p.stat().st_size)
def load(name):return json.loads((OUT/name).read_text())
def main():
    c=load('CHECKS.json');v=load('VERIFY.json');review=load('READ60_REVIEW.json');h=load('HISTOGRAMS.json');ref=load('REFUSALS.json')
    assert v['status']==review['status']=='PASS'
    assert review['full_record_file_sha256']==pin(OUT/'READ60.md')['sha256']
    assert review['review_text_sha256']==pin(OUT/'REVIEW_TEXT60.md')['sha256']
    assert review['rows']==60
    for name in ('build_rows.py','survey.py'):
        expected=c['input_sha256'][str(BASE/name)]['sha256'];assert pin(BASE/name)['sha256']==expected,(name,'stale build')
    for name in ('NEW_ROWS.jsonl','SOURCE_MAP.jsonl'):
        assert pin(OUT/name)['sha256']==c['outputs'][name]['sha256']
        assert pin(OUT/name)['sha256']==v['input_sha256'][str(OUT/name)]['sha256']
    for p in (BASE/'finalize.py',OUT/'VERIFY.json',OUT/'READ60_REVIEW.json'):
        x=pin(p);c['input_sha256'][str(p)]={k:x[k] for k in ('sha256','bytes')}
    c.update(status='PASS',binding_ready=True,READ60=dict(status='PASS',rows=60,
        full_records='All sixty complete JSON rows parsed and matched to emitted records.',
        semantic_review='All sixty questions, options, reference-heading relations and resulting answers read; no unresolved errors.',
        receipt=pin(OUT/'READ60_REVIEW.json')),independent_verifier=pin(OUT/'VERIFY.json'))
    c['command']+='; PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py; PYTHONDONTWRITEBYTECODE=1 python finalize.py'
    (OUT/'CHECKS.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
    lines=[
        'Built 8,000 direct VQA twins: 4,000 away twins with the Step 1 opening and 4,000 toward twins with the Seen opening. CHECKS.json and VERIFY.json pass.',
        'The exactness gate passes all 5,846 easy/hard pairs (3,664 easy; 2,182 hard). All 1,274 literal-flip disagreements are medium.',
        f'Medium is refused as a family: {ref["medium_existing_pairs_refused"]:,} existing twin pairs and {ref["medium_direction_rows_refused"]:,} direction source rows. No medium row is emitted.',
        '',
        '| New-row answer | Step 1 / away (a) | Seen / toward (b) |',
        '|---|---:|---:|',
        '| easy left | 1440 | 1440 |','| easy right | 1440 | 1440 |',
        '| hard front-left | 280 | 280 |','| hard front-right | 280 | 280 |',
        '| hard back-left | 280 | 280 |','| hard back-right | 280 | 280 |',
        '',
        'The equal split fills the two requested complementary cells. Each new row uses a different v7 source, at most once. Hard answers are exactly 25% per quadrant within each clause; easy answers are 50% left/right and do not specify front/back quadrants.',
        'The scarce Seen/away hard front-right cell has 298 admitted sources. A quota of 280 per hard quadrant preserves unique sources and leaves refusal margin; easy rows fill the remaining 2,880 rows per branch.',
        'TEACHING_SET.json identifies 8,000 unchanged v7 source controls. Combining those controls with the additions gives 16,000 turn-teaching rows:',
        '',
        '| Opening | Toward | Away |','|---|---:|---:|','| Step 1 | 4000 | 4000 |','| Seen | 4000 | 4000 |',
        '',
        'Object-name counts and ordered spatial-role triples match exactly across clauses within each opening in this source-plus-twin subset. Use TEACHING_SET.json to retain that pairing.',
        'The additions alone occupy Step 1/away and Seen/toward. The complete v7-plus-additions population remains imbalanced; the four-cell balance applies to the specified teaching subset.',
        f'The Step 1 toward-only family supplies {h["new_away_names"]:,} distinct names to new away rows, including {len(h["new_away_names_absent_from_old_away"]):,} absent from the admitted Seen/away name set. New toward twins use {len(h["new_names_by_branch"]["b"]):,} names. Objects are never renamed.',
        '',
        'Admitted v7 histograms before / after adding these rows (literal clause; medium labels remain unchanged):',
        '',
        '| Clause | easy left | easy right | hard front-left | hard front-right | hard back-left | hard back-right |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    hist={key:{(r['clause'],r['family'],r['label']):r['rows'] for r in h[key]} for key in ('per_clause_before','per_clause_after')}
    for clause in ('toward','away','opposite'):
        vals=[]
        for family,label in [('easy','left'),('easy','right'),('hard','front-left'),('hard','front-right'),('hard','back-left'),('hard','back-right')]:
            key=(clause,family,label);vals.append(f'{hist["per_clause_before"].get(key,0)} / {hist["per_clause_after"].get(key,0)}')
        lines.append('| '+clause+' | '+' | '.join(vals)+' |')
    lines += [
        'HISTOGRAMS.json also records every opening × clause × family × label cell, the full unfiltered v7 census, and name histograms. Easy/medium labels are never presented as four quadrants.',
        '',
        'All 8,000 new rows and 8,000 sources pass N’s direct packer and direct schema/trace validators. The exact native pack functions are loaded by AST to avoid importing the GPU trainer dependency; their source file matches the tree seal.',
        'All new qids and candidate_ids are unique and disjoint from v7. candidate_identity uses the new qid, question, scene, frame indices, type and original option list.',
        'Independent checks parse each source reference-heading relation and verify the half-turn answer against the option list. Every toward twin also matches its stored toward mate. This is the authorized v7 symbolic mapping; no numeric geometry is inferred.',
        'Field differences are limited to qid, pool, answer, target, facing, candidate_id, lineage keys, the question and added provenance. Scene, object identities, frame pins, indices, timestamps, options and other source fields remain exact.',
        'All five room exclusions apply: K1, R0, withheld-80, dev-S1 and BENCH v2. N’s configured removal files plus n/z/u-union apply to sources, ancestors and new rows.',
        'N scene_division_gate.check_rows admits all 8,000 new rows and all 8,000 source controls, with zero filtered, removed, outside-train or held-out rows.',
        'The direction census excludes 3,026 rows in the union of room/removal hits: K1 and u-union each hit those same 3,026 rows. Other room/removal hits and scene-division refusals are zero.',
        f'Candidate refusals after family/room admission: {sum(ref["candidate_refusals"].values())}; REFUSALS.json records reasons and counts.',
        f'New questions pass normalized Levenshtein filtering against {c["normalized_edit_distance"]["unique_wordings"]:,} distinct local dev/benchmark wordings. NFKC + casefold + collapsed whitespace; reject distance/max length ≤ 0.10; {c["normalized_edit_distance"]["removed"]} removed; {c["normalized_edit_distance"]["logical_comparisons"]:,} logical comparisons.',
        'WORDING_CORPUS.json pins every discovered local item/fixture file. Coverage is limited to available local wordings; a complete external benchmark corpus is not claimed. No benchmark wording was used to author the new templates.',
        'READ60.md contains 60 full rows (five per branch/family/answer cell); all records were parsed and matched, and all questions, options and traces were read for semantic correctness. READ30.md contains the first 30 full rows. READ60_REVIEW.json records the review.',
        '',
        f'Store v7 SHA256: {next(value["sha256"] for path,value in c["input_sha256"].items() if path.endswith("a2_vqa_v7/vqa/rows.sqlite"))}.',
        f'The newer sealed W/w19 tree is used: {c["tree_sha256"]}. The division SHA256 is {c["scene_division"]["pin"]["sha256"]}.',
        'Every output JSON includes its input hashes; each row and source-map entry includes source and generator hashes. SOURCE_MAP.jsonl maps every new qid to its exact source store index and row digest.',
        'Commands producing the numbers: `PYTHONDONTWRITEBYTECODE=1 python survey.py` (census/admission); `PYTHONDONTWRITEBYTECODE=1 python wording_corpus.py` (wording corpus); `g++ -O3 -std=c++17 -shared -fPIC edit_distance.cpp -o edit_distance.so`; `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (gate, selection and checks); `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py` (independent checks/histograms); `PYTHONDONTWRITEBYTECODE=1 python finalize.py` (report/archive/digests).',
        'The archive is out/sb_rowD6.tar; its digest is in out/sb_rowD6.tar.sha256. PACKAGE.json records archive-member verification.',
        'Not done: training, binding into N, image rereads, GPU work, network access, SSH, Git, process termination or writes outside this workspace. Existing frame pins are preserved and validated as metadata.',
        'Borderline prose retained: none.',
    ]
    assert len(lines)<=80,len(lines)
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (BASE/'STATUS.md').write_text('PASS: 8,000 reviewed easy/hard twins are complete, split equally between Step 1/away and Seen/toward. The 5,846-pair gate, native pack/validation, independent truth, exact quotas, source reuse, identifiers, field preservation, room/removal/scene gates, wording-distance filter and 60-row semantic review pass. The archive and its SHA256 are ready in out/.\n')
    includes=[BASE/name for name in ('build_rows.py','survey.py','wording_corpus.py','verify_outputs.py','record_review.py','finalize.py','edit_distance.cpp','edit_distance.so','wording_paths.txt','STATUS.md')]
    includes+=sorted((BASE/'reference').glob('*'))
    includes+=[OUT/name for name in ('NEW_ROWS.jsonl','SOURCE_MAP.jsonl','CHECKS.json','VERIFY.json','GATE.json','PREFLIGHT.json','SURVEY.json','WORDING_CORPUS.json','TEACHING_SET.json','HISTOGRAMS.json','REFUSALS.json','READ60.md','READ30.md','REVIEW_TEXT60.md','READ60_REVIEW.json','REPORT.md')]
    members={str(p.relative_to(BASE)):pin(p) for p in includes}
    archive=OUT/'sb_rowD6.tar'
    with tarfile.open(archive,'w') as tar:
        for p in includes:tar.add(p,arcname=str(p.relative_to(BASE)),recursive=False)
    with tarfile.open(archive,'r') as tar:
        assert set(tar.getnames())==set(members)
        for member in tar:
            hsh=hashlib.sha256()
            with tar.extractfile(member) as stream:
                for block in iter(lambda:stream.read(4<<20),b''):hsh.update(block)
            assert hsh.hexdigest()==members[member.name]['sha256'],member.name
    ap=pin(archive)
    (OUT/'sb_rowD6.tar.sha256').write_text(ap['sha256']+'  sb_rowD6.tar\n')
    package=dict(command='PYTHONDONTWRITEBYTECODE=1 python finalize.py',input_sha256={k:dict(sha256=v['sha256'],bytes=v['bytes']) for k,v in members.items()},
        status='PASS',archive=ap,member_count=len(members),all_member_hashes_verified=True,new_rows=8000,report_lines=len(lines))
    (OUT/'PACKAGE.json').write_text(json.dumps(package,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status='PASS',archive=ap,report_lines=len(lines),members=len(members))))

if __name__=='__main__':main()
