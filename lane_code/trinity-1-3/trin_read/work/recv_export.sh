#!/bin/bash
set -o pipefail
D=/scratch/jjyeung/orch_n30/trin_read/root/fsw/ap/8865619b/runs/469ddece
W=/scratch/jjyeung/orch_n30/trin_read/work
cd "$D" || exit 9
tee >(sha256sum > $W/export_stream.sha256) | tar xf -
rc=$?; echo "rc=$rc $(date -u +%FT%TZ)" > $W/export_recv.rc; exit $rc
