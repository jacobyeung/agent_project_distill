#!/bin/bash
# r1_ops7: read-only export check for run 6ed2c7aa step $1 (login node): marker, artifact on pool, GCS parts
export TZ=UTC; K=/project/community/jjyeung/okh7/x_ee227714; S=${1:?}; F=$K/o/gcs_6ed2c7aa_m$S.done; A=$K/runs/6ed2c7aa/m$S/artifact.json
date -u +%FT%TZ
if [[ -f $F ]]; then echo "DONE $(cat $F)"; echo "DONESHA $(sha256sum < $F | cut -c1-64) $(stat -c %Y $F)"; else echo "NODONE"; fi
if [[ -f $A ]]; then echo "ART $(sha256sum < $A | cut -c1-64) $(python3 -c "import json,sys; a=json.load(open(sys.argv[1])); print(a.get('step'), a.get('config_sha256'), a.get('schema'))" $A)"; else echo "NOART"; fi
if [[ -f $F ]]; then env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud gcloud storage ls -l "gs://cmu-gpucloud-jjyeung/q8/8865619b/6ed2c7aa_m$S*" 2>&1 | sed -E 's#gs://[^ ]+/##' | tail -6 | sed 's/^/GCS /'; fi
grep -E "export|m$S" $K/o/172660.steps 2>/dev/null | tail -3 | sed 's/^/STEPS /'
squeue -h -j 172660 -o 'JOB %T %M' 2>/dev/null
