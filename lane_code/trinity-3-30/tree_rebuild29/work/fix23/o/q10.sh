export TZ=UTC; date -u +%TZ; cd ~/a15o/f23
cat > l.sh <<'IN'
#!/bin/bash
export TZ=UTC; date -u +%TZ; hostname -s; ls -ld /tmp/a15_c6b1_174378 2>&1; df -B1 /tmp | tail -1
IN
chmod 700 l.sh; sbatch -p preempt -w orchard-community-3 -N1 -n1 -c1 --mem=1G -t 00:03:00 --job-name a15_cot_apc6b14e700ea2 -o ~/a15o/f23/l3.out ~/a15o/f23/l.sh
echo "=====MAIN"; grep -v 'error:' main_174378.out
for f in o_174378/*; do echo "=====$f"; cat $f; done
