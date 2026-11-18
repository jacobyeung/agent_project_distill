<!-- recovered by seal_plan: transcript=71f94277 line=28962 utc=2026-11-14T06:07:09.028Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_REQUEST_archive_member_listings_for_if_p0.md heredoc_quoted -->
# ORCH request: member listings of four staged archives (headers only), for lane if_p0

The IF-P0 baseline job (169413, a separate one-GPU job, not production) failed after 64 seconds because its kit expected a member name that the staged archive does not carry. To fix every such name at once I need the real member lists. In your next routine session on the login host (no step inside the production job; nothing written on the project filesystem):

For each archive, `tar -tvf` (GNU tar seeks past file data on a regular file, so this reads headers only; if any listing has not finished after 60 seconds, stop it and say so):
1. `/project/community/jjyeung/distill/okit/in/e00` (83 MB): the full listing.
2. `/project/community/jjyeung/distill/okit/in/d00` (the FLA archive): the full listing if it has fewer than 5,000 members, otherwise the first 300 lines and the member count.
3. The archive the production kit stages as the CP1 m200 init mirror (21,583,022,080 bytes; take its path from your staging record): the full listing.
4. `/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar` (19.3 GB): the full listing.

Write the four listings as text files into `/scratch/jjyeung/orch_cd/if_p0/inbox/` with a `date -u` stamp in each name and one covering note stating each archive's path, size and the listing's line count. One RESULT when delivered. This is the only extra session work I am asking for; production monitoring continues as it is.