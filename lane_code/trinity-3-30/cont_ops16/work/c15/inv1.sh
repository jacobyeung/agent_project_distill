export TZ=UTC
echo "## host $(hostname -s) $(date -u +%FT%TZ)"
for p in /home/jjyeung/okit /home/jjyeung/okit/r /home/jjyeung/okit/x /home/jjyeung/okit/j /home/jjyeung/okit/r/5da50f2b /home/jjyeung/okit/x/07ca49df /home/jjyeung/okit/x/07ca49df/o; do echo "$p -> $(readlink -f $p)"; done
echo "## ls okit"; ls -la /home/jjyeung/okit | head -30
echo "## ls run root"; ls -la --time-style=+%FT%TZ /home/jjyeung/okit/r/5da50f2b | head -40
echo "## slot records"; for f in A.json B.json A.sha256 B.sha256 RUN.json binding.json.sha256 A.verify; do echo "-- $f"; head -c 1500 /home/jjyeung/okit/r/5da50f2b/$f 2>&1; echo; done
echo "## kit dir"; ls -la --time-style=+%FT%TZ /home/jjyeung/okit/x/07ca49df | head -30
echo "## o dir (169* and recent)"; ls -la --time-style=+%FT%TZ /home/jjyeung/okit/x/07ca49df/o | tail -40
echo "## hashes"; sha256sum /home/jjyeung/okit/j/07ca49df.sh /home/jjyeung/okit/x/07ca49df/job.sh /home/jjyeung/okit/x/07ca49df/b/r.sh /home/jjyeung/okit/x/07ca49df/b/c.sh 2>&1
echo "## w.steps tail"; tail -n 25 /home/jjyeung/okit/x/07ca49df/o/169097.w.steps 2>&1
echo "## steps tail"; tail -n 25 /home/jjyeung/okit/x/07ca49df/o/169097.steps 2>&1 | cut -c1-400
echo "## out tail"; tail -c 2500 /home/jjyeung/okit/x/07ca49df/o/169097.out 2>&1
echo "## c.sh"; head -c 6000 /home/jjyeung/okit/x/07ca49df/b/c.sh
echo "## df"; df -PB1 /project/community /home/jjyeung /tmp /var/tmp 2>&1; df -hT 2>/dev/null | grep -v -E 'tmpfs|overlay' | head -30
echo "## quota"; (quota -s 2>&1; command -v lfs >/dev/null && lfs quota -h -u jjyeung /home 2>&1) | head -20
echo "## sacct 169097"; sacct -j 169097 -X -o JobID,JobName%20,Partition,State,ExitCode,Start,End,Elapsed,AllocTRES%60 2>&1 | head
echo "## squeue mine"; squeue -u jjyeung -o '%.10i %.12P %.30j %.8T %.10M %.12l %.6D %R %b' 2>&1
echo "## squeue advanced"; squeue -p advanced -o '%.10i %.10u %.30j %.8T %.10M %.12l %b %R %Q' 2>&1 | head -30
echo "## squeue general mine/others count"; squeue -p general -h -o '%u %T' 2>&1 | sort | uniq -c | sort -rn | head
echo "## sinfo"; sinfo -p advanced,general -o '%P %a %l %D %t %G %N' 2>&1
echo "## assoc"; sacctmgr -n -P show assoc user=jjyeung format=account,partition,grptres,maxtres,maxtrespu,maxwall,qos 2>&1 | head; sacctmgr -n -P show qos format=name,grptres,maxtrespu,maxwall,maxjobspu 2>&1 | head -20
echo "## partition advanced"; scontrol show partition advanced 2>&1 | head -20
echo "## test-only"; cd /home/jjyeung/okit && env -u TK_JOB_START sbatch --test-only -J a15_cot_ap989d2aa9 /home/jjyeung/okit/j/07ca49df.sh 2>&1
echo "## end"
