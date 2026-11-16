import csv
import socket
import subprocess

from .io import utc


def parse_card(gpu_text, process_text, run_host, actual_host):
    if not run_host or actual_host.split(".")[0] != run_host:
        raise PermissionError("The current host does not match --run-host")
    rows = list(csv.reader(gpu_text.strip().splitlines()))
    if len(rows) != 1 or len(rows[0]) != 5:
        raise ValueError("The selected card did not return a unique GPU record")
    index, uuid, name, total, used = [value.strip() for value in rows[0]]
    total, used = int(total), int(used)
    pids = []
    for row in csv.reader(process_text.strip().splitlines()):
        if not row:
            continue
        if len(row) != 2:
            raise ValueError("Unknown compute-process query format")
        if row[0].strip() == uuid:
            pids.append(int(row[1].strip()))
    if total*1024**2 < 48_000_000_000:
        raise RuntimeError("The selected card has less than 48 GB")
    if pids or used > 1024:
        raise RuntimeError(f"The selected card is not free: compute_pids={pids}, used_mib={used}")
    return {"host": run_host, "index": index, "uuid": uuid, "name": name,
            "total_mib": total, "used_mib": used, "compute_pids": pids}


def free_card(gpu, run_host):
    actual = socket.gethostname()
    if not run_host or actual.split(".")[0] != run_host:
        raise PermissionError("GPU admission requires the current --run-host")
    selected = subprocess.run(
        ["nvidia-smi", f"--id={gpu}", "--query-gpu=index,uuid,name,memory.total,memory.used",
         "--format=csv,noheader,nounits"], check=True, capture_output=True, text=True, timeout=15)
    processes = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=15)
    return {**parse_card(selected.stdout, processes.stdout, run_host, actual), "checked_at": utc()}
