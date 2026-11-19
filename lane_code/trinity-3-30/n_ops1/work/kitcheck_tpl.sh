# n_ops1: read-only check of an uploaded launch kit for ORCH 1734Z items 1-3 / 1752Z item 5. Placeholder __KD__ (kit dir), __WR__ (wrapper file)
KD=__KD__; WR=__WR__; echo "@@KIT $KD"; ls -la $KD $KD/b $KD/k 2>&1 | head -80
echo "@@SUMS"; (cd $KD && sha256sum -c --quiet SHA256SUMS.txt 2>&1 | tail -3; echo "rc=$? lines=$(wc -l < SHA256SUMS.txt) files=$(find . -type f ! -name SHA256SUMS.txt | wc -l)")
echo "@@SBATCH_WRAPPER $WR"; grep -E '^#SBATCH|sbatch|job-name' $WR 2>&1
echo "@@SBATCH_JOBSH"; grep -E '^#SBATCH' $KD/job.sh
dec() { python3 -B -c "import json,base64,sys;v=json.load(open(sys.argv[1]));print(base64.b64decode(v['payload']).decode())" $KD/k/$1; }
echo "@@A"; dec a.json | head -c 1500; echo
echo "@@JJSON_GREP"; grep -n -E 'trap|TK_JOB_START|SIGUSR1|USR1|TERM|gsutil|gcloud|storage|copier|copy|cp |rsync|sleep 600|done|marker|\.done' <(dec j.json) | cut -c1-220 | head -60
echo "@@OPY"; cat $KD/b/o.py
echo "@@TAILJ"; tail -40 <(dec j.json) | cut -c1-300
