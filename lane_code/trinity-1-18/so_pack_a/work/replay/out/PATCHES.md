# Patch layout and canonical source

Apply both patches with `patch -p1` at the root corresponding to the read-only input mirror `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`, using a writable copy. Patch 01 adds the wrapper, probes, fixtures, regression runners and documentation. Patch 02 adds `pack_token.py` and its regression test beside each native r10/D builder. Neither patch edits a native source file or an embedded Orchard script.

The top-level files in this delivery are canonical. The adapter copies in patch 02 have exactly the same bytes as the top-level adapter. `TOOL_SHA256.json` and `PATCH_VERIFIED.json` bind the delivered source set to a fresh patch application and the final test logs. Do not combine files from another package or revision.

Run the tool tests under the specified CPU Python with `-I -s -B`. Run each additive adapter test under real `/usr/bin/python3 -I -s -B` from its applied native directory. `test_native.py --work FRESH_LOCAL_DIRECTORY` runs actual D builds, default-OFF byte equality and the unchanged native checker. The raw supplied D tree's pre-existing scorer mismatch is recorded explicitly; only the documented coherent embedded-assets fixture passes that checker. The adapter does not change this source mismatch.

Production behavior requires `pack.py --enable`. Explicit tokens require the adapter's `--enable-token`. Wrapper normalization requires configuration `normalize_wrapper: true`. Their defaults preserve native code and archive bytes. The patches do not enable any running lane, arm an automatic submitter, change scheduler state or repair trainer signal handling.
