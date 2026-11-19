import json
import os
import sys


ENVIRONMENT = "S1_CPU_REHEARSAL"
_announced = False


def enabled():
    global _announced
    value = os.environ.get(ENVIRONMENT, "0")
    if value not in ("0", "1"):
        raise ValueError(f"{ENVIRONMENT} must be 0 or 1")
    active = value == "1"
    if active and not _announced:
        print(json.dumps(dict(rehearsal=True, switch=ENVIRONMENT, device="cpu", backend="gloo",
                              production_authorized=False)), file=sys.stderr, flush=True)
        _announced = True
    return active


def attempt_id():
    return os.environ["S1_REHEARSAL_ATTEMPT"] if enabled() else os.environ["SLURM_JOB_ID"]
