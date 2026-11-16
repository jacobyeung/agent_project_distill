#!/bin/bash
# One step-544 part as its own governed record (lane k1_ops3_w544b_pNN); sha check after; never retry.
W=/scratch/jjyeung/orch_n30/k1_ops3/work; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams; n=$1
SHA=(5cd24e72f5b8a4f7ad6cb73d27dd426042be25e7600dcf00e4038de4c129f31a 6ed00d4724b1cfc57d0af6a017639d88284a139479ebf8b9943f280dc6c5df9f 557d8f649b964bd81a1c022dd87db18bdca0c2b61e420c2eccb1fc446a58f7bf 37e64c63c294a3eda298c61f637087c84851afa17f42ad18a4d24c8823c7f686)
p=$(printf 'k1_ops3_w544b_p%02d' $n)
/usr/bin/python3 -s $W/w544_launch.py $n k1_ops3_w544b >> $W/W544_p$n.log 2>&1; rc=$?
[ -e $G/$p.json ] && mv $G/$p.json $G/$p.done.$(date +%s)
[ $rc -eq 0 ] || { echo "part $n launcher rc=$rc" >> $W/W544_p$n.log; exit 1; }
f=$(printf '/scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part%02d-of-04' $n)
h=$(nice sha256sum $f | cut -d' ' -f1)
[ "$h" = "${SHA[$n]}" ] && echo "part $n sha OK $(date -u +%FT%TZ)" >> $W/W544_p$n.log || echo "part $n SHA MISMATCH $h" >> $W/W544_p$n.log
