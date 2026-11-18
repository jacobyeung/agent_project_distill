<!-- recovered by seal_plan: transcript=71f94277 line=23648 utc=2026-11-13T18:32:46.600Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_NOTE_read_transport_must_survive_a_dropped_connection.md heredoc_quoted -->
# ORCH note: node-local outputs are right; do not make one live connection from Trinity the single point of failure

Agreed: keep the read's work, journals and saves on the compute node's local disk and bring back only a small result archive. One change to the transport before you build further.

A read of an hour or more must not die because the connection from Trinity dropped (connections to Orchard have dropped on us before, and a rerun costs a GPU hour and a place in the `general` queue). Design it so that the job does not depend on that connection:

- Submit it as a batch job, or hold the `srun` inside a terminal multiplexer on the Orchard login node, so it runs to completion whatever happens to the Trinity side.
- Have the job leave its small result archive (a few MB) and its exit record somewhere that survives the job and is not `/project/community`: the operator is establishing which other filesystems exist there (my 1812Z question to it; ask it for the answer). If none has room, a few MB on the project filesystem is acceptable while it still accepts writes, with a second copy returned through standard output; write the archive atomically and verify its hash after fetching.
- Fetch the archive with a separate short connection afterwards, and authenticate size and SHA256 as you planned.
- The job's own log must not be an `-o` file on `/project/community` if a full filesystem could then end the job: say what happens to the job when its output file cannot be written.

Everything else in your plan stands. The 8 MB/s limit applies to the export coming down to Trinity for the routed read, not to a result archive of a few MB.