export TZ=UTC; date -u +%TZ; mkdir -p ~/a15o/f23
for n in 0 1 2 3 4; do N=orchard-community-$n; echo "$N $(scontrol show node $N | grep -oE '(Arch|CPUTot|AvailableFeatures|ActiveFeatures|RealMemory|State|CPULoad|Sockets|CoresPerSocket|ThreadsPerCore)=[^ ]*' | tr '\n' ' ')"; done
cat > ~/a15o/f23/p.sh <<'PEOF'
#!/bin/bash
export TZ=UTC; echo "host $(hostname -s) $(date -u +%TZ)"
grep -m1 'model name' /proc/cpuinfo; echo "flags: $(grep -m1 '^flags' /proc/cpuinfo | grep -oE '\b(sha_ni|avx2|avx512f|vaes)\b' | sort -u | tr '\n' ' ')"; nproc --all; uptime
/usr/bin/python3 -I -c '
import hashlib,os,time,ssl
b=os.urandom(1<<30); m=memoryview(b); h=hashlib.sha256(); t=time.perf_counter()
for _ in range(4):
    for i in range(0,len(b),1<<20): h.update(m[i:i+(1<<20)])
s=time.perf_counter()-t; print("sha256 1MiB blocks: %.3f GB/s (%s)"%((4<<30)/s/1e9, ssl.OPENSSL_VERSION))'
PEOF
chmod 700 ~/a15o/f23/p.sh; dep=""
for n in 0 1 2 3 4; do
  j=$(sbatch --parsable -p preempt -w orchard-community-$n -N1 -n1 -c1 --mem=6G -t 00:05:00 $dep --job-name a15_cot_apc6b14e700ea2 -o ~/a15o/f23/p$n.out ~/a15o/f23/p.sh); echo "probe $n job $j"; dep="--dependency=afterany:$j"
done
squeue -u jjyeung -h -o '%i|%j|%T|%N|%r'
