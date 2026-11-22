#!/bin/bash
# CPU rehearsal of arm d through the launcher's own inner command line (launch_gpu.sh rehearse-cpu): nice 10, 8 threads, no CUDA
# device, output lever7/gtcd/work/rehearsal_cpu (ARKit manifest: work/rehearsal_cpu_ark).
# Usage: bash run_cpu_rehearsal.sh <capture> [--dense <manifest>] [--out <dir>]   (e.g. scannet/scene0380_01)
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$KIT/launch_gpu.sh" rehearse-cpu "$@"
