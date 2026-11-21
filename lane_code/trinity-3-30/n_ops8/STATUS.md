# n_ops8 STATUS (successor resumes from this file alone)
Updated 2026-11-21T00:10Z at rotation to n_ops9 (brief B/briefs/n_ops9.md). n_ops8 ran 2026-11-20T20:03Z-00:12Z on trinity-3-30; it submitted and cancelled nothing.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. X=/project/community/jjyeung/okh7/x_22c714e1 (Orchard).
## Now
- No job of ours on Orchard (watcher 00:03Z: adv_jobs []). Launch NOT submitted. tree_rebuild24 owns kit, discovery, e3, launch QUESTION (forecast ~03:30Z or later), submission.
- Kit line: 24m4z7 built (seals n bd20a9fe, n_go f392c95e; k/y.json e66824ff, 27 objects identical to 24m4z4 + "publication" block); review rev24m4z7 running; discovery-pin build 24m4z8 (armed qd, ORCH 2258Z option B) running; e3 harness 24m4z9 next (Trinity test with sessions 900003, then e3 on Orchard after fix round 24m4z10 + review: held -> mint (112 names if z10 adds a 28th object; take names from z10 y.json) -> release, 2 GiB rate payload, readback by us). Stop window: ORCH ANSWER 2345Z (measure first; config change authorized).
- Discovery 173912 (unarmed qd) FAILED 22:54:11Z in mode q by design (R1_ROUTING_SELECTION_PIN_MISSING); mode r witnesses: routing_selection.json a49f117f, db_bytes.json 5c4929e1 (BLOCKER 2255Z). Next discovery = armed qd; duty as in brief.
- /project/community free 28 GiB (steady since ~22:22Z; other tenants). Floors: discovery >=30 GiB with node-local logs (25 accepted if its /project writes <1 GB, ORCH 2256Z); launch on final kit >=20; CPU >=20 (lever 15). BLOCKER at once at 22 GiB. Owed: RESULT at recovery >150 GiB; BLOCKER near 0 with a job pending.
- Main-project notice NOT sent (at launch QUESTION). Newest known main inbox INBOX_TO_DISTILL_ORCH_20261118T002059Z.md.
## Sessions (n_ops8 tool, use in place)
- n_ops8/work/gcs/sess_job.sh JOB [names|mint|install|all] [DEST_DIR] [YJSON]; private/ (0700) holds sess_<job>.json + installers; never print URIs. y files: y_24m4z4.json f574ecec, y_24m4z7.json e66824ff (same 27 objects). Fetch the final kit's y.json from trinity-1-18 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z<N>/out/kit_n_go/k/y.json with one B/tools/tssh.sh call; check vs SHA256SUMS. Procedure: mint (local) -> wait for a watcher line in n_ops1/work/mon/hist.txt -> sleep 62 -> install (one ossh call) -> RESULT with sha256 -> submitter releases.
- Minted so far: 173911 (e2, used; all 108 were 308/no Range after the harness bug), 900001 + 900002 (Trinity tests, used; readback 16/16 each), 900003 (e3 Trinity test, used; readback 16/16 RESULT 0007Z; tool n_ops8/work/gcs/readback.py LIST). Ledger lines in n_ops1/work/ORCHARD_LEDGER.jsonl.
- Readback tools: n_ops8/work/gcs/status_range.py SESS NAME.. (HTTP code + Range); mint_n.py check NAME; receipt-list compare script pattern in readback_900002b.out's generator (see RESULT 2341Z).
- Launch GCS (24F) sessions: X/n_s/sess.json sha256 15c543a1, minted 2026-11-19T18:59Z (expire ~11-26T18:59Z) - for the OLD kit only; the 24m4z launch needs sess_<job>.json.
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 sleep 120, mon/noadv present (mv to noadv.used at the launch submission; keep for discoveries); mon2 job=none.
- parse.py 04eab4d2 (BARS.md line 1 + n_ops8 lines): adds HELD (JobHeld* >= 15 min), @@LSTATE (node-local $Q/live_spool/state gcs_*.done), @@RCPT/NO_RECEIPT_10MIN. Tests 47/47, replay 91 checks 0 FLAG. Backups parse.py.f74be9dd, parse.py.586cb4a9, inner.sh.61ef1f45, inner.sh.lstate.
- tmux nops8_hk: n_ops8/work/hkguard.sh (host-key warning in a raw check -> mon/stop + n_ops8/work/HOSTKEY_ALERT). Keep it running.
- Helpers n_ops8/work/{chk.sh, wait.sh (fs trigger <25 GiB, HOSTKEY_ALERT trigger), w.sh, cyc.sh, wit.sh.tpl}; copy to n_ops9/work with L=n_ops9 and chk.since.
- Orchard ssh blip 21:42-21:45Z (login side closed connections; host-key warning seen once by tree_rebuild23, ORCH 2152Z: hold on a second occurrence).
