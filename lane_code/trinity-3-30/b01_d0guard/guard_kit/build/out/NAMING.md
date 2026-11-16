# Naming

Release is blocked. Operational source-path renaming is reversible and preserves all other JSON scalars (`NAME_ROUNDTRIP.json`). It does not complete job-visible metadata renaming.

Every textual occurrence in the code tree is listed with file, line, column and context in `NAMING_OCCURRENCES.jsonl`. CONFIG occurrences are listed in `NAME_ROUNDTRIP.json`; counts and archive-member results are in `NAMING_SCAN.json`.

The original kernels contain capture-scope names. Prepared metadata and request item keys also carry names that are authenticated by nested digests. Replacing those strings changes the request/preparation identities. The current worker retains original keys to preserve C8r admission. `TRINITY_KEY_MAP.json` and `inputs/opaque_reference.json` provide the proposed opaque mapping; they are not a completed runtime migration.

Code identifiers and explanatory prose are not operational names. Literal path, item-key and capture-scope occurrences need a complete migration or an explicit ruling before this family can launch. No such ruling is assumed.

Orchard operator copies (identical bytes; never executed here):
```sh
mkdir -p /project/community/jjyeung/okh7/8c9d2e74
cp -- /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/8c9d2e74/ab626354ad7ea9b9
sha256sum -- /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/8c9d2e74/ab626354ad7ea9b9
# Required SHA256: 20a2ab6c54e22baba2c6b9065a7c0df24a9fe60a867fb078a017859dac2fdaca
cp -- /project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar /project/community/jjyeung/okh7/8c9d2e74/3f4e9154ba1f2066
sha256sum -- /project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar /project/community/jjyeung/okh7/8c9d2e74/3f4e9154ba1f2066
# Required SHA256: fa8681cba4c02d789bc60c09fac7a05936c5b1fde81d53f77830294ea7e7895c
cp -- /project/community/jjyeung/distill/okit/in/cr/436d1d64673f.p00 /project/community/jjyeung/okh7/8c9d2e74/8f38e81ca7758e70
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/436d1d64673f.p00 /project/community/jjyeung/okh7/8c9d2e74/8f38e81ca7758e70
# Required SHA256: fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7
cp -- /project/community/jjyeung/distill/okit/in/cr/9b9e03337df5.p00 /project/community/jjyeung/okh7/8c9d2e74/9bda75a7077ab157
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/9b9e03337df5.p00 /project/community/jjyeung/okh7/8c9d2e74/9bda75a7077ab157
# Required SHA256: 07c2d3b0358fd6f16e014f4a155bee6de921e6723a5b9633d08d0fb71e8fad39
cp -- /project/community/jjyeung/distill/okit/in/cr/c449bbe907be.p00 /project/community/jjyeung/okh7/8c9d2e74/2206733a423ef6ba
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/c449bbe907be.p00 /project/community/jjyeung/okh7/8c9d2e74/2206733a423ef6ba
# Required SHA256: 0482359088665775014cb46c10f6d87a6f99c4203a978b6b6d1a74a50155438d
cp -- /project/community/jjyeung/distill/okit/in/d00 /project/community/jjyeung/okh7/8c9d2e74/cb81e2210d956d4a
sha256sum -- /project/community/jjyeung/distill/okit/in/d00 /project/community/jjyeung/okh7/8c9d2e74/cb81e2210d956d4a
```
