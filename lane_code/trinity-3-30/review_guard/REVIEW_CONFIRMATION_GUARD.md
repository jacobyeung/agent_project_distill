# REVIEW_CONFIRMATION_GUARD: CONFIRMED (GO) (review_guard, Devin, trinity-3-30, 20261116T1733Z)
Confirmed: guard_read.py 5424e41c, code_g2.tar 6024aa2b, FAMILY.json 23cadfce, rehearsal whole/ffdbd8e3 (RESULT PASS_WITH_EXPECTED_REPORT_REFUSAL, log rc=0). Tests in /scratch/jjyeung/orch_n30/review_guard/work/.

## Fixes (my verdict's failing tests, paths adapted, assertions kept: test_fixes_v6.py 8/8 pass)
1. Report: --candidate-artifact is required (missing: argparse exit 2; empty: exit 3). Step 544 as candidate exits 3 and writes no report. RUN.md:94 binds CONFIG.artifact_sha256 without --self-pair and pins the source sha. Builder suite 38/38 OK with the real 170056 R1; my mutant rerun kills 31/31, each through a named failing test.
2. DIFF: applying DIFF_C8R.patch (== DIFF.patch) to code_c8r.tar f4535bc0 reproduces code_g2.tar byte for byte (diff -r empty). The DIFF.md table lists all 23 patched files, reviewed/ included.
3. Receipts: the rehearsal return (fetched == returned == store, 74eb7bdd) holds CANDIDATE_STAGE.json, CHECK.json and STAGE_RECEIPTS.json. Its stage file equals the root bytes, and its CHECK.json equals exports/359fcc3c_m50/CHECK.json. verify_return accepts the real return and refuses a dropped CHECK, stage or inventory, a changed stage byte, a resealed unverified CHECK, and an inventory set to step 544 (test_fix3_tamper.py 8/8).
4. Transfers: RUN.md has no pv; every fetch and upload goes through governed_transfer.py. That wrapper builds a stopped Python root that never execs and a ratelimit member, registers with --tier 3 --allow-resume --io-weight 1, gives each stream its own record and renames it .done.<epoch>. Its register.py arguments match the helper's argparse.

## Refute attempts on the report changes (no wrong PASS found; test_refute_v6.py Strict 10/10)
- String or missing call/no_answer flags, a string refusal, a list decode, a non-string decode text, mixed checkpoint ids, a wrong baseline, and --seed or --draws overrides all exit 3.
- In the rehearsal, the R1 checkpoint_sha256 equals CONFIG artifact 49a4b4b9, so the artifact check passes. The report then refuses on the 616 missing items, the expected refusal for the 20-row fixture.

## Advisory, non-blocking (Advisory tests fail as written; RUN.md reaches none of them)
- A1 guard_read.py:242: --self-pair accepts a non-544 candidate and labels a real read as a self-pair. Requiring candidate_artifact == STEP544_ARTIFACT when the flag is set would close this.
- A2 guard_read.py:357-363: a refused run leaves an earlier PASS GUARD_READ.json in the same --out. RUN.md uses a fresh per-token directory.
- A3 guard_read.py:103: scores are not type-checked ("1" and True read as 1.0). The value is unchanged, so the verdict is unaffected.
- A4 transport.py:115-133: verify_return checks the stage inventory only for internal consistency and never against the CONFIG step or artifact. The in-job check (worker.py:26-46) and guard_read's artifact pin cover this.
- A5 RUN.md:89-90: the EXIT and return fetches register one after the other without --priority. LANE_RULES asks for all of a step's streams to be registered at once.

Not checked: GPU parity, real tensors, live governor, Orchard and GCS. No GPU, ssh, Git or deletion was used.
