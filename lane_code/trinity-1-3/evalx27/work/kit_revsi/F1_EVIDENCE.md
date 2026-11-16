# F1 evidence

Package SHA256: `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b`; 125 files, 13,721,600 bytes. Two deterministic builds matched.
Baseline: `6e025a8898e112fd5282af03d8d0e82ce947a2ce2b714736de2745ee293f6572`, verified after one throttled read of the requested archive; reconstructed under `build/f1/baseline/`.
Diff: 112 files retain names and bytes; five input files retain bytes under opaque names; eight files contain path-string edits or package-list exclusions; two unused cell files are omitted.
The complete [hash table and unified diffs](DIFF.md), [machine-readable comparison](build/f1/package_comparison.json), and [zero-context diff](build/f1/path_strings.diff) cover every package member. The comparator asserts the exact replacements and exclusions.
The two cell files remain untouched in the local source directory and are excluded from both package.tar and the launcher payload.
The prepared batch payload was decoded independently: all five [input hashes](build/f1/payload_input_hashes.json) equal the baseline, and all seven F1 pathnames are absent.

| Job-root suffix | Unchanged input SHA256 |
|---|---|
| `p/cohort/c5.jsonl` | `62bb4df707ef6733ba708343be194e1dce083e25262057f86985eca2606be455` |
| `p/inputs/i1.json` | `511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9` |
| `p/inputs/i2.json` | `03456abc2fcd8199ed4fb4a3af54651ed07df2e5a1efa752aa165006ad4b6850` |
| `p/inputs/i3.json` | `badb56dc5cd95118c686262ed9af4055d92727ae9e282b5a3b41198a96411c82` |
| `p/inputs/i4.json` | `290111cf9c2bfa8fec66e70395922b830c2738633abf736600489cdff4b429b2` |

All 65 reader files appear in the [raw before/after hash table](build/f1/reader_hashes.tsv). All 36 evaluator files are byte-identical; 62 reader files are byte-identical. The three remaining reader files differ only by the path strings shown in DIFF.md.

| Reader file | Baseline SHA256 | Current SHA256 |
|---|---|---|
| `reader/chain.py` | `6eb8d7220726b74bc210c6befafa6312c1880742c5fb28ea2b7201464e89d435` | `96cf9ad22618899ddafe4b5ee8c337598f5612e9d4e5bc5cb8ded7061d833084` |
| `reader/official_adapter.py` | `243e03b584650edfb7d4c20967c772afb906654c8cba7c7c25957e98a781c522` | `a10f34f4b6d240e0e366e56c9928f1c7d9cd080a91886d6a3a1d6c1381b35109` |
| `reader/official_score.py` | `54a55bb6cf202c16d45a5479bd6242bfb4abb07a72fbe009cbade1b7edaad0a4` | `b279ddc18acd3e019b8343214d963a60d3bafcd929f2a3e4d965a0aa1b88d409` |

The scorer CLI default changes only its cohort pathname. The scorer functions, adapter decisions, reader logic, input bytes and SHA pin constants are unchanged.
The proof argv paths containing `legs1` and `rv_merge_fix` remain: changing them requires reader/chain.py and proof/phase_b.py, beyond the permitted launcher-only rename. They also occur in the unchanged VSI kit f42aa1a4.

Local proof: **PASS**, from a fresh extraction into `build/f1/extracted/`, with an absent work directory that the harness creates empty.
Command (from work/): `PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/kit_revsi/build/f1" OPENBLAS_NUM_THREADS=1 timeout --signal=INT 240 kit_revsi/.venv312/bin/python -B kit_revsi/build/f1/audit_run.py > kit_revsi/build/f1/proof04.log 2>&1`.
The proof exercised 261 generated clips, 10 task items and 20 dev items; see [result](build/f1/proof_result.json) and [log](build/f1/proof04.log). The recorder wraps local command boundaries without editing packaged code.
Local limitation: an independent [asyncio thread probe](build/f1/asyncio_probe.log) timed out; the proof wrapper bounds selector waits to 0.1 s in the parent and child processes. This external harness adjustment changes no packaged bytes. Initial recorder-error/stalled diagnostic runs are retained; only proof04 is a PASS.
Tests: **79 passed**, two metric divide warnings; command: `PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/kit_revsi/build/f1" kit_revsi/.venv312/bin/python -B -m pytest -q -p no:cacheprovider kit_revsi/tests` ([log](build/f1/tests.log)). All 76 packaged Python files compiled.

The complete [job-root path list](build/f1/job_paths.tsv) contains 1639 entries (files, directories and symlinks), enumerated from `/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/build/f1/empty04/a_900000_a1e894e51e01d`.
The complete [recorded local argv](build/f1/local_argv.jsonl) contains 19 command records; the [Orchard argv listing](build/f1/orchard_argv.jsonl) preserves the recorded argument order and labels projected paths and unexecuted namespace/submission/transport construction.
The local proof substitutes runtimes, model assets, media, GPU checks, parity and publication. Its path list is exhaustive for this local job root; real Orchard archive interiors and unexecuted transfer/error branches were not observed.
The [case-insensitive hit table](build/f1/path_hits.tsv) reports every matching string, source/index, term, classification and reason. Local audit/venv prefixes are labeled NEW LOCAL ONLY; they are not Orchard paths.
Search terms: `split, revsi, vsi, vsibench, distill, qgen, scannet, arkit, qwen, legs1, rv_merge, official, bench`. Counts and zero-hit terms appear in the [search summary](build/f1/inventory_summary.json).
Every remaining Orchard-name hit is pre-existing: alias paths or kit filenames shared with f42aa1a4. No new matching payload path was found.
No SSH, submission, Git, network, real media read, real engine or Orchard execution was performed.
