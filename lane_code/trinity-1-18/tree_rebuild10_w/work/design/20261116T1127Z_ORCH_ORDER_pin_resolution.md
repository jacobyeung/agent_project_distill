# ORCH ORDER: pin resolution and the base ViT's train flag in the next-leg kits
Sealed kit 07ca49df (config b02e4385.json) sets no max_pixels / min_pixels, so the Qwen3.5 processor default decides the training resolution; it also has no explicit freeze/train list (full_ft code decides the base ViT). Readers on other runtimes can silently differ.
- In A0/A2 kits, set max_pixels and min_pixels explicitly to the values D0 actually uses (read them from the processor config bound by base_identity c2022362...), and record them in the kit manifest and artifact.json.
- Add an explicit per-module trainable list (base ViT, merger, private ViT copy, pose head, depth head, LM) with LRs to the kit config, equal to what full_ft does today; a test asserts the list matches requires_grad after model build on CPU.
- Every reader kit asserts the same max_pixels and frame layout (duplicate, 32, frame_markers on) as training.
Facts: distill_design/ARCHITECTURE_CURRENT.md.
