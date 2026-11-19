GO AFTER FIXES (incomplete cross-segment artifact authentication).

**High: `code_py` does not replace the removed artifact binding.** [score_d3.py:22](/scratch/jjyeung/orch_n30/cont_ops20/work/d3/score_d3.py:22) hashes packaged Python files, while [line 58](/scratch/jjyeung/orch_n30/cont_ops20/work/d3/score_d3.py:58) excludes `artifact_manifest_sha256` from segment equality.

The artifact manifest also binds component roles, relative paths, sizes, and content hashes for weights, tokenizer files, G3T, selector heads, and SAM assets ([build_manifest.py:21](/scratch/jjyeung/orch_n30/cont_ops18/d544ret/pkg/src/b/parity_kit/build_manifest.py:21)). It includes staged SAM source outside the package ([prepare.py:43](/scratch/jjyeung/orch_n30/cont_ops18/d544ret/pkg/src/orchard_h10/prepare.py:43)); the parent’s 821-file `code_py` inventory contains no SAM source.

The surviving input check authenticates each segment independently, without comparing component pins across segments ([return_tools.py:96](/scratch/jjyeung/orch_n30/cont_ops18/dresume/return_tools.py:96)). Equal package code and settings therefore cannot exclude changed dependency contents at unchanged paths. This is an authentication gap; I did not establish that actual segment assets differ.

No additional defect was found:

- All three segments receive the shared authenticators, provenance/complement checks, fresh identities, evaluator/settings checks, and pairwise disjointness checks.
- Metrics and paired comparisons use the original helpers. In-memory checks confirmed missing-score exclusion and intersection-only pairing.
- All six scorer/helper files pass Python 3.6 grammar checks. The specified interpreter reports **Python 3.12.13**, so Python 3.6 execution remains unverified.

Parent package/manifest and receipt checks passed. Both supplied `/dev/shm` directories are absent, and remainder 2 has no return; the full merge could not be replayed.

The sandbox rejected writing `REVIEW_D3.md` because filesystem access is read-only and approval settings block writes. No file was created.