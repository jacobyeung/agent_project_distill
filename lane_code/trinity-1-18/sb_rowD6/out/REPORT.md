Built 8,000 direct VQA twins: 4,000 away twins with the Step 1 opening and 4,000 toward twins with the Seen opening. CHECKS.json and VERIFY.json pass.
The exactness gate passes all 5,846 easy/hard pairs (3,664 easy; 2,182 hard). All 1,274 literal-flip disagreements are medium.
Medium is refused as a family: 2,665 existing twin pairs and 29,124 direction source rows. No medium row is emitted.

| New-row answer | Step 1 / away (a) | Seen / toward (b) |
|---|---:|---:|
| easy left | 1440 | 1440 |
| easy right | 1440 | 1440 |
| hard front-left | 280 | 280 |
| hard front-right | 280 | 280 |
| hard back-left | 280 | 280 |
| hard back-right | 280 | 280 |

The equal split fills the two requested complementary cells. Each new row uses a different v7 source, at most once. Hard answers are exactly 25% per quadrant within each clause; easy answers are 50% left/right and do not specify front/back quadrants.
The scarce Seen/away hard front-right cell has 298 admitted sources. A quota of 280 per hard quadrant preserves unique sources and leaves refusal margin; easy rows fill the remaining 2,880 rows per branch.
TEACHING_SET.json identifies 8,000 unchanged v7 source controls. Combining those controls with the additions gives 16,000 turn-teaching rows:

| Opening | Toward | Away |
|---|---:|---:|
| Step 1 | 4000 | 4000 |
| Seen | 4000 | 4000 |

Object-name counts and ordered spatial-role triples match exactly across clauses within each opening in this source-plus-twin subset. Use TEACHING_SET.json to retain that pairing.
The additions alone occupy Step 1/away and Seen/toward. The complete v7-plus-additions population remains imbalanced; the four-cell balance applies to the specified teaching subset.
The Step 1 toward-only family supplies 1,026 distinct names to new away rows, including 953 absent from the admitted Seen/away name set. New toward twins use 73 names. Objects are never renamed.

Admitted v7 histograms before / after adding these rows (literal clause; medium labels remain unchanged):

| Clause | easy left | easy right | hard front-left | hard front-right | hard back-left | hard back-right |
|---|---:|---:|---:|---:|---:|---:|
| toward | 10096 / 11536 | 9629 / 11069 | 10498 / 10778 | 10037 / 10317 | 2037 / 2317 | 2290 / 2570 |
| away | 3561 / 5001 | 3757 / 5197 | 353 / 633 | 298 / 578 | 1832 / 2112 | 1877 / 2157 |
| opposite | 1792 / 1792 | 1872 / 1872 | 181 / 181 | 158 / 158 | 910 / 910 | 933 / 933 |
HISTOGRAMS.json also records every opening × clause × family × label cell, the full unfiltered v7 census, and name histograms. Easy/medium labels are never presented as four quadrants.

All 8,000 new rows and 8,000 sources pass N’s direct packer and direct schema/trace validators. The exact native pack functions are loaded by AST to avoid importing the GPU trainer dependency; their source file matches the tree seal.
All new qids and candidate_ids are unique and disjoint from v7. candidate_identity uses the new qid, question, scene, frame indices, type and original option list.
Independent checks parse each source reference-heading relation and verify the half-turn answer against the option list. Every toward twin also matches its stored toward mate. This is the authorized v7 symbolic mapping; no numeric geometry is inferred.
Field differences are limited to qid, pool, answer, target, facing, candidate_id, lineage keys, the question and added provenance. Scene, object identities, frame pins, indices, timestamps, options and other source fields remain exact.
All five room exclusions apply: K1, R0, withheld-80, dev-S1 and BENCH v2. N’s configured removal files plus n/z/u-union apply to sources, ancestors and new rows.
N scene_division_gate.check_rows admits all 8,000 new rows and all 8,000 source controls, with zero filtered, removed, outside-train or held-out rows.
The direction census excludes 3,026 rows in the union of room/removal hits: K1 and u-union each hit those same 3,026 rows. Other room/removal hits and scene-division refusals are zero.
Candidate refusals after family/room admission: 0; REFUSALS.json records reasons and counts.
New questions pass normalized Levenshtein filtering against 927 distinct local dev/benchmark wordings. NFKC + casefold + collapsed whitespace; reject distance/max length ≤ 0.10; 0 removed; 7,416,000 logical comparisons.
WORDING_CORPUS.json pins every discovered local item/fixture file. Coverage is limited to available local wordings; a complete external benchmark corpus is not claimed. No benchmark wording was used to author the new templates.
READ60.md contains 60 full rows (five per branch/family/answer cell); all records were parsed and matched, and all questions, options and traces were read for semantic correctness. READ30.md contains the first 30 full rows. READ60_REVIEW.json records the review.

Store v7 SHA256: 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443.
The newer sealed W/w19 tree is used: 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa. The division SHA256 is 0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad.
Every output JSON includes its input hashes; each row and source-map entry includes source and generator hashes. SOURCE_MAP.jsonl maps every new qid to its exact source store index and row digest.
Commands producing the numbers: `PYTHONDONTWRITEBYTECODE=1 python survey.py` (census/admission); `PYTHONDONTWRITEBYTECODE=1 python wording_corpus.py` (wording corpus); `g++ -O3 -std=c++17 -shared -fPIC edit_distance.cpp -o edit_distance.so`; `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (gate, selection and checks); `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py` (independent checks/histograms); `PYTHONDONTWRITEBYTECODE=1 python finalize.py` (report/archive/digests).
The archive is out/sb_rowD6.tar; its digest is in out/sb_rowD6.tar.sha256. PACKAGE.json records archive-member verification.
Not done: training, binding into N, image rereads, GPU work, network access, SSH, Git, process termination or writes outside this workspace. Existing frame pins are preserved and validated as metadata.
Borderline prose retained: none.
