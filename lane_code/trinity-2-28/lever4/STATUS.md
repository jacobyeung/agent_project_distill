# lever4 STATUS (trinity-2-28; started 06:19Z 11-21; 10 h timeout ~16:19Z; rotate event at ~15:19Z)
Lane dir /scratch/jjyeung/orch_n30/lever4 (work/, out/, inbox/; lever3 copy in from330/lever3 incl. its /dev/shm scripts r1c/r4c). Kits: /scratch/jjyeung/orch_n30/lever1_c/{r4kit,r1,boxdev}. Ledger work/ORCHARD_LEDGER.jsonl. Carriers: Claude subagents only (ORCH 0619Z).
## Orchard: host key accepted by USER (ORCH 0658Z); hold lifted. kex drops: wait 60 s, retry once. (STATUS checked 10:11Z: rank 1 CPU real-unit build running)
## Rank 4: DONE 09:10Z
- GPU read 174108 (token 2d1983684f183) COMPLETED: ORIG 100%, REVSI 100% (290/290 each), gate no change, arm D closed. RESULT 0914Z; plan record Rank 4 read entry written. Files events/lever/files/r4/, lever4/out/r4_gpu_174108, r4kit/out/*_174108*. Deaths fixed on the way: 173990 boot closure (causal_conv1d/fla absent), 174087 batch merge (transformers 5.19 dict states). Repeat on N's first export waits for that export.
## Rank 1 (waiting for general)
- a4282fee306d6 (placed): CPU check 174121 PASSED on preempt 12:42Z with the real unit (lever4/out/r1_cpu_174121). GPU submit = /dev/shm/lever4/r1/o_sub_hand.sh (refuses while any jjyeung job is on general; 174110 jjy_allonv_dsi holds general to ~21:10Z). Default (QUESTION 1302Z): submit it the minute 174110 leaves; check every 10 min.
- a89e8fdab55d4 (debug build, placed 12:59Z) is dead: sbatch refused debug for account mt01; its CPU lock is spent. Listed as removal candidate.
- After GPU: o_fetch, o_get, depth pull (governed, --io-weight 1), relift.py (p1cpu; parity gate), cells a-g, boxdev.
## Mirrors
- Rank 4 delivery on Orchard okh7/ad2d1983684f183/0.tgz, sha dd819d503161c64c30870b17a502a4f857a425015386fe0ca5e4a274446b1a31. Returns on /data2 events/lever/files/r4 and on 2-28 lever4/out.
## Rulings in force
ORCH 0720Z: one more rank 4 GPU read after fix+review+pinned batch parity+CPU preflight; rank 1 may use general meanwhile (never both); deaths in first 10 min returning a NEW cause: fix, review, CPU preflight of the failed path, resubmit without asking (RESULT per death); repeat cause / no return / death after 10 min -> orchestrator. Item 4: before each rank's next GPU read, its first real batch through the whole forward on CPU in the pinned env.
2211Z/2244Z resubmission terms; 0933Z /project floor 5 GiB (df in submitting call; replaces 2329Z 15 GiB); 0933Z rank 1 real unit inside Orchard CPU check: yes; 2222Z item 2 (ext4 job_tmp, <=50 MB /project); 2337Z rank 4 first, never both on general; 2244Z item 3 same flags; 2351Z boot+import before staging; 2152Z host-key -> BLOCKER; 0619Z Claude only.
