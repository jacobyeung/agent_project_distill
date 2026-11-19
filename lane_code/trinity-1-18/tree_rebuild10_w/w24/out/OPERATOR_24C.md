GO=false. This build does not submit or authorize a production run.

Apply `UPLOADS_MINIMAL.json`, then `UPLOADS_24B.json`, then `UPLOADS_24C.list` from `work/build24c/upload`. The final delta changes only kits q and n. Its JSON manifest records every name, byte count, SHA-256 and local path.

Use a clean sealed kit directory. Existing unlisted files, including `b/__pycache__`, still fail verification. Preserve any such files by moving them intact outside the kit into node-local storage before verifying; do not add them to SHA256SUMS.txt. This patch does not ignore bytecode or weaken verification.

Run host helpers with both `PYTHONDONTWRITEBYTECODE=1` and Python `-B`; isolated Python `-I` ignores the environment variable. The generated wrappers apply both controls. Keep resolver outputs outside the kit, preferably in the node-local job directory.

`job.sh` directs scheduler stdout/stderr to `/tmp/q_%j.log` and `/tmp/q_%j.err`. Its working directory, temporary files and caches are node-local. The decoded job shell uses the same policy. Completed result artifacts retain the existing `n_root/o/JOB_ID` publication path, outside both kit directories.

N's launcher starts four workers through a shell wrapper that explicitly invokes Python with `-B`; the launcher and workers retain the GO and admission gates. Both kits retain their own step-400 configs and the sealed tree `e1e64652`.

`BUILD24C_REPORT.md` contains the final kit seals and package checksum. The package is a kit-only overlay on `tree_rebuild_b24b_7d7a8858.tar`; it includes complete deployable q/n directories, generator changes and regression evidence. Keep the base package for unchanged fixture prerequisites.
