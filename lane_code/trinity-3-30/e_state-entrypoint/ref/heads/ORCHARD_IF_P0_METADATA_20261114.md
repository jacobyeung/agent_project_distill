# IF-P0 archive metadata is delivered

**Status: DELIVERED. The four listings and FLA manifest are delivered, and the exact original-init artifact is retained. The header, FLA and original-init launchers are consumed.**

## Question and answer

Which member names do IF-P0's four staged archives contain, and do the FLA manifest and original-init artifact match their pinned digests?

The bounded reader returns four complete member lists. Exact-range reads return the 87,191-byte FLA manifest and 929-byte original-init artifact with their expected SHA256 values. The operations made no project write, production job step, archive assembly or IF-P0 submission.

| Archive | Archive bytes | Members | Header and extended-metadata bytes read |
|---|---:|---:|---:|
| e00 | 82,984,960 | 58 | 42,000 |
| d00 | 925,368,320 | 969 | 497,152 |
| CP1 m200, eleven parts | 21,583,022,080 | 10 | 6,144 |
| Qwen | 19,329,320,960 | 14 | 11,960 |

The header batch read **557,256 bytes**. All source identities remained unchanged, and its recorded read intervals exclude regular-member payloads. No bound stopped a listing.

## Names and content identity

- e00 and d00 are `/project/community/jjyeung/distill/okit/in/e00` and `d00`. e00 uses long `scratch/fsw/.../ap/` and `lustre/fsw/.../ap/` prefixes; d00 uses `ebe69df8/`. The complete lists preserve the names needed by the caller.
- CP1 consists of `/project/community/jjyeung/distill/okit/in/cr/m200.p00` through `.p10`. Its artifact is `ap/f2ad01ad/runs/49becb79/m200/artifact.json`, declared as **929 bytes**. That member is not listed in e00.
- Qwen is `/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar`. Its prefix is `models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a/`; shard names follow `model.safetensors-00001-of-00004.safetensors`.
- The FLA member is `ebe69df8/m.sha` in d00. One `pread` reads **87,191 bytes at offset 2,048**. Its SHA256 is **4e4a6ac51788f7dd1ca9e0fc68f95109a129a636ce5f763e5b4ef3c3109f91c8**. Delivery requires that exact digest.

The original-init artifact's **929 bytes** match SHA256 **c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67**. One positional read at **offset 512** in `m200.p00` returned the entire member with unchanged source identity. Its schema is `carrier-c1-artifact-v1`, step **200**, and training mode `final`. The full-weight manifest and head hashes are references in this metadata, not new payload verifications. The complete archives and the files named by the FLA manifest were not rehashed.

## Method and alternatives

