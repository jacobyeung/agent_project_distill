R=/scratch/jjyeung/orch_n30; cd $R
F="sb_cachk/out/sb_cachk.tar sb_fhalias/out/sb_fhalias2.tar sb_fullinv/out/sb_fullinv2.tar sb_ktfix2/out/sb_ktfix4.tar sb_phfix/out/sb_phfix.tar sb_rlfix4/out/sb_rlfix4.tar"
nice -n 10 sha256sum $F > /tmp/sbm_local.txt; cat /tmp/sbm_local.txt | cut -c1-16,65-
tar cf - $F | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib 'mkdir -p /scratch/jjyeung/n30_mirror/swarm_build && tar xf - -C /scratch/jjyeung/n30_mirror/swarm_build && cd /scratch/jjyeung/n30_mirror/swarm_build && nice -n 10 sha256sum '"$F" > /tmp/sbm_remote.txt
diff /tmp/sbm_local.txt /tmp/sbm_remote.txt && echo MIRROR_MATCH
