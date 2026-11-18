Cause: Orchard's fresh per-job /tmp lacks /tmp/jjyeung, so the driver's private-directory check refuses before creating proof storage.
Change: tools/proof_prepare.py:23 validates ownership, mode 0700 and directory type with lstat; :33 creates an absent parent before validation; :151 calls it without reusing an existing work directory.
Audit: tools/package_proof.py:15 embeds the exact driver; proof_prepare.py:33/:61 creates and isolates storage; payload/jb.sh:27 and build/fx/b/c.sh:265/:361/:393 create run/staging/cache paths and stamps. No other pre-existing node-local state is required; the real job reuses nothing.
Tests: test_fix8_proof, test_fix8_submit (13 cases), test_fix8_pin and test_fix8b_patch (10 cases plus repeat refusal) PASS; absent parent becomes owned 0700, existing 0755 and symlinks refuse; empty-/tmp namespace and deterministic rebuild PASS.
Proof: build/a_8c74b291.sh SHA256 f1f6a1519b6a27a190363672bd8a428b2e635e367461c87a0150c3a440aba40a.
Patch: build/c_patch_8b.sh SHA256 aabc564581b8d5fd0b41d3fb4d63e2b13bfd806ee14820cb3043c3f05787ca0a; verifies old proof 22ddf08a… and sums 25a95544… before changing only BUN/a_8c74b291.sh and its sums.txt line; retains both old files in BUN/v_8b.
KH manifest, config identity, contract, go binding, s.sh, jb.sh and EXPORT_OBJECTS remain unchanged; evidence/fix8b_patch_manifest.json records full old/new hashes.
Operator: deliver build/c_patch_8b.sh as /project/community/jjyeung/okh7/t_8b.sh, then run `printf '%s  %s\n' aabc564581b8d5fd0b41d3fb4d63e2b13bfd806ee14820cb3043c3f05787ca0a /project/community/jjyeung/okh7/t_8b.sh | sha256sum -c - && bash /project/community/jjyeung/okh7/t_8b.sh`.
Validation was CPU-only and local; production preparation requires a fresh operator-submitted proof job and a PASS receipt before s.sh.
