# Mask-decoder grounding (MDG-3D): a [SEG]-token mask decoder with presence and 3D lifting (designer record, 2026-11-09)

## Question
T0's own clicks are the routing bottleneck. Its LM-text points land in the mask 58-61% of the time and refuse absent objects 36-88% of the time, while GT clicks let the routed programs beat direct by 15-31 points. The user asks for a drastic fix (11-09): the LM emits a query token whose hidden state prompts a SAM2-style mask decoder over every frame; the masks, with depth or point maps, give 3D centroids and extents; the target is >= 90% in-mask and >= 90% null-on-absent; the result stays one end-to-end model with RGB video in. What do we build, how do we warm-start it, and what is the smallest decisive test?

## Answer
- **Build MDG-3D on the current Qwen3.5-9B.** A routed call `<ground obj="NAME">` ends in a query token. A 39M-parameter decoder reads that token's hidden state and the frame features the prefill already computed, and returns, for every frame, a mask, a presence probability and an interior point. A fixed lifting layer turns masks plus the model's own depth and pose (or G3T point maps) into a 3D centroid, a gravity-aligned extent, closest-point distances and the first frame seen. The result re-enters the stream as text.
- **Presence is decoupled from localization** (SAM 3): a global presence token per object times a per-frame presence score. The LM never decides null with a coordinate token again.
- **No base switch.** The grounding failure is the coordinate-text interface and the missing presence head, not the 9B backbone. Switching bases discards T0's pose and depth heads; the decoder is base-agnostic.
- **Decisive test MDG-A:** frozen T0 m800, decoder trained from scratch on the 9,128 r7 full-instance clips, 8 H100 x 2.5 h (~36 GPU-h to the read), read on evalx's 1,000-item in-video set and the CP1 dev pool. Bars below.
- **Expectation, honestly:** null-on-absent ~92% (88-96), in-mask ~86% (80-91) in the first run. The 90/90 target probably needs stage B (span-gated LoRA, more mask data). P(GO) ~65%, P(90/90 in MDG-A) ~35%.
- Status: DESIGN (one of the radical-architecture designs; awaiting the judge).

## Why LM coordinates plateau and masks do not
- **One decision per prefill.** Each pointing row pays an 8-10K-token prefill for one point. An MDG unit supervises ~34 labels x 32 frames x 76,800 pixels per prefill.
- **The null decision is one token.** It is ~5% of an absent row's gradient (loss_doctor 06:13Z), and it erodes under mixed training: single-image null 72 -> 48 -> 36% (T0 m200 -> m600), in-video 88 -> 74% (m400 -> m600). GSVA shows the same failure in the literature: on gRefCOCO a single [SEG] reaches 11.96 N-acc, multiple [SEG] 30.32, and adding [REJ] 56.45.
- **Coordinate CE has no spatial metric:** a digit one cell off costs as much as one across the image.
- **A click has no extent.** With GT-oracle interior clicks, abs distance reaches only 31.3 vs 56.9 with GT edge clicks (evalx 0744Z). A box composed from a GT mask and GT depth reaches size MRA 84.1 vs Qwen's native 3D box 66.7 (QWEN35_NATIVE_BOX3D).
- **Program fixes cannot rescue false positives.** The size-0 fix and the fused scheme recover only 2-4 points of P1 (evalx 0744Z), because 66% of absent objects get a point.

## Architecture
All frame features come from T0's single prefill; the decoder adds no new LM forward. Grid sizes assume the current ~140 merged tokens per frame (10x14 merged, 20x28 ViT patches, frames 320x448).

| module | attaches to | trainable | init |
|---|---|---|---|
| Tap mixer + LM projection | LM hidden states at layers 16, 24 and final-norm, at each frame's visual tokens (GH0 `grounding_features.capture` hooks), softmax mix -> LN -> Linear 4096->512 | 2.1M | default |
| ViT projection | Qwen ViT blocks 9/17/25 pre-merge outputs (the depth head's `vit_layer_hooks`), 3 x (LN + Linear D_vit->512) | ~1.8M | default |
| Memory fuse | LM map upsampled x2 + ViT map -> conv3x3 -> 512 @ 20x28 per frame; 2D sincos + frame-index embedding (sincos of f/F + learned) | 2.4M | default |
| RGB stem | unpatchified `pixel_values_videos` (first frame of each duplicate group, GX unpatchify code), ResNet-18 conv1..layer2 -> stride 4 (64 ch) and 8 (128 ch) | 0.7M | ImageNet |
| Pixel decoder | memory 20x28 -> 40x56 (+stem s8) -> 80x112 (+stem s4); 64-d pixel embeddings per frame, shared by all queries (Mask2Former style) | 0.6M | default |
