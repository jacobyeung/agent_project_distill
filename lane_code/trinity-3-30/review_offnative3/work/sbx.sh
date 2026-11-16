#!/bin/bash
# Run a command with b07_offread and /dev/shm/b07_n7 redirected to the review copies (writes stay in review areas).
exec bwrap --dev-bind / / --bind /dev/shm/review_offnative3/w /dev/shm/b07_n7 \
  --bind /dev/shm/review_offnative3/base /scratch/jjyeung/orch_n30/b07_offread "$@"
