<!-- recovered by seal_plan: transcript=a97ad692 line=462 utc=2026-11-15T04:54:06.875Z kind=written original_path=/scratch/jjyeung/orch_cd/official544/inbox/$(date_ORCH_ANSWER_runtime_versions.md heredoc_quoted -->
# ORCH ANSWER: package versions of the accepted direct runtime

I know of no receipt that binds job 169526's torch, torchvision and transformers builds. Leads, each a single local file you may read (do not treat any as proof for 169526 unless it names that runtime asset's hash):
- `/scratch/jjyeung/orch_cd/orchard_kit/work/closure_x/pins_cu129.txt` and `/scratch/jjyeung/orch_cd/orchard_kit/work/okmix/requirements.txt` (pins of the Orchard environment builds);
- `/scratch/jjyeung/orch_cd/evalx/work/milestone/STATUS_RETAINED_20261114T0358Z.md` line 690 (the Trinity vLLM environment on trinity-1-18: torch 2.13, transformers 5.19, torchvision 0.28).

Your default stands: finish the kit, the score controls and the coverage audit; state the GPU package versions as unverified unless one of those files matches the accepted runtime asset hashes. Make the kit print torch, torchvision, transformers and vLLM versions into its first log lines and its PACKET, and make the first GPU boundary check compare frame count, grid and visual-token count per item with the accepted step-544 dev-S1 packet before any item is scored.