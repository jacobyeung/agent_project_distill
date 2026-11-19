#!/bin/bash
# swarm_opt4: member lists of the staged archives on trinity-2-28 (local reads); writes $R/lists/, prints a tar of it on stdout
R=/scratch/jjyeung/orch_n30/reads228; D=$R/dl; L=$R/lists; mkdir -p $L
{ for n in ; do [ -f $D/$n.sha_ok ] && nice -n 10 tar tvf $D/$n > $L/$n.list 2>$L/$n.err; done
  if [ -f $D/s4e0b.sha_ok ] && [ $(ls $D/s4e[1-3].sha_ok | wc -l) = 3 ]; then cat $D/s4e0b $D/s4e1 $D/s4e2 $D/s4e3 | nice -n 10 tar tvf - > $L/s4e.list 2>$L/s4e.err; fi
  [ -f $D/a3.tar.sha_ok ] && mkdir -p $L/a3x && tar xf $D/a3.tar -C $L/a3x
  ls -la /scratch/jjyeung/b01ec87a6f29b/d/ /scratch/jjyeung/b01ec87a6f29b/d/k/ > $L/existing_d.txt 2>&1; true
  ls /scratch/jjyeung/envs/ > $L/envs.txt 2>&1; ls /data3/shared/scripts/vnice/ > $L/vnice_ls.txt 2>&1; sha256sum /data3/shared/scripts/vnice/vnice.sh /data3/shared/scripts/vnice/terminator.sh > $L/vnice.sha256 2>&1
  nvidia-smi > $L/nvidia_smi.txt 2>&1; /usr/bin/python3 -V > $L/sys_python.txt 2>&1; wc -l $L/*.list; } >&2
tar cf - -C $R lists
