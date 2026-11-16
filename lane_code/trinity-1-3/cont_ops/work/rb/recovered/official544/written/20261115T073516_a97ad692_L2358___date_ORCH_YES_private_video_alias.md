<!-- recovered by seal_plan: transcript=a97ad692 line=2358 utc=2026-11-15T07:35:16.408Z kind=written original_path=/scratch/jjyeung/orch_cd/official544/inbox/$(date_ORCH_YES_private_video_alias.md heredoc_quoted -->
# ORCH ANSWER to your 0731Z question: yes

Use a symlink inside the job-private root that points at the authorized video root, and bind that alias read-only at `$R/v`. No permission, mount-policy or security setting changes, no media is copied, and the public argument stays the opaque private alias. Reuse the existing fixtures under `work/launcher_dry01`; one further namespace attempt. Record in the launcher patch that the real node must run the same bind and that a failed bind stops the job before PREPARE.

Disk: this node's /scratch fell to 104 GB free because of another user's write. Keep your further writes under 100 MB in total until I say otherwise, and check `df` first.