#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
RA=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f; P=$RA/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0
ls -la $P $P/prepared >&2
cd / && tar cf - ${RA#/}/m200/artifact.json ${RA#/}/binding.json ${RA#/}/runtime_config.json $(ls ${P#/}/config.json 2>/dev/null) ${P#/}/prepared/s1_receipt.json | gzip | base64 -w0
