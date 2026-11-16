cd /scratch/jjyeung/orch_n30/evalx27/work || exit 1
sha256sum kit/package.tar; cat kit/KIT_SHA256
tar cf - kit/package.tar kit/DIFF.md kit/PROOF_JOB.md kit/REPORT.md kit/KIT_SHA256 kit/cohort kit/parity kit_revsi/DIFF.md kit_revsi/F1_EVIDENCE.md kit_revsi/REPORT.md kit_revsi/media analyze_official.py analyze_revsi.py | ssh -o ConnectTimeout=20 trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b07_offread/in/x27 && cd /scratch/jjyeung/orch_n30/b07_offread/in/x27 && tar xf -"
echo TAR_RC=$?
