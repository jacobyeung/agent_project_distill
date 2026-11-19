# Pending current-source fixes

Do not edit the tree while the R2 run is active. Rerun affected tests after applying fixes.

- `tests/test_r2_build5.py`: fixture updates call the immutable `p3_provenance.write` helper on existing files in the receipt-protocol and late-refusal tests. Use explicit `Path.write_text` for those owned fixture updates. Preserve the production helper's exclusive-create behavior. Confirm the actual tracebacks before counting these as fixed.
- Rerun `tests.test_r2_build3_gaps.Gaps.test_host_packet_refusals` against stable source; its observed source-seal mismatch occurred while the checklist was edited.
- Rerun the round-trip test after the updated fixture loads. The current interpreter loaded the earlier fixture without `b/wh.json`; the current file supplies that scanner pin.
- Do not weaken the legacy bank refusal to satisfy an obsolete positive-path test. Compare the same case on the base first; update a test's expected contract only when the new refusal is the required behavior, and report that change explicitly.

The initial fixture corrections and stable-source native proof passed in `work/build5/proofs/new/results.json`. After the generator run, extend the host packet test to reach `apply_native` before its output-path refusal: use the existing GF1 fixture configuration with `r2_all_stream_exclusions` and `r2_build2` omitted, the existing dense and assets pins, and the escaping output path. This exercises host.py's remaining CPU-reachable arm binding without any store or tower load.
