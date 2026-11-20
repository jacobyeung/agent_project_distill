# RESULT cont_ops21: D at step 400, the reworded-distance entry baseline for vehicle N, completed all 580 items in one job, so it needs no remainder
- Job 173241 (a15_cot_apda6f7936c1779) COMPLETED at 20:28:55Z in 2:51:46, 580/580, returncode 0. Its sealed argv says general; it ran on advanced (scontrol, QOS adv_4gpu_qos) on orchard-community-1, CUDA device 0, one H100. Return sha c2052ea2...; authenticated unpack and the step-400 D scorer (dbuild score_d.py = dresume score_base.py, EXPORTS[400]) passed.
- MRA and call rate by unit, step 400 vs step 544 (the merged 580 of RESULT 1615Z):
  all (580): 47.2 vs 31.3; calls 72.2% vs 98.8%
  reworded (290): 41.4 vs 17.0; calls 44.5% vs 97.6%. By unit: cm (72) 36.4 vs 2.6, calls 22.2% vs 93.1%; ft (73) 35.9 vs 11.6, calls 46.6% vs 98.6%; in (72) 47.5 vs 7.5, calls 29.2% vs 98.6%; m (73) 45.8 vs 45.9, calls 79.5% vs 100%.
  twin (290, all metres): 53.0 vs 45.6; calls 100% vs 100%.
- Reworded minus twin at step 400 (room bootstrap, 290 pairs): all -11.6 [-16.8,-6.3]; cm -11.9 [-24.8,+0.9]; ft -22.2 [-31.1,-13.4]; in -8.1 [-18.0,+2.1]; m -4.1 [-9.3,+1.0].
- Reading: at step 400 the reworded non-metre questions mostly skip the tool (22-47% calls), yet they score far above step 544 (36-48 vs 3-12), because step 544's calls returned values in the wrong unit. Metre twins still call every time and gain 7.4 points.
- Files: trinity-3-30 /scratch/jjyeung/orch_n30/cont_ops21/work/D400 (ret/ return, package/, src/, scores_D400.json). Corpus read 6ed2c7aa_s400_R0dev_D580_173241 (WROTE, 580 items, sha 9dede92c...; published).
- Its card freed at 20:29Z; k1fwd1 had the claim on the next free card. D@400's remainder kit is no longer needed.
