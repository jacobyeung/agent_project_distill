# Build N2: finish the native official read worker in place (one-shot Codex build, continues build N)

You run once on trinity-3-30; nobody answers questions while you run. Same rules as `BRIEF.md` in
this folder (read it first, including its "Binding rulings" section, which still wins): write only
inside `/scratch/jjyeung/orch_n30/b07_offread/builds/N/` (at most 4 GB total; check `df -h /scratch`
before writing more than 1 GB); no ssh, network, Git, GPU, Slurm or Orchard command; no deletion
(write new files or new versions, never remove); no recursive search of /home or /data*; Python
`/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer or score to choose anything.
Tests run as `"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=work/<fresh dir> -q`.

## Where build N stopped
Read `out/NATIVE_KIT_READY.md`, `out/OPEN_INPUTS.md`, `out/ORCHARD_ONLY.md`, `out/MODULE_MAP.md`,
`SIZING.md`, `DIFF.md`, `RUN.md`. 24 tests pass; ReVSI CPU fixtures pass for both readers with a
synthetic serving socket. Unfinished code (build all of it now; inputs that only an owner can supply
stay open inputs and the launcher refuses production on each missing one, by name, instead of the
current unconditional refusal):
1. Production stager: reuse build R's reviewed staging unchanged by import or byte-equal copy
   (`/scratch/jjyeung/orch_n30/b07_offread/builds/R/kit/revsi/launcher/{export_stage.py,s1.py,gate.py}`,
   `kit/rebind.py`; never modify build R's files) for the step-544 and D0 exports, towers by sha256
   (G3T as V1c stages it; SAM 3 by sha256 9999e234... as the K1 kit stages it), media by manifest.
2. C8r context builder and proposal/cache bridge: in-job SAM 3 proposals for every question operand of
   a video (the 501 pairs of `NAME_INVENTORY.json`), written in C8r's mask-cache and geometry-manifest
   formats so C8r's real decoder (`nomdg.py` and its call servers) serves calls unchanged. A model-emitted
   name outside the inventory goes through the same frozen proposal contract in-job (or, if C8r cannot,
   is a recorded refusal that scores 0 in the primary arm). Run C8r's real decode loop (not the
   synthetic socket) in the harness CPU fixture with a tiny model and synthetic tower arrays.
3. In-job identity proof on the original export: the ten `PROOF_KEYS.json` items decoded through the
   bound reader and compared with job 170056's journal; independent distance serving from the pinned
   170056 mask cache where present (C8r's `MASK_CACHE_C8_BOUND.json` under `in/c8r/`); where only
   digests exist, compare digests of the served queries and responses.
4. Portable opaque Orchard bootstrap and packet (relative staged roots, no Trinity path, no project,
   benchmark, dataset, model or method word; run the name inventory check on the packed bytes), remote
   return authentication and governed fetch: reuse build R's launcher patterns (`submit-command`,
   `record-submission`, `fetch` through the IO governor, `report`).
5. Outer deadline watchdog, item-start cutoff and return reserve as V1c S7.
6. ReVSI dense G3T source: tier-32 clips cannot give 64 distinct frames. Add a binding parameter
   `--g3t-source {clip32,original}`: `clip32` runs G3T on the clip's 32 anchors (the frames the model
   sees) and labels every harness report "G3T on the 32 viewed frames, not the pre-registered dense 64";
   `original` needs a registered clip-to-original-video mapping file with anchor correspondence (open
   input; refuse without it). Production refuses until the P8 freeze file names the source. The e2e
   reader keeps its towers inside `generate` on its own frames.
7. Whole-worker CPU rehearsal of ReVSI with the production CONFIG changed only in transport, for both
   readers, two videos; record executed lines; list Orchard-only lines.
8. Then VSI-Bench 5,130 the same way (cohort, media manifest of 288 videos, name inventory, fixtures,
   production-CONFIG rehearsal). If time runs short, ReVSI complete and VSI listed as not done.
9. SIZING.md: keep the measured-rate method; add the SAM 3 term from any elapsed-time field you find in
   named K1 or C8r files (C8r's `native/out2/` receipts, V1c `out/SIZING.md`), else keep it symbolic.

## Deliver
Update `out/NATIVE_KIT_READY.md` (state READY or NOT READY per benchmark x reader in its first
sentence, then what changed, tests and their results, executed-line census, open inputs), a new
`code.tar` with hashes, `SHIP_SHA256SUMS`, `DIFF.md`, `RUN.md`. Do not submit or upload anything.
