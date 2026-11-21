W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; hostname -s; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls 2>&1 | grep -v iogov
du -sh $W 2>/dev/null; ls $W | head -50
for z in w24z13b w24z15 w24z16; do echo "=== $z"; ls -la $W/$z/out 2>&1 | tail -25; for s in $W/$z/out/*.sha256; do test -f $s && { echo SHA $s; cat $s; t=${s%.sha256}; sha256sum $t; }; done; cat $W/$z/out/BUILD*_REPORT.md 2>/dev/null | cut -c1-400; done
for l in b24m4z13b b24m4z15 b24m4z16; do echo "--- log $l"; tail -c 1500 $W/work/$l.log; echo; done
echo ARMLOG; ls -la $W/work/arm_0216Z.log; tail -c 2500 $W/work/arm_0216Z.log
ls $W/w24z11b/ | head; ls $W/w24z11b/a_zffhb1q8 2>&1 | head
