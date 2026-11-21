"""Submit the CPU check and the GPU job to Orchard's debug partition.

The build writes PARTITION and QOS into the payload's submission contract
(orchard_h10/common.py), the retained template launcher
(orchard_h10/vendor/orchard_launcher.py) and the queue check in
orchard/o_check_sub.sh and orchard/o_sub_hand.sh. Every other Slurm flag is
unchanged; the CPU check still differs from the GPU job only by --gres.

debug allocates whole nodes (Exclusive=NODE). An exclusive allocation can
expose every GPU on the node, also to the CPU check, which requests none. The
bootstrap therefore runs the CPU check whenever this package has no CPU
receipt yet and hides the node's GPUs from it, and the GPU job runs on the
first of the GPUs it can see.
"""
PARTITION = 'debug'
QOS = 'debug_qos'
# Every job of this lane is named LANE_JOB_PREFIX + token.
LANE_JOB_PREFIX = 'a15_cot_ap'
# Variables through which Slurm exposes assigned GPUs to the batch step.
GPU_ENV = ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS', 'SLURM_GPUS_ON_NODE', 'GPU_DEVICE_ORDINAL')

OLD_QUEUE = "squeue -u jjyeung -p general -h > a/9.txt\ntest ! -s a/9.txt\n"
# Refuse only while a GPU job of this lane (any a15_cot_ap* job of the user,
# including this package's own) is already on the debug partition.
QUEUE = ("squeue -u jjyeung -p %s -h -o '%%j|%%b' > a/9.txt\n"
         "if grep -Eiq '^%s[^|]*[|].*gpu' a/9.txt; then exit 1; fi\n") % (PARTITION, LANE_JOB_PREFIX)

COMMON_CONSTANTS = ("POOL = '/project/community/jjyeung/okh7/ae71c903'\n"
                    "PARTITION = %r\nQOS = %r\n" % (PARTITION, QOS))

LAUNCHER_ADMISSION_OLD = '''def queue_admission(text, user):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    if any(len(row) != 5 for row in rows):
        raise ValueError('The general queue observation is malformed')
    if any(row[2] == user and 'gpu' in row[4].lower() for row in rows):
        raise ValueError('An existing user GPU job has the general queue; coordinate before submitting')
    return rows
'''
LAUNCHER_ADMISSION = '''def queue_admission(text, user):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    if any(len(row) != 5 for row in rows):
        raise ValueError('The %(p)s queue observation is malformed')
    if any(row[2] == user and row[1].startswith(LANE_JOB_PREFIX) and 'gpu' in row[4].lower() for row in rows):
        raise ValueError('A GPU job of this lane is already on the %(p)s partition; coordinate before submitting')
    return rows
''' % dict(p=PARTITION)

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
    pf['orchard_h10/common.py'] = common.encode()
    launcher = pf['orchard_h10/vendor/orchard_launcher.py'].decode()
    launcher = B.once(launcher, "\n\nROOT = Path(__file__).resolve().parent\n",
                      "\n\nPARTITION = %r\nQOS = %r\nLANE_JOB_PREFIX = %r\nROOT = Path(__file__).resolve().parent\n" % (PARTITION, QOS, LANE_JOB_PREFIX))
    launcher = B.once(launcher, "'--partition=general', '--nodes=1',", "'--partition='+PARTITION, '--qos='+QOS, '--nodes=1',")
    launcher = B.once(launcher, LAUNCHER_ADMISSION_OLD, LAUNCHER_ADMISSION)
    launcher = B.once(launcher, "['squeue', '-p', 'general', '-h',", "['squeue', '-p', PARTITION, '-h',")
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
