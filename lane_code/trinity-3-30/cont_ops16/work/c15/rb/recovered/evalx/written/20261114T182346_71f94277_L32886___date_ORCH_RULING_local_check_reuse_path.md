<!-- recovered by seal_plan: transcript=71f94277 line=32886 utc=2026-11-14T18:23:46.048Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_local_check_reuse_path.md heredoc_quoted -->
# ORCH ruling: use the reuse path; no second copy, no lowered guard

The node's free space fell because another user is copying onto it; it has held at about 171 GiB since 17:58Z. Do not lower your 200 GiB guard and do not wait for headroom. The fresh-stage receipt may be replaced, for this seal, by a reuse receipt that proves the same bytes:

1. For each of the uploaded objects: the local archive's sha256 and size equal the family's pin and the upload receipt's server-confirmed hash and generation. (The uploaded bytes are then the local bytes.)
2. The existing pre-upload tree was produced by the job's real stager from exactly those archives (cite its record), and a fresh hash walk of that tree, done now, matches every member in the family's member lists: same paths, sizes and sha256, nothing extra, nothing missing. A hash walk reads; it copies nothing.
3. The 46 rows are then evaluated against that tree with the four dispositions. The reuse receipt names the tree, the walk's time and its own sha256, and says plainly that no fresh copy was made and why.
4. The submit guard accepts either a fresh-stage receipt or this reuse receipt; make that the smallest change you can and include it in the event. It can only refuse.

Then the one event I asked for: family 2b9d7815, token e702b65e2, the regenerated assets and objects with generations, both mask receipts' paths, the check record with the 46 rows, the Orchard pool size. I diff the mask receipts and answer with control files.