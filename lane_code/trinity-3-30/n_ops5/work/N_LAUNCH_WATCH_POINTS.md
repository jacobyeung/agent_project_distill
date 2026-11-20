# Vehicle N launch watch: refusal points after preparation, in order, with expected times (n_ops5, 2026-11-20T09:27Z; ORCH ANSWER 0924Z item 3)
T0 = job start (TK_JOB_START). R = time review.json is installed in x_22c714e1/n_r. S1 = time of step 1. Times use P's 172660 rates (preparation 141 min at 48 CPUs; step 130-156 s; 600 s per checkpoint or export) and discoveries 173626/173661 (staging 18-22 min). The watcher polls every 60 s from submission until the first checkpoint and the first export land; each point below has a bar in parse.py f74be9dd (n_ops1/work/BARS.md), so a miss shows within one poll after its deadline.
| # | Point (where it refuses) | Evidence of pass | Expected | Bar (FLAG) |
|---|---|---|---|---|
| 1 | resolve + stage full (z.py/tk_stage) | "stage full done", "init mirror verified" in j log | T0+20 min | JOUT_ERR, STALL |
| 2 | a.py q preparation + host receipt | q.log {"ok": true}; p/q/RESULT.json ADMIT | T0+2 h 40 min | LOGERR_q.log, NOT_ADMIT, STALL |
| 3 | d.py rooms, h.py v.json, rv.py census refusals before the wait | live/WAITING_REVIEW | T0+2 h 45 min | LOGERR_rooms.log/h.log, JOUT_ERR |
| 4 | review receipt pin (h.py/rv.py mismatch, R1_REVIEW_TIMEOUT at 120 min) | review.json installed, t.log appears | R+5 min (R ~T0+3 h if n_review2 starts at 75% preparation) | NO_REVIEW_30MIN, NO_TRAIN_START (20 min after R) |
| 5 | t.py 4 ranks: network_preflight, attempt_<job>.json, u.py admit(cfg) on every rank (entry.admit legacy branch, tree C') | t.log network_preflight line; attempt json | R+10 min | LOGERR_t.log, JOUT_ERR |
| 6 | first optimizer step (processor on every rank, tree C') | metrics line "step": 1 on 4 ranks, finite losses | S1 ~ R+20-30 min (~T0+3.5 h) | NO_FIRST_STEP (45 min after t.log), NONFINITE, STOP_BAR |
| 7 | first checkpoint (first_step_admission, step 1) | new checkpoint_000001/ dir | S1+10 min | NO_FIRST_CK (25 min after S1) |
| 8 | first export m100 (tar + 4-part GCS upload, done marker) | live/gcs_m100.done | S1 + 99 x 130-156 s + 2 x 600 s (2-hourly checkpoints) + 600 s ~ S1+4.0-4.8 h (~T0+7.5-8.3 h) | NO_EXPORT_m100 (45 min after step 101) |
| 9 | export m200 | live/gcs_m200.done | m100 + 3.8-4.6 h (~T0+11.5-13 h) | NO_EXPORT_m200, TIME |
| 10 | self-stop (limit - 3,600 s): stop checkpoint to GCS ckstop, stop export _mstop | run_<job>.json stop_reason budget_or_signal; gcs_mstop*.done | T0+23 h | TIME, state checks |
Not proven before the launch (first met in the launch): points 5-8 under tree C' with N's prepared rows on 4 ranks (ORCH 0924Z: the launch is its own canary).
