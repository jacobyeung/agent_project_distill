BUILT_AND_LOCALLY_VALIDATED — r1_drv7, Packet A round 12.

Archive: p_9dd2fbb7.tar
SHA256: 9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192
Config: fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f
Run/job: 673bc60f / a15_cot_ap673bc60f.
Bundle/kit: /project/community/jjyeung/okh7/i_69d2930d and x_69d2930d.

Start at u1.sh. m0.sh, m0.v1.sh and m0.out are byte-preserved; PRESERVED_R1DRV7.json records their hashes. The old bundle/kit at *.f170956 remain required admission evidence. No completed driver was rerun.

pr1.sh and pr2.sh support general and advanced. Select advanced, 48 CPUs, 800G RAM, no GPU request, and 06:00:00. The sealed CPU binder and stub sbatch argv tests accept both partitions. Live scheduler placement was not queried.

Use go_submit_canary_9dd2fbb7.sh immediately after the advanced proof submission, with its job ID and the SHA of events/r1_ops/20261118T0044Z_ORCH_RULING_canary_launch_parallel_proof.md. It binds job.id, the proof submission output/marker, and an active PENDING/RUNNING proof. It checks six-hour CPU/no-GRES resources, prints the pending reason, and refuses held or unsatisfiable proofs. It authenticates packet members, writes byte-equal-only canary GO, checks queue/accounting, and refuses a second attempt. The training record binds sbatch's ID to the retained gate marker and GO. Training keeps advanced, four GPUs and 13 hours. go_submit_9dd2fbb7.sh retains the non-canary PASS-proof path for a separately authorized later launch.

Current checks pass: 27 canary wrapper cases plus repeated-attempt refusals; 4 review acceptances and 24 A/B/ambiguity refusals; eight-review, certificate and session builders; seven actual antecedents; 17 proof submission guard cases; both sealed proof partitions; PASS-wrapper GO reuse and mocked export absence checks; frozen files and all 37 member pins; REMOVE corruption refusals; 108 switch cases; shell/Python syntax; final scan generation. See *_p7.txt. Tests reuse the retained local READY kit because derived-kit inputs are unchanged; they do not claim a new full derivation or production admission proof.

archive_delta_p7.json independently verifies that only s.sh and sums.txt differ from p_a5dc8f30.tar. The proof, jb.sh and training sbatch line are byte-equal. The frozen KIT_DIFF12.md reports 0/99 derived-kit differences against the scanned kit; its complete visible surface requires a quick scan.

R1P8's actual Packet A GO is accepted and pinned with all seven antecedents in rv1.sh; see review_status_p7.txt. Its operator conditions require proof provenance, resource/reason evidence and the training-ID/marker association. The wrapper checks and prints these; the operator must retain them in the launch event. The requested six-hour proof limit applies. sc1.sh and si1.sh remain inert placeholders until independent certificate and fresh session inputs arrive. No production certificate, live session or job was created here. The operator must enforce the ruling's admission/audit/first-step kill criteria and write the card/row evidence before training step 1. README.md contains the ordered commands and expected outputs.

All writes stayed in drv_p5. Local Python used /scratch/jjyeung/envs/p1cpu/bin/python. No SSH, Orchard call, Git, GPU, deletion, job stop, external event write or mirror transfer occurred. DRIVER_SHA256SUMS.txt seals this handoff; check it before installer builders run.
