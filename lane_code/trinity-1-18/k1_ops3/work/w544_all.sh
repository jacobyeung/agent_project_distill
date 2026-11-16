#!/bin/bash
# Pull the 4 step-544 export parts one after another; stop at the first failure; never retry.
W=/scratch/jjyeung/orch_n30/k1_ops3/work; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams
SHA=(5cd24e72f5b8a4f7ad6cb73d27dd426042be25e7600dcf00e4038de4c129f31a 6ed00d4724b1cfc57d0af6a017639d88284a139479ebf8b9943f280dc6c5df9f 557d8f649b964bd81a1c022dd87db18bdca0c2b61e420c2eccb1fc446a58f7bf 37e64c63c294a3eda298c61f637087c84851afa17f42ad18a4d24c8823c7f686)
for n in 0 1 2 3; do
  /usr/bin/python3 -s $W/w544_launch.py $n >> $W/W544.log 2>&1; rc=$?
  p=$(printf 'k1_ops3_w544_p%02d' $n)
  [ -e $G/$p.json ] && mv $G/$p.json $G/$p.done.$(date +%s)
  [ $rc -eq 0 ] || { echo "part $n launcher rc=$rc; stop" >> $W/W544.log; exit 1; }
  f=$(printf '/scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part%02d-of-04' $n)
  h=$(nice sha256sum $f | cut -d' ' -f1)
  if [ "$h" = "${SHA[$n]}" ]; then echo "part $n sha OK $(date -u +%FT%TZ)" >> $W/W544.log; else echo "part $n SHA MISMATCH $h; stop" >> $W/W544.log; exit 1; fi
done
echo "ALL PARTS OK $(date -u +%FT%TZ)" >> $W/W544.log
