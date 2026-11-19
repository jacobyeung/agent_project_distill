#!/usr/bin/env bash
set -eu
# Run inside N's staged patched tree after its native step-2 export exists.
# These inputs must be staged and pinned by N; this script supplies no fallback.
: "${N_INIT_ARTIFACT:?MISSING native step-400 init artifact.json}"
: "${N_INIT_ARTIFACT_SHA:?MISSING init artifact SHA256}"
: "${N_STEP2_ARTIFACT:?MISSING native first-two-step artifact.json}"
: "${N_STEP2_ARTIFACT_SHA:?MISSING step-2 artifact SHA256}"
: "${N_PREPARATION:?MISSING N preparation receipt}"
: "${N_PREPARATION_SHA:?MISSING preparation SHA256}"
: "${N_MODEL_CONFIG:?MISSING native Qwen model config.json}"
: "${N_MODEL_CONFIG_SHA:?MISSING model config SHA256}"
: "${K1_SELECTION:?MISSING pinned two-capture selection with local RGB paths and G3T FoV}"
: "${K1_SELECTION_SHA:?MISSING capture selection SHA256}"
: "${N_DONOR_BINDING:?MISSING JSON containing the exact scale_donor configuration}"
: "${N_DONOR_BINDING_SHA:?MISSING donor binding SHA256}"
: "${DONOR_IMAGE_SIDE:?MISSING explicit fixture resolution, a native patch/merge multiple}"
: "${DONOR_CHECK_OUTPUT:?MISSING output JSON path}"
replicas=()
if [ -n "${N_REPLICAS:-}" ]; then
  : "${N_REPLICAS_SHA:?MISSING replica-map SHA256}"
  replicas=(--replicas "$N_REPLICAS" --replicas-sha "$N_REPLICAS_SHA")
fi
exec nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 \
  /scratch/jjyeung/envs/p1cpu/bin/python -B -m student_pilot.scale_donor_check \
  --init-artifact "$N_INIT_ARTIFACT" --init-artifact-sha "$N_INIT_ARTIFACT_SHA" \
  --after-artifact "$N_STEP2_ARTIFACT" --after-artifact-sha "$N_STEP2_ARTIFACT_SHA" \
  --preparation "$N_PREPARATION" --preparation-sha "$N_PREPARATION_SHA" \
  --model-config "$N_MODEL_CONFIG" --model-config-sha "$N_MODEL_CONFIG_SHA" \
  --selection "$K1_SELECTION" --selection-sha "$K1_SELECTION_SHA" \
  --binding "$N_DONOR_BINDING" --binding-sha "$N_DONOR_BINDING_SHA" \
  --image-side "$DONOR_IMAGE_SIDE" --output "$DONOR_CHECK_OUTPUT" "${replicas[@]}"
