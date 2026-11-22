#!/bin/bash
# Re-decode all held raw members with the k6-matched cv2 (4.14.0.94) into frames_k6/; never touches frames/ or DECODE_ARKIT.json.
set -u
cd /scratch/jjyeung/orch_n30/lever7/gtcd/arkit
export PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=/scratch/jjyeung/.cache
/scratch/jjyeung/envs/k6cv2/bin/python -B tools/decode_arkit.py --raw raw --plan plan/PLAN_ARKIT.json --frames frames_k6 \
  --rejected frames_k6_rejected --manifest DECODE_ARKIT_K6.json --workers 8 > cv2k6/decode_k6.log 2> cv2k6/decode_k6.err
echo "RC=$?" >> cv2k6/decode_k6.log
