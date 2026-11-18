<!-- recovered by seal_plan: transcript=71f94277 line=2976 utc=2026-11-11T14:35:24.630Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ) && T=$(date -u +%Y%m%dT%H%MZ) && m=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat > $m/data-reads-no-ask-20261111.md <<'EOF'
---
name: data-reads-no-ask-20261111
description: USER 2026-11-11 - reads from /data* need no approval unless they are on the order of a terabyte; the cluster's throttling rules still apply
metadata:
  type: feedback
---

The user, 2026-11-11 ~06:35 PT, when I asked whether a lane may read 4.6 GB of scene assets from /data2: "Yes of course. You can always read from data too. Don't ask me. Unless you know you're reading like a terabyte or something."

**Why:** asking for small reads wastes the user's time; I had set myself a 2 GB ask-first limit after noticing that the admin rules ("ask before any heavy IO") and an older note ([[aws-pull-under-100gb-approved]]) disagreed.

**How to apply:** approve lanes' reads from /data* myself, whatever their size below roughly a terabyte, and ask the user only near that scale. The cluster's rates still bind every read: one copy at a time, 8 MB/s for reads, archives or a single tar stream, through the IO governor, 20 MB/s per user in total, main's copies first ([[io-governor-copy-archive]], [[trinity-thrash-penalties]]). Writes to /data* and deletions are unchanged: governed archives only, and only the user deletes.
EOF
echo '- **READ FIRST, USER 11-11:** [Reads from /data* need no ask](data-reads-no-ask-20261111.md) approve them myself below ~1 TB; throttling and the governor still apply' >> $m/MEMORY.md
cat > dose_pool/inbox/${T}_ORCH_T1_read_approved.md <<EOF
# ORCH ($NOW): the T1 read is approved by the user; go
- The user: "Yes of course. You can always read from data too. Don't ask me. Unless you know you're reading like a terabyte or something." Read the 4.6 GB of compact stagec assets for the 877 T1 scenes as ONE governed tar stream at 8 MB/s or less (through /scratch/jjyeung/io_governor/copy_archive.py --job, behind main's copies) into /dev/shm or /scratch, whichever has room (check first: /dev/shm has about 26 GB free), then run the CPU raycast and generate head-backed traces for T1 exactly as for T0 (same acceptance: every row replays to its ground truth; five rows per type quoted for me to read; first batch on every rank with no checkpoint saved).
- ScanNet++ raw for the 162 T2 scenes (about 20 GB) is also allowed on the same terms after T1, if your T0 and T1 results show the generator works. The ScanNet sensor files (about 1 TB) are not.
- Rates and the one-stream rule still bind; print \`du -s\` of your folder in STATUS.md after each step.
EOF
python3 - <<'EOF'
d='/data2/jjyeung/agent_project_data/'
o=d+'SAVED_USER_QUESTIONS.md'; a=d+'SAVED_USER_QUESTIONS_ANSWERED.md'
L=open(o).read().split('\n'); keep=[]; moved=0
for l in L:
    if '[orch-home-distill-79]' in l and ('Disk: please remove 169 GB' in l or 'Downloads and copies: your admin rules' in l or 'Five owner-only copies of the Devin authentication file' in l):
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        if 'Disk: please remove' in l: ans='USER 14:3xZ: removed all 169 GB; and "Yes of course. You can always read from data too. Do not ask me. Unless you know you are reading like a terabyte or something." The 4.6 GB read is approved.'
        elif 'Downloads and copies' in l: ans='USER 14:35Z: reads from /data* need no ask unless near a terabyte (memory data-reads-no-ask-20261111); the cluster rates still apply.'
        else: ans='USER 14:3xZ removed the five credential copies. The 62,864-row decode question in the same row stays with its default (left out); superseded by the frame-level scope (dose_pool 1452Z).'
        open(a,'a').write(f'| USER | {c[0]} | {c[1]} | {ans} |\n'); moved+=1
    else: keep.append(l)
open(o,'w').write('\n'.join(keep)); print('moved',moved)
EOF
echo "$NOW orch-home-distill-79: USER ~14:35Z: 'Yes of course. You can always read from data too. Don't ask me. Unless you know you're reading like a terabyte or something.' Memory data-reads-no-ask-20261111 (my 2 GB ask-first limit is withdrawn; rates and governor still apply). dose_pool told: T1 read (4.6 GB) approved, then ScanNet++ raw (20 GB) if T0/T1 work. Three saved-question rows moved to ANSWERED." >> ORCH_HANDOFF.md