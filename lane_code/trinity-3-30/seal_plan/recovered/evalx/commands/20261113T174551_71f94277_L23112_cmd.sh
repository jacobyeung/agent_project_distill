<!-- recovered by seal_plan: transcript=71f94277 line=23112 utc=2026-11-13T17:45:51.222Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/ORCH_STATE_20261111T0935Z.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$F" <<'EOF'
import sys
f = sys.argv[1]
s = open(f).read()
old = "Unproven: full-population admission on Orchard (the production job is the gate), the 256 GiB native cap with a3v2, restored-state equality, a large upload, project-filesystem slot throughput, the routed reader on GPU."
new = ("Proven in job 169097: full-population data admission (mode p exit 0 at 17:26:18Z, 2 h after start, under the 256 GiB cap; pointing 20,239, pose 194,987, routing 57,136, VQA 114,904; orchard_cp2/out/DATA_ADMISSION_169097.json); training (mode t) launched 17:28:26Z. Project filesystem: 275 MB/s write, 284 MB/s re-read (job 169107); other tenants took ~120 GB of it between 16:15Z and 17:10Z (520 GB free at 17:41Z; alarms at 400/300/200 GB and on the rate; our removable footprint is ~16 GB). "
       "Unproven: restored-state equality (checker bundle leg_s1_canary/out/continuation_check_20261113T170656Z.tgz; fixture rehearsal on Orchard pre-authorized once), a large upload (the step-1 export is the first), the production slot size (read-only size step inside the job approved after step 1), the routed reader on GPU (evalx moves it to Trinity; export download approved under the user's 11-12 ruling). "
       "Contingency if no slot can be written: warm start from the last export (leg_s1_tree out/WARM_START_CONTINGENCY_07ca49df.md; needs a private source patch; no release without review and my word). No early-stop attempt (leg_s1_tree out/EARLY_SAVED_STOP_PATH_07ca49df.md: signal path unproven on GPU).")
assert s.count(old) == 1
s = s.replace(old, new)
old2 = "memory cap (default keep 256 GiB); "
assert s.count(old2) == 1
s = s.replace(old2, "")
s = s.replace("| leg_s1_tree (successor 6) |", "| leg_s1_tree (successor 7, relaunched 17:29Z after a provider failure) |")
open(f, "w").write(s)
print("ok")
EOF