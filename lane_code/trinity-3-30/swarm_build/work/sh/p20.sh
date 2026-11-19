R=/scratch/jjyeung/orch_n30; cd $R
ls -la sb_cachk/out/sb_cachk.tar sb_ktfix2/out/sb_ktfix4.tar sb_fhalias/out/sb_fhalias2.tar sb_fullinv/out/sb_fullinv2.tar sb_phfix/out/sb_phfix.tar sb_rlfix4/out/sb_rlfix4.tar 2>&1 | awk '{print $5, $9}'
for n in trinity-1-13 trinity-0-28; do timeout 40 ssh -o ConnectTimeout=20 -o BatchMode=yes $n.ib "hostname -s; df -h /scratch | tail -1; ls -d /scratch/jjyeung/n30_mirror 2>&1; ls /scratch/jjyeung/n30_mirror 2>/dev/null | head" ; done
