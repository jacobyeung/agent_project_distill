#!/usr/bin/env bash
set -euo pipefail
: "${O3_PYTHON:?Bind the existing Orchard native Python}"
: "${O3_NATIVE_ROOT:?Bind staged native reader sources}"
: "${LEGS1_TREE:?Bind staged frozen trainer sources}"
: "${O3_MANIFEST:?Bind the verified one-capture manifest}"
: "${O3_OUTPUT:?Bind compute-local output}"
: "${O3_KIT:?Bind this kit's staged directory}"
: "${CUDA_VISIBLE_DEVICES:?The allocation must expose one assigned GPU}"
export O3_MAX_SECONDS=5400 O3_MAX_BYTES=1000000000
exec bash "$O3_KIT/launch.sh"
