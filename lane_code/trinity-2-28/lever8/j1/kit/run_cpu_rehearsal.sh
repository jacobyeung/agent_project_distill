#!/bin/bash
# CPU rehearsal of the J1 detector pass through the launcher's own inner command line (launch_gpu.sh rehearse-cpu): nice 10,
# 8 threads, no CUDA device, output j1/work/rehearsal_cpu. Usage: bash run_cpu_rehearsal.sh <capture> [anchors]
#   (the brief's capture: PROMPTS_J1.json rehearsal_capture, the one with the fewest operand-frames)
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$KIT/launch_gpu.sh" rehearse-cpu "$@"
