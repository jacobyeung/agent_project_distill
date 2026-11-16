set -u
W=/scratch/jjyeung/orch_n30/k1_ops3
ip route get $(getent hosts trinity-3-30.ib | awk '{print $1}') | head -1
cd $W/work/partb
ls -la --time-style=+%FT%T . | head -80
echo "--- evidence top"; ls -la --time-style=+%FT%T build/evidence | head -80
echo "--- ret170193"; ls -la ret170193 2>&1 | head
tar cf - --exclude='build/evidence' --exclude='build/rh' --exclude='build/out/RH_RESULT.tar' --exclude='build/payload' \
   build/*.py build/*.txt build/*.md build/*.json build/*.sh build/*.jsonl build/*.diff build/packet build/reference build/manifest_v2 build/inputs build/out \
   $(ls -d build/evidence/REPORT6* 2>/dev/null) ret170193 $(ls -p | grep -v / ) -C $W kc \
 | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/k1_ops6/src118 && cd /scratch/jjyeung/orch_n30/k1_ops6/src118 && tar xf - && echo TAR_OK"
echo "pipe rc=${PIPESTATUS[*]}"
