#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
R=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f
cd $R && tar czf - attempt_171377.json binding.json metrics_171377.jsonl | base64 -w0
