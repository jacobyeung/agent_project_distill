# Recovery map after the trinity-2-18 and trinity-2-28 outages (2026-11-15)

Status: complete 2026-11-15 ~17:30Z (lane recover_map2, trinity-3-30). Listings only; no rebuild started, no copy made except a 49 MB read of the Devin sessions database into the lane folder.

## Question

trinity-2-18 went down at 10:00Z with every lane folder (`/scratch/jjyeung/orch_cd`), and trinity-2-28 stopped accepting logins at about 16:15Z. For each queued experiment and build, which inputs survive elsewhere, and what is the cheapest restart?

## Answer

The model state survives, and most of the work built on it does not. Google Cloud Storage holds every LEG-S1 export (steps 1, 50, 100, 200, 400 and 544), and Orchard holds slot A, the direct reader, its runtimes, the videos, the official questions and the raw returns of every accepted read. Two restarts can therefore begin at once: the official VSI-Bench direct read of step 544, which lane evalx27 is already rebuilding, and the ReVSI direct read once that kit exists. The rest of the queue must be rebuilt, or exists only on 2-18. That covers the native routed candidate C7, the stacked seal's tree (`tree_r1`), its rows (`rows_r3`) and grammar, the R2 contract patches, K1's rules file and GT rasters, and the reviews. trinity-1-18 holds a partial code mirror with three useful pieces: the LEG-S1 base tree, the native package s24_05 sources, and 93 GT rasters. No session store holds the bytes of any file a lane wrote on 2-18: Codex homes and Devin session databases lived on 2-18's own disk.

## Where things were looked for (all listings; times UTC)

| place | how | result |
|---|---|---|
| trinity-3-30 `/scratch/jjyeung` | local ls / du -s / bounded find | old distillation material only (orch_cd: mp3d_dl, nav_build, nav_survey, p1cb_build2_*, p2_build, all 11-06); Devin trace imports stop at 11-11 22:25Z and hold 640 captures of main's lanes, none of orch_cd; `io_governor` is a partial helper copy |
| trinity-0-13 | one ssh 16:44Z (`work/LIST_0_13.txt`) | orch_cd from 11-07 to 11-12 (argon_traces, derivgen, devs1_direct, evalx, mdg_build, mixdata, streams2, weak_data, p1cb_build, p2_build); `devs1c_models/cp1` is a dangling link to the removed `/dev/shm/jjyeung_evalx`; 271 GB free |
| trinity-0-28 | two ssh calls, 16:45Z and 17:04Z (`LIST_0_28*.txt`) | `/scratch/jjyeung/evalx_native_step200_20261114`: base model 85fc3486 (19.33 GB, VERIFIED sha d8de88fb), native runtime (17.81 GB, 158,296 files, RECEIVED sha 14cd2fd8), export_BAD (partial m200, FAILED); 128 GB free (96% used) |
| trinity-1-8 | three ssh calls, 17:01Z to 17:07Z (`LIST_1_8*.txt`) | `/scratch/jjyeung/orch_cd` is a link to `/dev/shm/jjyeung_mdg_next/root/orch_cd` (11-10 tree: mdg_build/work/{data/t0mind, fla, t0bundle} 21 GB, ttower 4.5 GB, evalx 0.6 GB with a 11-13 native parity probe, nav_build, sam3_tower, tower_read, mdg_next); `/dev/shm/jjyeung_evalx` 88.6 GB is 11-10/11-11 material (sj 39.5 GB, rt/85fc3486 base model 18.9 GB, fsw 18.4 GB, g3t 5.5 GB, teach_r5, head labels); /scratch 0 B free |
| trinity-1-18 | lane k1_ops3's files `SCRATCH_1_18_LISTING.txt`, `ORCH_CD_MIRROR_1_18_FILES.txt` (140,504 files) | the mirror described in rows 2 to 5 below; also `/scratch/jjyeung/k1`, `geo_bakeoff_kit`, `geo_bakeoff_runs_0ef8fe08`, `own_ground_gpu/kit_{A,B}`, `mask_recall_run`, `devs1_mask_run` |
| Orchard | lane evalx27's `ORCHARD_INVENTORY.md` (16:42 to 17:05Z) | reader pieces, runtimes, base model alias, videos, questions, 17 returns, slot A |
| GCS | `gsutil ls -l` 16:55Z (`work/GCS_q8_20261115.txt`, `GCS_q7.txt`) | q8/8865619b: 48 objects, 124.07 GiB; q7/7822a58d: 27 objects, 142.24 GiB (CP1-Rv kit inputs held for jobs 168042 and 168043) |
| Mind | mover receipts `/data3/jjyeung/mover_20261111/receipts/` | batch 4 orch_cd archives verified 11-14 18:59Z: streams2, mixdata, mdg_build (1.07 GB, 11,440 members), gx_build, derivgen, p1c_build_d451, p2_build; ttower aws_tk/tu/tg; Argon archive |
| NFS session stores | named-file reads | Codex `/home/jjyeung/.codex/sessions/2026/11/{14,15}`: 60 heads read, all main's (cwd codex_launch_*, orch_home, gemma_dsi4d_1115...), none orch_cd; `agent/scratch/codex_runs` stops at 11-10; Devin CLI logs `/data2/jjyeung/cli_agents/home/.local/share/devin/cli/logs/devin_2026111{3,4,5}-*.log` hold every exec command of the 2-18 lanes but no outputs; the shared Devin `sessions.db` is corrupt and its newest message is 2026-09-23; orchestrator transcripts `/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/*.jsonl` hold what the orchestrator read |

## Map, one row per item

`restart now` = every input verified on a reachable host. `rebuild` = a base survives and the item can be regenerated. `only on 2-18` = no copy and no practical rebuild before 2-18 returns. "(unverified)" marks a line I did not check myself.

