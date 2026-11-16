<!-- recovered by seal_plan: transcript=71f94277 line=27912 utc=2026-11-14T02:53:09.354Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ORDER_one_readonly_step_model_manifest.md heredoc_quoted -->
# ORCH order: one read-only step inside the job to return one small file (the model manifest)

The routed read of the step-200 export on Trinity needs the hash-pinned model manifest, and no copy exists outside the production job's staged tree.

Approved, ONCE: a read-only step in job 169097 that returns the bytes of the file whose logical path is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/arm/frozen/6f27ae81/model.json` (under the job's staged root, i.e. `/tmp/jjyeung/okit_8865619b/root/aws/u/ap/e84d901c/arm/frozen/6f27ae81/model.json`), with its size and sha256. Expected sha256: cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7.

Conditions: the proven metadata-step form (absolute program paths, your encoded transport, raw saved first); one CPU, 60 seconds; the step refuses and returns only the size if the file is larger than 1 MB or is not a regular file; it reads nothing else and writes nothing on the node; not within 10 minutes of a save or a milestone export (the next ordinary save is due about 03:49Z); production checked before and after with step times; no retry if it fails. If your own held records already contain these exact bytes (matching the hash), use them and skip the step.

Deliver the file to `/scratch/jjyeung/orch_cd/evalx/inbox/` with a `date -u` stamp in its name and a one-line note with the hash, and post one RESULT.