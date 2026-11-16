#!/bin/bash
# Build the one-file R0 archive, then copy it to /data3 through the IO governor (copy_archive.py, write + sha256 readback).
set -eu
L=/scratch/jjyeung/orch_n30/b10_reserve; cd $L
A=$L/archive/R0_RESERVE_20261116.tar; DEST=/data3/jjyeung/n30_b10_reserve/R0_RESERVE_20261116.tar
mkdir -p archive
if [ ! -s $A ]; then
  tar cf $A.part --sort=name --owner=0 --group=0 --numeric-owner STATUS.md code in/d0v5_templates.jsonl in/WITHHELD_ROOMS_80.json \
    out/R0_SCENES.json out/R0_ROOMS.txt out/R0_DEV_ROOMS.txt out/R0_REGISTRATION_NOTE.md out/CENSUS.json out/CENSUS_PER_CAPTURE.json \
    out/clean_candidates.txt out/census_stdout.txt out/scannetpp_assets.json out/DEFERRED.json out/FRAMES_MANIFEST.json out/REDECODE_CHECK.json \
    out/qsets out/questions out/questions_meta out/frame_manifests frames
  mv $A.part $A
fi
SHA=$(sha256sum $A | cut -d' ' -f1); BYTES=$(stat -c %s $A); echo "$SHA  $A" > $A.sha256
JOB=$(python3 -c "import json,base64,sys;print(base64.b64encode(json.dumps(dict(id='b10r0_archive',transport='archive',tier=3,priority=15,expected_bytes=int(sys.argv[1]),source=dict(host=sys.argv[2],archive=sys.argv[3],sha256=sys.argv[4]),destination=dict(host=sys.argv[2],path=sys.argv[5]))).encode()).decode())" $BYTES $(hostname -s) $A $SHA $DEST)
echo "$(date -u +%FT%TZ) archive $A bytes=$BYTES sha=$SHA -> $DEST"
/usr/bin/python3 -s /scratch/jjyeung/io_governor/copy_archive.py --job $JOB --receipt $L/work/archive_receipt.json
echo "$(date -u +%FT%TZ) ARCHIVE_DONE"
