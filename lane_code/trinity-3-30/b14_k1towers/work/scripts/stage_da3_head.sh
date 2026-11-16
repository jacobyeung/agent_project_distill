set -u
S=/dev/shm/jjyeung/b14; date -u
timeout 600 ssh -n -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "tar cf - -C /scratch/jjyeung geo_bakeoff_kit/assets/da3" | tar xf - -C $S && echo DA3_STAGED
du -sh $S; du -sh /dev/shm/jjyeung/b05 /dev/shm/jjyeung/b11_presence /dev/shm/jjyeung/exports
