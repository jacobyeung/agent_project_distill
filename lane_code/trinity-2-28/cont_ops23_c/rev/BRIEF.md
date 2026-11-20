# Read-only review: local scoring route for the merged H@544 held-out camera read

You review; you do not edit, run ssh, or kill anything. Write your findings to REVIEW.md in this directory (at most 40 lines): a verdict GO / NO-GO for "these numbers may enter a design decision", then only verified problems (file:line, why it matters, evidence). No fix designs.

## What happened
- A sealed kit (`kit/`, an exact copy of the kit deployed on the cluster as `<stage>-kit`) normally runs `orchard_hrem.py fetch` on the cluster login node: `fetch_validation.fetch()` copies the pool return (`<pool>/<token>/result.tar.gz, EXIT.json, RETURN_RECEIPT.json`) into `<package>/a/f/` and then `score_h_merge.score()` merges parent (partial, 482 items) and remainder (complete, 418 items) and writes SCORES.json.
- The cluster filesystem was below the kit's 300 GiB free-space guard, so the operator did NOT run `fetch`. Instead (`o_pull2.sh`, `local_score.py`): the pool return files and the remainder package (minus four multi-GB hard-linked data parts under a/e, not listed in PACKAGE.json files) were streamed to a RAM disk; `result.tar.gz` was copied to `<local package>/a/f/0.tgz` with EXIT.json and RETURN_RECEIPT.json beside it; the parent, H@400 and H@200 packages came from earlier fetched tar copies (pkg.tar, which include their a/f publications). `local_score.py` then calls the kit's unchanged `score()` for the merged spec, with `--other`-equivalent comparisons against H@400 and H@200, and for H@400 and H@200 alone. `fmt.py` prints the summary (`SUMMARY.txt`).
- `remainder_EXIT.json`, `remainder_RECEIPT.json`: the pool files. Their archive sha256 is c4912084e5a2dd5b3a3cc3914ec7d2b5fd1f76028b968e8c0d333277448dd645.

## Questions
1. Does the local route keep every authentication that `fetch()` + `score()` perform on the cluster (token/job match, plan, receipt pool pins, payload pins, completion flags)? Name any check that fetch() does and score()'s unpack()/package_info() does not, and say whether skipping it can change a number.
2. Could path differences (local root instead of /project paths; `cfg['pool']` unused) change any scored number or let a wrong publication be scored?
3. Are the numbers in `RESULT.md` exactly what SCORES*.json / ALONE_*.json contain (cells, reworded-minus-original, step differences with CIs, the "gap change" rows, and the call-rate claim "97-100% at 544 vs 46-88% at 400 and 200" from the `call_rate` fields)? Check fmt.py's arithmetic.
4. Anything in local_score.py that mixes segments, reuses a work dir, or scores the wrong package for a name.
