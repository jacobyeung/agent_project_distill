import os
from pathlib import Path


ORIGINAL_PREFIXES = {
    "/scratch/jjyeung/orch_cd/gt_ceiling/work": "gt_ceiling_work",
    "/scratch/jjyeung/orch_cd/toolprog/work": "toolprog_work",
    "/scratch/jjyeung/orch_cd/toolprog/data/scannet_gt/raw": "scannet_raw",
    "/scratch/jjyeung/orch_cd/ttower/work": "ttower_work",
    "/scratch/jjyeung/orch_cd/grd_selector/work/setsel/data": "selector",
    "/scratch/jjyeung/orch_cd/grd_selector/out/price2_vsi": "selector_config",
    "/dev/shm/jjyeung_mdg_next/recache_vsi": "selector_raw",
    "/scratch/jjyeung/orch_cd/frames/work/harness": "frame_contract",
    "/scratch/jjyeung/orch_cd/tower_read/work/inputs": "fixture",
    "/scratch/jjyeung/orch_cd/official_reads/ref": "direct",
    "/scratch/jjyeung/orch_cd/aws_32/a_build/eval/orchard_bin/cp4tk_eval/official": "official",
}


def mapped(value):
    root = os.environ.get("GEO_BAKEOFF_DATA_ROOT")
    if not root or not isinstance(value, str):
        return value
    for old, relative in sorted(ORIGINAL_PREFIXES.items(), key=lambda item: -len(item[0])):
        if value == old or value.startswith(old + "/"):
            return str(Path(root) / relative) + value[len(old):]
    return value


def path(value):
    return Path(mapped(str(value)))
