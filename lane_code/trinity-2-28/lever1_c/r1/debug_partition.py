"""Scheduler placement for the CPU check and the GPU job (Orchard preempt).

The build writes PARTITION, QOS and EXCLUDE into the payload's submission
contract (orchard_h10/common.py) and PARTITION and QOS into the retained
template launcher (orchard_h10/vendor/orchard_launcher.py); it writes the
queue check into orchard/o_check_sub.sh and orchard/o_sub_hand.sh. Every other
Slurm flag is unchanged; the CPU check still differs from the GPU job only by
--gres. EXCLUDE keeps the job on the orchard-community H100 nodes.

preempt requeues preempted jobs; with --no-requeue a preemption ends the job.
Slurm then signals every process with SIGTERM: the supervisor forwards it,
publishes its failure receipt and exits, and the batch shell's TERM trap then
records status 143 in a/21, so fetch can recover even when the supervisor was
killed before publishing. o_fetch.sh records the scheduler's final state and
names it in every report on a missing receipt.

An exclusive allocation can expose every GPU on the node, also to the CPU
check, which requests none. The bootstrap therefore runs the CPU check
whenever this package has no CPU receipt yet and hides the node's GPUs from
it, and the GPU job runs on the first of the GPUs it can see. On a shared node
both rules are no-ops.
"""
PARTITION = 'preempt'
QOS = 'preempt_qos'
EXCLUDE = 'orchard-community-4,orchard-flame-[0-31]'
# Every job of this lane is named LANE_JOB_PREFIX + token.
LANE_JOB_PREFIX = 'a15_cot_ap'
# Variables through which Slurm exposes assigned GPUs to the batch step.
GPU_ENV = ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS', 'SLURM_GPUS_ON_NODE', 'GPU_DEVICE_ORDINAL')

OLD_QUEUE = "squeue -u jjyeung -p general -h > a/9.txt\ntest ! -s a/9.txt\n"
# Refuse while any job named for this package exists in any state on any
# partition, except this package's own CPU check (a/4.txt), or if squeue fails.
QUEUE = ("cpu=$(cat a/4.txt); [[ \"$cpu\" =~ ^[0-9]+$ ]]\n"
         "squeue -u jjyeung -h -t all -o '%%i|%%j' > a/9.txt\n"
         "if awk -F'|' -v cpu=\"$cpu\" -v name=\"%s${P##*/}\" '$2==name && $1!=cpu{f=1} END{exit !f}' a/9.txt; then exit 1; fi\n") % LANE_JOB_PREFIX
# Fetch records the scheduler's final state before reading receipts.
FETCH_STATE_OLD = "test ! -e a/f\n"
FETCH_STATE = "test ! -e a/f\ntimeout 60 sacct -j \"$job\" -X -n -P -o JobID,State,ExitCode > a/12.txt 2>&1 || true\n"
FETCH_RECOVER_OLD = "if not (source/'RETURN_RECEIPT.json').exists():runpy.run_path(str(p/'a/29.py'))['recover'](p,job)\n"
FETCH_RECOVER = ("state=(p/'a/12.txt').read_text(errors='replace').strip()[:400] if (p/'a/12.txt').exists() else 'unknown'\n"
                 "sys.stderr.write('scheduler state: '+state+'\\n')\n"
                 "if not (source/'RETURN_RECEIPT.json').exists():\n"
                 "    try:runpy.run_path(str(p/'a/29.py'))['recover'](p,job)\n"
                 "    except Exception as error:raise SystemExit('E85: job '+job+' left no receipt and no nonzero trap record (scheduler state: '+state+'; '+type(error).__name__+': '+str(error)[:200]+')')\n")

COMMON_CONSTANTS = ("POOL = '/project/community/jjyeung/okh7/ae71c903'\n"
                    "PARTITION = %r\nQOS = %r\nEXCLUDE = %r\n" % (PARTITION, QOS, EXCLUDE))

LAUNCHER_ADMISSION_OLD = '''def queue_admission(text, user):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    if any(len(row) != 5 for row in rows):
        raise ValueError('The general queue observation is malformed')
    if any(row[2] == user and 'gpu' in row[4].lower() for row in rows):
        raise ValueError('An existing user GPU job has the general queue; coordinate before submitting')
    return rows
'''
LAUNCHER_ADMISSION = '''def queue_admission(text, user, name):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    if any(len(row) != 5 for row in rows):
        raise ValueError('The queue observation is malformed')
    if any(row[2] == user and row[1] == name for row in rows):
        raise ValueError('A job named '+name+' already exists; never submit this package twice')
    return rows
'''

BOOT_OLD = b" if not os.environ.get('SLURM_JOB_GPUS') and not os.environ.get('CUDA_VISIBLE_DEVICES'):\n"
BOOT_NEW = (b" if not (os.environ.get('SLURM_JOB_GPUS') or os.environ.get('CUDA_VISIBLE_DEVICES')) or not (shared/'a/c/CPU.json').exists():\n"
            b"  # Exclusive debug nodes can expose GPUs to the CPU check; hide them.\n"
            b"  for key in " + repr(GPU_ENV).encode() + b":os.environ.pop(key,None)\n"
            b"  os.environ['CUDA_VISIBLE_DEVICES']=''\n")

JOB_CARDS_OLD = "        cards=os.environ.get('CUDA_VISIBLE_DEVICES','').split(',')\n"
JOB_CARDS_NEW = "        assigned=os.environ.get('CUDA_VISIBLE_DEVICES','');cards=select_cards(assigned,n)\n"
JOB_EVIDENCE_OLD = "write(out/'metadata/CARDS.json',dict(visible=cards,query=evidence.stdout))"
JOB_EVIDENCE_NEW = "write(out/'metadata/CARDS.json',dict(visible=cards,assigned=assigned.split(','),query=evidence.stdout))"
JOB_HELPER = '''def select_cards(value, n):
    """Exclusive debug nodes can assign every GPU; the job uses the first n."""
    cards=value.split(',')
    return cards[:n] if all(cards) else cards


def main(root):
'''


def patch(nf, pf, B):
    common = pf['orchard_h10/common.py'].decode()
    common = B.once(common, "POOL = '/project/community/jjyeung/okh7/ae71c903'\n", COMMON_CONSTANTS)
    common = B.once(common, "'--partition=general', '--nodes=1',", "'--partition='+PARTITION, '--qos='+QOS, '--nodes=1',")
    common = B.once(common, "'--exclude=orchard-community-4',", "'--exclude='+EXCLUDE,")
    pf['orchard_h10/common.py'] = common.encode()
    launcher = pf['orchard_h10/vendor/orchard_launcher.py'].decode()
    launcher = B.once(launcher, "\n\nROOT = Path(__file__).resolve().parent\n",
                      "\n\nPARTITION = %r\nQOS = %r\nLANE_JOB_PREFIX = %r\nROOT = Path(__file__).resolve().parent\n" % (PARTITION, QOS, LANE_JOB_PREFIX))
    launcher = B.once(launcher, "'--partition=general', '--nodes=1',", "'--partition='+PARTITION, '--qos='+QOS, '--nodes=1',")
    launcher = B.once(launcher, LAUNCHER_ADMISSION_OLD, LAUNCHER_ADMISSION)
    launcher = B.once(launcher, "queue = remote(['squeue', '-p', 'general', '-h', '-o', '%i|%j|%u|%T|%b'], text=True)",
                      "queue = remote(['squeue', '-u', 'jjyeung', '-h', '-t', 'all', '-o', '%i|%j|%u|%T|%b'], text=True)")
    launcher = B.once(launcher, "queue_admission(queue.stdout, 'jjyeung')", "queue_admission(queue.stdout, 'jjyeung', LANE_JOB_PREFIX+config['token'])")
    if 'general' in launcher or 'general' in common:
        raise ValueError('general partition remains')
    pf['orchard_h10/vendor/orchard_launcher.py'] = launcher.encode()
    job = pf['orchard_h10/job.py'].decode()
    job = B.once(job, JOB_CARDS_OLD, JOB_CARDS_NEW)
    job = B.once(job, JOB_EVIDENCE_OLD, JOB_EVIDENCE_NEW)
    job = B.once(job, "\ndef main(root):\n", "\n" + JOB_HELPER)
    pf['orchard_h10/job.py'] = job.encode()


def bootstrap(data):
    if data.count(BOOT_OLD) != 1:
        raise ValueError('bootstrap mode test differs')
    return data.replace(BOOT_OLD, BOOT_NEW)


def scripts(text):
    if text.count(OLD_QUEUE) != 1:
        raise ValueError('queue check differs')
    return text.replace(OLD_QUEUE, QUEUE)


def fetch(text):
    for old, new in ((FETCH_STATE_OLD, FETCH_STATE), (FETCH_RECOVER_OLD, FETCH_RECOVER)):
        if text.count(old) != 1:
            raise ValueError('fetch differs')
        text = text.replace(old, new)
    return text


def batch_header(text, token):
    """Record a nonzero trap status when Slurm terminates the batch shell."""
    anchor = "' EXIT\n"
    if text.count(anchor) != 1:
        raise ValueError('batch header differs')
    term = ("trap 'trap - ERR EXIT TERM; printf \"%s %s %s\\n\" 143 \"$LINENO\" \"${SLURM_JOB_ID:-0}\" >>"
            "/project/community/jjyeung/" + token + "/a/21; exit 143' TERM\n")
    return text.replace(anchor, anchor + term)
