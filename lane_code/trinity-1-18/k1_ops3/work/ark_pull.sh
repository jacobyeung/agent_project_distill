#!/bin/bash
W=/scratch/jjyeung/orch_n30/k1_ops3/work; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams
/usr/bin/python3 -s $W/ark_pull_launch.py >> $W/ARKPULL.log 2>&1; rc=$?
[ -e $G/k1_ops3_ark_pinned.json ] && mv $G/k1_ops3_ark_pinned.json $G/k1_ops3_ark_pinned.done.$(date +%s)
h=$(sha256sum $W/k1_arkit_pinned_2200.tar | cut -d' ' -f1)
echo "launcher rc=$rc sha=$h expected=8049ab2e3f3497dbe8a13f0a688e6b35f19336cb10d6f0ee9996caa739f3755e $(date -u +%FT%TZ)" >> $W/ARKPULL.log
